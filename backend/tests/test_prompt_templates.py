"""Testes unitários para PromptTemplate e PromptRenderer."""
from datetime import datetime
import uuid

from app.domain.agent.prompt_templates import PromptTemplate
from app.domain.agent.types import AgentInstruction
from app.domain.artifacts.types import ArtifactChunk, ChunkMetadata
from app.domain.conversations.types import Author, ConversationId, Message, MessageId
from app.domain.learnings.types import Learning
from app.domain.shared_kernel import ArtifactId, ChunkId, Embedding, FeedbackId, LearningId


def _build_sample_message(content: str, author: Author) -> Message:
    """Cria mensagem de teste."""
    return Message(
        id=MessageId(uuid.uuid4()),
        conversation_id=ConversationId(uuid.uuid4()),
        author=author,
        content=content,
        cited_sources=[],
        created_at=datetime.utcnow(),
    )


def test_build_messages_contains_expected_sections():
    """Garante que o template monta mensagens com seções esperadas."""
    template = PromptTemplate()
    instruction = AgentInstruction(
        content="Aja como guardião da cultura, promovendo reflexão conjunta.",
        updated_at=datetime.utcnow(),
        prompt_version="professional-rag-v1",
    )

    artifact_chunk = ArtifactChunk(
        id=ChunkId(uuid.uuid4()),
        artifact_id=ArtifactId(uuid.uuid4()),
        content="Texto do artefato descrevendo o valor de colaboração radical.",
        embedding=Embedding(vector=[0.1, 0.2, 0.3]),
        metadata=ChunkMetadata(
            section_title="Colaboração Radical",
            section_level=2,
            content_type="paragraph",
            position=1,
            token_count=42,
            breadcrumbs=["Valores", "Colaboração"],
        ),
    )

    learning = Learning(
        id=LearningId(uuid.uuid4()),
        content="Praticar escuta ativa antes de oferecer conselhos fortalece confiança.",
        embedding=Embedding(vector=[0.2, 0.1, 0.5]),
        source_feedback_id=FeedbackId(uuid.uuid4()),
        created_at=datetime.utcnow(),
    )

    history = [
        _build_sample_message("Como posso lidar com desacordos no meu time?", Author.USER),
        _build_sample_message("Exploramos recentemente o valor de diálogo transparente.", Author.AGENT),
    ]

    messages = template.build_messages(
        instruction=instruction,
        artifacts=[artifact_chunk],
        learnings=[learning],
        conversation_history=history,
        user_query="Preciso incentivar colaboração sem gerar burnout.",
        few_shot_examples=None,
    )

    assert messages[0]["role"] == "system"
    assert "Regras de atuação" in messages[0]["parts"][0]["text"]

    user_message = messages[-1]["parts"][0]["text"]
    assert "## Artefatos Relevantes" in user_message
    assert "### Fonte 1 — Colaboração Radical" in user_message
    assert "## Aprendizados Priorizados" in user_message
    assert "🧠 Insight Relevante #1" in user_message
    assert "## Checklist de Meta-Avaliação" in user_message
    assert "## Pedido Atual do Usuário" in user_message


def test_build_self_reflection_prompt_requests_json_report():
    """Valida que o metaprompt exige relatório em JSON estruturado."""
    template = PromptTemplate()
    reflection_prompt = template.build_self_reflection_prompt(
        user_query="Como aplicar o valor de coragem?",
        draft_response="Resposta inicial do agente com [Fonte 1].",
        cited_artifacts=[],
        learnings=[],
    )

    assert '"revision_needed": true|false' in reflection_prompt
    assert '"issues": ["descrição do problema"...]' in reflection_prompt
    assert '"improvements": "texto curto' in reflection_prompt
