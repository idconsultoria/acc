"""Rotas para gerenciamento de Conversas."""
from fastapi import APIRouter, HTTPException
from app.api.dto import MessageDTO, CreateMessagePayload, CitedSourceDTO, ConversationTopicDTO
from app.domain.conversations.workflows import continue_conversation
from app.domain.shared_kernel import ConversationId, MessageId
from app.infrastructure.persistence.conversations_repo import ConversationsRepository
from app.infrastructure.persistence.knowledge_repo import KnowledgeRepository
from app.infrastructure.persistence.agent_settings_repo import AgentSettingsRepository
from app.infrastructure.ai.gemini_service import GeminiService, get_gemini_api_key
from app.infrastructure.ai.embedding_service import EmbeddingGenerator
from app.infrastructure.ai.topic_classifier import TopicClassifier
from app.infrastructure.persistence.topics_repo import TopicsRepository
from app.infrastructure.persistence.config import GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY
from app.domain.shared_kernel import TopicId
from supabase import create_client
import uuid
from datetime import datetime

router = APIRouter()

# Inicializa repositórios
conversations_repo = ConversationsRepository()
knowledge_repo = KnowledgeRepository()
agent_settings_repo = AgentSettingsRepository()
topics_repo = TopicsRepository()

# Valida chaves antes de inicializar
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY deve estar configurado no arquivo .env")


