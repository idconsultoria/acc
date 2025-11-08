"""Testes para DTOs."""
import pytest
from datetime import datetime
from uuid import UUID
from app.api.dto import (
    ArtifactDTO, UpdateArtifactPayload, UpdateArtifactTagsPayload,
    CitedSourceDTO, MessageDTO, CreateMessagePayload,
    PendingFeedbackDTO, SubmitFeedbackPayload,
    LearningDTO, AgentInstructionDTO, UpdateAgentInstructionPayload,
    TopicDTO, ConversationSummaryDTO, ConversationTopicDTO,
    BatchFeedbackRequestDTO, ErrorDTO
)


class TestArtifactDTO:
    """Testes para ArtifactDTO."""
    
    def test_create_artifact_dto(self):
        """Testa criação de ArtifactDTO."""
        artifact_id = UUID('12345678-1234-5678-1234-567812345678')
        dto = ArtifactDTO(
            id=artifact_id,
            title="Teste",
            source_type="TEXT",
            created_at=datetime.utcnow(),
            description="Descrição",
            tags=["tag1", "tag2"],
            color="#FF0000"
        )
        
        assert dto.id == artifact_id
        assert dto.title == "Teste"
        assert dto.source_type == "TEXT"
        assert dto.description == "Descrição"
        assert dto.tags == ["tag1", "tag2"]
        assert dto.color == "#FF0000"
    
    def test_artifact_dto_optional_fields(self):
        """Testa ArtifactDTO com campos opcionais."""
        artifact_id = UUID('12345678-1234-5678-1234-567812345678')
        dto = ArtifactDTO(
            id=artifact_id,
            title="Teste",
            source_type="PDF",
            created_at=datetime.utcnow()
        )
        
        assert dto.description is None
        assert dto.tags == []
        assert dto.color is None


class TestUpdateArtifactPayload:
    """Testes para UpdateArtifactPayload."""
    
    def test_create_update_payload(self):
        """Testa criação de UpdateArtifactPayload."""
        payload = UpdateArtifactPayload(
            title="Novo título",
            description="Nova descrição",
            tags=["tag1"],
            color="#00FF00"
        )
        
        assert payload.title == "Novo título"
        assert payload.description == "Nova descrição"
        assert payload.tags == ["tag1"]
        assert payload.color == "#00FF00"
    
    def test_update_payload_all_none(self):
        """Testa UpdateArtifactPayload com todos os campos None."""
        payload = UpdateArtifactPayload()
        
        assert payload.title is None
        assert payload.description is None
        assert payload.tags is None
        assert payload.color is None


class TestUpdateArtifactTagsPayload:
    """Testes para UpdateArtifactTagsPayload."""
    
    def test_create_tags_payload(self):
        """Testa criação de UpdateArtifactTagsPayload."""
        payload = UpdateArtifactTagsPayload(tags=["tag1", "tag2", "tag3"])
        
        assert payload.tags == ["tag1", "tag2", "tag3"]
    
    def test_empty_tags_payload(self):
        """Testa UpdateArtifactTagsPayload com lista vazia."""
        payload = UpdateArtifactTagsPayload(tags=[])
        
        assert payload.tags == []


class TestCitedSourceDTO:
    """Testes para CitedSourceDTO."""
    
    def test_create_cited_source_dto(self):
        """Testa criação de CitedSourceDTO."""
        artifact_id = UUID('12345678-1234-5678-1234-567812345678')
        chunk_id = UUID('87654321-4321-8765-4321-876543218765')
        dto = CitedSourceDTO(
            chunk_id=chunk_id,
            artifact_id=artifact_id,
            title="Fonte de Teste",
            chunk_content_preview="Preview do conteúdo...",
            section_title="Introdução",
            section_level=1,
            content_type="paragraph",
            breadcrumbs=["Introdução"]
        )
        
        assert dto.artifact_id == artifact_id
        assert dto.title == "Fonte de Teste"
        assert dto.chunk_content_preview == "Preview do conteúdo..."
        assert dto.chunk_id == chunk_id
        assert dto.section_title == "Introdução"
        assert dto.breadcrumbs == ["Introdução"]


class TestMessageDTO:
    """Testes para MessageDTO."""
    
    def test_create_message_dto(self):
        """Testa criação de MessageDTO."""
        message_id = UUID('12345678-1234-5678-1234-567812345678')
        conversation_id = UUID('87654321-4321-8765-4321-876543218765')
        artifact_id = UUID('11111111-1111-1111-1111-111111111111')
        chunk_id = UUID('22222222-2222-2222-2222-222222222222')
        
        cited_source = CitedSourceDTO(
            chunk_id=chunk_id,
            artifact_id=artifact_id,
            title="Fonte",
            chunk_content_preview="Preview",
            section_title="Seção",
            section_level=2,
            content_type="bullet",
            breadcrumbs=["Pai", "Seção"]
        )
        
        dto = MessageDTO(
            id=message_id,
            conversation_id=conversation_id,
            author="USER",
            content="Mensagem de teste",
            cited_sources=[cited_source],
            created_at=datetime.utcnow()
        )
        
        assert dto.id == message_id
        assert dto.conversation_id == conversation_id
        assert dto.author == "USER"
        assert dto.content == "Mensagem de teste"
        assert len(dto.cited_sources) == 1
        assert dto.cited_sources[0].artifact_id == artifact_id
        assert dto.cited_sources[0].chunk_id == chunk_id


