"""Rotas para gerenciamento de Feedbacks."""
from fastapi import APIRouter, HTTPException
from app.api.dto import PendingFeedbackDTO, SubmitFeedbackPayload, BatchFeedbackRequestDTO
from app.domain.feedbacks.workflows import submit_feedback, approve_feedback, reject_feedback
from app.domain.feedbacks.types import FeedbackStatus
from app.domain.shared_kernel import FeedbackId, MessageId
from app.infrastructure.persistence.feedbacks_repo import FeedbacksRepository
from app.infrastructure.persistence.conversations_repo import ConversationsRepository
from app.infrastructure.persistence.learnings_repo import LearningsRepository
from app.domain.learnings.workflows import synthesize_learning_from_feedback
from app.infrastructure.ai.gemini_service import GeminiService, get_gemini_api_key
from app.infrastructure.ai.embedding_service import EmbeddingGenerator
from app.infrastructure.persistence.config import GEMINI_API_KEY
import uuid

router = APIRouter()

# Inicializa repositórios
feedbacks_repo = FeedbacksRepository()
conversations_repo = ConversationsRepository()
learnings_repo = LearningsRepository()


@router.post("/messages/{message_id}/feedback", response_model=PendingFeedbackDTO, status_code=201)
async def submit_feedback_route(message_id: str, payload: SubmitFeedbackPayload):
    """Envia feedback sobre uma mensagem do agente."""
    try:
        message_id_uuid = MessageId(uuid.UUID(message_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    # Verifica se a mensagem existe
    # Por enquanto, apenas cria o feedback
    
    feedback = await submit_feedback(
        message_id=message_id_uuid,
        feedback_text=payload.feedback_text,
        feedback_repo=feedbacks_repo,
        feedback_type=payload.feedback_type
    )
    
    return PendingFeedbackDTO(
        id=feedback.id,
        message_id=feedback.message_id,
        feedback_text=feedback.feedback_text,
        status=feedback.status.name,
        created_at=feedback.created_at,
        message_preview=None,
        feedback_type=feedback.feedback_type
    )


@router.get("/feedbacks/pending", response_model=list[PendingFeedbackDTO])
async def list_pending_feedbacks():
    """Lista todos os feedbacks pendentes de moderação."""
    feedbacks = await feedbacks_repo.find_pending()
    
    # Adiciona preview das mensagens
    feedbacks_with_preview = []
    for feedback in feedbacks:
        # Busca a mensagem para obter preview
        message_preview = None
        try:
            # Busca a mensagem no banco
            from app.infrastructure.persistence.config import SUPABASE_URL, SUPABASE_KEY
            from supabase import create_client
            
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            message_result = supabase.table("messages").select("content").eq("id", str(feedback.message_id)).execute()
            
            if message_result.data:
                message_content = message_result.data[0].get("content", "")
                # Limita o preview para 200 caracteres
                message_preview = message_content[:200] + "..." if len(message_content) > 200 else message_content
        except Exception:
            # Se não conseguir buscar, usa o feedback_text como fallback
            message_preview = feedback.feedback_text[:100] + "..." if len(feedback.feedback_text) > 100 else feedback.feedback_text
        
        feedbacks_with_preview.append(
            PendingFeedbackDTO(
                id=feedback.id,
                message_id=feedback.message_id,
                feedback_text=feedback.feedback_text,
                status=feedback.status.name,
                created_at=feedback.created_at,
                message_preview=message_preview,
                feedback_type=feedback.feedback_type
            )
        )
    
    return feedbacks_with_preview


@router.post("/feedbacks/{feedback_id}/approve")
async def approve_feedback_route(feedback_id: str):
    """Aprova um feedback pendente e sintetiza um aprendizado."""
    try:
        feedback_id_uuid = FeedbackId(uuid.UUID(feedback_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    # Aprova o feedback
    approved_feedback = await approve_feedback(
        feedback_id=feedback_id_uuid,
        feedback_repo=feedbacks_repo
    )
    
    # Obtém a chave de API (personalizada ou padrão)
    api_key = await get_gemini_api_key()
    gemini_service = GeminiService(api_key)
    embedding_generator = EmbeddingGenerator(api_key)
    
    # Sintetiza um aprendizado
    learning = await synthesize_learning_from_feedback(
        feedback=approved_feedback,
        llm_service=gemini_service,
        embedding_generator=embedding_generator,
        learning_repo=learnings_repo
    )
    
    from app.api.dto import LearningDTO
    
    return {
        "feedback": PendingFeedbackDTO(
            id=approved_feedback.id,
            message_id=approved_feedback.message_id,
            feedback_text=approved_feedback.feedback_text,
            status=approved_feedback.status.name,
            created_at=approved_feedback.created_at,
            message_preview=None
        ),
        "learning": LearningDTO(
            id=learning.id,
            content=learning.content,
            source_feedback_id=learning.source_feedback_id,
            created_at=learning.created_at
        )
    }


@router.post("/feedbacks/{feedback_id}/reject", response_model=PendingFeedbackDTO)
async def reject_feedback_route(feedback_id: str):
    """Rejeita um feedback pendente."""
    try:
        feedback_id_uuid = FeedbackId(uuid.UUID(feedback_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    rejected_feedback = await reject_feedback(
        feedback_id=feedback_id_uuid,
        feedback_repo=feedbacks_repo
    )
    
    return PendingFeedbackDTO(
        id=rejected_feedback.id,
        message_id=rejected_feedback.message_id,
        feedback_text=rejected_feedback.feedback_text,
        status=rejected_feedback.status.name,
        created_at=rejected_feedback.created_at,
        message_preview=None
    )


@router.get("/feedbacks/reviewed", response_model=list[PendingFeedbackDTO])
async def list_reviewed_feedbacks():
    """Lista todos os feedbacks revisados (aprovados ou rejeitados)."""
    feedbacks = await feedbacks_repo.find_reviewed()
    
    # Adiciona preview das mensagens
    feedbacks_with_preview = []
    for feedback in feedbacks:
        # Busca a mensagem para obter preview
        message_preview = None
        try:
            # Busca a mensagem no banco
            from app.infrastructure.persistence.config import SUPABASE_URL, SUPABASE_KEY
            from supabase import create_client
            
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            message_result = supabase.table("messages").select("content").eq("id", str(feedback.message_id)).execute()
            
            if message_result.data:
                message_content = message_result.data[0].get("content", "")
                # Limita o preview para 200 caracteres
                message_preview = message_content[:200] + "..." if len(message_content) > 200 else message_content
        except Exception:
            # Se não conseguir buscar, usa o feedback_text como fallback
            message_preview = feedback.feedback_text[:100] + "..." if len(feedback.feedback_text) > 100 else feedback.feedback_text
        
        feedbacks_with_preview.append(
            PendingFeedbackDTO(
                id=feedback.id,
                message_id=feedback.message_id,
                feedback_text=feedback.feedback_text,
                status=feedback.status.name,
                created_at=feedback.created_at,
                message_preview=message_preview,
                feedback_type=feedback.feedback_type
            )
        )
    
    return feedbacks_with_preview


@router.get("/messages/{message_id}/conversation_id")
async def get_conversation_id_by_message_id(message_id: str):
    """Busca o conversation_id a partir de um message_id."""
    try:
        message_id_uuid = MessageId(uuid.UUID(message_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    conversation_id = await feedbacks_repo.get_conversation_id_by_message_id(message_id_uuid)
    
    if not conversation_id:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    
    return {"conversation_id": str(conversation_id)}


@router.get("/messages/{message_id}/feedback", response_model=PendingFeedbackDTO | None)
async def get_feedback_by_message_id(message_id: str):
    """Busca o feedback de uma mensagem específica."""
    try:
        message_id_uuid = MessageId(uuid.UUID(message_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    feedback = await feedbacks_repo.find_by_message_id(message_id_uuid)
    
    if not feedback:
        return None
    
    return PendingFeedbackDTO(
        id=feedback.id,
        message_id=feedback.message_id,
        feedback_text=feedback.feedback_text,
        status=feedback.status.name,
        created_at=feedback.created_at,
        message_preview=None,
        feedback_type=feedback.feedback_type
    )


@router.put("/feedbacks/{feedback_id}", response_model=PendingFeedbackDTO)
async def update_feedback_route(feedback_id: str, payload: SubmitFeedbackPayload):
    """Atualiza um feedback existente."""
    try:
        feedback_id_uuid = FeedbackId(uuid.UUID(feedback_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    feedback = await feedbacks_repo.find_by_id(feedback_id_uuid)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback não encontrado")
    
    updated_feedback = await feedbacks_repo.update(
        feedback_id=feedback_id_uuid,
        feedback_text=payload.feedback_text,
        feedback_type=payload.feedback_type
    )
    
    return PendingFeedbackDTO(
        id=updated_feedback.id,
        message_id=updated_feedback.message_id,
        feedback_text=updated_feedback.feedback_text,
        status=updated_feedback.status.name,
        created_at=updated_feedback.created_at,
        message_preview=None,
        feedback_type=updated_feedback.feedback_type
    )


@router.delete("/feedbacks/{feedback_id}", status_code=204)
async def delete_feedback_route(feedback_id: str):
    """Deleta um feedback."""
    try:
        feedback_id_uuid = FeedbackId(uuid.UUID(feedback_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    feedback = await feedbacks_repo.find_by_id(feedback_id_uuid)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback não encontrado")
    
    await feedbacks_repo.delete(feedback_id_uuid)
    
    return None


@router.post("/messages/feedbacks/batch")
async def get_feedbacks_by_message_ids(payload: BatchFeedbackRequestDTO):
    """
    Busca feedbacks para múltiplas mensagens de uma vez.
    Retorna um dicionário mapeando message_id para feedback (ou null se não houver).
    """
    try:
        message_id_uuids = [MessageId(uuid.UUID(msg_id)) for msg_id in payload.message_ids]
    except ValueError:
        raise HTTPException(status_code=400, detail="IDs inválidos")
    
    feedbacks_dict = await feedbacks_repo.find_by_message_ids(message_id_uuids)
    
    # Converte para formato de resposta: dicionário com message_id (string) -> feedback ou null
    result = {}
    for msg_id in payload.message_ids:
        feedback = feedbacks_dict.get(msg_id)
        if feedback:
            result[msg_id] = PendingFeedbackDTO(
                id=feedback.id,
                message_id=feedback.message_id,
                feedback_text=feedback.feedback_text,
                status=feedback.status.name,
                created_at=feedback.created_at,
                message_preview=None,
                feedback_type=feedback.feedback_type
            )
        else:
            result[msg_id] = None
    
    return result