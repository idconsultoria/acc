"""Testes para serviços de infraestrutura."""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from app.infrastructure.ai.embedding_service import EmbeddingGenerator
from app.infrastructure.ai.gemini_service import GeminiService, RelevantKnowledge, get_gemini_api_key
from app.infrastructure.ai.topic_classifier import TopicClassifier
from app.infrastructure.files.pdf_processor import PDFProcessor
from app.domain.artifacts.types import ArtifactChunk, ChunkMetadata
from app.domain.learnings.types import Learning
from app.domain.agent.types import AgentInstruction
from app.domain.conversations.types import Message, Author
from app.domain.shared_kernel import ArtifactId, ChunkId, FeedbackId, LearningId, Embedding
from datetime import datetime
import uuid


class TestEmbeddingGenerator:
    """Testes para EmbeddingGenerator."""
    
    @patch('app.infrastructure.ai.embedding_service.genai')
    def test_generate_embedding(self, mock_genai):
        """Testa geração de embedding."""
        mock_embed_content = Mock(return_value={'embedding': [0.1, 0.2, 0.3] * 33})
        mock_genai.embed_content = mock_embed_content
        
        generator = EmbeddingGenerator(api_key="test-key")
        result = generator.generate("Texto de teste")
        
        assert isinstance(result, list)
        assert len(result) > 0
        mock_embed_content.assert_called_once()
    
    @patch('app.infrastructure.ai.embedding_service.genai')
    def test_generate_embedding_fallback(self, mock_genai):
        """Testa geração de embedding com fallback."""
        # Primeira chamada falha
        mock_embed_content = Mock(side_effect=[
            Exception("Erro"),
            {'embedding': [0.1, 0.2, 0.3] * 33}
        ])
        mock_genai.embed_content = mock_embed_content
        
        generator = EmbeddingGenerator(api_key="test-key")
        result = generator.generate("Texto de teste")
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert mock_embed_content.call_count == 2
    
    @patch('app.infrastructure.ai.embedding_service.genai')
    def test_generate_embedding_error(self, mock_genai):
        """Testa geração de embedding com erro."""
        mock_embed_content = Mock(side_effect=Exception("Erro"))
        mock_genai.embed_content = mock_embed_content
        
        generator = EmbeddingGenerator(api_key="test-key")
        
        with pytest.raises(ValueError):
            generator.generate("Texto de teste")


