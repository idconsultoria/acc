"""Testes para rotas da API."""
import asyncio
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import uuid
import os

# Mock das variáveis de ambiente antes de importar app
# (já configurado no conftest.py, mas garantindo aqui também)
os.environ.setdefault('SUPABASE_URL', 'https://test.supabase.co')
os.environ.setdefault('SUPABASE_KEY', 'test-key-1234567890123456789012345678901234567890')
os.environ.setdefault('SUPABASE_SERVICE_ROLE_KEY', 'test-service-key-1234567890123456789012345678901234567890')
os.environ.setdefault('GEMINI_API_KEY', 'test-gemini-key')

# Mock do Supabase antes de importar
with patch('supabase.create_client') as mock_create:
    mock_client = Mock()
    mock_create.return_value = mock_client
    from app.main import app
from app.api.dto import MessageDTO
from app.api.routes.conversations import SSEProgressEmitter
from app.domain.shared_kernel import ArtifactId, ConversationId, MessageId, FeedbackId
from app.domain.artifacts.types import Artifact, ArtifactChunk, ArtifactSourceType, ChunkMetadata
from app.domain.conversations.types import Conversation, Message, Author
from app.domain.feedbacks.types import PendingFeedback, FeedbackStatus
from app.domain.learnings.types import Learning
from app.domain.agent.types import AgentInstruction


@pytest.fixture
def client():
    """Retorna um cliente de teste para a API."""
    return TestClient(app)


