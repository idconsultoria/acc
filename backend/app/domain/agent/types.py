"""Tipos de dados do domínio do Agente."""
from dataclasses import dataclass
from datetime import datetime


# Value Object para configuração do agente
@dataclass(frozen=True)
class AgentInstruction:
    """Instrução geral do agente que define sua persona e comportamento."""
    content: str
    updated_at: datetime

