"""Tipos de dados do domínio de Feedbacks."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Literal
from app.domain.shared_kernel import MessageId, FeedbackId


class FeedbackStatus(Enum):
    """Status do feedback."""
    PENDING = auto()
    APPROVED = auto()
    REJECTED = auto()


FeedbackType = Literal["POSITIVE", "NEGATIVE", None]


# Entidade principal deste domínio
@dataclass(frozen=True)
class PendingFeedback:
    """Feedback pendente de moderação."""
    id: FeedbackId
    message_id: MessageId
    feedback_text: str
    status: FeedbackStatus
    created_at: datetime
    feedback_type: FeedbackType = None  # POSITIVE (thumbs up) ou NEGATIVE (thumbs down)