class TestCreateMessagePayload:
    """Testes para CreateMessagePayload."""
    
    def test_create_message_payload(self):
        """Testa criação de CreateMessagePayload."""
        payload = CreateMessagePayload(content="Nova mensagem")
        
        assert payload.content == "Nova mensagem"


class TestPendingFeedbackDTO:
    """Testes para PendingFeedbackDTO."""
    
    def test_create_pending_feedback_dto(self):
        """Testa criação de PendingFeedbackDTO."""
        feedback_id = UUID('12345678-1234-5678-1234-567812345678')
        message_id = UUID('87654321-4321-8765-4321-876543218765')
        
        dto = PendingFeedbackDTO(
            id=feedback_id,
            message_id=message_id,
            feedback_text="Feedback de teste",
            status="PENDING",
            created_at=datetime.utcnow(),
            message_preview="Preview...",
            feedback_type="POSITIVE"
        )
        
        assert dto.id == feedback_id
        assert dto.message_id == message_id
        assert dto.feedback_text == "Feedback de teste"
        assert dto.status == "PENDING"
        assert dto.message_preview == "Preview..."
        assert dto.feedback_type == "POSITIVE"


class TestSubmitFeedbackPayload:
    """Testes para SubmitFeedbackPayload."""
    
    def test_create_submit_feedback_payload(self):
        """Testa criação de SubmitFeedbackPayload."""
        payload = SubmitFeedbackPayload(
            feedback_text="Feedback",
            feedback_type="NEGATIVE"
        )
        
        assert payload.feedback_text == "Feedback"
        assert payload.feedback_type == "NEGATIVE"
    
    def test_submit_feedback_payload_no_type(self):
        """Testa SubmitFeedbackPayload sem tipo."""
        payload = SubmitFeedbackPayload(feedback_text="Feedback")
        
        assert payload.feedback_text == "Feedback"
        assert payload.feedback_type is None


class TestLearningDTO:
    """Testes para LearningDTO."""
    
    def test_create_learning_dto(self):
        """Testa criação de LearningDTO."""
        learning_id = UUID('12345678-1234-5678-1234-567812345678')
        feedback_id = UUID('87654321-4321-8765-4321-876543218765')
        
        dto = LearningDTO(
            id=learning_id,
            content="Aprendizado de teste",
            source_feedback_id=feedback_id,
            created_at=datetime.utcnow()
        )
        
        assert dto.id == learning_id
        assert dto.content == "Aprendizado de teste"
        assert dto.source_feedback_id == feedback_id


class TestAgentInstructionDTO:
    """Testes para AgentInstructionDTO."""
    
    def test_create_agent_instruction_dto(self):
        """Testa criação de AgentInstructionDTO."""
        dto = AgentInstructionDTO(
            instruction="Instrução de teste",
            updated_at=datetime.utcnow()
        )
        
        assert dto.instruction == "Instrução de teste"


class TestUpdateAgentInstructionPayload:
    """Testes para UpdateAgentInstructionPayload."""
    
    def test_create_update_instruction_payload(self):
        """Testa criação de UpdateAgentInstructionPayload."""
        payload = UpdateAgentInstructionPayload(instruction="Nova instrução")
        
        assert payload.instruction == "Nova instrução"


class TestTopicDTO:
    """Testes para TopicDTO."""
    
    def test_create_topic_dto(self):
        """Testa criação de TopicDTO."""
        dto = TopicDTO(
            id="12345678-1234-5678-1234-567812345678",
            name="Tópico de Teste",
            conversation_count=5
        )
        
        assert dto.id == "12345678-1234-5678-1234-567812345678"
        assert dto.name == "Tópico de Teste"
        assert dto.conversation_count == 5


class TestConversationSummaryDTO:
    """Testes para ConversationSummaryDTO."""
    
    def test_create_conversation_summary_dto(self):
        """Testa criação de ConversationSummaryDTO."""
        dto = ConversationSummaryDTO(
            id="12345678-1234-5678-1234-567812345678",
            title="Título da Conversa",
            summary="Resumo da conversa",
            topic="Tópico",
            created_at="2024-01-01T00:00:00"
        )
        
        assert dto.id == "12345678-1234-5678-1234-567812345678"
        assert dto.title == "Título da Conversa"
        assert dto.summary == "Resumo da conversa"
        assert dto.topic == "Tópico"
        assert dto.created_at == "2024-01-01T00:00:00"


class TestConversationTopicDTO:
    """Testes para ConversationTopicDTO."""
    
    def test_create_conversation_topic_dto(self):
        """Testa criação de ConversationTopicDTO."""
        dto = ConversationTopicDTO(topic="Tópico", is_processing=False)
        
        assert dto.topic == "Tópico"
        assert dto.is_processing is False
    
    def test_conversation_topic_dto_none(self):
        """Testa ConversationTopicDTO com tópico None."""
        dto = ConversationTopicDTO(topic=None, is_processing=True)
        
        assert dto.topic is None
        assert dto.is_processing is True


class TestBatchFeedbackRequestDTO:
    """Testes para BatchFeedbackRequestDTO."""
    
    def test_create_batch_feedback_request_dto(self):
        """Testa criação de BatchFeedbackRequestDTO."""
        dto = BatchFeedbackRequestDTO(
            message_ids=["id1", "id2", "id3"]
        )
        
        assert dto.message_ids == ["id1", "id2", "id3"]
        assert len(dto.message_ids) == 3


class TestErrorDTO:
    """Testes para ErrorDTO."""
    
    def test_create_error_dto(self):
        """Testa criação de ErrorDTO."""
        dto = ErrorDTO(detail="Erro de teste")
        
        assert dto.detail == "Erro de teste"
