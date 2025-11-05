# Documento 4: Modelagem Tática do Domínio (Backend - Python)

**Arquivo:** `design/4_modelagem_tatica_backend.md`

**Propósito:** Detalhar a estrutura interna do backend em Python. Este documento define os tipos de dados do domínio e as assinaturas das funções de negócio (workflows), servindo como um guia para a implementação da lógica central da aplicação de forma limpa, testável e desacoplada.

**Público-alvo:** Desenvolvedor Backend.

---

### 1. Estrutura de Módulos (Pacotes)

A organização do código seguirá a separação de responsabilidades inspirada na "Onion Architecture" e nos Bounded Contexts.

```
backend/app/
├── api/                  # Camada de Apresentação (FastAPI)
│   ├── routes/
│   │   ├── artifacts.py
│   │   ├── conversations.py
│   │   ├── feedbacks.py
│   │   ├── learnings.py
│   │   └── agent.py
│   └── dto.py            # Data Transfer Objects (Pydantic models)
│
├── domain/               # Lógica de Negócio e Tipos do Domínio
│   ├── artifacts/
│   │   ├── types.py
│   │   └── workflows.py
│   ├── conversations/
│   │   ├── types.py
│   │   └── workflows.py
│   ├── feedbacks/
│   │   ├── types.py
│   │   └── workflows.py
│   ├── learnings/
│   │   ├── types.py
│   │   └── workflows.py
│   ├── agent/
│   │   ├── types.py
│   │   └── workflows.py
│   └── shared_kernel.py  # Tipos compartilhados entre domínios
│
└── infrastructure/       # Implementação de I/O
    ├── persistence/
    │   ├── artifacts_repo.py
    │   ├── conversations_repo.py
    │   ├── feedbacks_repo.py
    │   └── learnings_repo.py
    ├── ai/
    │   ├── gemini_service.py
    │   └── embedding_service.py
    └── files/
        └── pdf_processor.py
```

### 2. Modelagem de Domínio (`domain/`)

Esta é a parte mais importante. Define os "substantivos" (tipos) e "verbos" (workflows) do nosso negócio.

#### 2.1. Kernel Compartilhado (`domain/shared_kernel.py`)

Tipos simples e IDs que são usados em múltiplos contextos.

```python
# domain/shared_kernel.py
from dataclasses import dataclass
from datetime import datetime
from typing import NewType
import uuid

# Usando NewType para criar tipos distintos e evitar misturar UUIDs
ArtifactId = NewType("ArtifactId", uuid.UUID)
ConversationId = NewType("ConversationId", uuid.UUID)
MessageId = NewType("MessageId", uuid.UUID)
ChunkId = NewType("ChunkId", uuid.UUID)
FeedbackId = NewType("FeedbackId", uuid.UUID)
LearningId = NewType("LearningId", uuid.UUID)

# Value Object para representar o texto de um embedding
@dataclass(frozen=True)
class Embedding:
    vector: list[float]
```

#### 2.2. Domínio de Artefatos (`domain/artifacts/`)

##### `types.py` - Tipos de Dados

```python
# domain/artifacts/types.py
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
from app.domain.shared_kernel import ArtifactId, ChunkId, Embedding

class ArtifactSourceType(Enum):
    PDF = auto()
    TEXT = auto()

# Value Object que representa um pedaço de um artefato
@dataclass(frozen=True)
class ArtifactChunk:
    id: ChunkId
    artifact_id: ArtifactId
    content: str
    embedding: Embedding

# Entidade principal/Aggregate Root deste domínio
@dataclass(frozen=True)
class Artifact:
    id: ArtifactId
    title: str
    source_type: ArtifactSourceType
    chunks: list[ArtifactChunk]
    source_url: Optional[str] = None # Link para o PDF no Supabase Storage
```

##### `workflows.py` - Assinaturas das Funções

Estas são funções puras que recebem todas as suas dependências como argumentos (o I/O).

