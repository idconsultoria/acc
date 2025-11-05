"""Rotas para gerenciamento de Aprendizados."""
from fastapi import APIRouter
from app.api.dto import LearningDTO
from app.infrastructure.persistence.learnings_repo import LearningsRepository

router = APIRouter()

# Inicializa serviços
learnings_repo = LearningsRepository()


@router.get("/learnings", response_model=list[LearningDTO])
async def list_learnings():
    """Lista todos os Aprendizados."""
    learnings = await learnings_repo.find_all()
    
    return [
        LearningDTO(
            id=learning.id,
            content=learning.content,
            source_feedback_id=learning.source_feedback_id,
            created_at=learning.created_at
        )
        for learning in learnings
    ]

