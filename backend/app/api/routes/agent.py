"""Rotas para configuração do Agente."""
from fastapi import APIRouter
from app.api.dto import AgentInstructionDTO, UpdateAgentInstructionPayload
from app.domain.agent.workflows import get_agent_instruction, update_agent_instruction
from app.infrastructure.persistence.agent_settings_repo import AgentSettingsRepository

router = APIRouter()

# Inicializa serviços
agent_settings_repo = AgentSettingsRepository()


@router.get("/agent/instruction", response_model=AgentInstructionDTO)
async def get_agent_instruction_route():
    """Obtém a Instrução Geral do Agente."""
    instruction = await get_agent_instruction(agent_settings_repo)
    
    return AgentInstructionDTO(
        instruction=instruction.content,
        updated_at=instruction.updated_at,
        prompt_version=instruction.prompt_version
    )


@router.put("/agent/instruction", response_model=AgentInstructionDTO)
async def update_agent_instruction_route(payload: UpdateAgentInstructionPayload):
    """Atualiza a Instrução Geral do Agente."""
    instruction = await update_agent_instruction(
        new_content=payload.instruction,
        new_prompt_version=payload.prompt_version,
        settings_repo=agent_settings_repo
    )
    
    return AgentInstructionDTO(
        instruction=instruction.content,
        updated_at=instruction.updated_at,
        prompt_version=instruction.prompt_version
    )

