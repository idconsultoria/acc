"""Testes para repositórios."""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import uuid
from app.domain.shared_kernel import (
    ArtifactId, ConversationId, MessageId, ChunkId,
    FeedbackId, LearningId, TopicId, Embedding
)
from app.domain.artifacts.types import Artifact, ArtifactChunk, ArtifactSourceType, ChunkMetadata
from app.domain.conversations.types import Conversation, Message, Author
from app.domain.feedbacks.types import PendingFeedback, FeedbackStatus
from app.domain.learnings.types import Learning
from app.domain.topics.types import Topic
from app.domain.agent.types import AgentInstruction


class TestArtifactsRepository:
    """Testes para ArtifactsRepository."""
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.artifacts_repo.create_client')
    async def test_save_artifact(self, mock_create_client):
        """Testa salvamento de artefato."""
        from app.infrastructure.persistence.artifacts_repo import ArtifactsRepository
        
        mock_supabase = Mock()
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_create_client.return_value = mock_supabase
        
        repo = ArtifactsRepository()
        repo.supabase = mock_supabase
        
        artifact_id = ArtifactId(uuid.uuid4())
        chunk = ArtifactChunk(
            id=ChunkId(uuid.uuid4()),
            artifact_id=artifact_id,
            content="Conteúdo",
            embedding=Embedding(vector=[0.1] * 100),
            metadata=ChunkMetadata(
                section_title="Seção",
                section_level=1,
                content_type="paragraph",
                position=0,
                token_count=10,
                breadcrumbs=["Seção"],
            ),
        )
        artifact = Artifact(
            id=artifact_id,
            title="Artefato",
            source_type=ArtifactSourceType.TEXT,
            chunks=[chunk],
            source_url=None
        )
        
        result = await repo.save(artifact, source_url=None, color=None)
        
        assert result == artifact
        assert mock_table.insert.call_count >= 1
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.artifacts_repo.create_client')
    async def test_find_by_id(self, mock_create_client):
        """Testa busca de artefato por ID."""
        from app.infrastructure.persistence.artifacts_repo import ArtifactsRepository
        
        mock_supabase = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_select
        mock_select.execute.return_value = Mock(data=[{
            "id": str(uuid.uuid4()),
            "title": "Artefato",
            "source_type": "TEXT",
            "source_url": None
        }])
        
        mock_chunks_table = Mock()
        mock_chunks_select = Mock()
        mock_chunks_table.select.return_value = mock_chunks_select
        mock_chunks_select.eq.return_value = mock_chunks_select
        mock_chunks_select.execute.return_value = Mock(data=[{
            "id": str(uuid.uuid4()),
            "artifact_id": str(uuid.uuid4()),
            "content": "Conteúdo",
            "embedding": [0.1] * 100,
            "section_title": "Seção",
            "section_level": 1,
            "content_type": "paragraph",
            "position": 0,
            "token_count": 10,
            "breadcrumbs": ["Seção"],
        }])
        
        def table_side_effect(table_name):
            if table_name == "artifacts":
                return mock_table
            elif table_name == "artifact_chunks":
                return mock_chunks_table
            return Mock()
        
        mock_supabase.table.side_effect = table_side_effect
        mock_create_client.return_value = mock_supabase
        
        repo = ArtifactsRepository()
        repo.supabase = mock_supabase
        
        artifact_id = ArtifactId(uuid.uuid4())
        result = await repo.find_by_id(artifact_id)
        
        # Pode retornar None se não encontrar ou Artifact se encontrar
        assert result is None or isinstance(result, Artifact)
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.artifacts_repo.create_client')
    async def test_find_all(self, mock_create_client):
        """Testa busca de todos os artefatos."""
        from app.infrastructure.persistence.artifacts_repo import ArtifactsRepository
        
        mock_supabase = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_table.select.return_value = mock_select
        mock_select.order.return_value = mock_select
        mock_select.execute.return_value = Mock(data=[{
            "id": str(uuid.uuid4()),
            "title": "Artefato",
            "source_type": "TEXT",
            "source_url": None
        }])
        
        mock_supabase.table.return_value = mock_table
        mock_create_client.return_value = mock_supabase
        
        repo = ArtifactsRepository()
        repo.supabase = mock_supabase
        
        result = await repo.find_all()
        
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.artifacts_repo.create_client')
    async def test_delete(self, mock_create_client):
        """Testa deleção de artefato."""
        from app.infrastructure.persistence.artifacts_repo import ArtifactsRepository
        
        mock_supabase = Mock()
        mock_table = Mock()
        mock_delete = Mock()
        mock_table.delete.return_value = mock_delete
        mock_delete.eq.return_value = mock_delete
        mock_delete.execute.return_value = Mock()
        
        mock_supabase.table.return_value = mock_table
        mock_create_client.return_value = mock_supabase
        
        repo = ArtifactsRepository()
        repo.supabase = mock_supabase
        
        artifact_id = ArtifactId(uuid.uuid4())
        await repo.delete(artifact_id)
        
        assert mock_table.delete.call_count >= 1


