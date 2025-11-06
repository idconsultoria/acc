"""Configuração compartilhada para testes."""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
import uuid
from app.domain.shared_kernel import (
    ArtifactId, ConversationId, MessageId, ChunkId, 
    FeedbackId, LearningId, TopicId, Embedding
)
from app.domain.artifacts.types import Artifact, ArtifactChunk, ArtifactSourceType
from app.domain.conversations.types import Conversation, Message, Author, CitedSource
from app.domain.feedbacks.types import PendingFeedback, FeedbackStatus
from app.domain.learnings.types import Learning
from app.domain.agent.types import AgentInstruction
from app.domain.topics.types import Topic


@pytest.fixture
def sample_artifact_id():
    """Retorna um ArtifactId de exemplo."""
    return ArtifactId(uuid.uuid4())


@pytest.fixture
def sample_conversation_id():
    """Retorna um ConversationId de exemplo."""
    return ConversationId(uuid.uuid4())


@pytest.fixture
def sample_message_id():
    """Retorna um MessageId de exemplo."""
    return MessageId(uuid.uuid4())


@pytest.fixture
def sample_chunk_id():
    """Retorna um ChunkId de exemplo."""
    return ChunkId(uuid.uuid4())


@pytest.fixture
def sample_embedding():
    """Retorna um Embedding de exemplo."""
    return Embedding(vector=[0.1, 0.2, 0.3, 0.4, 0.5] * 20)  # 100 dimensões


@pytest.fixture
def sample_artifact_chunk(sample_chunk_id, sample_artifact_id, sample_embedding):
    """Retorna um ArtifactChunk de exemplo."""
    return ArtifactChunk(
        id=sample_chunk_id,
        artifact_id=sample_artifact_id,
        content="Este é um chunk de exemplo com conteúdo de teste.",
        embedding=sample_embedding
    )


@pytest.fixture
def sample_artifact(sample_artifact_id, sample_artifact_chunk):
    """Retorna um Artifact de exemplo."""
    return Artifact(
        id=sample_artifact_id,
        title="Artefato de Teste",
        source_type=ArtifactSourceType.TEXT,
        chunks=[sample_artifact_chunk],
        source_url=None
    )


@pytest.fixture
def sample_conversation(sample_conversation_id):
    """Retorna uma Conversation de exemplo."""
    return Conversation(
        id=sample_conversation_id,
        messages=[],
        created_at=datetime.utcnow()
    )


@pytest.fixture
def sample_message(sample_message_id, sample_conversation_id):
    """Retorna uma Message de exemplo."""
    return Message(
        id=sample_message_id,
        conversation_id=sample_conversation_id,
        author=Author.USER,
        content="Mensagem de teste",
        cited_sources=[],
        created_at=datetime.utcnow()
    )


@pytest.fixture
def mock_embedding_generator():
    """Retorna um mock de EmbeddingGenerator."""
    mock = Mock()
    mock.generate = Mock(return_value=[0.1, 0.2, 0.3] * 33)  # ~100 dimensões
    return mock


@pytest.fixture
def mock_pdf_processor():
    """Retorna um mock de PDFProcessor."""
    mock = Mock()
    mock.extract_text = Mock(return_value="Texto extraído do PDF")
    return mock


@pytest.fixture
def mock_llm_service():
    """Retorna um mock de LLMService."""
    mock = AsyncMock()
    mock.generate_advice = AsyncMock(return_value=("Resposta do agente", []))
    mock.synthesize_learning = AsyncMock(return_value="Aprendizado sintetizado")
    return mock


@pytest.fixture
def mock_knowledge_repo():
    """Retorna um mock de KnowledgeRepository."""
    mock = AsyncMock()
    mock_knowledge = Mock()
    mock_knowledge.relevant_artifacts = []
    mock_knowledge.relevant_learnings = []
    mock.find_relevant_knowledge = AsyncMock(return_value=mock_knowledge)
    return mock


@pytest.fixture
def mock_feedback_repo():
    """Retorna um mock de FeedbackRepository."""
    mock = AsyncMock()
    mock.save = AsyncMock()
    mock.find_by_id = AsyncMock(return_value=None)
    mock.find_pending = AsyncMock(return_value=[])
    mock.update_status = AsyncMock()
    return mock


@pytest.fixture
def mock_agent_settings_repo():
    """Retorna um mock de AgentSettingsRepository."""
    mock = AsyncMock()
    mock.get_instruction = AsyncMock(return_value=AgentInstruction(
        content="Instrução de teste",
        updated_at=datetime.utcnow()
    ))
    mock.update_instruction = AsyncMock(return_value=AgentInstruction(
        content="Nova instrução",
        updated_at=datetime.utcnow()
    ))
    return mock
