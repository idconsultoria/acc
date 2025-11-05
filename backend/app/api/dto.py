"""Data Transfer Objects (DTOs) para a API."""
from pydantic import BaseModel
from typing import Literal
from datetime import datetime
from uuid import UUID


class ArtifactDTO(BaseModel):
    """DTO para Artefato."""
    id: UUID
    title: str
    source_type: Literal["PDF", "TEXT"]
    created_at: datetime
    description: str | None = None
    tags: list[str] = []


class UpdateArtifactTagsPayload(BaseModel):
    """Payload para atualizar tags de um artefato."""
    tags: list[str] = []


class CitedSourceDTO(BaseModel):
    """DTO para Fonte Citada."""
    artifact_id: UUID
    title: str
    chunk_content_preview: str


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


class UpdateAgentInstructionPayload(BaseModel):
    """Payload para atualizar instrução do agente."""
    instruction: str


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


class ErrorDTO(BaseModel):
    """DTO para Erro."""
    detail: str