class TestConversationsRepository:
    """Testes para ConversationsRepository."""
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.conversations_repo.create_client')
    async def test_create_conversation(self, mock_create_client):
        """Testa criação de conversa."""
        from app.infrastructure.persistence.conversations_repo import ConversationsRepository
        
        mock_supabase = Mock()
        mock_table = Mock()
        mock_upsert = Mock()
        mock_upsert.execute.return_value = Mock()
        mock_table.upsert.return_value = mock_upsert
        mock_table.insert.return_value = Mock()
        mock_table.insert.return_value.execute.return_value = Mock()
        mock_supabase.table.return_value = mock_table
        mock_create_client.return_value = mock_supabase
        
        repo = ConversationsRepository()
        repo.supabase = mock_supabase
        
        result = await repo.create()
        
        assert isinstance(result, Conversation)
        assert len(result.messages) == 0
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.conversations_repo.create_client')
    async def test_find_by_id(self, mock_create_client):
        """Testa busca de conversa por ID."""
        from app.infrastructure.persistence.conversations_repo import ConversationsRepository
        
        mock_supabase = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_select
        mock_select.execute.return_value = Mock(data=[{
            "id": str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat()
        }])
        
        mock_messages_table = Mock()
        mock_messages_select = Mock()
        mock_messages_table.select.return_value = mock_messages_select
        mock_messages_select.eq.return_value = mock_messages_select
        mock_messages_select.order.return_value = mock_messages_select
        mock_messages_select.execute.return_value = Mock(data=[])
        
        def table_side_effect(table_name):
            if table_name == "conversations":
                return mock_table
            elif table_name == "messages":
                return mock_messages_table
            return Mock()
        
        mock_supabase.table.side_effect = table_side_effect
        mock_create_client.return_value = mock_supabase
        
        repo = ConversationsRepository()
        repo.supabase = mock_supabase
        
        conversation_id = ConversationId(uuid.uuid4())
        result = await repo.find_by_id(conversation_id)
        
        assert result is None or isinstance(result, Conversation)


