"""Rotas para gerenciamento de Configurações."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.infrastructure.persistence.settings_repo import SettingsRepository

router = APIRouter()

# Inicializa repositório
settings_repo = SettingsRepository()


class GeminiApiKeyPayload(BaseModel):
    api_key: str


@router.get("/settings")
async def get_settings():
    """Retorna o status das configurações."""
    custom_api_key = await settings_repo.get_custom_gemini_api_key()
    return {"hasCustomApiKey": bool(custom_api_key)}


@router.put("/settings/gemini-api-key")
async def save_gemini_api_key(payload: GeminiApiKeyPayload):
    """Salva ou remove a chave de API personalizada do Gemini."""
    if payload.api_key.strip():
        await settings_repo.save_custom_gemini_api_key(payload.api_key.strip())
        return {"message": "Chave de API salva com sucesso"}
    else:
        await settings_repo.remove_custom_gemini_api_key()
        return {"message": "Chave de API removida com sucesso"}

