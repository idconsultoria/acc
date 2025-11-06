"""Rotas para gerenciamento de Tópicos."""
from fastapi import APIRouter, HTTPException
from app.api.dto import TopicDTO, ConversationSummaryDTO
from app.domain.shared_kernel import TopicId
from app.infrastructure.persistence.topics_repo import TopicsRepository
from app.infrastructure.persistence.conversations_repo import ConversationsRepository
from app.infrastructure.persistence.config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client
import uuid

router = APIRouter()

# Inicializa repositórios
topics_repo = TopicsRepository()
conversations_repo = ConversationsRepository()


@router.get("/topics", response_model=list[TopicDTO])
async def list_topics():
    """Lista todos os tópicos com contagem de conversas."""
    # Usa agregação SQL para contar conversas de uma vez, evitando N+1 queries
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Busca tópicos com contagem de conversas usando agregação
        # Usa uma query SQL para contar conversas por tópico de uma vez
        topics_result = supabase.table("topics").select("id, name").order("name").execute()
        
        # Busca contagem de conversas por tópico em uma única query
        conversations_count_result = supabase.table("conversations").select("topic_id").execute()
        
        # Cria um dicionário com contagem de conversas por tópico
        topic_counts = {}
        for conv in conversations_count_result.data:
            topic_id = conv.get("topic_id")
            if topic_id:
                topic_counts[topic_id] = topic_counts.get(topic_id, 0) + 1
        
        # Monta a resposta
        topics_with_counts = []
        for topic_row in topics_result.data:
            topic_id = topic_row["id"]
            topics_with_counts.append({
                "id": topic_id,
                "name": topic_row["name"],
                "conversation_count": topic_counts.get(topic_id, 0)
            })
        
        return topics_with_counts
    except Exception:
        # Fallback para método antigo em caso de erro
        topics = await topics_repo.find_all()
        topics_with_counts = []
        for topic in topics:
            conversations = await conversations_repo.find_by_topic(topic.id)
            topics_with_counts.append({
                "id": str(topic.id),
                "name": topic.name,
                "conversation_count": len(conversations)
            })
        return topics_with_counts


@router.get("/topics/conversations", response_model=list[ConversationSummaryDTO])
async def get_conversations_all():
    """Busca resumos de todas as conversas."""
    return await _get_conversations_by_topic(None)


@router.get("/topics/{topic_id}/conversations", response_model=list[ConversationSummaryDTO])
async def get_conversations_by_topic(topic_id: str):
    """Busca resumos de conversas por tópico."""
    if topic_id == "null" or topic_id == "all":
        topic_id_uuid = None
    else:
        try:
            topic_id_uuid = TopicId(uuid.UUID(topic_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="ID de tópico inválido")
    
    return await _get_conversations_by_topic(topic_id_uuid)


async def _get_conversations_by_topic(topic_id_uuid: TopicId | None):
    """Função auxiliar para buscar conversas por tópico."""
    # Otimizado: busca tudo em uma única query com JOINs ao invés de múltiplas queries
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Monta a query base
        query = supabase.table("conversations").select("id, title, summary, topic_id, created_at, topics(name)")
        
        # Filtra por tópico se especificado
        if topic_id_uuid is not None:
            query = query.eq("topic_id", str(topic_id_uuid))
        
        # Ordena por data de criação (mais recente primeiro)
        query = query.order("created_at", desc=True)
        
        result = query.execute()
        
        # Se não tem título/resumo, precisa buscar mensagens
        conversations_needing_messages = []
        summaries = []
        
        for row in result.data:
            conv_id = row["id"]
            title = row.get("title")
            summary = row.get("summary")
            topic_name = None
            
            # Extrai nome do tópico do join
            if row.get("topics"):
                if isinstance(row["topics"], dict):
                    topic_name = row["topics"].get("name")
                elif isinstance(row["topics"], list) and row["topics"]:
                    topic_name = row["topics"][0].get("name")
            
            # Se não tem título ou resumo, precisa buscar mensagens
            if not title or not summary:
                conversations_needing_messages.append((conv_id, row))
                continue
            
            summaries.append({
                "id": conv_id,
                "title": title,
                "summary": summary,
                "topic": topic_name,
                "created_at": row["created_at"]
            })
        
        # Busca mensagens apenas para conversas que precisam
        if conversations_needing_messages:
            conv_ids = [conv_id for conv_id, _ in conversations_needing_messages]
            
            # Busca primeira mensagem do usuário e do agente para cada conversa
            for conv_id, row in conversations_needing_messages:
                try:
                    messages_result = supabase.table("messages").select("author, content").eq("conversation_id", conv_id).order("created_at").limit(10).execute()
                    
                    user_message = None
                    agent_message = None
                    
                    for msg in messages_result.data:
                        if msg["author"] == "USER" and not user_message:
                            user_message = msg
                        elif msg["author"] == "AGENT" and not agent_message:
                            agent_message = msg
                        if user_message and agent_message:
                            break
                    
                    title = row.get("title")
                    summary = row.get("summary")
                    
                    if not title and user_message:
                        title = user_message["content"].split('\n')[0][:100]
                    if not summary and agent_message:
                        summary = agent_message["content"][:300] + ("..." if len(agent_message["content"]) > 300 else "")
                    
                    if title and summary:
                        topic_name = None
                        if row.get("topics"):
                            if isinstance(row["topics"], dict):
                                topic_name = row["topics"].get("name")
                            elif isinstance(row["topics"], list) and row["topics"]:
                                topic_name = row["topics"][0].get("name")
                        
                        summaries.append({
                            "id": conv_id,
                            "title": title,
                            "summary": summary,
                            "topic": topic_name,
                            "created_at": row["created_at"]
                        })
                except Exception:
                    # Ignora erros e continua
                    pass
        
        return summaries
    except Exception:
        # Fallback para método antigo
        conversations = await conversations_repo.find_by_topic(topic_id_uuid)
        summaries = []
        for conv in conversations:
            if not conv.messages:
                continue
            
            user_message = next((msg for msg in conv.messages if msg.author.value == 1), None)
            agent_message = next((msg for msg in conv.messages if msg.author.value == 2), None)
            
            if not user_message or not agent_message:
                continue
            
            title = user_message.content.split('\n')[0][:100]
            summary = agent_message.content[:300] + ("..." if len(agent_message.content) > 300 else "")
            
            summaries.append({
                "id": str(conv.id),
                "title": title,
                "summary": summary,
                "topic": None,
                "created_at": conv.created_at.isoformat()
            })
        return summaries

