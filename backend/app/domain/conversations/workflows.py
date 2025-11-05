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
        user_query: str
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


# --- Assinatura do Workflow Principal ---

async def continue_conversation(
    conversation: Conversation,
    user_query: str,
    embedding_generator: EmbeddingGenerator,
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
    # Gera embedding para a consulta do usuário
    query_embedding = embedding_generator.generate(user_query)
    
    # Busca conhecimento relevante
    knowledge = await knowledge_repo.find_relevant_knowledge(user_query, query_embedding)
    
    # Gera a resposta do agente
    agent_content, cited_chunks = await llm_service.generate_advice(
        instruction=agent_instruction,
        conversation_history=conversation.messages,
        knowledge=knowledge,
        user_query=user_query
    )
    
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
            artifact_id=chunk.artifact_id,
            title="",  # Será preenchido na camada de infraestrutura
            chunk_content_preview=chunk.content[:200]  # Primeiros 200 caracteres
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
    
    # Adiciona as mensagens à conversa
    new_messages = conversation.messages + [user_message, agent_message]
    
    # Retorna a nova conversa
    return Conversation(
        id=conversation.id,
        messages=new_messages,
        created_at=conversation.created_at
    )

