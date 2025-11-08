"""Repositório de Configurações do Agente usando Supabase."""
from datetime import datetime
from typing import Optional

from supabase import Client, create_client

from app.domain.agent.prompt_templates import PromptTemplate
from app.domain.agent.types import AgentInstruction
from app.infrastructure.persistence.config import SUPABASE_KEY, SUPABASE_URL

DEFAULT_PROMPT_VERSION = PromptTemplate().version


class AgentSettingsRepository:
    """Repositório para persistência de configurações do agente no Supabase."""

    def __init__(self):
        """Inicializa o repositório com cliente Supabase."""
        try:
            if SUPABASE_URL and SUPABASE_KEY:
                self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            else:
                self.supabase = None
        except Exception:
            self.supabase = None

    async def get_instruction(self) -> AgentInstruction:
        """Obtém a instrução atual do agente."""
        default_instruction = (
            "Você é um Conselheiro Cultural de uma organização. Sua missão é ajudar colaboradores a "
            "refletirem sobre dilemas do dia a dia, sempre baseando suas respostas nos valores e práticas "
            "documentadas da organização."
        )

        if not self.supabase:
            return AgentInstruction(
                content=default_instruction,
                updated_at=datetime.utcnow(),
                prompt_version=DEFAULT_PROMPT_VERSION,
            )

        try:
            result = (
                self.supabase.table("agent_settings")
                .select("*")
                .order("updated_at", desc=True)
                .limit(1)
                .execute()
            )
        except Exception:
            result = None

        if not result or not result.data:
            payload = {
                "instruction": default_instruction,
                "updated_at": datetime.utcnow().isoformat(),
                "prompt_version": DEFAULT_PROMPT_VERSION,
            }
            try:
                self.supabase.table("agent_settings").insert(payload).execute()
            except Exception:
                pass

            return AgentInstruction(
                content=default_instruction,
                updated_at=datetime.utcnow(),
                prompt_version=DEFAULT_PROMPT_VERSION,
            )

        row = result.data[0]
        updated_at = row.get("updated_at")
        prompt_version = row.get("prompt_version") or DEFAULT_PROMPT_VERSION

        return AgentInstruction(
            content=row["instruction"],
            updated_at=datetime.fromisoformat(updated_at.replace("Z", "+00:00")) if updated_at else datetime.utcnow(),
            prompt_version=prompt_version,
        )

    async def update_instruction(self, content: str, prompt_version: Optional[str] = None) -> AgentInstruction:
        """Atualiza a instrução do agente."""
        selected_version = prompt_version or DEFAULT_PROMPT_VERSION
        payload = {
            "instruction": content,
            "updated_at": datetime.utcnow().isoformat(),
            "prompt_version": selected_version,
        }

        if self.supabase:
            result = (
                self.supabase.table("agent_settings")
                .select("*")
                .order("updated_at", desc=True)
                .limit(1)
                .execute()
            )

            if result.data:
                self.supabase.table("agent_settings").update(payload).eq("id", result.data[0]["id"]).execute()
            else:
                self.supabase.table("agent_settings").insert(payload).execute()

        return AgentInstruction(
            content=content,
            updated_at=datetime.utcnow(),
            prompt_version=selected_version,
        )