@router.post("/conversations")
async def create_conversation():
    """Inicia uma nova conversa."""
    conversation = await conversations_repo.create()
    
    return {"conversation_id": str(conversation.id)}


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageDTO])
async def get_conversation_messages(conversation_id: str):
    """Lista as mensagens de uma conversa."""
    try:
        conversation_id_uuid = ConversationId(uuid.UUID(conversation_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    conversation = await conversations_repo.find_by_id(conversation_id_uuid)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    
    return [
        MessageDTO(
            id=msg.id,
            conversation_id=msg.conversation_id,
            author=msg.author.name,
            content=msg.content,
            cited_sources=[
                CitedSourceDTO(
                    artifact_id=cs.artifact_id,
                    title=cs.title,
                    chunk_content_preview=cs.chunk_content_preview
                )
                for cs in msg.cited_sources
            ],
            created_at=msg.created_at
        )
        for msg in conversation.messages
    ]


@router.post("/conversations/{conversation_id}/messages", response_model=MessageDTO)
async def post_message(conversation_id: str, payload: CreateMessagePayload):
    """Envia uma nova mensagem para o agente."""
    try:
        conversation_id_uuid = ConversationId(uuid.UUID(conversation_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    # Busca a conversa
    conversation = await conversations_repo.find_by_id(conversation_id_uuid)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    
    # Obtém a instrução do agente
    agent_instruction = await agent_settings_repo.get_instruction()
    
    # Obtém a chave de API (personalizada ou padrão)
    api_key = await get_gemini_api_key()
    gemini_service = GeminiService(api_key)
    embedding_generator = EmbeddingGenerator(api_key)
    
    # Continua a conversa (gera resposta do agente)
    updated_conversation = await continue_conversation(
        conversation=conversation,
        user_query=payload.content,
        embedding_generator=embedding_generator,
        knowledge_repo=knowledge_repo,
        llm_service=gemini_service,
        agent_instruction=agent_instruction
    )
    
    # Verifica se esta é a primeira resposta do agente ANTES de salvar
    # (verifica se não havia mensagens do agente na conversa antes desta)
    old_agent_messages = [msg for msg in conversation.messages if msg.author.value == 2]
    is_first_agent_response = len(old_agent_messages) == 0
    
    # Salva as mensagens
    await conversations_repo.save_messages(updated_conversation)
    
    # Classifica a conversa por tópico se for a primeira resposta do agente
    if is_first_agent_response:
        print(f"[TOPIC] Primeira resposta do agente detectada para conversa {conversation_id_uuid}")
        # Busca a primeira mensagem do usuário e do agente na conversa atualizada
        user_messages = [msg for msg in updated_conversation.messages if msg.author.value == 1]
        agent_messages = [msg for msg in updated_conversation.messages if msg.author.value == 2]
        
        print(f"[TOPIC] Mensagens encontradas: {len(user_messages)} do usuário, {len(agent_messages)} do agente")
        
        if user_messages and agent_messages:
            # Busca todos os tópicos existentes
            existing_topics = await topics_repo.find_all()
            existing_topic_names = [topic.name for topic in existing_topics]
            print(f"[TOPIC] Tópicos existentes: {existing_topic_names}")
            
            # Classifica a conversa usando a primeira troca
            user_query = user_messages[0].content
            agent_response = agent_messages[0].content
            print(f"[TOPIC] Classificando conversa. Query: {user_query[:100]}...")
            
            # Cria o classificador com a chave de API
            topic_classifier = TopicClassifier(api_key)
            
            try:
                topic_name = await topic_classifier.classify_conversation(
                    user_query=user_query,
                    agent_response=agent_response,
                    existing_topics=existing_topic_names
                )
                print(f"[TOPIC] Tópico classificado: '{topic_name}'")
                
                # Busca ou cria o tópico
                topic = await topics_repo.find_by_name(topic_name)
                if not topic:
                    print(f"[TOPIC] Criando novo tópico: '{topic_name}'")
                    topic = await topics_repo.create(topic_name)
                    print(f"[TOPIC] Tópico criado com ID: {topic.id}")
                else:
                    print(f"[TOPIC] Tópico já existe: {topic.name} (ID: {topic.id})")
                
                # Atualiza a conversa com o tópico
                print(f"[TOPIC] Atualizando conversa {conversation_id_uuid} com tópico {topic.id}")
                await conversations_repo.update_topic(conversation_id_uuid, topic.id)
                print(f"[TOPIC] Conversa atualizada com sucesso")
                
                # Gera título e resumo básicos
                title = user_query.split('\n')[0][:100]
                summary = agent_response[:300] + ("..." if len(agent_response) > 300 else "")
                await conversations_repo.update_summary_and_title(
                    conversation_id_uuid,
                    summary=summary,
                    title=title
                )
                print(f"[TOPIC] Título e resumo atualizados")
            except Exception as e:
                # Em caso de erro na classificação, loga mas não interrompe o fluxo
                print(f"[TOPIC] Erro ao classificar conversa por tópico: {e}")
                import traceback
                traceback.print_exc()
    
    # Retorna a última mensagem (do agente)
    agent_message = updated_conversation.messages[-1]
    
    return MessageDTO(
        id=agent_message.id,
        conversation_id=agent_message.conversation_id,
        author=agent_message.author.name,
        content=agent_message.content,
        cited_sources=[
            CitedSourceDTO(
                artifact_id=cs.artifact_id,
                title=cs.title,
                chunk_content_preview=cs.chunk_content_preview
            )
            for cs in agent_message.cited_sources
        ],
        created_at=agent_message.created_at
    )


@router.get("/conversations/{conversation_id}/topic", response_model=ConversationTopicDTO)
async def get_conversation_topic(conversation_id: str):
    """Busca o tópico de uma conversa."""
    try:
        conversation_id_uuid = ConversationId(uuid.UUID(conversation_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    # Busca a conversa para verificar se tem mensagens do agente
    conversation = await conversations_repo.find_by_id(conversation_id_uuid)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    
    # Verifica se tem mensagens do agente (primeira resposta já foi dada)
    agent_messages = [msg for msg in conversation.messages if msg.author.value == 2]
    has_agent_response = len(agent_messages) > 0
    
    if not has_agent_response:
        # Se ainda não tem resposta do agente, não tem tópico ainda
        return ConversationTopicDTO(topic=None, is_processing=False)
    
    # Busca o tópico no banco
    topic = None
    is_processing = False
    
    try:
        if SUPABASE_URL and SUPABASE_KEY:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            conv_row = supabase.table("conversations").select("topic_id").eq("id", str(conversation_id_uuid)).execute()
            
            if conv_row.data and conv_row.data[0]:
                topic_id_from_db = conv_row.data[0].get("topic_id")
                
                if topic_id_from_db:
                    # Tópico já foi definido
                    topic_id_uuid = TopicId(uuid.UUID(topic_id_from_db))
                    topic_obj = await topics_repo.find_by_id(topic_id_uuid)
                    if topic_obj:
                        topic = topic_obj.name
                else:
                    # Tópico ainda não foi definido (processando)
                    is_processing = True
    except Exception:
        # Em caso de erro, assume que está processando
        is_processing = True
    
    return ConversationTopicDTO(topic=topic, is_processing=is_processing)

