"""Serviço responsável por recalcular pesos dinâmicos de aprendizados."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.domain.learnings.types import Learning
from app.domain.shared_kernel import LearningId


class LearningWeightsRepository(Protocol):
    """Contrato mínimo esperado pelo recalculador de pesos."""

    async def find_all(self) -> list[Learning]:
        ...

    async def update_weights(self, updates: dict[LearningId, float]) -> None:
        ...


@dataclass
class LearningWeightingConfig:
    """Configurações do processo de ponderação."""

    max_weight: float = 2.0
    min_weight: float = 0.0
    base_scale: float = 0.6
    recency_bonus_recent: float = 0.3
    recency_bonus_active: float = 0.15
    recency_penalty_stale: float = -0.1
    recency_penalty_inactive: float = -0.25
    freshness_bonus_new: float = 0.2
    freshness_bonus_recent: float = 0.1
    freshness_penalty_old: float = -0.05


class LearningWeighter:
    """Calcula pesos dinâmicos para aprendizados aprovados."""

    def __init__(
        self,
        repository: LearningWeightsRepository,
        config: LearningWeightingConfig | None = None,
    ) -> None:
        self.repository = repository
        self.config = config or LearningWeightingConfig()

    async def recalculate(self, now: datetime | None = None) -> dict[LearningId, float]:
        """Recalcula todos os pesos e retorna o dicionário de atualizações."""
        reference = now or datetime.utcnow()
        learnings = await self.repository.find_all()

        updates: dict[LearningId, float] = {}
        for learning in learnings:
            base_component = self._base_component(learning)
            recency_component = self._recency_component(learning.last_used_at, reference)
            freshness_component = self._freshness_component(learning.created_at, reference)

            raw_weight = (
                base_component * self.config.base_scale
                + recency_component
                + freshness_component
            )
            bounded_weight = max(
                self.config.min_weight, min(self.config.max_weight, raw_weight)
            )
            updates[learning.id] = round(bounded_weight, 4)

        if updates:
            await self.repository.update_weights(updates)

        return updates

    def _base_component(self, learning: Learning) -> float:
        """Retorna componente base (feedback signal)."""
        if learning.relevance_weight is None:
            return 0.7
        return float(learning.relevance_weight)

    def _recency_component(self, last_used_at: datetime | None, reference: datetime) -> float:
        """Calcula bônus/penalidade baseada em uso recente."""
        if last_used_at is None:
            return self.config.recency_penalty_inactive

        delta_days = (reference - last_used_at).days
        if delta_days <= 7:
            return self.config.recency_bonus_recent
        if delta_days <= 30:
            return self.config.recency_bonus_active
        if delta_days <= 90:
            return 0.0
        if delta_days <= 180:
            return self.config.recency_penalty_stale
        return self.config.recency_penalty_inactive

    def _freshness_component(self, created_at: datetime, reference: datetime) -> float:
        """Calcula bônus baseado na idade do aprendizado."""
        age_days = (reference - created_at).days
        if age_days <= 14:
            return self.config.freshness_bonus_new
        if age_days <= 60:
            return self.config.freshness_bonus_recent
        if age_days <= 365:
            return 0.0
        return self.config.freshness_penalty_old