class TestFeedbacksRepository:
    """Testes para FeedbacksRepository."""
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.feedbacks_repo.create_client')
    async def test_save_feedback(self, mock_create_client):
        """Testa salvamento de feedback."""
        from app.infrastructure.persistence.feedbacks_repo import FeedbacksRepository
        
        mock_supabase = Mock()
        mock_table = Mock()
        mock_table.insert.return_value = Mock()
        mock_table.insert.return_value.execute.return_value = Mock()
        mock_supabase.table.return_value = mock_table
        mock_create_client.return_value = mock_supabase
        
        repo = FeedbacksRepository()
        repo.supabase = mock_supabase
        
        feedback = PendingFeedback(
            id=FeedbackId(uuid.uuid4()),
            message_id=MessageId(uuid.uuid4()),
            feedback_text="Feedback",
            status=FeedbackStatus.PENDING,
            created_at=datetime.utcnow(),
            feedback_type="POSITIVE"
        )
        
        result = await repo.save(feedback)
        
        assert result == feedback
        mock_table.insert.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.feedbacks_repo.create_client')
    async def test_find_by_id(self, mock_create_client):
        """Testa busca de feedback por ID."""
        from app.infrastructure.persistence.feedbacks_repo import FeedbacksRepository
        
        feedback_id = FeedbackId(uuid.uuid4())
        message_id = MessageId(uuid.uuid4())
        
        mock_supabase = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_select
        mock_select.execute.return_value = Mock(data=[{
            "id": str(feedback_id),
            "message_id": str(message_id),
            "feedback_text": "Feedback",
            "status": "PENDING",
            "created_at": datetime.utcnow().isoformat(),
            "feedback_type": "POSITIVE"
        }])
        
        mock_supabase.table.return_value = mock_table
        mock_create_client.return_value = mock_supabase
        
        repo = FeedbacksRepository()
        repo.supabase = mock_supabase
        
        result = await repo.find_by_id(feedback_id)
        
        assert result is None or isinstance(result, PendingFeedback)
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.feedbacks_repo.create_client')
    async def test_find_pending(self, mock_create_client):
        """Testa busca de feedbacks pendentes."""
        from app.infrastructure.persistence.feedbacks_repo import FeedbacksRepository
        
        mock_supabase = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_select
        mock_select.order.return_value = mock_select
        mock_select.execute.return_value = Mock(data=[])
        
        mock_supabase.table.return_value = mock_table
        mock_create_client.return_value = mock_supabase
        
        repo = FeedbacksRepository()
        repo.supabase = mock_supabase
        
        result = await repo.find_pending()
        
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.feedbacks_repo.create_client')
    async def test_update_status(self, mock_create_client):
        """Testa atualização de status de feedback."""
        from app.infrastructure.persistence.feedbacks_repo import FeedbacksRepository
        
        feedback_id = FeedbackId(uuid.uuid4())
        message_id = MessageId(uuid.uuid4())
        
        mock_supabase = Mock()
        mock_table = Mock()
        mock_update = Mock()
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_update
        
        # Mock do resultado da query - precisa buscar após update
        mock_result = Mock()
        mock_result.data = [{
            "id": str(feedback_id),
            "message_id": str(message_id),
            "feedback_text": "Feedback",
            "status": "APPROVED",
            "created_at": datetime.utcnow().isoformat(),
            "feedback_type": None
        }]
        mock_update.execute.return_value = mock_result
        
        # Mock do select após update
        mock_select = Mock()
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_select
        mock_select.execute.return_value = mock_result
        
        mock_supabase.table.return_value = mock_table
        mock_create_client.return_value = mock_supabase
        
        repo = FeedbacksRepository()
        repo.supabase = mock_supabase
        
        result = await repo.update_status(feedback_id, FeedbackStatus.APPROVED)
        
        assert isinstance(result, PendingFeedback)
        assert result.status == FeedbackStatus.APPROVED


