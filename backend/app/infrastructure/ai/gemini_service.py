"""Serviço de integração com Google Gemini 2.5 Flash."""
import json
import logging
import google.generativeai as genai

from app.domain.agent.types import AgentInstruction
from app.domain.conversations.types import Message
from app.domain.artifacts.types import ArtifactChunk
from app.domain.learnings.types import Learning
from app.domain.conversations.workflows import ProgressEmitter


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
    logger = logging.getLogger("app.ai.gemini")
    
    def __init__(self, api_key: str):
        """
        Inicializa o serviço Gemini.
        
        Args:
            api_key: Chave da API do Google Gemini
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def generate_advice(
        self,
        instruction: AgentInstruction,
        conversation_history: list[Message],
        knowledge: RelevantKnowledge,
        user_query: str,
        progress_emitter: ProgressEmitter | None = None,
    ) -> tuple[str, list[ArtifactChunk]]:
        """
        Gera conselho cultural baseado no contexto (RAG).
        """
        artifacts_context = ""
        cited_chunks: list[ArtifactChunk] = []

        for idx, chunk in enumerate(knowledge.relevant_artifacts[:5], start=1):
            metadata = chunk.metadata
            section_title = metadata.section_title if metadata else None
            breadcrumbs = (
                " › ".join(metadata.breadcrumbs)
                if metadata and metadata.breadcrumbs
                else ""
            )
            content_type = metadata.content_type if metadata else None
            header_title = section_title or f"Trecho {idx}"
            header = f"### Fonte {idx} — {header_title}"
            details = []
            if breadcrumbs:
                details.append(f"Breadcrumbs: {breadcrumbs}")
            if content_type:
                details.append(f"Tipo: {content_type}")
            metadata_block = "\n".join(details)
            chunk_text = (
                f"{header}\n{metadata_block}\n\n{chunk.content}"
                if metadata_block
                else f"{header}\n\n{chunk.content}"
            )
            artifacts_context += f"\n\n{chunk_text.strip()}"
            cited_chunks.append(chunk)

        learnings_limit = knowledge.relevant_learnings[:3]
        learnings_context = "".join(
            f"\n\n--- Aprendizado ---\n{learning.content}\n"
            for learning in learnings_limit
        )

        conversation_history_limit = conversation_history[-5:]
        conversation_context = ""
        for msg in conversation_history_limit:
            author = "Usuário" if msg.author.value == 1 else "Agente"
            conversation_context += f"\n{author}: {msg.content}\n"

        if progress_emitter:
            await progress_emitter.phase_complete(
                "prompt_build",
                {
                    "chunk_count": len(cited_chunks),
                    "learning_count": len(learnings_limit),
                    "history_messages": len(conversation_history_limit),
                },
            )
            await progress_emitter.phase_update("llm_stream", {"status": "running"})
            if self.logger.isEnabledFor(logging.INFO):
                self.logger.info(
                    json.dumps(
                        {
                            "event": "prompt_build_complete",
                            "chunk_count": len(cited_chunks),
                            "learning_count": len(learnings_limit),
                            "history_messages": len(conversation_history_limit),
                        }
                    )
                )

        system_prompt = f"""Você é um Conselheiro Cultural de uma organização. Sua missão é ajudar colaboradores a refletirem sobre dilemas do dia a dia, sempre baseando suas respostas nos valores e práticas documentadas da organização.

{instruction.content}

REGRAS IMPORTANTES:
1. Sempre cite as fontes quando usar informações dos artefatos culturais. Use o formato [Fonte X] onde X é o número da fonte.
2. Seja reflexivo e não prescritivo. Ajude o usuário a pensar, não a obedecer.
3. Use Markdown para formatar suas respostas (negrito, itálico, listas, etc.).
4. Base suas respostas nos artefatos e aprendizados fornecidos abaixo.

ARTEFATOS CULTURAIS RELEVANTES:
{artifacts_context}

APRENDIZADOS RELEVANTES:
{learnings_context}

HISTÓRICO DA CONVERSA:
{conversation_context}

PERGUNTA DO USUÁRIO:
{user_query}

RESPOSTA (use Markdown e cite as fontes):"""

        try:
            content = ""
            tokens_emitted = 0

            if progress_emitter:
                response = await self.model.generate_content_async(
                    system_prompt,
                    stream=True,
                )

                async for chunk in response:
                    text_fragment = self._extract_text_from_chunk(chunk)
                    if text_fragment:
                        content += text_fragment
                        tokens_emitted += len(text_fragment.split())
                        await progress_emitter.emit_token(text_fragment)

                await progress_emitter.phase_complete(
                    "llm_stream",
                    {
                        "tokens_emitted": tokens_emitted,
                    },
                )
                if self.logger.isEnabledFor(logging.INFO):
                    self.logger.info(
                        json.dumps(
                            {
                                "event": "llm_stream_complete",
                                "tokens_emitted": tokens_emitted,
                                "streaming": True,
                            }
                        )
                    )
            else:
                response = await self.model.generate_content_async(system_prompt)
                content = self._extract_text_from_chunk(response)
                if self.logger.isEnabledFor(logging.INFO):
                    self.logger.info(
                        json.dumps(
                            {
                                "event": "llm_response_generated",
                                "tokens_emitted": len(content.split()),
                                "streaming": False,
                            }
                        )
                    )

            return content, cited_chunks
        except Exception as e:
            if self.logger.isEnabledFor(logging.ERROR):
                self.logger.error(
                    json.dumps(
                        {
                            "event": "llm_generation_error",
                            "error": str(e),
                        }
                    )
                )
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
            return response.text.strip()
        except Exception as e:
            raise ValueError(f"Erro ao sintetizar aprendizado: {str(e)}")

    @staticmethod
    def _extract_text_from_chunk(chunk) -> str:
        """Extrai texto de um chunk retornado pelo Gemini."""
        if chunk is None:
            return ""

        if hasattr(chunk, "text") and chunk.text:
            return chunk.text

        if hasattr(chunk, "parts") and chunk.parts:
            return "".join(
                getattr(part, "text", "")
                for part in chunk.parts
                if getattr(part, "text", "")
            )

        if hasattr(chunk, "candidates") and chunk.candidates:
            for candidate in chunk.candidates:
                candidate_content = getattr(candidate, "content", None)
                if candidate_content and getattr(candidate_content, "parts", None):
                    parts_text = "".join(
                        getattr(part, "text", "")
                        for part in candidate_content.parts
                        if getattr(part, "text", "")
                    )
                    if parts_text:
                        return parts_text

        return str(chunk) if chunk else ""

