"""Data Transfer Objects (DTOs) para a API."""
from pydantic import BaseModel
from typing import Literal
from datetime import datetime
from uuid import UUID


class ChunkMetadataDTO(BaseModel):
    """DTO para metadados de chunk."""
    section_title: str | None = None
    section_level: int | None = None
    content_type: str | None = None
    position: int | None = None
    token_count: int | None = None
    breadcrumbs: list[str] = []


class ArtifactChunkDTO(BaseModel):
    """DTO para chunk de artefato."""
    id: UUID
    artifact_id: UUID
    content: str
    metadata: ChunkMetadataDTO | None = None


class ArtifactDTO(BaseModel):
    """DTO para Artefato."""
    id: UUID
    title: str
    source_type: Literal["PDF", "TEXT"]
    created_at: datetime
    description: str | None = None
    tags: list[str] = []
    color: str | None = None
    source_url: str | None = None
    original_content: str | None = None


class UpdateArtifactPayload(BaseModel):
    """Payload para atualizar um artefato."""
    title: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    color: str | None = None


class UpdateArtifactTagsPayload(BaseModel):
    """Payload para atualizar tags de um artefato."""
    tags: list[str] = []


class CitedSourceDTO(BaseModel):
    """DTO para Fonte Citada."""
    chunk_id: UUID
    artifact_id: UUID
    title: str
    chunk_content_preview: str
    section_title: str | None = None
    section_level: int | None = None
    content_type: str | None = None
    breadcrumbs: list[str] = []


class MessageDTO(BaseModel):
    """DTO para Mensagem."""
    id: UUID
    conversation_id: UUID
    author: Literal["USER", "AGENT"]
    content: str
    cited_sources: list[CitedSourceDTO] = []
    created_at: datetime


class CreateMessagePayload(BaseModel):
    """Payload para criar mensagem."""
    content: str


class PendingFeedbackDTO(BaseModel):
    """DTO para Feedback Pendente."""
    id: UUID
    message_id: UUID
    feedback_text: str
    status: Literal["PENDING", "APPROVED", "REJECTED"]
    created_at: datetime
    message_preview: str | None = None
    feedback_type: Literal["POSITIVE", "NEGATIVE", None] | None = None


class SubmitFeedbackPayload(BaseModel):
    """Payload para enviar feedback."""
    feedback_text: str
    feedback_type: Literal["POSITIVE", "NEGATIVE", None] | None = None


class LearningDTO(BaseModel):
    """DTO para Aprendizado."""
    id: UUID
    content: str
    source_feedback_id: UUID
    created_at: datetime


class AgentInstructionDTO(BaseModel):
    """DTO para Instrução do Agente."""
    instruction: str
    updated_at: datetime
    prompt_version: str | None = None


class UpdateAgentInstructionPayload(BaseModel):
    """Payload para atualizar instrução do agente."""
    instruction: str
    prompt_version: str | None = None


class TopicDTO(BaseModel):
    """DTO para Tópico."""
    id: str
    name: str
    conversation_count: int


class ConversationSummaryDTO(BaseModel):
    """DTO para Resumo de Conversa."""
    id: str
    title: str
    summary: str
    topic: str | None
    created_at: str


class ConversationTopicDTO(BaseModel):
    """DTO para Tópico de uma Conversa."""
    topic: str | None
    is_processing: bool = False


class BatchFeedbackRequestDTO(BaseModel):
    """DTO para requisição de feedbacks em batch."""
    message_ids: list[str]


class ErrorDTO(BaseModel):
    """DTO para Erro."""
    detail: str
