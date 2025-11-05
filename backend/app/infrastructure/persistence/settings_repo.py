"""Repositório para persistência de configurações no Supabase."""
from supabase import create_client, Client
from app.infrastructure.persistence.config import SUPABASE_URL, SUPABASE_KEY


class SettingsRepository:
    """Repositório para gerenciar configurações do sistema."""

    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    async def get_custom_gemini_api_key(self) -> str | None:
        """Busca a chave de API personalizada do Gemini."""
        result = self.supabase.table("settings").select("value").eq("key", "custom_gemini_api_key").execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]["value"]
        return None

    async def save_custom_gemini_api_key(self, api_key: str) -> None:
        """Salva a chave de API personalizada do Gemini."""
        # Verifica se já existe
        existing = self.supabase.table("settings").select("key").eq("key", "custom_gemini_api_key").execute()
        
        if existing.data and len(existing.data) > 0:
            # Atualiza
            self.supabase.table("settings").update({"value": api_key}).eq("key", "custom_gemini_api_key").execute()
        else:
            # Insere
            self.supabase.table("settings").insert({"key": "custom_gemini_api_key", "value": api_key}).execute()

    async def remove_custom_gemini_api_key(self) -> None:
        """Remove a chave de API personalizada do Gemini."""
        self.supabase.table("settings").delete().eq("key", "custom_gemini_api_key").execute()

