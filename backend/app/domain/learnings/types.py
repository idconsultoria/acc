"""Tipos de dados do domínio de Aprendizados."""
from dataclasses import dataclass
from datetime import datetime
from app.domain.shared_kernel import LearningId, FeedbackId, Embedding


# Entidade principal deste domínio
@dataclass(frozen=True)
class Learning:
    """Um aprendizado sintetizado a partir de um feedback aprovado."""
    id: LearningId
    content: str
    embedding: Embedding
    source_feedback_id: FeedbackId
    created_at: datetime
    relevance_weight: float | None = None
    last_used_at: datetime | None = None


@dataclass(frozen=True)
class LearningMergeCandidate:
    """Sugestão de agrupamento de aprendizados semelhantes para merge."""
    base_learning: Learning
    duplicate_learnings: list[Learning]
    similarity_score: float | None = None

