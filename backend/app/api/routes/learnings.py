"""Rotas para gerenciamento de Aprendizados."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.dto import (
    LearningDTO,
    UpdateLearningWeightsPayload,
    MergeLearningsPayload,
    MergeLearningsResponse,
    DeduplicateLearningsPayload,
    DeduplicateLearningsResponse,
    RecalculateLearningWeightsResponse,
    LearningMergeCandidateDTO,
)
from app.domain.learnings.types import Learning, LearningMergeCandidate
from app.domain.learnings.weighter import LearningWeighter
from app.domain.shared_kernel import LearningId
from app.infrastructure.persistence.learnings_repo import LearningsRepository

router = APIRouter()

# Inicializa serviços
learnings_repo = LearningsRepository()
learning_weighter = LearningWeighter(learnings_repo)


@router.get("/learnings", response_model=list[LearningDTO])
async def list_learnings():
    """Lista todos os Aprendizados."""
    learnings = await learnings_repo.find_all()
    
    return [
        _to_learning_dto(learning)
        for learning in learnings
    ]


@router.post(
    "/learnings/weights",
    response_model=RecalculateLearningWeightsResponse,
    status_code=status.HTTP_200_OK,
)
async def update_learning_weights(payload: UpdateLearningWeightsPayload):
    """Atualiza pesos manualmente via painel admin."""
    updates = {
        LearningId(item.learning_id): float(item.relevance_weight)
        for item in payload.updates
    }

    await learnings_repo.update_weights(updates)
    return RecalculateLearningWeightsResponse(
        updated_learning_ids=[item.learning_id for item in payload.updates],
        recalculated_at=datetime.utcnow(),
    )


@router.post(
    "/learnings/recalculate",
    response_model=RecalculateLearningWeightsResponse,
    status_code=status.HTTP_200_OK,
)
async def recalculate_learning_weights():
    """Dispara recálculo dinâmico de pesos."""
    updates = await learning_weighter.recalculate()
    return RecalculateLearningWeightsResponse(
        updated_learning_ids=[UUID(str(learning_id)) for learning_id in updates.keys()],
        recalculated_at=datetime.utcnow(),
    )


@router.post(
    "/learnings/merge",
    response_model=MergeLearningsResponse,
    status_code=status.HTTP_200_OK,
)
async def merge_learnings(payload: MergeLearningsPayload):
    """Realiza merge de aprendizados duplicados."""
    if len(payload.learning_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="É necessário informar pelo menos dois aprendizados para merge.",
        )

    learning_ids = [LearningId(learning_id) for learning_id in payload.learning_ids]
    merged_learning = await learnings_repo.merge(
        learning_ids,
        merged_content=payload.merged_content,
        merged_weight=payload.merged_weight,
    )

    return MergeLearningsResponse(
        merged_learning=_to_learning_dto(merged_learning),
        archived_learning_ids=list(payload.learning_ids),
    )


@router.post(
    "/learnings/deduplicate",
    response_model=DeduplicateLearningsResponse,
    status_code=status.HTTP_200_OK,
)
async def deduplicate_learnings(payload: DeduplicateLearningsPayload):
    """Sugere candidatos para merge/deduplicação."""
    threshold = payload.similarity_threshold if payload.similarity_threshold is not None else 0.85
    limit = payload.limit if payload.limit is not None else 20

    candidates = await learnings_repo.suggest_merge_candidates(
        similarity_threshold=threshold,
        limit=limit,
    )

    return DeduplicateLearningsResponse(
        candidates=[
            _merge_candidate_to_dto(candidate)
            for candidate in candidates
        ]
    )


def _to_learning_dto(learning: Learning) -> LearningDTO:
    """Converte entidade de domínio em DTO."""
    return LearningDTO(
        id=learning.id,
        content=learning.content,
        source_feedback_id=learning.source_feedback_id,
        created_at=learning.created_at,
        relevance_weight=learning.relevance_weight,
        last_used_at=learning.last_used_at,
    )


def _merge_candidate_to_dto(candidate: LearningMergeCandidate) -> LearningMergeCandidateDTO:
    """Transforma candidato de merge em DTO correspondente."""
    return LearningMergeCandidateDTO(
        base_learning=_to_learning_dto(candidate.base_learning),
        duplicate_learnings=[
            _to_learning_dto(learning) for learning in candidate.duplicate_learnings
        ],
        similarity_score=candidate.similarity_score,
    )
