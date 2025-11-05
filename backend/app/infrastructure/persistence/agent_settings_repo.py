"""Repositório de Configurações do Agente usando Supabase."""
from supabase import create_client, Client
from app.domain.agent.types import AgentInstruction
from app.infrastructure.persistence.config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime


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
        if not self.supabase:
            # Retorna instrução padrão se não houver Supabase
            default_instruction = """Você é um Conselheiro Cultural de uma organização. Sua missão é ajudar colaboradores a refletirem sobre dilemas do dia a dia, sempre baseando suas respostas nos valores e práticas documentadas da organização."""
            return AgentInstruction(
                content=default_instruction,
                updated_at=datetime.utcnow()
            )
        
        try:
            result = self.supabase.table("agent_settings").select("*").limit(1).execute()
        except Exception as e:
            # Se não conseguir buscar, retorna instrução padrão
            result = None
        
        if not result or not result.data:
            # Retorna instrução padrão se não houver configuração
            default_instruction = """Você é um Conselheiro Cultural de uma organização. Sua missão é ajudar colaboradores a refletirem sobre dilemas do dia a dia, sempre baseando suas respostas nos valores e práticas documentadas da organização."""
            
            # Cria a configuração padrão
            default_data = {
                "instruction": default_instruction,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self.supabase.table("agent_settings").insert(default_data).execute()
            
            return AgentInstruction(
                content=default_instruction,
                updated_at=datetime.utcnow()
            )
        
        row = result.data[0]
        
        return AgentInstruction(
            content=row["instruction"],
            updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00"))
        )
    
    async def update_instruction(self, content: str) -> AgentInstruction:
        """Atualiza a instrução do agente."""
        # Verifica se já existe uma configuração
        result = self.supabase.table("agent_settings").select("*").limit(1).execute()
        
        if result.data:
            # Atualiza a existente
            self.supabase.table("agent_settings").update({
                "instruction": content,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", result.data[0]["id"]).execute()
        else:
            # Cria nova
            self.supabase.table("agent_settings").insert({
                "instruction": content,
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
        
        return AgentInstruction(
            content=content,
            updated_at=datetime.utcnow()
        )

