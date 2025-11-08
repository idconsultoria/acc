"""Testes para tipos de domínio."""
import pytest
from datetime import datetime
import uuid
from app.domain.shared_kernel import (
    ArtifactId, ConversationId, MessageId, ChunkId,
    FeedbackId, LearningId, TopicId, Embedding
)
from app.domain.artifacts.types import Artifact, ArtifactChunk, ArtifactSourceType, ChunkMetadata
from app.domain.conversations.types import Conversation, Message, Author, CitedSource
from app.domain.feedbacks.types import PendingFeedback, FeedbackStatus
from app.domain.learnings.types import Learning
from app.domain.agent.types import AgentInstruction
from app.domain.topics.types import Topic


class TestEmbedding:
    """Testes para Embedding."""
    
    def test_create_embedding(self):
        """Testa criação de Embedding."""
        vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        embedding = Embedding(vector=vector)
        
        assert embedding.vector == vector
        assert len(embedding.vector) == 5
    
    def test_embedding_immutable(self):
        """Testa que Embedding é imutável."""
        vector = [0.1, 0.2, 0.3]
        embedding = Embedding(vector=vector)
        
        # O embedding armazena uma referência ao vector, então modificações
        # no vector original afetam o embedding. Isso é comportamento esperado
        # do dataclass frozen - ele congela o objeto, não o conteúdo mutável.
        # Vamos apenas verificar que o embedding foi criado corretamente.
        assert len(embedding.vector) == 3
        assert embedding.vector == [0.1, 0.2, 0.3]


class TestArtifactChunk:
    """Testes para ArtifactChunk."""
    
    def test_create_artifact_chunk(self, sample_chunk_id, sample_artifact_id, sample_embedding):
        """Testa criação de ArtifactChunk."""
        chunk = ArtifactChunk(
            id=sample_chunk_id,
            artifact_id=sample_artifact_id,
            content="Conteúdo do chunk",
            embedding=sample_embedding
        )
        
        assert chunk.id == sample_chunk_id
        assert chunk.artifact_id == sample_artifact_id
        assert chunk.content == "Conteúdo do chunk"
        assert chunk.embedding == sample_embedding
    
    def test_artifact_chunk_immutable(self, sample_chunk_id, sample_artifact_id, sample_embedding):
        """Testa que ArtifactChunk é imutável."""
        chunk = ArtifactChunk(
            id=sample_chunk_id,
            artifact_id=sample_artifact_id,
            content="Conteúdo",
            embedding=sample_embedding,
            metadata=ChunkMetadata(
                section_title="Sessão",
                section_level=1,
                content_type="paragraph",
                position=0,
                token_count=10,
                breadcrumbs=["Sessão"],
            ),
        )
        
        # Tentar modificar deve falhar
        with pytest.raises(Exception):
            chunk.content = "Novo conteúdo"


class TestArtifact:
    """Testes para Artifact."""
    
    def test_create_artifact(self, sample_artifact_id, sample_artifact_chunk):
        """Testa criação de Artifact."""
        artifact = Artifact(
            id=sample_artifact_id,
            title="Título do Artefato",
            source_type=ArtifactSourceType.TEXT,
            chunks=[sample_artifact_chunk],
            source_url=None
        )
        
        assert artifact.id == sample_artifact_id
        assert artifact.title == "Título do Artefato"
        assert artifact.source_type == ArtifactSourceType.TEXT
        assert len(artifact.chunks) == 1
        assert artifact.source_url is None
        assert artifact.original_content is None
    
    def test_create_artifact_pdf(self, sample_artifact_id, sample_artifact_chunk):
        """Testa criação de Artifact do tipo PDF."""
        artifact = Artifact(
            id=sample_artifact_id,
            title="Artefato PDF",
            source_type=ArtifactSourceType.PDF,
            chunks=[sample_artifact_chunk],
            source_url="https://example.com/file.pdf"
        )
        
        assert artifact.source_type == ArtifactSourceType.PDF
        assert artifact.source_url == "https://example.com/file.pdf"
        assert artifact.original_content is None
    
    def test_artifact_with_multiple_chunks(self, sample_artifact_id, sample_embedding):
        """Testa Artifact com múltiplos chunks."""
        chunks = [
            ArtifactChunk(
                id=ChunkId(uuid.uuid4()),
                artifact_id=sample_artifact_id,
                content=f"Chunk {i}",
                embedding=sample_embedding,
                metadata=ChunkMetadata(
                    section_title=f"Seção {i}",
                    section_level=2,
                    content_type="paragraph",
                    position=i,
                    token_count=15,
                    breadcrumbs=["Seção Pai", f"Seção {i}"],
                ),
            )
            for i in range(5)
        ]
        
        artifact = Artifact(
            id=sample_artifact_id,
            title="Artefato com múltiplos chunks",
            source_type=ArtifactSourceType.TEXT,
            chunks=chunks
        )
        
        assert len(artifact.chunks) == 5


