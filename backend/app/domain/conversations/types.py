"""Tipos de dados do domínio de Conversas."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from app.domain.shared_kernel import ConversationId, MessageId, ArtifactId, ChunkId


class Author(Enum):
    """Autor da mensagem."""
    USER = auto()
    AGENT = auto()


# Value Object que representa uma fonte citada
@dataclass(frozen=True)
class CitedSource:
    """Fonte citada em uma mensagem do agente."""
    chunk_id: ChunkId
    artifact_id: ArtifactId
    title: str
    chunk_content_preview: str
    section_title: str | None = None
    section_level: int | None = None
    content_type: str | None = None
    breadcrumbs: list[str] = field(default_factory=list)


# Entidade que compõe o agregado Conversa
@dataclass(frozen=True)
class Message:
    """Uma mensagem individual em uma conversa."""
    id: MessageId
    conversation_id: ConversationId
    author: Author
    content: str
    cited_sources: list[CitedSource]
    created_at: datetime


# Aggregate Root deste domínio
@dataclass(frozen=True)
class Conversation:
    """Uma sequência de trocas entre um usuário e o agente."""
    id: ConversationId
    messages: list[Message]
    created_at: datetime