class TestAgentSettingsRepository:
    """Testes para AgentSettingsRepository."""
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.agent_settings_repo.create_client')
    async def test_get_instruction(self, mock_create_client):
        """Testa obtenção de instrução do agente."""
        from app.infrastructure.persistence.agent_settings_repo import AgentSettingsRepository
        
        mock_supabase = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_table.select.return_value = mock_select
        mock_select.order.return_value = mock_select
        mock_select.limit.return_value = mock_select
        
        # Mock do resultado da query
        mock_result = Mock()
        mock_result.data = [{
            "instruction": "Instrução de teste",
            "updated_at": datetime.utcnow().isoformat()
        }]
        mock_select.execute.return_value = mock_result
        
        mock_supabase.table.return_value = mock_table
        mock_create_client.return_value = mock_supabase
        
        repo = AgentSettingsRepository()
        repo.supabase = mock_supabase
        
        result = await repo.get_instruction()
        
        assert isinstance(result, AgentInstruction)
        assert result.content == "Instrução de teste"
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.agent_settings_repo.create_client')
    async def test_update_instruction(self, mock_create_client):
        """Testa atualização de instrução do agente."""
        from app.infrastructure.persistence.agent_settings_repo import AgentSettingsRepository
        
        mock_supabase = Mock()
        mock_table = Mock()
        mock_upsert = Mock()
        mock_table.upsert.return_value = mock_upsert
        
        # Mock do resultado da query - primeiro select verifica se existe
        mock_result_select = Mock()
        mock_result_select.data = [{
            "id": "test-id",
            "instruction": "Instrução antiga",
            "updated_at": datetime.utcnow().isoformat()
        }]
        
        # Mock do select após upsert
        mock_select = Mock()
        mock_table.select.return_value = mock_select
        mock_select.limit.return_value = mock_select
        mock_select.execute.return_value = mock_result_select
        
        # Mock do update
        mock_update = Mock()
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_update
        mock_update.execute.return_value = Mock()
        
        mock_supabase.table.return_value = mock_table
        mock_create_client.return_value = mock_supabase
        
        repo = AgentSettingsRepository()
        repo.supabase = mock_supabase
        
        result = await repo.update_instruction("Nova instrução")
        
        assert isinstance(result, AgentInstruction)
        assert result.content == "Nova instrução"


