"""Kernel compartilhado com tipos base usados em múltiplos domínios."""
from dataclasses import dataclass
from typing import NewType
import uuid


# Usando NewType para criar tipos distintos e evitar misturar UUIDs
ArtifactId = NewType("ArtifactId", uuid.UUID)
ConversationId = NewType("ConversationId", uuid.UUID)
MessageId = NewType("MessageId", uuid.UUID)
ChunkId = NewType("ChunkId", uuid.UUID)
FeedbackId = NewType("FeedbackId", uuid.UUID)
LearningId = NewType("LearningId", uuid.UUID)
TopicId = NewType("TopicId", uuid.UUID)


# Value Object para representar o texto de um embedding
@dataclass(frozen=True)
class Embedding:
    """Representa um vetor de embedding."""
    vector: list[float]