class TestGeminiService:
    """Testes para GeminiService."""
    
    @pytest.fixture
    def gemini_service(self):
        """Retorna uma instância de GeminiService."""
        with patch('app.infrastructure.ai.gemini_service.genai'):
            return GeminiService(api_key="test-key")
    
    @pytest.mark.asyncio
    async def test_generate_advice(self, gemini_service):
        """Testa geração de conselho."""
        with patch.object(gemini_service.model, 'generate_content') as mock_generate:
            mock_response = Mock()
            mock_response.text = "Resposta do agente"
            mock_generate.return_value = mock_response
            
            instruction = AgentInstruction(
                content="Instrução",
                updated_at=datetime.utcnow()
            )
            
            knowledge = RelevantKnowledge(
                relevant_artifacts=[],
                relevant_learnings=[]
            )
            
            content, cited_chunks = await gemini_service.generate_advice(
                instruction=instruction,
                conversation_history=[],
                knowledge=knowledge,
                user_query="Pergunta"
            )
            
            assert content == "Resposta do agente"
            assert isinstance(cited_chunks, list)
            mock_generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_advice_with_artifacts(self, gemini_service):
        """Testa geração de conselho com artefatos."""
        with patch.object(gemini_service.model, 'generate_content') as mock_generate:
            mock_response = Mock()
            mock_response.text = "Resposta com citação"
            mock_generate.return_value = mock_response
            
            artifact_chunk = ArtifactChunk(
                id=ChunkId(uuid.uuid4()),
                artifact_id=ArtifactId(uuid.uuid4()),
                content="Conteúdo do chunk",
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
            
            knowledge = RelevantKnowledge(
                relevant_artifacts=[artifact_chunk],
                relevant_learnings=[]
            )
            
            instruction = AgentInstruction(
                content="Instrução",
                updated_at=datetime.utcnow()
            )
            
            content, cited_chunks = await gemini_service.generate_advice(
                instruction=instruction,
                conversation_history=[],
                knowledge=knowledge,
                user_query="Pergunta"
            )
            
            assert len(cited_chunks) == 1
            assert cited_chunks[0] == artifact_chunk
    
    @pytest.mark.asyncio
    async def test_synthesize_learning(self, gemini_service):
        """Testa síntese de aprendizado."""
        with patch.object(gemini_service.model, 'generate_content') as mock_generate:
            mock_response = Mock()
            mock_response.text = "Aprendizado sintetizado"
            mock_generate.return_value = mock_response
            
            result = await gemini_service.synthesize_learning("Feedback de teste")
            
            assert result == "Aprendizado sintetizado"
            mock_generate.assert_called_once()


class TestGetGeminiApiKey:
    """Testes para get_gemini_api_key."""
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.settings_repo.SettingsRepository')
    async def test_get_custom_api_key(self, mock_settings_repo_class):
        """Testa obtenção de chave de API personalizada."""
        mock_settings_repo = AsyncMock()
        mock_settings_repo.get_custom_gemini_api_key = AsyncMock(return_value="custom-key")
        mock_settings_repo_class.return_value = mock_settings_repo
        
        # Mock do GEMINI_API_KEY
        with patch('app.infrastructure.persistence.config.GEMINI_API_KEY', 'default-key'):
            result = await get_gemini_api_key()
        
        assert result == "custom-key"
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.persistence.settings_repo.SettingsRepository')
    async def test_get_default_api_key(self, mock_settings_repo_class):
        """Testa obtenção de chave de API padrão."""
        mock_settings_repo = AsyncMock()
        mock_settings_repo.get_custom_gemini_api_key = AsyncMock(return_value=None)
        mock_settings_repo_class.return_value = mock_settings_repo
        
        # Mock do GEMINI_API_KEY
        with patch('app.infrastructure.persistence.config.GEMINI_API_KEY', 'default-key'):
            result = await get_gemini_api_key()
        
        assert result == "default-key"


class TestTopicClassifier:
    """Testes para TopicClassifier."""
    
    @pytest.fixture
    def topic_classifier(self):
        """Retorna uma instância de TopicClassifier."""
        with patch('app.infrastructure.ai.topic_classifier.genai'):
            return TopicClassifier(api_key="test-key")
    
    @pytest.mark.asyncio
    async def test_classify_conversation_new_topic(self, topic_classifier):
        """Testa classificação de conversa com novo tópico."""
        with patch.object(topic_classifier.model, 'generate_content') as mock_generate:
            mock_response = Mock()
            mock_response.text = "Novo Tópico"
            mock_generate.return_value = mock_response
            
            result = await topic_classifier.classify_conversation(
                user_query="Pergunta",
                agent_response="Resposta",
                existing_topics=[]
            )
            
            assert result == "Novo Tópico"
            mock_generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_classify_conversation_existing_topic(self, topic_classifier):
        """Testa classificação de conversa com tópico existente."""
        with patch.object(topic_classifier.model, 'generate_content') as mock_generate:
            mock_response = Mock()
            mock_response.text = "Tópico Existente"
            mock_generate.return_value = mock_response
            
            result = await topic_classifier.classify_conversation(
                user_query="Pergunta",
                agent_response="Resposta",
                existing_topics=["Tópico Existente", "Outro Tópico"]
            )
            
            assert result == "Tópico Existente"
    
    @pytest.mark.asyncio
    async def test_classify_conversation_error(self, topic_classifier):
        """Testa classificação de conversa com erro."""
        with patch.object(topic_classifier.model, 'generate_content') as mock_generate:
            mock_generate.side_effect = Exception("Erro")
            
            result = await topic_classifier.classify_conversation(
                user_query="Pergunta",
                agent_response="Resposta",
                existing_topics=[]
            )
            
            # Deve retornar "Geral" em caso de erro
            assert result == "Geral"
    
    @pytest.mark.asyncio
    async def test_classify_conversation_normalize(self, topic_classifier):
        """Testa normalização de nome de tópico."""
        with patch.object(topic_classifier.model, 'generate_content') as mock_generate:
            mock_response = Mock()
            mock_response.text = "Tópico com pontuação!!!"
            mock_generate.return_value = mock_response
            
            result = await topic_classifier.classify_conversation(
                user_query="Pergunta",
                agent_response="Resposta",
                existing_topics=[]
            )
            
            # Deve remover pontuação extra
            assert "!!!" not in result


class TestPDFProcessor:
    """Testes para PDFProcessor."""
    
    def test_extract_text_not_implemented(self):
        """Testa que extract_text retorna string vazia quando não há suporte."""
        processor = PDFProcessor()
        
        text = processor.extract_text(b"PDF content")
        assert isinstance(text, str)
        assert text == ""
    
    def test_pdf_processor_message(self):
        """Testa fallback de extract_with_metadata quando não há suporte."""
        processor = PDFProcessor()
        
        segments = processor.extract_with_metadata(b"PDF content")
        assert isinstance(segments, list)
        assert segments == [] or (len(segments) == 1 and isinstance(segments[0], tuple))


class TestRelevantKnowledge:
    """Testes para RelevantKnowledge."""
    
    def test_create_relevant_knowledge(self):
        """Testa criação de RelevantKnowledge."""
        artifact_chunk = ArtifactChunk(
            id=ChunkId(uuid.uuid4()),
            artifact_id=ArtifactId(uuid.uuid4()),
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
        
        learning = Learning(
            id=LearningId(uuid.uuid4()),
            content="Aprendizado",
            embedding=Embedding(vector=[0.1] * 100),
            source_feedback_id=FeedbackId(uuid.uuid4()),
            created_at=datetime.utcnow()
        )
        
        knowledge = RelevantKnowledge(
            relevant_artifacts=[artifact_chunk],
            relevant_learnings=[learning]
        )
        
        assert len(knowledge.relevant_artifacts) == 1
        assert len(knowledge.relevant_learnings) == 1
        assert knowledge.relevant_artifacts[0] == artifact_chunk
        assert knowledge.relevant_learnings[0] == learning
    
    def test_relevant_knowledge_empty(self):
        """Testa RelevantKnowledge vazio."""
        knowledge = RelevantKnowledge(
            relevant_artifacts=[],
            relevant_learnings=[]
        )
        
        assert len(knowledge.relevant_artifacts) == 0
        assert len(knowledge.relevant_learnings) == 0