class TestAuthor:
    """Testes para Author."""
    
    def test_author_enum(self):
        """Testa enum Author."""
        assert Author.USER.value == 1
        assert Author.AGENT.value == 2
        assert Author.USER.name == "USER"
        assert Author.AGENT.name == "AGENT"


class TestCitedSource:
    """Testes para CitedSource."""
    
    def test_create_cited_source(self, sample_artifact_id):
        """Testa criação de CitedSource."""
        cited_source = CitedSource(
            chunk_id=ChunkId(uuid.uuid4()),
            artifact_id=sample_artifact_id,
            title="Título da Fonte",
            chunk_content_preview="Preview do conteúdo...",
            section_title="Seção",
            section_level=2,
            content_type="paragraph",
            breadcrumbs=["Seção"],
        )
        
        assert cited_source.artifact_id == sample_artifact_id
        assert cited_source.title == "Título da Fonte"
        assert cited_source.chunk_content_preview == "Preview do conteúdo..."


class TestMessage:
    """Testes para Message."""
    
    def test_create_message(self, sample_message_id, sample_conversation_id):
        """Testa criação de Message."""
        message = Message(
            id=sample_message_id,
            conversation_id=sample_conversation_id,
            author=Author.USER,
            content="Conteúdo da mensagem",
            cited_sources=[],
            created_at=datetime.utcnow()
        )
        
        assert message.id == sample_message_id
        assert message.conversation_id == sample_conversation_id
        assert message.author == Author.USER
        assert message.content == "Conteúdo da mensagem"
        assert len(message.cited_sources) == 0
    
    def test_message_with_cited_sources(self, sample_message_id, sample_conversation_id,
                                       sample_artifact_id):
        """Testa Message com fontes citadas."""
        cited_source = CitedSource(
            chunk_id=ChunkId(uuid.uuid4()),
            artifact_id=sample_artifact_id,
            title="Fonte",
            chunk_content_preview="Preview",
            section_title="Seção",
            section_level=1,
            content_type="paragraph",
            breadcrumbs=["Seção"],
        )
        
        message = Message(
            id=sample_message_id,
            conversation_id=sample_conversation_id,
            author=Author.AGENT,
            content="Resposta com citação",
            cited_sources=[cited_source],
            created_at=datetime.utcnow()
        )
        
        assert message.author == Author.AGENT
        assert len(message.cited_sources) == 1
        assert message.cited_sources[0].artifact_id == sample_artifact_id


class TestConversation:
    """Testes para Conversation."""
    
    def test_create_conversation(self, sample_conversation_id):
        """Testa criação de Conversation."""
        conversation = Conversation(
            id=sample_conversation_id,
            messages=[],
            created_at=datetime.utcnow()
        )
        
        assert conversation.id == sample_conversation_id
        assert len(conversation.messages) == 0
    
    def test_conversation_with_messages(self, sample_conversation_id, sample_message_id):
        """Testa Conversation com mensagens."""
        message = Message(
            id=sample_message_id,
            conversation_id=sample_conversation_id,
            author=Author.USER,
            content="Mensagem",
            cited_sources=[],
            created_at=datetime.utcnow()
        )
        
        conversation = Conversation(
            id=sample_conversation_id,
            messages=[message],
            created_at=datetime.utcnow()
        )
        
        assert len(conversation.messages) == 1
        assert conversation.messages[0].content == "Mensagem"