class TestLearningsRepository:
    """Testes para LearningsRepository."""
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.learnings_repo.create_client')
    async def test_save_learning(self, mock_create_client):
        """Testa salvamento de aprendizado."""
        from app.infrastructure.persistence.learnings_repo import LearningsRepository
        
        mock_supabase = Mock()
        mock_table = Mock()
        mock_table.insert.return_value = Mock()
        mock_table.insert.return_value.execute.return_value = Mock()
        mock_supabase.table.return_value = mock_table
        mock_create_client.return_value = mock_supabase
        
        repo = LearningsRepository()
        repo.supabase = mock_supabase
        
        learning = Learning(
            id=LearningId(uuid.uuid4()),
            content="Aprendizado",
            embedding=Embedding(vector=[0.1] * 100),
            source_feedback_id=FeedbackId(uuid.uuid4()),
            created_at=datetime.utcnow()
        )
        
        result = await repo.save(learning)
        
        assert result == learning
        mock_table.upsert.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.learnings_repo.create_client')
    async def test_find_all(self, mock_create_client):
        """Testa busca de todos os aprendizados."""
        from app.infrastructure.persistence.learnings_repo import LearningsRepository
        
        mock_supabase = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_table.select.return_value = mock_select
        mock_select.order.return_value = mock_select
        mock_select.execute.return_value = Mock(data=[])
        
        mock_supabase.table.return_value = mock_table
        mock_create_client.return_value = mock_supabase
        
        repo = LearningsRepository()
        repo.supabase = mock_supabase
        
        result = await repo.find_all()
        
        assert isinstance(result, list)

    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.learnings_repo.create_client')
    async def test_update_weights(self, mock_create_client):
        """Testa atualização de pesos de aprendizados."""
        from app.infrastructure.persistence.learnings_repo import LearningsRepository

        mock_supabase = Mock()
        mock_table = Mock()
        mock_update = Mock()
        mock_update.execute.return_value = Mock()
        mock_table.update.return_value = mock_update
        mock_supabase.table.return_value = mock_table
        mock_create_client.return_value = mock_supabase

        repo = LearningsRepository()
        repo.supabase = mock_supabase

        learning_id = LearningId(uuid.uuid4())
        await repo.update_weights({learning_id: 0.9})

        mock_table.update.assert_called_once_with({"relevance_weight": 0.9})
        mock_update.eq.assert_called_once_with("id", str(learning_id))

    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.learnings_repo.create_client')
    async def test_touch_last_used(self, mock_create_client):
        """Testa atualização de last_used_at."""
        from app.infrastructure.persistence.learnings_repo import LearningsRepository

        mock_supabase = Mock()
        mock_table = Mock()
        mock_update = Mock()
        mock_update.execute.return_value = Mock()
        mock_table.update.return_value = mock_update
        mock_supabase.table.return_value = mock_table
        mock_create_client.return_value = mock_supabase

        repo = LearningsRepository()
        repo.supabase = mock_supabase

        learning_id = LearningId(uuid.uuid4())
        await repo.touch_last_used([learning_id])

        mock_table.update.assert_called_once()
        mock_update.eq.assert_called_once_with("id", str(learning_id))

    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.learnings_repo.create_client')
    async def test_merge_learnings(self, mock_create_client):
        """Testa merge de aprendizados."""
        from app.infrastructure.persistence.learnings_repo import LearningsRepository

        mock_supabase = Mock()
        mock_table = Mock()
        mock_update = Mock()
        mock_update.execute.return_value = Mock()
        mock_table.update.return_value = mock_update
        mock_history_table = Mock()
        mock_history_table.insert.return_value = Mock()
        mock_history_table.insert.return_value.execute.return_value = Mock()

        def table_side_effect(name):
            if name == "learnings":
                return mock_table
            if name == "learning_merge_history":
                return mock_history_table
            return Mock()

        mock_supabase.table.side_effect = table_side_effect
        mock_create_client.return_value = mock_supabase

        repo = LearningsRepository()
        repo.supabase = mock_supabase

        embedding = Embedding(vector=[0.1, 0.2])
        base_learning = Learning(
            id=LearningId(uuid.uuid4()),
            content="Base",
            embedding=embedding,
            source_feedback_id=FeedbackId(uuid.uuid4()),
            created_at=datetime.utcnow(),
            relevance_weight=0.8,
        )
        duplicate_learning = Learning(
            id=LearningId(uuid.uuid4()),
            content="Duplicado",
            embedding=embedding,
            source_feedback_id=base_learning.source_feedback_id,
            created_at=datetime.utcnow(),
            relevance_weight=0.6,
        )

        repo.get_by_ids = AsyncMock(return_value=[base_learning, duplicate_learning])
        repo.save = AsyncMock(return_value=base_learning)

        result = await repo.merge(
            [base_learning.id, duplicate_learning.id],
            "Conteúdo unificado",
            merged_weight=0.9,
        )

        repo.save.assert_awaited()
        assert isinstance(result, Learning)
        assert result.relevance_weight == 0.9
        assert mock_table.update.call_count == 2

    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.learnings_repo.create_client')
    async def test_suggest_merge_candidates(self, mock_create_client):
        """Testa sugestão de candidatos a merge."""
        from app.infrastructure.persistence.learnings_repo import LearningsRepository

        base_id = uuid.uuid4()
        feedback_id = uuid.uuid4()

        mock_supabase = Mock()
        mock_rpc = Mock()
        mock_rpc.execute.return_value = Mock(data=[
            {
                "base": {
                    "id": str(base_id),
                    "content": "Base",
                    "embedding": [0.1, 0.2],
                    "source_feedback_id": str(feedback_id),
                    "created_at": datetime.utcnow().isoformat(),
                    "relevance_weight": 0.9,
                    "last_used_at": datetime.utcnow().isoformat(),
                },
                "duplicates": [],
                "similarity_score": 0.88,
            }
        ])
        mock_supabase.rpc.return_value = mock_rpc
        mock_supabase.table.return_value = Mock()
        mock_create_client.return_value = mock_supabase

        repo = LearningsRepository()
        repo.supabase = mock_supabase

        candidates = await repo.suggest_merge_candidates()
        assert len(candidates) == 1
        assert candidates[0].similarity_score == 0.88


