"""Infraestrutura de templates e renderização de prompts para o agente."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence
import re
from datetime import datetime

from app.domain.agent.types import AgentInstruction
from app.domain.agent.prompt_examples import PromptExample
from app.domain.artifacts.types import ArtifactChunk
from app.domain.conversations.types import Message, Author
from app.domain.learnings.types import Learning


@dataclass(frozen=True)
class PromptSection:
    """Representa uma seção estruturada do prompt principal."""
    title: str
    content: str

    def to_markdown(self) -> str:
        """Converte a seção em markdown com título de segundo nível."""
        normalized_content = self.content.strip()
        if not normalized_content:
            normalized_content = "_Nenhum conteúdo disponível no momento._"
        return f"## {self.title}\n{normalized_content}"


class PromptRenderer:
    """Responsável por renderizar partes dinâmicas do prompt em Markdown."""

    def __init__(
        self,
        summary_sentence_limit: int = 2,
        max_learning_preview_chars: int = 280,
    ) -> None:
        self.summary_sentence_limit = summary_sentence_limit
        self.max_learning_preview_chars = max_learning_preview_chars

    def render_system_instruction(
        self,
        instruction: AgentInstruction,
        template_version: str,
    ) -> str:
        """Constrói o conteúdo do system prompt."""
        base_persona = (
            "Você é o Conselheiro Cultural oficial do Instituto. Sua missão é apoiar "
            "colaboradores a refletirem sobre dilemas cotidianos à luz dos valores, princípios "
            "e aprendizados registrados nos artefatos culturais."
        )

        rules = [
            "Cite sempre as fontes na forma [Fonte X], mantendo X coerente com os artefatos fornecidos.",
            "Se não houver contexto suficiente, admita limitações e sugira próximos passos.",
            "Mantenha tom acolhedor, curioso e convidativo à reflexão (evite ordens diretas).",
            "Use Markdown avançado (títulos, listas, blockquotes) quando isso tornar a resposta mais clara.",
            "Antes de entregar a resposta final, faça uma autoavaliação silenciosa para verificar se todas as recomendações seguem as fontes e os aprendizados citados.",
        ]

        rules_block = "\n".join(f"- {item}" for item in rules)
        prompt_version = instruction.prompt_version or template_version

        return (
            f"{base_persona}\n\n"
            f"Versão ativa do template: {prompt_version}\n"
            f"Atualizado em: {instruction.updated_at.isoformat()}\n\n"
            f"{instruction.content.strip()}\n\n"
            "Regras de atuação:\n"
            f"{rules_block}"
        )

    def format_artifact_chunk(self, chunk: ArtifactChunk, index: int) -> str:
        """Formata um chunk de artefato com metadados e resumo."""
        metadata = chunk.metadata
        section_title = metadata.section_title if metadata and metadata.section_title else f"Trecho {index}"
        breadcrumbs = metadata.breadcrumbs if metadata else []
        breadcrumbs_text = f" › ".join(breadcrumbs) if breadcrumbs else ""
        content_type = metadata.content_type if metadata and metadata.content_type else "texto"
        token_count = metadata.token_count if metadata else "?"
        position = metadata.position if metadata else "?"

        summary = self._summarize_text(chunk.content)
        breadcrumb_line = f"- Breadcrumbs: {breadcrumbs_text}\n" if breadcrumbs_text else ""

        details = (
            f"- Tipo: {content_type}\n"
            f"- Chunk ID: {chunk.id}\n"
            f"- Posição: {position}\n"
            f"- Tokens (aprox.): {token_count}\n"
            f"{breadcrumb_line}"
            f"- Resumo: {summary}"
        ).strip()

        return (
            f"### Fonte {index} — {section_title}\n"
            f"{details}\n\n"
            f"{chunk.content.strip()}"
        ).strip()

    def format_learning(self, learning: Learning, index: int) -> str:
        """Formata aprendizados priorizados com destaque visual."""
        preview = learning.content.strip()
        if len(preview) > self.max_learning_preview_chars:
            preview = f"{preview[:self.max_learning_preview_chars]}..."

        created_at = learning.created_at.isoformat() if isinstance(learning.created_at, datetime) else str(learning.created_at)

        return (
            f"🧠 Insight Relevante #{index}\n"
            f"- Learning ID: {learning.id}\n"
            f"- Registrado em: {created_at}\n"
            f"> {preview}"
        ).strip()

    def render_conversation_history(self, conversation_history: Sequence[Message], limit: int) -> str:
        """Renderiza as mensagens recentes em formato cronológico."""
        if not conversation_history:
            return "_Não há histórico relevante registrado._"

        recent_messages = conversation_history[-limit:]
        lines: List[str] = []

        for message in recent_messages:
            role = "Usuário" if message.author == Author.USER else "Agente"
            lines.append(f"- **{role}**: {message.content.strip()}")

        return "\n".join(lines)

    def compose_user_message(self, sections: Sequence[PromptSection]) -> str:
        """Combina múltiplas seções em um único conteúdo markdown."""
        rendered_sections = [section.to_markdown() for section in sections]
        return "\n\n".join(rendered_sections)

    def build_meta_instructions(self) -> str:
        """Retorna instruções explícitas para a etapa de metaprompt dentro do contexto."""
        return (
            "Antes de responder, sintetize mentalmente (sem escrever) os passos a seguir:\n"
            "1. Identificar quais fontes sustentam cada recomendação.\n"
            "2. Garantir que aprendizados destacados estejam conectados à situação.\n"
            "3. Revisar o tom para manter postura de parceiro reflexivo.\n"
            "Quando concluir a resposta, confirme se todas as citações estão corretas. "
            "Se perceber inconsistências, ajuste a resposta antes de finalizá-la."
        )

    def _summarize_text(self, text: str) -> str:
        """Extrai um resumo simples com base nas primeiras frases."""
        sanitized = re.sub(r"\s+", " ", text.strip())
        if not sanitized:
            return "Conteúdo indisponível."

        sentences = re.split(r"(?<=[.!?])\s+", sanitized)
        summary = " ".join(sentences[: self.summary_sentence_limit])
        return summary if summary else sanitized[:200]


@dataclass
class PromptTemplate:
    """Template principal que organiza o prompt em seções e mensagens."""
    name: str = "professional_rag"
    version: str = "v1"
    max_artifacts: int = 5
    max_learnings: int = 3
    max_history_messages: int = 6
    renderer: PromptRenderer = field(default_factory=PromptRenderer)
    self_reflection_schema: str = field(
        default=(
            "Analise a resposta gerada e retorne um JSON com o formato:\n"
            "{\n"
            '  "revision_needed": true|false,\n'
            '  "issues": ["descrição do problema"...],\n'
            '  "improvements": "texto curto com orientações para corrigir"\n'
            "}\n"
            "Considere aderência às fontes, alinhamento com aprendizados e tom adotado."
        )
    )

    def build_messages(
        self,
        instruction: AgentInstruction,
        artifacts: Sequence[ArtifactChunk],
        learnings: Sequence[Learning],
        conversation_history: Sequence[Message],
        user_query: str,
        few_shot_examples: Sequence[PromptExample] | None = None,
    ) -> List[dict]:
        """Constrói a lista de mensagens para envio ao modelo Gemini."""
        system_content = self.renderer.render_system_instruction(instruction, self.version)

        artifact_entries = [
            self.renderer.format_artifact_chunk(chunk, index=index)
            for index, chunk in enumerate(artifacts[: self.max_artifacts], start=1)
        ]
        artifacts_section = PromptSection(
            title="Artefatos Relevantes",
            content="\n\n".join(artifact_entries) if artifact_entries else "_Nenhum artefato disponível._",
        )

        learning_entries = [
            self.renderer.format_learning(learning, index=index)
            for index, learning in enumerate(learnings[: self.max_learnings], start=1)
        ]
        learnings_section = PromptSection(
            title="Aprendizados Priorizados",
            content="\n\n".join(learning_entries) if learning_entries else "_Nenhum aprendizado selecionado._",
        )

        history_section = PromptSection(
            title="Histórico Recente da Conversa",
            content=self.renderer.render_conversation_history(conversation_history, self.max_history_messages),
        )

        meta_section = PromptSection(
            title="Checklist de Meta-Avaliação",
            content=self.renderer.build_meta_instructions(),
        )

        user_section = PromptSection(
            title="Pedido Atual do Usuário",
            content=user_query.strip(),
        )

        user_content = self.renderer.compose_user_message(
            [artifacts_section, learnings_section, history_section, meta_section, user_section]
        )

        messages: List[dict] = [
            {"role": "system", "parts": [{"text": system_content}]},
        ]

        if few_shot_examples:
            for example in few_shot_examples:
                messages.extend(example.to_messages())

        messages.append({"role": "user", "parts": [{"text": user_content}]})
        return messages

    def build_self_reflection_prompt(
        self,
        user_query: str,
        draft_response: str,
        cited_artifacts: Sequence[ArtifactChunk],
        learnings: Sequence[Learning],
    ) -> str:
        """Constrói o prompt que solicita autoavaliação após a primeira resposta."""
        artifacts_summary = "\n".join(
            f"- Fonte {index}: {self.renderer._summarize_text(chunk.content)}"
            for index, chunk in enumerate(cited_artifacts[: self.max_artifacts], start=1)
        )
        learnings_summary = "\n".join(
            f"- {self.renderer._summarize_text(learning.content)}"
            for learning in learnings[: self.max_learnings]
        )

        return (
            "Você agora atua como revisor crítico da resposta anterior do Conselheiro Cultural.\n"
            "Avalie se a resposta mantém aderência aos artefatos e aprendizados e se as citações estão corretas.\n\n"
            f"Pergunta original: {user_query.strip()}\n\n"
            "Resumo dos artefatos utilizados:\n"
            f"{artifacts_summary if artifacts_summary else '- Nenhum artefato informado.'}\n\n"
            "Resumo dos aprendizados selecionados:\n"
            f"{learnings_summary if learnings_summary else '- Nenhum aprendizado selecionado.'}\n\n"
            "Resposta proposta:\n"
            f"{draft_response.strip()}\n\n"
            f"{self.self_reflection_schema}"
        ).strip()

    def build_revision_messages(
        self,
        base_messages: Sequence[dict],
        draft_response: str,
        reflection_report: dict,
    ) -> List[dict]:
        """Gera nova sequência de mensagens para solicitar revisão da resposta."""
        revised_messages = list(base_messages)
        revised_messages.append({"role": "model", "parts": [{"text": draft_response.strip()}]})

        reflection_summary = self._render_reflection_summary(reflection_report)
        revised_messages.append({"role": "user", "parts": [{"text": reflection_summary}]})
        return revised_messages

    def _render_reflection_summary(self, reflection_report: dict) -> str:
        """Transforma o relatório JSON em instrução textual para revisão."""
        issues = reflection_report.get("issues") or []
        improvements = reflection_report.get("improvements") or ""
        issues_block = "\n".join(f"- {issue}" for issue in issues) if issues else "- Sem problemas listados explicitamente."

        return (
            "Com base na autoavaliação anterior, revise a resposta para corrigir os pontos a seguir. "
            "Mantenha as regras originais e cite as fontes coerentemente. "
            "Não mencione esta revisão ao usuário.\n\n"
            "Problemas identificados:\n"
            f"{issues_block}\n\n"
            "Orientação adicional:\n"
            f"{improvements if improvements else 'Ajuste apenas o necessário para garantir aderência e tom adequado.'}"
        )