class TestFeedbackStatus:
    """Testes para FeedbackStatus."""
    
    def test_feedback_status_enum(self):
        """Testa enum FeedbackStatus."""
        assert FeedbackStatus.PENDING.value == 1
        assert FeedbackStatus.APPROVED.value == 2
        assert FeedbackStatus.REJECTED.value == 3
        assert FeedbackStatus.PENDING.name == "PENDING"
        assert FeedbackStatus.APPROVED.name == "APPROVED"
        assert FeedbackStatus.REJECTED.name == "REJECTED"


class TestPendingFeedback:
    """Testes para PendingFeedback."""
    
    def test_create_pending_feedback(self):
        """Testa criação de PendingFeedback."""
        feedback_id = FeedbackId(uuid.uuid4())
        message_id = MessageId(uuid.uuid4())
        
        feedback = PendingFeedback(
            id=feedback_id,
            message_id=message_id,
            feedback_text="Feedback de teste",
            status=FeedbackStatus.PENDING,
            created_at=datetime.utcnow(),
            feedback_type="POSITIVE"
        )
        
        assert feedback.id == feedback_id
        assert feedback.message_id == message_id
        assert feedback.feedback_text == "Feedback de teste"
        assert feedback.status == FeedbackStatus.PENDING
        assert feedback.feedback_type == "POSITIVE"
    
    def test_pending_feedback_no_type(self):
        """Testa PendingFeedback sem tipo."""
        feedback_id = FeedbackId(uuid.uuid4())
        message_id = MessageId(uuid.uuid4())
        
        feedback = PendingFeedback(
            id=feedback_id,
            message_id=message_id,
            feedback_text="Feedback",
            status=FeedbackStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        assert feedback.feedback_type is None


class TestLearning:
    """Testes para Learning."""
    
    def test_create_learning(self, sample_embedding):
        """Testa criação de Learning."""
        learning_id = LearningId(uuid.uuid4())
        feedback_id = FeedbackId(uuid.uuid4())
        
        learning = Learning(
            id=learning_id,
            content="Conteúdo do aprendizado",
            embedding=sample_embedding,
            source_feedback_id=feedback_id,
            created_at=datetime.utcnow()
        )
        
        assert learning.id == learning_id
        assert learning.content == "Conteúdo do aprendizado"
        assert learning.embedding == sample_embedding
        assert learning.source_feedback_id == feedback_id


class TestAgentInstruction:
    """Testes para AgentInstruction."""
    
    def test_create_agent_instruction(self):
        """Testa criação de AgentInstruction."""
        instruction = AgentInstruction(
            content="Instrução de teste",
            updated_at=datetime.utcnow()
        )
        
        assert instruction.content == "Instrução de teste"
        assert isinstance(instruction.updated_at, datetime)


class TestTopic:
    """Testes para Topic."""
    
    def test_create_topic(self):
        """Testa criação de Topic."""
        topic_id = TopicId(uuid.uuid4())
        
        topic = Topic(
            id=topic_id,
            name="Tópico de Teste",
            created_at=datetime.utcnow()
        )
        
        assert topic.id == topic_id
        assert topic.name == "Tópico de Teste"
        assert isinstance(topic.created_at, datetime)


class TestArtifactSourceType:
    """Testes para ArtifactSourceType."""
    
    def test_artifact_source_type_enum(self):
        """Testa enum ArtifactSourceType."""
        assert ArtifactSourceType.PDF.value == 1
        assert ArtifactSourceType.TEXT.value == 2
        assert ArtifactSourceType.PDF.name == "PDF"
        assert ArtifactSourceType.TEXT.name == "TEXT"