```python
# domain/artifacts/workflows.py
from typing import Protocol, Union
from app.domain.artifacts.types import Artifact, AgentInstruction

# --- Interfaces de Dependência (Protocolos) ---
# Definem o "contrato" que a infraestrutura deve implementar

class PDFProcessor(Protocol):
    def extract_text(self, file_content: bytes) -> str: ...

class EmbeddingGenerator(Protocol):
    def generate(self, text: str) -> list[float]: ...

# --- Assinaturas dos Workflows ---

def create_artifact_from_text(
    title: str,
    text_content: str,
    embedding_generator: EmbeddingGenerator
) -> Artifact:
    """
    Workflow para criar um artefato a partir de texto.
    Ele é responsável por dividir o texto em chunks e gerar os embeddings.
    """
    # ... Lógica de chunking e criação do objeto Artifact ...
    pass

def create_artifact_from_pdf(
    title: str,
    pdf_content: bytes,
    pdf_processor: PDFProcessor,
    embedding_generator: EmbeddingGenerator
) -> tuple[Artifact, bytes]: # Retorna o artefato e o conteúdo original para salvar
    """
    Workflow para criar um artefato a partir de um PDF.
    Extrai o texto, faz o chunking e gera embeddings.
    """
    # ... Lógica de extração, chunking e criação ...
    pass
```

#### 2.3. Domínio de Conversas (`domain/conversations/`)

##### `types.py` - Tipos de Dados

```python
# domain/conversations/types.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from app.domain.shared_kernel import ConversationId, MessageId, ArtifactId

class Author(Enum):
    USER = auto()
    AGENT = auto()

# Value Object que representa uma fonte citada
@dataclass(frozen=True)
class CitedSource:
    artifact_id: ArtifactId
    title: str
    chunk_content_preview: str

# Entidade que compõe o agregado Conversa
@dataclass(frozen=True)
class Message:
    id: MessageId
    author: Author
    content: str
    cited_sources: list[CitedSource]
    created_at: datetime

# Aggregate Root deste domínio
@dataclass(frozen=True)
class Conversation:
    id: ConversationId
    messages: list[Message]
    created_at: datetime
```

##### `workflows.py` - Assinaturas das Funções

```python
# domain/conversations/workflows.py
from typing import Protocol
from app.domain.conversations.types import Conversation, Message
from app.domain.artifacts.types import ArtifactChunk
from app.domain.learnings.types import Learning
from app.domain.agent.types import AgentInstruction

# --- Interfaces de Dependência (Protocolos) ---

class RelevantKnowledge(Protocol):
    """Representa o conhecimento relevante encontrado para uma consulta."""
    relevant_artifacts: list[ArtifactChunk]
    relevant_learnings: list[Learning]

class KnowledgeRepository(Protocol):
    """Interface para buscar conhecimento relevante (RAG)."""
    async def find_relevant_knowledge(self, user_query: str) -> RelevantKnowledge: ...

class LLMService(Protocol):
    """Interface para o Large Language Model."""
    async def generate_advice(
        self,
        instruction: AgentInstruction,
        conversation_history: list[Message],
        knowledge: RelevantKnowledge,
        user_query: str
    ) -> Message: # Retorna a nova mensagem do agente
        ...

# --- Assinatura do Workflow Principal ---

async def continue_conversation(
    conversation: Conversation,
    user_query: str,
    knowledge_repo: KnowledgeRepository,
    llm_service: LLMService,
    agent_instruction: AgentInstruction
) -> Conversation:
    """
    Orquestra a continuação de uma conversa, gerando a resposta do agente.    
    1. Busca conhecimento relevante.
    2. Constrói o prompt.
    3. Chama o LLM.
    4. Adiciona a mensagem do usuário e a resposta do agente à conversa.      
    5. Retorna o novo estado da conversa.
    """
    # ... Lógica pura de orquestração ...
    pass
```

#### 2.4. Domínio de Feedbacks (`domain/feedbacks/`)

##### `types.py` - Tipos de Dados

```python
# domain/feedbacks/types.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from app.domain.shared_kernel import MessageId, FeedbackId

class FeedbackStatus(Enum):
    PENDING = auto()
    APPROVED = auto()
    REJECTED = auto()

# Entidade principal deste domínio
@dataclass(frozen=True)
class PendingFeedback:
    id: FeedbackId
    message_id: MessageId
    feedback_text: str
    status: FeedbackStatus
    created_at: datetime
```

