# Testes do Backend

Este diretório contém os testes automatizados para o backend da aplicação.

## Estrutura

```
tests/
├── __init__.py
├── conftest.py              # Configuração compartilhada e fixtures
├── test_dto.py              # Testes para DTOs
├── test_domain_types.py     # Testes para tipos de domínio
├── test_domain_workflows.py # Testes para workflows de domínio
├── test_api_routes.py       # Testes para rotas da API
├── test_repositories.py      # Testes para repositórios
└── test_infrastructure_services.py # Testes para serviços de infraestrutura
```

## Executando os Testes

### Instalar dependências

```bash
pip install -r requirements.txt
```

### Executar todos os testes

```bash
pytest
```

### Executar com cobertura

```bash
pytest --cov=app --cov-report=html --cov-report=term-missing
```

Isso irá:
- Executar todos os testes
- Gerar relatório de cobertura no terminal
- Gerar relatório HTML em `htmlcov/index.html`

### Executar testes específicos

```bash
# Executar um arquivo específico
pytest tests/test_dto.py

# Executar uma classe específica
pytest tests/test_dto.py::TestArtifactDTO

# Executar um teste específico
pytest tests/test_dto.py::TestArtifactDTO::test_create_artifact_dto
```

### Executar com verbose

```bash
pytest -v
```

### Executar apenas testes marcados

```bash
# Testes unitários
pytest -m unit

# Testes de integração
pytest -m integration
```

## Cobertura de Testes

Os testes cobrem:

- ✅ **DTOs**: Todos os Data Transfer Objects
- ✅ **Tipos de Domínio**: Todas as entidades e value objects
- ✅ **Workflows de Domínio**: Todas as regras de negócio
- ✅ **Rotas da API**: Todos os endpoints REST
- ✅ **Repositórios**: Persistência de dados (com mocks)
- ✅ **Serviços de Infraestrutura**: Integrações externas (com mocks)

## Fixtures Compartilhadas

O arquivo `conftest.py` contém fixtures compartilhadas que podem ser usadas em todos os testes:

- `sample_artifact_id`: ArtifactId de exemplo
- `sample_conversation_id`: ConversationId de exemplo
- `sample_message_id`: MessageId de exemplo
- `sample_embedding`: Embedding de exemplo
- `sample_artifact_chunk`: ArtifactChunk de exemplo
- `sample_artifact`: Artifact de exemplo
- `sample_conversation`: Conversation de exemplo
- `sample_message`: Message de exemplo
- `mock_embedding_generator`: Mock de EmbeddingGenerator
- `mock_pdf_processor`: Mock de PDFProcessor
- `mock_llm_service`: Mock de LLMService
- `mock_knowledge_repo`: Mock de KnowledgeRepository
- `mock_feedback_repo`: Mock de FeedbackRepository
- `mock_agent_settings_repo`: Mock de AgentSettingsRepository

## Notas

- Os testes usam mocks para isolar dependências externas (Supabase, Gemini API, etc.)
- Testes assíncronos usam `pytest-asyncio`
- A configuração do pytest está em `pytest.ini` na raiz do projeto
