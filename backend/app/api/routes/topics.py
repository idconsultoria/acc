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
    topics = await topics_repo.find_all()
    
    # Para cada tópico, conta quantas conversas tem
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
    # Cria cliente Supabase temporário para buscar dados da conversa
    supabase = None
    try:
        if SUPABASE_URL and SUPABASE_KEY:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        pass
    
    conversations = await conversations_repo.find_by_topic(topic_id_uuid)
    
    # Converte para DTOs de resumo
    summaries = []
    for conv in conversations:
        if not conv.messages:
            continue
        
        # Busca título e resumo do banco, ou gera a partir das mensagens
        title = None
        summary = None
        
        if supabase:
            try:
                conv_row = supabase.table("conversations").select("title, summary, topic_id").eq("id", str(conv.id)).execute()
                if conv_row.data and conv_row.data[0]:
                    title = conv_row.data[0].get("title")
                    summary = conv_row.data[0].get("summary")
            except Exception:
                pass
        
        # Se não encontrou no banco, gera a partir das mensagens
        if not title or not summary:
            user_message = next((msg for msg in conv.messages if msg.author.value == 1), None)
            agent_message = next((msg for msg in conv.messages if msg.author.value == 2), None)
            
            if not user_message or not agent_message:
                continue
            
            if not title:
                title = user_message.content.split('\n')[0][:100]
            if not summary:
                summary = agent_message.content[:300] + ("..." if len(agent_message.content) > 300 else "")
        
        # Busca o tópico da conversa no banco
        topic = None
        if supabase:
            try:
                conv_row = supabase.table("conversations").select("topic_id").eq("id", str(conv.id)).execute()
                if conv_row.data and conv_row.data[0].get("topic_id"):
                    topic_id_from_db = TopicId(uuid.UUID(conv_row.data[0]["topic_id"]))
                    topic_obj = await topics_repo.find_by_id(topic_id_from_db)
                    if topic_obj:
                        topic = topic_obj.name
            except Exception:
                pass
        
        summaries.append({
            "id": str(conv.id),
            "title": title,
            "summary": summary,
            "topic": topic,
            "created_at": conv.created_at.isoformat()
        })
    
    return summaries

