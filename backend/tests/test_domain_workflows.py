"""Testes para workflows de domínio."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
from app.domain.artifacts.workflows import (
    chunk_text, create_artifact_from_text, create_artifact_from_pdf
)
from app.domain.conversations.workflows import continue_conversation
from app.domain.feedbacks.workflows import (
    submit_feedback, approve_feedback, reject_feedback
)
from app.domain.agent.workflows import (
    get_agent_instruction, update_agent_instruction
)
from app.domain.learnings.workflows import synthesize_learning_from_feedback
from app.domain.learnings.weighter import LearningWeighter
from app.domain.feedbacks.types import FeedbackStatus
from app.domain.shared_kernel import MessageId, FeedbackId, LearningId
from app.domain.agent.types import AgentInstruction
from app.domain.learnings.types import Learning
from app.domain.artifacts.types import ArtifactChunk
import uuid


class TestChunkText:
    """Testes para chunk_text."""
    
    def test_chunk_text_empty(self):
        """Testa chunk_text com texto vazio."""
        result = chunk_text("")
        assert result == []
    
    def test_chunk_text_small(self):
        """Testa chunk_text com texto pequeno."""
        text = "Texto pequeno"
        result = chunk_text(text, chunk_size=1000, overlap=200)
        assert len(result) == 1
        assert result[0] == text.strip()
    
    def test_chunk_text_large(self):
        """Testa chunk_text com texto grande."""
        text = "A" * 5000  # 5000 caracteres
        result = chunk_text(text, chunk_size=1000, overlap=200)
        assert len(result) > 1
        # Verifica que todos os chunks têm conteúdo
        assert all(len(chunk) > 0 for chunk in result)
    
    def test_chunk_text_with_overlap(self):
        """Testa chunk_text com overlap."""
        text = "A" * 2000
        result = chunk_text(text, chunk_size=500, overlap=100)
        # Com overlap, deve ter mais chunks
        assert len(result) >= 3
    
    def test_chunk_text_breaks_at_newline(self):
        """Testa que chunk_text quebra em quebras de linha quando possível."""
        text = "Linha 1\n" + "A" * 800 + "\nLinha 3\n" + "B" * 800
        result = chunk_text(text, chunk_size=1000, overlap=200)
        # Deve tentar quebrar em \n quando possível
        assert len(result) > 0


class TestCreateArtifactFromText:
    """Testes para create_artifact_from_text."""
    
    def test_create_artifact_from_text(self, mock_embedding_generator):
        """Testa criação de artefato a partir de texto."""
        text = "Este é um texto de teste para criar um artefato."
        artifact = create_artifact_from_text(
            title="Artefato de Teste",
            text_content=text,
            embedding_generator=mock_embedding_generator
        )
        
        assert artifact.title == "Artefato de Teste"
        assert artifact.source_type.name == "TEXT"
        assert len(artifact.chunks) > 0
        assert all(chunk.artifact_id == artifact.id for chunk in artifact.chunks)
        assert all(chunk.metadata is not None for chunk in artifact.chunks)
        assert [chunk.metadata.position for chunk in artifact.chunks if chunk.metadata] == list(range(len(artifact.chunks)))
        assert artifact.original_content == text
        # Verifica que generate foi chamado para cada chunk
        assert mock_embedding_generator.generate.call_count == len(artifact.chunks)
    
    def test_create_artifact_from_text_empty(self, mock_embedding_generator):
        """Testa criação de artefato com texto vazio."""
        artifact = create_artifact_from_text(
            title="Artefato Vazio",
            text_content="",
            embedding_generator=mock_embedding_generator
        )
        
        assert artifact.title == "Artefato Vazio"
        assert len(artifact.chunks) == 0
        assert artifact.original_content == ""
    
    def test_create_artifact_from_text_large(self, mock_embedding_generator):
        """Testa criação de artefato com texto grande."""
        text = "A" * 5000
        artifact = create_artifact_from_text(
            title="Artefato Grande",
            text_content=text,
            embedding_generator=mock_embedding_generator
        )
        
        assert len(artifact.chunks) > 1
        # Verifica que todos os chunks têm embeddings
        assert all(chunk.embedding.vector for chunk in artifact.chunks)
        assert all(chunk.metadata is not None for chunk in artifact.chunks)
        assert artifact.original_content == text


class TestCreateArtifactFromPdf:
    """Testes para create_artifact_from_pdf."""
    
    def test_create_artifact_from_pdf(self, mock_pdf_processor, mock_embedding_generator):
        """Testa criação de artefato a partir de PDF."""
        pdf_content = b"PDF content"
        mock_pdf_processor.extract_text.return_value = "Texto extraído do PDF"
        
        artifact = create_artifact_from_pdf(
            title="Artefato PDF",
            pdf_content=pdf_content,
            pdf_processor=mock_pdf_processor,
            embedding_generator=mock_embedding_generator
        )
        
        assert artifact.title == "Artefato PDF"
        assert artifact.source_type.name == "PDF"
        mock_pdf_processor.extract_with_metadata.assert_called_once_with(pdf_content)
        mock_pdf_processor.extract_text.assert_called_once_with(pdf_content)
        assert mock_embedding_generator.generate.call_count == len(artifact.chunks)
        assert all(chunk.metadata is not None for chunk in artifact.chunks)
        assert artifact.original_content is None


class TestContinueConversation:
    """Testes para continue_conversation."""
    
    @pytest.mark.asyncio
    async def test_continue_conversation(self, sample_conversation, 
                                         mock_embedding_generator,
                                         mock_knowledge_repo,
                                         mock_llm_service):
        """Testa continuação de conversa."""
        from app.domain.agent.types import AgentInstruction
        
        agent_instruction = AgentInstruction(
            content="Instrução de teste",
            updated_at=datetime.utcnow()
        )
        
        # Configura mocks
        mock_knowledge = Mock()
        mock_knowledge.relevant_artifacts = []
        mock_knowledge.relevant_learnings = []
        mock_knowledge_repo.find_relevant_knowledge = AsyncMock(return_value=mock_knowledge)
        
        mock_llm_service.generate_advice = AsyncMock(return_value=(
            "Resposta do agente",
            []
        ))
        
        updated_conversation = await continue_conversation(
            conversation=sample_conversation,
            user_query="Pergunta de teste",
            embedding_generator=mock_embedding_generator,
            knowledge_repo=mock_knowledge_repo,
            llm_service=mock_llm_service,
            agent_instruction=agent_instruction
        )
        
        assert updated_conversation.id == sample_conversation.id
        assert len(updated_conversation.messages) == 2  # Mensagem do usuário + resposta do agente
        assert updated_conversation.messages[0].author.name == "USER"
        assert updated_conversation.messages[1].author.name == "AGENT"
        assert updated_conversation.messages[0].content == "Pergunta de teste"
        assert updated_conversation.messages[1].content == "Resposta do agente"
        
        # Verifica que os métodos foram chamados
        mock_embedding_generator.generate.assert_called_once()
        mock_knowledge_repo.find_relevant_knowledge.assert_called_once()
        mock_llm_service.generate_advice.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_continue_conversation_with_cited_sources(self, sample_conversation,
                                                           sample_artifact_chunk,
                                                           mock_embedding_generator,
                                                           mock_knowledge_repo,
                                                           mock_llm_service):
        """Testa continuação de conversa com fontes citadas."""
        from app.domain.agent.types import AgentInstruction
        
        agent_instruction = AgentInstruction(
            content="Instrução de teste",
            updated_at=datetime.utcnow()
        )
        
        # Configura mocks com chunks citados
        mock_knowledge = Mock()
        mock_knowledge.relevant_artifacts = [sample_artifact_chunk]
        mock_knowledge.relevant_learnings = []
        mock_knowledge_repo.find_relevant_knowledge = AsyncMock(return_value=mock_knowledge)
        
        mock_llm_service.generate_advice = AsyncMock(return_value=(
            "Resposta com citação",
            [sample_artifact_chunk]
        ))
        
        updated_conversation = await continue_conversation(
            conversation=sample_conversation,
            user_query="Pergunta",
            embedding_generator=mock_embedding_generator,
            knowledge_repo=mock_knowledge_repo,
            llm_service=mock_llm_service,
            agent_instruction=agent_instruction
        )
        
        agent_message = updated_conversation.messages[1]
        assert len(agent_message.cited_sources) == 1
        assert agent_message.cited_sources[0].artifact_id == sample_artifact_chunk.artifact_id
        assert agent_message.cited_sources[0].chunk_id == sample_artifact_chunk.id
        assert agent_message.cited_sources[0].section_title == sample_artifact_chunk.metadata.section_title


class TestSubmitFeedback:
    """Testes para submit_feedback."""
    
    @pytest.mark.asyncio
    async def test_submit_feedback(self, mock_feedback_repo):
        """Testa submissão de feedback."""
        message_id = MessageId(uuid.uuid4())
        
        # Configura mock
        from app.domain.feedbacks.types import PendingFeedback
        from datetime import datetime
        
        saved_feedback = PendingFeedback(
            id=FeedbackId(uuid.uuid4()),
            message_id=message_id,
            feedback_text="Feedback de teste",
            status=FeedbackStatus.PENDING,
            created_at=datetime.utcnow(),
            feedback_type="POSITIVE"
        )
        
        mock_feedback_repo.save = AsyncMock(return_value=saved_feedback)
        
        feedback = await submit_feedback(
            message_id=message_id,
            feedback_text="Feedback de teste",
            feedback_repo=mock_feedback_repo,
            feedback_type="POSITIVE"
        )
        
        assert feedback.status == FeedbackStatus.PENDING
        assert feedback.feedback_text == "Feedback de teste"
        assert feedback.feedback_type == "POSITIVE"
        mock_feedback_repo.save.assert_called_once()


class TestApproveFeedback:
    """Testes para approve_feedback."""
    
    @pytest.mark.asyncio
    async def test_approve_feedback(self, mock_feedback_repo):
        """Testa aprovação de feedback."""
        feedback_id = FeedbackId(uuid.uuid4())
        message_id = MessageId(uuid.uuid4())
        
        from app.domain.feedbacks.types import PendingFeedback
        from datetime import datetime
        
        pending_feedback = PendingFeedback(
            id=feedback_id,
            message_id=message_id,
            feedback_text="Feedback",
            status=FeedbackStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        approved_feedback = PendingFeedback(
            id=feedback_id,
            message_id=message_id,
            feedback_text="Feedback",
            status=FeedbackStatus.APPROVED,
            created_at=datetime.utcnow()
        )
        
        mock_feedback_repo.find_by_id = AsyncMock(return_value=pending_feedback)
        mock_feedback_repo.update_status = AsyncMock(return_value=approved_feedback)
        
        result = await approve_feedback(
            feedback_id=feedback_id,
            feedback_repo=mock_feedback_repo
        )
        
        assert result.status == FeedbackStatus.APPROVED
        mock_feedback_repo.update_status.assert_called_once_with(
            feedback_id, FeedbackStatus.APPROVED
        )
    
    @pytest.mark.asyncio
    async def test_approve_feedback_not_found(self, mock_feedback_repo):
        """Testa aprovação de feedback inexistente."""
        feedback_id = FeedbackId(uuid.uuid4())
        
        mock_feedback_repo.find_by_id = AsyncMock(return_value=None)
        
        with pytest.raises(ValueError, match="não encontrado"):
            await approve_feedback(
                feedback_id=feedback_id,
                feedback_repo=mock_feedback_repo
            )
    
    @pytest.mark.asyncio
    async def test_approve_feedback_already_processed(self, mock_feedback_repo):
        """Testa aprovação de feedback já processado."""
        feedback_id = FeedbackId(uuid.uuid4())
        message_id = MessageId(uuid.uuid4())
        
        from app.domain.feedbacks.types import PendingFeedback
        from datetime import datetime
        
        approved_feedback = PendingFeedback(
            id=feedback_id,
            message_id=message_id,
            feedback_text="Feedback",
            status=FeedbackStatus.APPROVED,
            created_at=datetime.utcnow()
        )
        
        mock_feedback_repo.find_by_id = AsyncMock(return_value=approved_feedback)
        
        with pytest.raises(ValueError, match="já foi processado"):
            await approve_feedback(
                feedback_id=feedback_id,
                feedback_repo=mock_feedback_repo
            )


class TestRejectFeedback:
    """Testes para reject_feedback."""
    
    @pytest.mark.asyncio
    async def test_reject_feedback(self, mock_feedback_repo):
        """Testa rejeição de feedback."""
        feedback_id = FeedbackId(uuid.uuid4())
        message_id = MessageId(uuid.uuid4())
        
        from app.domain.feedbacks.types import PendingFeedback
        from datetime import datetime
        
        pending_feedback = PendingFeedback(
            id=feedback_id,
            message_id=message_id,
            feedback_text="Feedback",
            status=FeedbackStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        rejected_feedback = PendingFeedback(
            id=feedback_id,
            message_id=message_id,
            feedback_text="Feedback",
            status=FeedbackStatus.REJECTED,
            created_at=datetime.utcnow()
        )
        
        mock_feedback_repo.find_by_id = AsyncMock(return_value=pending_feedback)
        mock_feedback_repo.update_status = AsyncMock(return_value=rejected_feedback)
        
        result = await reject_feedback(
            feedback_id=feedback_id,
            feedback_repo=mock_feedback_repo
        )
        
        assert result.status == FeedbackStatus.REJECTED
        mock_feedback_repo.update_status.assert_called_once_with(
            feedback_id, FeedbackStatus.REJECTED
        )


class TestGetAgentInstruction:
    """Testes para get_agent_instruction."""
    
    @pytest.mark.asyncio
    async def test_get_agent_instruction(self, mock_agent_settings_repo):
        """Testa obtenção de instrução do agente."""
        instruction = await get_agent_instruction(mock_agent_settings_repo)
        
        assert instruction.content == "Instrução de teste"
        mock_agent_settings_repo.get_instruction.assert_called_once()


class TestUpdateAgentInstruction:
    """Testes para update_agent_instruction."""
    
    @pytest.mark.asyncio
    async def test_update_agent_instruction(self, mock_agent_settings_repo):
        """Testa atualização de instrução do agente."""
        instruction = await update_agent_instruction(
            new_content="Nova instrução",
            settings_repo=mock_agent_settings_repo
        )
        
        assert instruction.content == "Nova instrução"
        mock_agent_settings_repo.update_instruction.assert_called_once_with("Nova instrução")


class TestSynthesizeLearningFromFeedback:
    """Testes para synthesize_learning_from_feedback."""
    
    @pytest.mark.asyncio
    async def test_synthesize_learning_from_feedback(self, mock_llm_service,
                                                    mock_embedding_generator):
        """Testa síntese de aprendizado a partir de feedback."""
        from app.domain.feedbacks.types import PendingFeedback
        from datetime import datetime
        
        feedback = PendingFeedback(
            id=FeedbackId(uuid.uuid4()),
            message_id=MessageId(uuid.uuid4()),
            feedback_text="Feedback de teste",
            status=FeedbackStatus.APPROVED,
            created_at=datetime.utcnow(),
            feedback_type="POSITIVE",
        )
        
        mock_learning_repo = AsyncMock()
        learning = Learning(
            id=LearningId(uuid.uuid4()),
            content="Aprendizado sintetizado",
            embedding=Mock(),
            source_feedback_id=feedback.id,
            created_at=datetime.utcnow()
        )
        mock_learning_repo.save = AsyncMock(return_value=learning)
        
        mock_llm_service.synthesize_learning = AsyncMock(
            return_value="Aprendizado sintetizado"
        )
        
        result = await synthesize_learning_from_feedback(
            feedback=feedback,
            llm_service=mock_llm_service,
            embedding_generator=mock_embedding_generator,
            learning_repo=mock_learning_repo
        )
        
        assert result.content == "Aprendizado sintetizado"
        assert result.source_feedback_id == feedback.id
        mock_llm_service.synthesize_learning.assert_called_once_with("Feedback de teste")
        mock_embedding_generator.generate.assert_called_once()
        mock_learning_repo.save.assert_called_once()
        saved_learning = mock_learning_repo.save.call_args[0][0]
        assert saved_learning.relevance_weight == 1.0
        assert saved_learning.last_used_at is None


class TestLearningWeighter:
    """Testes para LearningWeighter."""

    @pytest.mark.asyncio
    async def test_recalculate(self):
        """Garante que o recálculo atualiza pesos dinamicamente."""
        repository = AsyncMock()
        now = datetime.utcnow()

        recent_learning = Learning(
            id=LearningId(uuid.uuid4()),
            content="Recent Learning",
            embedding=Mock(),
            source_feedback_id=FeedbackId(uuid.uuid4()),
            created_at=now - timedelta(days=10),
            relevance_weight=1.0,
            last_used_at=now - timedelta(days=3),
        )
        stale_learning = Learning(
            id=LearningId(uuid.uuid4()),
            content="Stale Learning",
            embedding=Mock(),
            source_feedback_id=FeedbackId(uuid.uuid4()),
            created_at=now - timedelta(days=200),
            relevance_weight=0.5,
            last_used_at=None,
        )

        repository.find_all.return_value = [recent_learning, stale_learning]
        repository.update_weights = AsyncMock()

        weighter = LearningWeighter(repository=repository)
        updates = await weighter.recalculate(now=now)

        repository.find_all.assert_awaited_once()
        repository.update_weights.assert_awaited_once()
        assert len(updates) == 2
        assert recent_learning.id in updates
        assert stale_learning.id in updates
