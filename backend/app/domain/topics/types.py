"""Tipos de dados do domínio de Tópicos."""
from dataclasses import dataclass
from datetime import datetime
from app.domain.shared_kernel import ConversationId, TopicId


# Aggregate Root deste domínio
@dataclass(frozen=True)
class Topic:
    """Um tópico que agrupa conversas relacionadas."""
    id: TopicId
    name: str
    created_at: datetime