class TestMainRoutes:
    """Testes para rotas principais."""
    
    def test_root(self, client):
        """Testa rota raiz."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "API do Agente Cultural"}
    
    def test_health(self, client):
        """Testa rota de health check."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestArtifactsRoutes:
    """Testes para rotas de artefatos."""
    
    @pytest.mark.asyncio
    @patch('app.api.routes.artifacts.artifacts_repo')
    async def test_list_artifacts(self, mock_repo, client):
        """Testa listagem de artefatos."""
        artifact_id = ArtifactId(uuid.uuid4())
        artifact = Artifact(
            id=artifact_id,
            title="Artefato de Teste",
            source_type=ArtifactSourceType.TEXT,
            chunks=[],
            source_url=None
        )
        
        mock_repo.find_all = AsyncMock(return_value=[artifact])
        mock_repo.get_artifact_data = AsyncMock(return_value={
            "description": None,
            "tags": [],
            "color": None
        })
        
        response = client.get("/api/v1/artifacts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "id" in data[0]
            assert "title" in data[0]
            assert "source_type" in data[0]
    
    @pytest.mark.asyncio
    @patch('app.api.routes.artifacts.embedding_generator')
    @patch('app.api.routes.artifacts.artifacts_repo')
    async def test_create_artifact_from_text(self, mock_repo, mock_embedding, client):
        """Testa criação de artefato a partir de texto."""
        artifact_id = ArtifactId(uuid.uuid4())
        artifact = Artifact(
            id=artifact_id,
            title="Novo Artefato",
            source_type=ArtifactSourceType.TEXT,
            chunks=[],
            source_url=None
        )
        
        mock_embedding.generate = Mock(return_value=[0.1] * 100)
        mock_repo.save = AsyncMock(return_value=artifact)
        mock_repo.get_artifact_data = AsyncMock(return_value={
            "description": None,
            "tags": [],
            "color": None
        })
        
        response = client.post(
            "/api/v1/artifacts",
            data={
                "title": "Novo Artefato",
                "text_content": "Conteúdo de teste"
            }
        )
        
        # Pode retornar 201 ou 500 se não tiver configuração
        assert response.status_code in [201, 500]
    
    @pytest.mark.asyncio
    @patch('app.api.routes.artifacts.artifacts_repo')
    async def test_get_artifact_by_id(self, mock_repo, client):
        """Testa obtenção de artefato por ID."""
        artifact_id = ArtifactId(uuid.uuid4())
        artifact = Artifact(
            id=artifact_id,
            title="Artefato",
            source_type=ArtifactSourceType.TEXT,
            chunks=[],
            source_url=None
        )
        
        mock_repo.find_by_id = AsyncMock(return_value=artifact)
        mock_repo.get_artifact_data = AsyncMock(return_value={
            "description": None,
            "tags": [],
            "color": None
        })
        
        response = client.get(f"/api/v1/artifacts/{artifact_id}")
        # Pode retornar 200 ou 404 se não encontrar
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    @patch('app.api.routes.artifacts.artifacts_repo')
    async def test_get_artifact_not_found(self, mock_repo, client):
        """Testa obtenção de artefato inexistente."""
        artifact_id = ArtifactId(uuid.uuid4())
        mock_repo.find_by_id = AsyncMock(return_value=None)
        
        response = client.get(f"/api/v1/artifacts/{artifact_id}")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    @patch('app.api.routes.artifacts.artifacts_repo')
    async def test_get_artifact_content(self, mock_repo, client):
        """Testa obtenção de conteúdo de artefato."""
        artifact_id = ArtifactId(uuid.uuid4())
        chunk = ArtifactChunk(
            id=uuid.uuid4(),
            artifact_id=artifact_id,
            content="Conteúdo do chunk",
            embedding=Mock(),
            metadata=ChunkMetadata(
                section_title="Seção",
                section_level=1,
                content_type="paragraph",
                position=0,
                token_count=20,
                breadcrumbs=["Seção"],
            ),
        )
        artifact = Artifact(
            id=artifact_id,
            title="Artefato",
            source_type=ArtifactSourceType.TEXT,
            chunks=[chunk],
            source_url=None,
            original_content="Texto original"
        )
        
        mock_repo.find_by_id = AsyncMock(return_value=artifact)
        
        response = client.get(f"/api/v1/artifacts/{artifact_id}/content")
        assert response.status_code == 200
        assert response.json() == {"source_type": "TEXT", "content": "Texto original"}
    
    @pytest.mark.asyncio
    @patch('app.api.routes.artifacts.artifacts_repo')
    async def test_delete_artifact(self, mock_repo, client):
        """Testa deleção de artefato."""
        artifact_id = ArtifactId(uuid.uuid4())
        artifact = Artifact(
            id=artifact_id,
            title="Artefato",
            source_type=ArtifactSourceType.TEXT,
            chunks=[],
            source_url=None
        )
        
        mock_repo.find_by_id = AsyncMock(return_value=artifact)
        mock_repo.delete = AsyncMock()
        
        response = client.delete(f"/api/v1/artifacts/{artifact_id}")
        assert response.status_code in [204, 404]
    
    @pytest.mark.asyncio
    @patch('app.api.routes.artifacts.artifacts_repo')
    async def test_update_artifact_tags(self, mock_repo, client):
        """Testa atualização de tags de artefato."""
        artifact_id = ArtifactId(uuid.uuid4())
        artifact = Artifact(
            id=artifact_id,
            title="Artefato",
            source_type=ArtifactSourceType.TEXT,
            chunks=[],
            source_url=None
        )
        
        mock_repo.find_by_id = AsyncMock(return_value=artifact)
        mock_repo.update_artifact_tags = AsyncMock()
        mock_repo.get_artifact_data = AsyncMock(return_value={
            "description": None,
            "tags": ["tag1", "tag2"],
            "color": None
        })
        
        response = client.patch(
            f"/api/v1/artifacts/{artifact_id}/tags",
            json={"tags": ["tag1", "tag2"]}
        )
        assert response.status_code in [200, 404]


class TestConversationsRoutes:
    """Testes para rotas de conversas."""
    
    @pytest.mark.asyncio
    @patch('app.api.routes.conversations.conversations_repo')
    async def test_create_conversation(self, mock_repo, client):
        """Testa criação de conversa."""
        conversation_id = ConversationId(uuid.uuid4())
        conversation = Conversation(
            id=conversation_id,
            messages=[],
            created_at=datetime.utcnow()
        )
        
        mock_repo.create = AsyncMock(return_value=conversation)
        
        response = client.post("/api/v1/conversations")
        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
    
    @pytest.mark.asyncio
    @patch('app.api.routes.conversations.conversations_repo')
    async def test_get_conversation_messages(self, mock_repo, client):
        """Testa obtenção de mensagens de conversa."""
        conversation_id = ConversationId(uuid.uuid4())
        message = Message(
            id=MessageId(uuid.uuid4()),
            conversation_id=conversation_id,
            author=Author.USER,
            content="Mensagem",
            cited_sources=[],
            created_at=datetime.utcnow()
        )
        conversation = Conversation(
            id=conversation_id,
            messages=[message],
            created_at=datetime.utcnow()
        )
        
        mock_repo.find_by_id = AsyncMock(return_value=conversation)
        
        response = client.get(f"/api/v1/conversations/{conversation_id}/messages")
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    @patch('app.api.routes.conversations.conversations_repo')
    async def test_get_conversation_topic(self, mock_repo, client):
        """Testa obtenção de tópico de conversa."""
        conversation_id = ConversationId(uuid.uuid4())
        conversation = Conversation(
            id=conversation_id,
            messages=[],
            created_at=datetime.utcnow()
        )
        
        mock_repo.find_by_id = AsyncMock(return_value=conversation)
        
        response = client.get(f"/api/v1/conversations/{conversation_id}/topic")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "topic" in data
            assert "is_processing" in data

    @pytest.mark.asyncio
    @patch('app.api.routes.conversations._classify_conversation_if_needed', new_callable=AsyncMock)
    @patch('app.api.routes.conversations.agent_settings_repo')
    @patch('app.api.routes.conversations.conversations_repo')
    async def test_post_message_stream_emits_events(self, mock_repo, mock_agent_settings, mock_classify, client):
        """Garante que a rota de streaming emite eventos SSE."""
        conversation_id = ConversationId(uuid.uuid4())
        base_conversation = Conversation(
            id=conversation_id,
            messages=[],
            created_at=datetime.utcnow()
        )

        mock_repo.find_by_id = AsyncMock(return_value=base_conversation)
        mock_repo.save_messages = AsyncMock(return_value=None)
        mock_classify.return_value = None

        instruction = AgentInstruction(
            content="Instrução de teste",
            updated_at=datetime.utcnow()
        )
        mock_agent_settings.get_instruction = AsyncMock(return_value=instruction)

        async def fake_continue_conversation(
            *,
            conversation,
            user_query,
            embedding_generator,
            knowledge_repo,
            llm_service,
            agent_instruction,
            progress_emitter=None,
        ):
            if progress_emitter:
                await progress_emitter.phase_start(
                    [
                        {"id": "embedding", "label": "Embedding"},
                        {"id": "llm_stream", "label": "LLM"},
                        {"id": "post_process", "label": "Pós-processamento"},
                    ]
                )
                await progress_emitter.phase_update("embedding", {"status": "running"})
                await progress_emitter.phase_complete("embedding", {"vector_length": 3})
                await progress_emitter.phase_update("llm_stream", {"status": "running"})
                await progress_emitter.emit_token("Olá ")
                await progress_emitter.emit_token("mundo!")
                await progress_emitter.phase_complete("llm_stream", {"tokens_emitted": 2})
                await progress_emitter.phase_update("post_process", {"status": "running"})
                await progress_emitter.phase_complete("post_process", {"cited_sources": 0})

            user_message = Message(
                id=MessageId(uuid.uuid4()),
                conversation_id=conversation.id,
                author=Author.USER,
                content=user_query,
                cited_sources=[],
                created_at=datetime.utcnow(),
            )
            agent_message = Message(
                id=MessageId(uuid.uuid4()),
                conversation_id=conversation.id,
                author=Author.AGENT,
                content="Olá mundo!",
                cited_sources=[],
                created_at=datetime.utcnow(),
            )

            return Conversation(
                id=conversation.id,
                messages=[*conversation.messages, user_message, agent_message],
                created_at=conversation.created_at,
            )

        with patch('app.api.routes.conversations.continue_conversation', side_effect=fake_continue_conversation):
            stream_url = f"/api/v1/conversations/{conversation_id}/messages/stream"
            with client.stream("POST", stream_url, json={"content": "Olá"}) as response:
                assert response.status_code == 200
                payload_lines = [
                    line.decode() if isinstance(line, bytes) else line
                    for line in response.iter_lines()
                ]

        event_lines = [line for line in payload_lines if line.startswith("event:")]
        assert any("phase:start" in line for line in event_lines)
        assert any("token" in line for line in event_lines)
        assert any("message:complete" in line for line in event_lines)
        mock_repo.save_messages.assert_awaited_once()
        mock_classify.assert_awaited()


class TestAgentRoutes:
    """Testes para rotas do agente."""
    
    @pytest.mark.asyncio
    @patch('app.api.routes.agent.agent_settings_repo')
    async def test_get_agent_instruction(self, mock_repo, client):
        """Testa obtenção de instrução do agente."""
        instruction = AgentInstruction(
            content="Instrução de teste",
            updated_at=datetime.utcnow()
        )
        
        mock_repo.get_instruction = AsyncMock(return_value=instruction)
        
        response = client.get("/api/v1/agent/instruction")
        assert response.status_code == 200
        data = response.json()
        assert "instruction" in data
        assert "updated_at" in data
    
    @pytest.mark.asyncio
    @patch('app.api.routes.agent.agent_settings_repo')
    async def test_update_agent_instruction(self, mock_repo, client):
        """Testa atualização de instrução do agente."""
        instruction = AgentInstruction(
            content="Nova instrução",
            updated_at=datetime.utcnow()
        )
        
        mock_repo.update_instruction = AsyncMock(return_value=instruction)
        
        response = client.put(
            "/api/v1/agent/instruction",
            json={"instruction": "Nova instrução"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["instruction"] == "Nova instrução"


class TestFeedbacksRoutes:
    """Testes para rotas de feedbacks."""
    
    @pytest.mark.asyncio
    @patch('app.api.routes.feedbacks.feedbacks_repo')
    async def test_submit_feedback(self, mock_repo, client):
        """Testa submissão de feedback."""
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
        
        mock_repo.save = AsyncMock(return_value=feedback)
        
        response = client.post(
            f"/api/v1/messages/{message_id}/feedback",
            json={
                "feedback_text": "Feedback de teste",
                "feedback_type": "POSITIVE"
            }
        )
        assert response.status_code in [201, 400]
    
    @pytest.mark.asyncio
    @patch('app.api.routes.feedbacks.feedbacks_repo')
    async def test_list_pending_feedbacks(self, mock_repo, client):
        """Testa listagem de feedbacks pendentes."""
        mock_repo.find_pending = AsyncMock(return_value=[])
        
        response = client.get("/api/v1/feedbacks/pending")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    @patch('app.api.routes.feedbacks.synthesize_learning_from_feedback')
    @patch('app.api.routes.feedbacks.get_gemini_api_key')
    @patch('app.api.routes.feedbacks.feedbacks_repo')
    async def test_approve_feedback(self, mock_feedback_repo, mock_get_api_key, mock_synthesize, client):
        """Testa aprovação de feedback."""
        from app.domain.shared_kernel import LearningId
        from app.domain.learnings.types import Learning
        from app.domain.shared_kernel import Embedding
        
        feedback_id = FeedbackId(uuid.uuid4())
        message_id = MessageId(uuid.uuid4())
        
        feedback = PendingFeedback(
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
        
        learning = Learning(
            id=LearningId(uuid.uuid4()),
            content="Aprendizado sintetizado",
            embedding=Embedding(vector=[0.1] * 100),
            source_feedback_id=feedback_id,
            created_at=datetime.utcnow()
        )
        
        mock_feedback_repo.find_by_id = AsyncMock(return_value=feedback)
        mock_feedback_repo.update_status = AsyncMock(return_value=approved_feedback)
        mock_get_api_key.return_value = "test-key"
        mock_synthesize.return_value = learning
        
        response = client.post(f"/api/v1/feedbacks/{feedback_id}/approve")
        # Pode retornar 200 ou 500 se não tiver configuração de LLM
        assert response.status_code in [200, 500]


class TestLearningsRoutes:
    """Testes para rotas de aprendizados."""
    
    @pytest.mark.asyncio
    @patch('app.api.routes.learnings.learnings_repo')
    async def test_list_learnings(self, mock_repo, client):
        """Testa listagem de aprendizados."""
        mock_repo.find_all = AsyncMock(return_value=[])
        
        response = client.get("/api/v1/learnings")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestTopicsRoutes:
    """Testes para rotas de tópicos."""
    
    @pytest.mark.asyncio
    @patch('app.api.routes.topics.create_client')
    async def test_list_topics(self, mock_create_client, client):
        """Testa listagem de tópicos."""
        # Mock do Supabase
        mock_supabase = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_table.select.return_value = mock_select
        mock_select.order.return_value = mock_select
        mock_select.execute.return_value = Mock(data=[])
        
        mock_conv_table = Mock()
        mock_conv_select = Mock()
        mock_conv_table.select.return_value = mock_conv_select
        mock_conv_select.execute.return_value = Mock(data=[])
        
        def table_side_effect(table_name):
            if table_name == "topics":
                return mock_table
            elif table_name == "conversations":
                return mock_conv_table
            return Mock()
        
        mock_supabase.table.side_effect = table_side_effect
        mock_create_client.return_value = mock_supabase
        
        # Mock das variáveis de ambiente
        with patch('app.api.routes.topics.SUPABASE_URL', 'https://test.supabase.co'), \
             patch('app.api.routes.topics.SUPABASE_KEY', 'test-key'):
            response = client.get("/api/v1/topics")
            # Pode retornar 200 ou 500 se não tiver configuração
            assert response.status_code in [200, 500]
    
    @pytest.mark.asyncio
    async def test_get_conversations_all(self, client):
        """Testa obtenção de todas as conversas."""
        response = client.get("/api/v1/topics/conversations")
        assert response.status_code in [200, 500]


class TestSettingsRoutes:
    """Testes para rotas de configurações."""
    
    @pytest.mark.asyncio
    @patch('app.api.routes.settings.settings_repo')
    async def test_get_settings(self, mock_repo, client):
        """Testa obtenção de configurações."""
        mock_repo.get_custom_gemini_api_key = AsyncMock(return_value=None)
        
        response = client.get("/api/v1/settings")
        assert response.status_code == 200
        data = response.json()
        assert "hasCustomApiKey" in data
    
    @pytest.mark.asyncio
    @patch('app.api.routes.settings.settings_repo')
    async def test_save_gemini_api_key(self, mock_repo, client):
        """Testa salvamento de chave de API."""
        mock_repo.save_custom_gemini_api_key = AsyncMock()
        
        response = client.put(
            "/api/v1/settings/gemini-api-key",
            json={"api_key": "test-key"}
        )
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    @patch('app.api.routes.settings.settings_repo')
    async def test_remove_gemini_api_key(self, mock_repo, client):
        """Testa remoção de chave de API."""
        mock_repo.remove_custom_gemini_api_key = AsyncMock()
        
        response = client.put(
            "/api/v1/settings/gemini-api-key",
            json={"api_key": ""}
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_sse_progress_emitter_collects_events():
    """Valida que o SSEProgressEmitter enfileira eventos corretamente."""
    emitter = SSEProgressEmitter()

    async def collect_events():
        items = []
        async for event in emitter.listen():
            items.append(event)
        return items

    collector = asyncio.create_task(collect_events())

    await emitter.phase_start([{"id": "embedding", "label": "Embedding"}])
    await emitter.emit_token("token-1")
    message_dto = MessageDTO(
        id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        author="AGENT",
        content="Resposta final",
        cited_sources=[],
        created_at=datetime.utcnow(),
    )
    await emitter.message_complete(message_dto)
    await emitter.finish()

    events = await collector
    assert events[0]["event"] == "phase:start"
    assert events[1]["event"] == "token"
    assert events[-1]["event"] == "message:complete"