class TestKnowledgeRepository:
    """Testes para KnowledgeRepository."""

    @pytest.mark.asyncio
    async def test_find_relevant_knowledge_combines_scores(self):
        """Garante ordenação por pontuação combinada e atualização de uso."""
        from app.infrastructure.persistence.knowledge_repo import KnowledgeRepository

        mock_client = Mock()
        artifact_id = uuid.uuid4()
        chunk_id = uuid.uuid4()

        def make_rpc_response(data):
            response = Mock()
            response.error = None
            response.data = data
            rpc_call = Mock()
            rpc_call.execute.return_value = response
            return rpc_call

        artifact_rows = [
            {
                "id": str(chunk_id),
                "artifact_id": str(artifact_id),
                "content": "Chunk",
                "embedding": [0.1, 0.2],
                "chunk_position": 0,
                "token_count": 20,
                "section_title": "Intro",
                "section_level": 1,
                "content_type": "paragraph",
                "similarity": 0.5,
                "breadcrumbs": [],
            }
        ]

        learning_row_a_id = uuid.uuid4()
        learning_row_b_id = uuid.uuid4()

        learnings_rows = [
            {
                "id": str(learning_row_a_id),
                "source_feedback_id": str(uuid.uuid4()),
                "content": "Learning A",
                "embedding": [0.3, 0.4],
                "created_at": datetime.utcnow().isoformat(),
                "relevance_weight": 0.9,
                "similarity": 0.4,
                "last_used_at": None,
            },
            {
                "id": str(learning_row_b_id),
                "source_feedback_id": str(uuid.uuid4()),
                "content": "Learning B",
                "embedding": [0.3, 0.4],
                "created_at": datetime.utcnow().isoformat(),
                "relevance_weight": 0.2,
                "similarity": 0.7,
                "last_used_at": None,
            },
        ]

        mock_client.rpc.side_effect = [
            make_rpc_response(artifact_rows),
            make_rpc_response(learnings_rows),
        ]

        mock_learnings_repo = AsyncMock()
        repo = KnowledgeRepository(client=mock_client, learnings_repo=mock_learnings_repo)

        knowledge = await repo.find_relevant_knowledge("pergunta", [0.1, 0.2, 0.3])

        assert len(knowledge.relevant_learnings) == 2
        # Learning A deve vir antes por causa do peso maior
        assert knowledge.relevant_learnings[0].content == "Learning A"
        assert knowledge.learning_scores[
            knowledge.relevant_learnings[0].id
        ] >= knowledge.learning_scores[knowledge.relevant_learnings[1].id]
        mock_learnings_repo.touch_last_used.assert_awaited_once()


class TestTopicsRepository:
    """Testes para TopicsRepository."""
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.topics_repo.create_client')
    async def test_create_topic(self, mock_create_client):
        """Testa criação de tópico."""
        from app.infrastructure.persistence.topics_repo import TopicsRepository
        
        mock_supabase = Mock()
        mock_table = Mock()
        mock_table.insert.return_value = Mock()
        mock_table.insert.return_value.execute.return_value = Mock(data=[{
            "id": str(uuid.uuid4()),
            "name": "Tópico",
            "created_at": datetime.utcnow().isoformat()
        }])
        
        mock_supabase.table.return_value = mock_table
        mock_create_client.return_value = mock_supabase
        
        repo = TopicsRepository()
        repo.supabase = mock_supabase
        
        result = await repo.create("Tópico")
        
        assert isinstance(result, Topic)
        assert result.name == "Tópico"
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.topics_repo.create_client')
    async def test_find_all(self, mock_create_client):
        """Testa busca de todos os tópicos."""
        from app.infrastructure.persistence.topics_repo import TopicsRepository
        
        mock_supabase = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_table.select.return_value = mock_select
        mock_select.order.return_value = mock_select
        mock_select.execute.return_value = Mock(data=[])
        
        mock_supabase.table.return_value = mock_table
        mock_create_client.return_value = mock_supabase
        
        repo = TopicsRepository()
        repo.supabase = mock_supabase
        
        result = await repo.find_all()
        
        assert isinstance(result, list)
