"""Workflows do domínio do Agente."""
from typing import Optional, Protocol
from datetime import datetime
from app.domain.agent.types import AgentInstruction


# --- Interfaces de Dependência (Protocolos) ---

class AgentSettingsRepository(Protocol):
    """Interface para persistir a instrução do agente."""
    async def get_instruction(self) -> AgentInstruction:
        """Obtém a instrução atual do agente."""
        ...
    
    async def update_instruction(self, content: str, prompt_version: Optional[str] = None) -> AgentInstruction:
        """Atualiza a instrução do agente."""
        ...


# --- Assinaturas dos Workflows ---

async def get_agent_instruction(
    settings_repo: AgentSettingsRepository
) -> AgentInstruction:
    """
    Obtém a instrução geral atual do agente.
    """
    return await settings_repo.get_instruction()


async def update_agent_instruction(
    new_content: str,
    new_prompt_version: Optional[str],
    settings_repo: AgentSettingsRepository
) -> AgentInstruction:
    """
    Atualiza a instrução geral do agente.
    """
    return await settings_repo.update_instruction(new_content, new_prompt_version)

