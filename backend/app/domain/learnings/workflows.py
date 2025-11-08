"""Workflows do domínio de Aprendizados."""
from typing import Protocol
from datetime import datetime
from app.domain.learnings.types import Learning
from app.domain.feedbacks.types import PendingFeedback, FeedbackType
from app.domain.shared_kernel import LearningId, Embedding
import uuid


# --- Interfaces de Dependência (Protocolos) ---

class LLMService(Protocol):
    """Interface para síntese de aprendizados usando LLM."""
    async def synthesize_learning(self, feedback_text: str) -> str:
        """Sintetiza um aprendizado a partir de um texto de feedback."""
        ...


class EmbeddingGenerator(Protocol):
    """Interface para geração de embeddings."""
    def generate(self, text: str) -> list[float]:
        """Gera um embedding para um texto."""
        ...


class LearningRepository(Protocol):
    """Interface para persistir aprendizados."""
    async def save(self, learning: Learning) -> Learning:
        """Salva um aprendizado."""
        ...
    
    async def find_all(self) -> list[Learning]:
        """Busca todos os aprendizados."""
        ...


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
    # Sintetiza o aprendizado usando o LLM
    learning_content = await llm_service.synthesize_learning(feedback.feedback_text)
    
    # Gera embedding para o aprendizado
    embedding_vector = embedding_generator.generate(learning_content)
    embedding = Embedding(vector=embedding_vector)
    
    # Cria o aprendizado
    learning = Learning(
        id=LearningId(uuid.uuid4()),
        content=learning_content,
        embedding=embedding,
        source_feedback_id=feedback.id,
        created_at=datetime.utcnow(),
        relevance_weight=_compute_initial_weight(feedback.feedback_type),
        last_used_at=None,
    )
    
    # Persiste o aprendizado
    return await learning_repo.save(learning)


def _compute_initial_weight(feedback_type: FeedbackType) -> float:
    """Calcula peso inicial baseado no tipo de feedback."""
    if feedback_type == "POSITIVE":
        return 1.0
    if feedback_type == "NEGATIVE":
        return 0.4
    return 0.7

