"""Serviço de integração com Google Gemini 2.5 Flash."""
import os
import google.generativeai as genai
from typing import Protocol
from app.domain.agent.types import AgentInstruction
from app.domain.conversations.types import Message
from app.domain.artifacts.types import ArtifactChunk
from app.domain.learnings.types import Learning


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
        # Constrói o contexto dos artefatos
        artifacts_context = ""
        cited_chunks = []
        
        for chunk in knowledge.relevant_artifacts[:5]:  # Limita a 5 chunks mais relevantes
            artifacts_context += f"\n\n--- Fonte: {chunk.artifact_id} ---\n{chunk.content}\n"
            cited_chunks.append(chunk)
        
        # Constrói o contexto dos aprendizados
        learnings_context = ""
        for learning in knowledge.relevant_learnings[:3]:  # Limita a 3 aprendizados
            learnings_context += f"\n\n--- Aprendizado ---\n{learning.content}\n"
        
        # Constrói o histórico da conversa
        conversation_context = ""
        for msg in conversation_history[-5:]:  # Últimas 5 mensagens
            author = "Usuário" if msg.author.value == 1 else "Agente"
            conversation_context += f"\n{author}: {msg.content}\n"
        
        # Monta o prompt completo
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

        # Gera a resposta
        try:
            # Usa generate_content com o prompt como conteúdo da mensagem
            response = self.model.generate_content(system_prompt)
            # O Gemini retorna um objeto com .text
            if hasattr(response, 'text'):
                content = response.text
            elif hasattr(response, 'parts') and response.parts:
                content = response.parts[0].text
            else:
                content = str(response)
            
            # Extrai os chunks citados (por enquanto, retornamos todos os chunks relevantes)
            # Em uma versão mais sofisticada, poderíamos analisar a resposta para identificar quais chunks foram realmente citados
            
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
            return response.text.strip()
        except Exception as e:
            raise ValueError(f"Erro ao sintetizar aprendizado: {str(e)}")

