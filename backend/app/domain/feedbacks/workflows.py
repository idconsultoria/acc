"""Workflows do domínio de Feedbacks."""
from typing import Protocol
from datetime import datetime
from app.domain.feedbacks.types import PendingFeedback, FeedbackStatus
from app.domain.shared_kernel import MessageId, FeedbackId
import uuid


# --- Interfaces de Dependência (Protocolos) ---

class FeedbackRepository(Protocol):
    """Interface para persistir e recuperar feedbacks."""
    async def save(self, feedback: PendingFeedback) -> PendingFeedback:
        """Salva um feedback."""
        ...
    
    async def find_by_id(self, feedback_id: FeedbackId) -> PendingFeedback | None:
        """Busca um feedback por ID."""
        ...
    
    async def find_pending(self) -> list[PendingFeedback]:
        """Busca todos os feedbacks pendentes."""
        ...
    
    async def update_status(self, feedback_id: FeedbackId, status: FeedbackStatus) -> PendingFeedback:
        """Atualiza o status de um feedback."""
        ...


# --- Assinaturas dos Workflows ---

async def submit_feedback(
    message_id: MessageId,
    feedback_text: str,
    feedback_repo: FeedbackRepository,
    feedback_type: str | None = None
) -> PendingFeedback:
    """
    Cria um novo feedback pendente associado a uma mensagem do agente.
    feedback_type pode ser "POSITIVE" (thumbs up) ou "NEGATIVE" (thumbs down).
    """
    feedback = PendingFeedback(
        id=FeedbackId(uuid.uuid4()),
        message_id=message_id,
        feedback_text=feedback_text,
        status=FeedbackStatus.PENDING,
        created_at=datetime.utcnow(),
        feedback_type=feedback_type
    )
    
    return await feedback_repo.save(feedback)


async def approve_feedback(
    feedback_id: FeedbackId,
    feedback_repo: FeedbackRepository
) -> PendingFeedback:
    """
    Aprova um feedback, alterando seu status para APPROVED.
    """
    feedback = await feedback_repo.find_by_id(feedback_id)
    if not feedback:
        raise ValueError(f"Feedback {feedback_id} não encontrado")
    
    if feedback.status != FeedbackStatus.PENDING:
        raise ValueError(f"Feedback {feedback_id} já foi processado")
    
    return await feedback_repo.update_status(feedback_id, FeedbackStatus.APPROVED)


async def reject_feedback(
    feedback_id: FeedbackId,
    feedback_repo: FeedbackRepository
) -> PendingFeedback:
    """
    Rejeita um feedback, alterando seu status para REJECTED.
    """
    feedback = await feedback_repo.find_by_id(feedback_id)
    if not feedback:
        raise ValueError(f"Feedback {feedback_id} não encontrado")
    
    if feedback.status != FeedbackStatus.PENDING:
        raise ValueError(f"Feedback {feedback_id} já foi processado")
    
    return await feedback_repo.update_status(feedback_id, FeedbackStatus.REJECTED)