##### `workflows.py` - Assinaturas das Funções

```python
# domain/feedbacks/workflows.py
from typing import Protocol
from app.domain.feedbacks.types import PendingFeedback, FeedbackStatus

# --- Interfaces de Dependência (Protocolos) ---

class FeedbackRepository(Protocol):
    """Interface para persistir e recuperar feedbacks."""
    async def save(self, feedback: PendingFeedback) -> PendingFeedback: ...
    async def find_by_id(self, feedback_id: FeedbackId) -> PendingFeedback | None: ...
    async def find_pending(self) -> list[PendingFeedback]: ...
    async def update_status(self, feedback_id: FeedbackId, status: FeedbackStatus) -> PendingFeedback: ...

# --- Assinaturas dos Workflows ---

async def submit_feedback(
    message_id: MessageId,
    feedback_text: str,
    feedback_repo: FeedbackRepository
) -> PendingFeedback:
    """
    Cria um novo feedback pendente associado a uma mensagem do agente.
    """
    # ... Lógica de criação ...
    pass

async def approve_feedback(
    feedback_id: FeedbackId,
    feedback_repo: FeedbackRepository
) -> PendingFeedback:
    """
    Aprova um feedback, alterando seu status para APPROVED.
    """
    # ... Lógica de aprovação ...
    pass

async def reject_feedback(
    feedback_id: FeedbackId,
    feedback_repo: FeedbackRepository
) -> PendingFeedback:
    """
    Rejeita um feedback, alterando seu status para REJECTED.
    """
    # ... Lógica de rejeição ...
    pass
```

#### 2.5. Domínio de Aprendizados (`domain/learnings/`)

##### `types.py` - Tipos de Dados

```python
# domain/learnings/types.py
from dataclasses import dataclass
from datetime import datetime
from app.domain.shared_kernel import LearningId, FeedbackId, Embedding

# Entidade principal deste domínio
@dataclass(frozen=True)
class Learning:
    id: LearningId
    content: str
    embedding: Embedding
    source_feedback_id: FeedbackId
    created_at: datetime
```

##### `workflows.py` - Assinaturas das Funções

```python
# domain/learnings/workflows.py
from typing import Protocol
from app.domain.learnings.types import Learning
from app.domain.feedbacks.types import PendingFeedback

# --- Interfaces de Dependência (Protocolos) ---

class LLMService(Protocol):
    """Interface para síntese de aprendizados usando LLM."""
    async def synthesize_learning(self, feedback_text: str) -> str: ...

class EmbeddingGenerator(Protocol):
    def generate(self, text: str) -> list[float]: ...

class LearningRepository(Protocol):
    """Interface para persistir aprendizados."""
    async def save(self, learning: Learning) -> Learning: ...
    async def find_all(self) -> list[Learning]: ...

# --- Assinaturas dos Workflows ---

async def synthesize_learning_from_feedback(
    feedback: PendingFeedback,
    llm_service: LLMService,
    embedding_generator: EmbeddingGenerator,
    learning_repo: LearningRepository
) -> Learning:
    """
    Sintetiza um novo aprendizado a partir de um feedback aprovado.
    1. Usa o LLM para transformar o feedback_text em um insight conciso e reutilizável.
    2. Gera um embedding para o aprendizado.
    3. Persiste o aprendizado no repositório.
    4. Retorna o aprendizado criado.
    """
    # ... Lógica de síntese ...
    pass
```

#### 2.6. Domínio do Agente (`domain/agent/`)

##### `types.py` - Tipos de Dados

```python
# domain/agent/types.py
from dataclasses import dataclass
from datetime import datetime

# Value Object para configuração do agente
@dataclass(frozen=True)
class AgentInstruction:
    content: str
    updated_at: datetime
```

##### `workflows.py` - Assinaturas das Funções

