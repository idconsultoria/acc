"""Workflows do domínio de Conversas."""
from typing import Protocol
from datetime import datetime
from app.domain.conversations.types import Conversation, Message, Author, CitedSource
from app.domain.artifacts.types import ArtifactChunk
from app.domain.learnings.types import Learning
from app.domain.agent.types import AgentInstruction
from app.domain.shared_kernel import ConversationId, MessageId
import uuid


# --- Interfaces de Dependência (Protocolos) ---

class RelevantKnowledge(Protocol):
    """Representa o conhecimento relevante encontrado para uma consulta."""
    relevant_artifacts: list[ArtifactChunk]
    relevant_learnings: list[Learning]


class KnowledgeRepository(Protocol):
    """Interface para buscar conhecimento relevante (RAG)."""
    async def find_relevant_knowledge(self, user_query: str, embedding: list[float]) -> RelevantKnowledge:
        """Busca conhecimento relevante usando busca vetorial."""
        ...


class LLMService(Protocol):
    """Interface para o Large Language Model."""
    async def generate_advice(
        self,
        instruction: AgentInstruction,
        conversation_history: list[Message],
        knowledge: RelevantKnowledge,
        user_query: str,
        progress_emitter: "ProgressEmitter | None" = None
    ) -> tuple[str, list[ArtifactChunk]]:
        """
        Gera conselho cultural baseado no contexto.
        
        Returns:
            Tupla com (conteúdo da resposta em markdown, lista de chunks citados)
        """
        ...


class EmbeddingGenerator(Protocol):
    """Interface para geração de embeddings."""
    def generate(self, text: str) -> list[float]:
        """Gera um embedding para um texto."""
        ...


class ProgressEmitter(Protocol):
    """Interface para emissão de eventos de progresso durante o workflow."""

    async def phase_start(self, phases: list[dict[str, str]]) -> None:
        """Emite evento inicial com as fases do pipeline."""
        ...

    async def phase_update(self, phase: str, data: dict[str, object] | None = None) -> None:
        """Atualiza o status ou metadados de uma fase."""
        ...

    async def phase_complete(self, phase: str, data: dict[str, object] | None = None) -> None:
        """Marca a conclusão de uma fase."""
        ...

    async def emit_token(self, token: str) -> None:
        """Emite um token gerado pelo modelo."""
        ...


# --- Assinatura do Workflow Principal ---

async def continue_conversation(
    conversation: Conversation,
    user_query: str,
    embedding_generator: EmbeddingGenerator,
    knowledge_repo: KnowledgeRepository,
    llm_service: LLMService,
    agent_instruction: AgentInstruction,
    progress_emitter: ProgressEmitter | None = None
) -> Conversation:
    """
    Orquestra a continuação de uma conversa, gerando a resposta do agente.
    1. Busca conhecimento relevante.
    2. Constrói o prompt.
    3. Chama o LLM.
    4. Adiciona a mensagem do usuário e a resposta do agente à conversa.
    5. Retorna o novo estado da conversa.
    """
    phases_definition = [
        {"id": "embedding", "label": "Geração de embedding"},
        {"id": "retrieval", "label": "Busca de conhecimento"},
        {"id": "prompt_build", "label": "Construção do prompt"},
        {"id": "llm_stream", "label": "Geração da resposta"},
        {"id": "post_process", "label": "Pós-processamento"},
    ]

    if progress_emitter:
        await progress_emitter.phase_start(phases_definition)
        await progress_emitter.phase_update("embedding", {"status": "running"})

    # Gera embedding para a consulta do usuário
    query_embedding = embedding_generator.generate(user_query)

    if progress_emitter:
        await progress_emitter.phase_complete(
            "embedding",
            {
                "vector_length": len(query_embedding),
            },
        )
        await progress_emitter.phase_update("retrieval", {"status": "running"})
    
    # Busca conhecimento relevante
    knowledge = await knowledge_repo.find_relevant_knowledge(user_query, query_embedding)

    if progress_emitter:
        await progress_emitter.phase_complete(
            "retrieval",
            {
                "chunks": len(knowledge.relevant_artifacts),
                "learnings": len(knowledge.relevant_learnings),
            },
        )
        await progress_emitter.phase_update("prompt_build", {"status": "running"})
    
    # Gera a resposta do agente
    agent_content, cited_chunks = await llm_service.generate_advice(
        instruction=agent_instruction,
        conversation_history=conversation.messages,
        knowledge=knowledge,
        user_query=user_query,
        progress_emitter=progress_emitter
    )

    if progress_emitter:
        await progress_emitter.phase_update("post_process", {"status": "running"})
    
    # Cria mensagem do usuário
    user_message = Message(
        id=MessageId(uuid.uuid4()),
        conversation_id=conversation.id,
        author=Author.USER,
        content=user_query,
        cited_sources=[],
        created_at=datetime.utcnow()
    )
    
    # Cria fontes citadas a partir dos chunks citados
    cited_sources = []
    for chunk in cited_chunks:
        # Aqui precisaríamos buscar o título do artefato, mas por enquanto usamos o chunk_id
        cited_source = CitedSource(
            chunk_id=chunk.id,
            artifact_id=chunk.artifact_id,
            title="",  # Será preenchido na camada de infraestrutura
            chunk_content_preview=chunk.content[:200],  # Primeiros 200 caracteres
            section_title=chunk.metadata.section_title if chunk.metadata else None,
            section_level=chunk.metadata.section_level if chunk.metadata else None,
            content_type=chunk.metadata.content_type if chunk.metadata else None,
            breadcrumbs=chunk.metadata.breadcrumbs if chunk.metadata else [],
        )
        cited_sources.append(cited_source)
    
    # Cria mensagem do agente
    agent_message = Message(
        id=MessageId(uuid.uuid4()),
        conversation_id=conversation.id,
        author=Author.AGENT,
        content=agent_content,
        cited_sources=cited_sources,
        created_at=datetime.utcnow()
    )

    if progress_emitter:
        await progress_emitter.phase_complete(
            "post_process",
            {
                "cited_sources": len(cited_sources),
            },
        )
    
    # Adiciona as mensagens à conversa
    new_messages = conversation.messages + [user_message, agent_message]
    
    # Retorna a nova conversa
    return Conversation(
        id=conversation.id,
        messages=new_messages,
        created_at=conversation.created_at
    )

