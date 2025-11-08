"""Serviço de integração com Google Gemini 2.5 Flash."""
import json
import google.generativeai as genai
from typing import Protocol, Sequence

from app.domain.agent.types import AgentInstruction
from app.domain.agent.prompt_examples import FEW_SHOT_EXAMPLES
from app.domain.agent.prompt_templates import PromptTemplate
from app.domain.conversations.types import Message
from app.domain.artifacts.types import ArtifactChunk
from app.domain.learnings.types import Learning


async def get_gemini_api_key() -> str:
    """
    Retorna a chave de API do Gemini.
    Prioriza a chave personalizada do usuário, senão usa a padrão do sistema.
    """
    from app.infrastructure.persistence.settings_repo import SettingsRepository
    from app.infrastructure.persistence.config import GEMINI_API_KEY
    
    settings_repo = SettingsRepository()
    custom_key = await settings_repo.get_custom_gemini_api_key()
    
    return custom_key if custom_key else GEMINI_API_KEY


class RelevantKnowledge:
    """Representa o conhecimento relevante encontrado."""
    def __init__(
        self,
        relevant_artifacts: list[ArtifactChunk],
        relevant_learnings: list[Learning]
    ):
        self.relevant_artifacts = relevant_artifacts
        self.relevant_learnings = relevant_learnings


class GeminiService:
    """Serviço para integração com Google Gemini 2.5 Flash."""
    
    def __init__(self, api_key: str):
        """
        Inicializa o serviço Gemini.
        
        Args:
            api_key: Chave da API do Google Gemini
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.prompt_template = PromptTemplate()
    
    async def generate_advice(
        self,
        instruction: AgentInstruction,
        conversation_history: list[Message],
        knowledge: RelevantKnowledge,
        user_query: str
    ) -> tuple[str, list[ArtifactChunk]]:
        """
        Gera conselho cultural baseado no contexto (RAG).
        
        Args:
            instruction: Instrução geral do agente
            conversation_history: Histórico da conversa
            knowledge: Conhecimento relevante encontrado
            user_query: Pergunta do usuário
        
        Returns:
            Tupla com (conteúdo da resposta em markdown, lista de chunks citados)
        """
        cited_chunks = list(knowledge.relevant_artifacts[:5])
        messages = self.prompt_template.build_messages(
            instruction=instruction,
            artifacts=cited_chunks,
            learnings=knowledge.relevant_learnings,
            conversation_history=conversation_history,
            user_query=user_query,
            few_shot_examples=FEW_SHOT_EXAMPLES,
        )

        try:
            response = self.model.generate_content(messages=messages)
            content = self._extract_response_text(response)

            content = await self._maybe_apply_self_reflection(
                base_messages=messages,
                user_query=user_query,
                draft_response=content,
                cited_chunks=cited_chunks,
                learnings=knowledge.relevant_learnings,
            )

            return content, cited_chunks
        except Exception as e:
            raise ValueError(f"Erro ao gerar conselho: {str(e)}")
    
    async def synthesize_learning(self, feedback_text: str) -> str:
        """
        Sintetiza um aprendizado a partir de um texto de feedback.
        
        Args:
            feedback_text: Texto do feedback do usuário
        
        Returns:
            Conteúdo sintetizado do aprendizado (insight conciso e reutilizável)
        """
        prompt = f"""Você é um assistente que sintetiza feedbacks em aprendizados concisos e reutilizáveis.

O feedback recebido foi:
"{feedback_text}"

Sintetize este feedback em um aprendizado conciso (máximo 2-3 frases) que possa ser usado para melhorar futuras respostas do agente cultural. O aprendizado deve ser:
- Conciso e direto
- Reutilizável (não específico demais)
- Focado em melhorias práticas

Aprendizado sintetizado:"""

        try:
            response = self.model.generate_content(prompt)
            return self._extract_response_text(response).strip()
        except Exception as e:
            raise ValueError(f"Erro ao sintetizar aprendizado: {str(e)}")

    def _extract_response_text(self, response: object) -> str:
        """Normaliza o conteúdo textual retornado pelo Gemini."""
        if not response:
            return ""
        if hasattr(response, "text") and response.text:
            return response.text
        if hasattr(response, "parts") and getattr(response, "parts"):
            first_part = response.parts[0]
            if hasattr(first_part, "text"):
                return first_part.text
            if isinstance(first_part, dict) and "text" in first_part:
                return first_part["text"]
        return str(response)

    async def _maybe_apply_self_reflection(
        self,
        base_messages: Sequence[dict],
        user_query: str,
        draft_response: str,
        cited_chunks: Sequence[ArtifactChunk],
        learnings: Sequence[Learning],
    ) -> str:
        """Executa autoavaliação opcional e ajusta a resposta se necessário."""
        from app.infrastructure.persistence.config import ENABLE_SELF_REFLECTION

        content = draft_response.strip()
        if not ENABLE_SELF_REFLECTION or not content:
            return content

        reflection_prompt = self.prompt_template.build_self_reflection_prompt(
            user_query=user_query,
            draft_response=content,
            cited_artifacts=cited_chunks,
            learnings=learnings,
        )

        reflection_response = self.model.generate_content(reflection_prompt)
        reflection_text = self._extract_response_text(reflection_response)

        try:
            reflection_report = json.loads(reflection_text)
        except json.JSONDecodeError:
            return content

        if not reflection_report.get("revision_needed"):
            return content

        revision_messages = self.prompt_template.build_revision_messages(
            base_messages=base_messages,
            draft_response=content,
            reflection_report=reflection_report,
        )

        revision_response = self.model.generate_content(messages=revision_messages)
        revised_content = self._extract_response_text(revision_response)
        return revised_content.strip() if revised_content else content