```python
# domain/agent/workflows.py
from typing import Protocol
from app.domain.agent.types import AgentInstruction
from datetime import datetime

# --- Interfaces de Dependência (Protocolos) ---

class AgentSettingsRepository(Protocol):
    """Interface para persistir a instrução do agente."""
    async def get_instruction(self) -> AgentInstruction: ...
    async def update_instruction(self, content: str) -> AgentInstruction: ...

# --- Assinaturas dos Workflows ---

async def get_agent_instruction(
    settings_repo: AgentSettingsRepository
) -> AgentInstruction:
    """
    Obtém a instrução geral atual do agente.
    """
    # ... Lógica de recuperação ...
    pass

async def update_agent_instruction(
    new_content: str,
    settings_repo: AgentSettingsRepository
) -> AgentInstruction:
    """
    Atualiza a instrução geral do agente.
    """
    # ... Lógica de atualização ...
    pass
```

### 3. Camada de Apresentação (`api/dto.py`)

Estes são os modelos `Pydantic` que definem os DTOs (Data Transfer Objects) para a API, alinhados com a especificação OpenAPI. Eles atuam como a camada de validação e serialização na borda da aplicação. 

```python
# api/dto.py
from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Literal

class ArtifactDTO(BaseModel):
    id: UUID4
    title: str
    source_type: Literal["PDF", "TEXT"]
    created_at: datetime

class CitedSourceDTO(BaseModel):
    artifact_id: UUID4
    title: str
    chunk_content_preview: str

class MessageDTO(BaseModel):
    id: UUID4
    conversation_id: UUID4
    author: Literal["USER", "AGENT"]
    content: str
    cited_sources: list[CitedSourceDTO] = []
    created_at: datetime

class CreateMessagePayload(BaseModel):
    content: str

class PendingFeedbackDTO(BaseModel):
    id: UUID4
    message_id: UUID4
    feedback_text: str
    status: Literal["PENDING", "APPROVED", "REJECTED"]
    created_at: datetime
    message_preview: str | None = None

class SubmitFeedbackPayload(BaseModel):
    feedback_text: str

class LearningDTO(BaseModel):
    id: UUID4
    content: str
    source_feedback_id: UUID4
    created_at: datetime

class AgentInstructionDTO(BaseModel):
    instruction: str
    updated_at: datetime

class UpdateAgentInstructionPayload(BaseModel):
    instruction: str
```

### 4. Guia para o Desenvolvedor Backend

1.  **Comece pelos Tipos:** Implemente os arquivos `types.py` em `domain/`. Use `dataclasses(frozen=True)` para garantir a imutabilidade. Comece pelos domínios mais fundamentais: `shared_kernel`, `artifacts`, `conversations`, `agent`, `feedbacks`, e `learnings`.                       
2.  **Implemente os Workflows Puros:** Escreva a lógica nos arquivos `workflows.py`. Finja que as dependências (protocolos) já existem. Você pode escrever testes unitários para esses workflows usando implementações falsas (mocks/stubs) dos protocolos. Note que o workflow de `approve_feedback` deve acionar `synthesize_learning_from_feedback`.                                                              
3.  **Implemente a Infraestrutura:** Crie as classes concretas em `infrastructure/` que implementam os protocolos definidos no domínio.                        
    *   `infrastructure/persistence/artifacts_repo.py` implementará a busca no Supabase.                                                                       
    *   `infrastructure/persistence/feedbacks_repo.py` implementará o CRUD de feedbacks.
    *   `infrastructure/persistence/learnings_repo.py` implementará o CRUD de aprendizados.
    *   `infrastructure/ai/gemini_service.py` implementará a chamada à API do Gemini (tanto para geração de conselhos quanto para síntese de aprendizados).                                                                         
    *   `infrastructure/ai/embedding_service.py` implementará a geração de embeddings.
4.  **Conecte Tudo na API:** Nos arquivos em `api/routes/`, use um sistema de injeção de dependência (como o do FastAPI) para "montar" os workflows, injetando as implementações da infraestrutura nas funções de domínio. O código do endpoint deve ser mínimo, apenas orquestrando as chamadas. Implemente os routers para: `artifacts.py`, `conversations.py`, `feedbacks.py`, `learnings.py`, e `agent.py`.

Este documento fornece a estrutura e os contratos internos do backend. O desenvolvedor tem um caminho claro, começando do núcleo puro do domínio e movendo-se para as bordas impuras da infraestrutura.