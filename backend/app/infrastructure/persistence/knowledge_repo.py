"""Repositório para busca de conhecimento relevante (RAG)."""
import asyncio
import json
import logging
import uuid
from datetime import datetime

from supabase import Client, create_client

from typing import Iterable

from app.domain.artifacts.types import ArtifactChunk, ChunkMetadata
from app.domain.learnings.types import Learning
from app.domain.shared_kernel import ArtifactId, ChunkId, Embedding, FeedbackId, LearningId
from app.infrastructure.persistence.config import SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL
from app.infrastructure.persistence.learnings_repo import LearningsRepository


logger = logging.getLogger("app.rag.retrieval")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
logger.propagate = False


class RelevantKnowledge:
    """Representa o conhecimento relevante encontrado."""

    def __init__(
        self,
        relevant_artifacts: list[ArtifactChunk],
        relevant_learnings: list[Learning],
        *,
        artifact_scores: dict[ChunkId, float] | None = None,
        learning_scores: dict[LearningId, float] | None = None,
    ):
        self.relevant_artifacts = relevant_artifacts
        self.relevant_learnings = relevant_learnings
        self.artifact_scores = artifact_scores or {}
        self.learning_scores = learning_scores or {}


class KnowledgeRepository:
    """Repositório para busca vetorial de conhecimento relevante."""

    def __init__(
        self,
        client: Client | None = None,
        learnings_repo: LearningsRepository | None = None,
    ):
        """Inicializa o repositório utilizando o client do Supabase."""
        self.supabase_url = SUPABASE_URL
        self.supabase_service_key = SUPABASE_SERVICE_ROLE_KEY
        self.client: Client | None = client
        self.learnings_repo = learnings_repo

        if self.client is None and self.supabase_url and self.supabase_service_key:
            self.client = create_client(self.supabase_url, self.supabase_service_key)

    async def find_relevant_knowledge(
        self,
        user_query: str,
        embedding: list[float],
        exclude_learning_ids: Iterable[LearningId] | None = None,
    ) -> RelevantKnowledge:
        """
        Busca conhecimento relevante usando funções RPC expostas no Supabase.
        """
        if not self.client:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "Busca RAG ignorada: credenciais do Supabase ausentes. Consulta='%s'",
                    user_query[:80] + ("…" if len(user_query) > 80 else ""),
                )
            return RelevantKnowledge(relevant_artifacts=[], relevant_learnings=[])

        try:
            artifact_rows = await self._call_supabase_rpc(
                "rag_get_relevant_chunks",
                {"query_embedding": embedding, "match_limit": 5},
            )

            artifact_chunks: list[ArtifactChunk] = []
            artifact_scores: dict[ChunkId, float] = {}
            for row in artifact_rows:
                chunk_id = row.get("id")
                artifact_id = row.get("artifact_id")
                if not chunk_id or not artifact_id:
                    continue
                content = row.get("content") or ""
                embedding_vec = row.get("embedding") or []
                section_title = row.get("section_title")
                section_level = row.get("section_level")
                content_type = row.get("content_type")
                position = row.get("chunk_position") or 0
                token_count = row.get("token_count") or 0
                breadcrumbs_raw = row.get("breadcrumbs") or []

                breadcrumbs = breadcrumbs_raw
                if isinstance(breadcrumbs_raw, str):
                    try:
                        breadcrumbs = json.loads(breadcrumbs_raw)
                    except json.JSONDecodeError:
                        breadcrumbs = []

                metadata = ChunkMetadata(
                    section_title=section_title,
                    section_level=section_level,
                    content_type=content_type,
                    position=position,
                    token_count=token_count,
                    breadcrumbs=breadcrumbs,
                )
                similarity = row.get("similarity") or row.get("score")

                chunk = ArtifactChunk(
                    id=ChunkId(uuid.UUID(chunk_id)),
                    artifact_id=ArtifactId(uuid.UUID(artifact_id)),
                    content=content,
                    embedding=Embedding(vector=embedding_vec),
                    metadata=metadata,
                )
                artifact_chunks.append(chunk)
                if similarity is not None:
                    try:
                        artifact_scores[chunk.id] = float(similarity)
                    except (TypeError, ValueError):
                        pass

            learnings_rows = await self._call_supabase_rpc(
                "rag_get_relevant_learnings",
                {"query_embedding": embedding, "match_limit": 3},
            )

            exclude_learning_ids_set = {
                str(learning_id) for learning_id in (exclude_learning_ids or [])
            }

            learnings_candidates: list[tuple[Learning, float]] = []
            for row in learnings_rows:
                learning_id = row.get("id")
                source_feedback_id = row.get("source_feedback_id")
                if not learning_id or not source_feedback_id:
                    continue
                content = row.get("content") or ""
                embedding_vec = row.get("embedding") or []
                created_at_raw = row.get("created_at")
                relevance_weight_raw = row.get("relevance_weight")
                last_used_raw = row.get("last_used_at")
                similarity = row.get("similarity") or row.get("score")

                if isinstance(created_at_raw, datetime):
                    created_at_value = created_at_raw
                elif isinstance(created_at_raw, str):
                    normalized = (
                        created_at_raw.replace("Z", "+00:00")
                        if created_at_raw.endswith("Z")
                        else created_at_raw
                    )
                    try:
                        created_at_value = datetime.fromisoformat(normalized)
                    except ValueError:
                        created_at_value = datetime.utcnow()
                else:
                    created_at_value = datetime.utcnow()

                try:
                    relevance_weight = (
                        float(relevance_weight_raw)
                        if relevance_weight_raw is not None
                        else None
                    )
                except (TypeError, ValueError):
                    relevance_weight = None

                last_used_at = self._parse_datetime(last_used_raw)

                learning = Learning(
                    id=LearningId(uuid.UUID(learning_id)),
                    content=content,
                    embedding=Embedding(vector=embedding_vec),
                    source_feedback_id=FeedbackId(uuid.UUID(source_feedback_id)),
                    created_at=created_at_value,
                    relevance_weight=relevance_weight,
                    last_used_at=last_used_at,
                )
                if str(learning.id) in exclude_learning_ids_set:
                    continue

                combined_score = self._combine_learning_score(
                    similarity=similarity,
                    relevance_weight=relevance_weight,
                    last_used_at=last_used_at,
                )
                learnings_candidates.append((learning, combined_score))

            learnings_candidates.sort(key=lambda item: item[1], reverse=True)
            learnings: list[Learning] = [
                candidate[0] for candidate in learnings_candidates
            ]
            learning_scores: dict[LearningId, float] = {
                candidate[0].id: candidate[1] for candidate in learnings_candidates
            }

            if self.learnings_repo and learnings:
                try:
                    await self.learnings_repo.touch_last_used(
                        [learning.id for learning in learnings]
                    )
                except Exception as touch_error:
                    logger.warning(
                        "Não foi possível atualizar last_used_at dos aprendizados: %s",
                        touch_error,
                    )

            query_preview = user_query[:80] + ("…" if len(user_query) > 80 else "")

            if logger.isEnabledFor(logging.DEBUG):
                chunk_summary = [
                    {
                        "chunk_id": str(chunk.id),
                        "artifact_id": str(chunk.artifact_id),
                        "position": chunk.metadata.position if chunk.metadata else None,
                        "section_title": chunk.metadata.section_title
                        if chunk.metadata
                        else None,
                        "token_count": chunk.metadata.token_count
                        if chunk.metadata
                        else None,
                        "preview": (
                            chunk.content[:120]
                            + ("…" if len(chunk.content) > 120 else "")
                        ).replace("\n", " "),
                    }
                    for chunk in artifact_chunks
                ]
                logger.debug(
                    "RAG encontrou %d chunks relevantes para a consulta '%s': %s",
                    len(artifact_chunks),
                    query_preview,
                    chunk_summary,
                )
            elif not artifact_chunks:
                logger.debug(
                    "RAG não retornou chunks relevantes para a consulta '%s'",
                    query_preview,
                )

            if logger.isEnabledFor(logging.DEBUG) and learnings:
                learning_summary = [
                    {
                        "learning_id": str(learning.id),
                        "preview": (
                            learning.content[:120]
                            + ("…" if len(learning.content) > 120 else "")
                        ).replace("\n", " "),
                    }
                    for learning in learnings
                ]
                logger.debug(
                    "RAG encontrou %d aprendizados relevantes para a consulta '%s': %s",
                    len(learnings),
                    query_preview,
                    learning_summary,
                )
            elif not learnings:
                logger.debug(
                    "RAG não retornou aprendizados relevantes para a consulta '%s'",
                    query_preview,
                )

            return RelevantKnowledge(
                relevant_artifacts=artifact_chunks,
                relevant_learnings=learnings,
                artifact_scores=artifact_scores,
                learning_scores=learning_scores,
            )
        except Exception as e:
            logger.exception("Erro durante a busca de conhecimento relevante: %s", e)
            return RelevantKnowledge(relevant_artifacts=[], relevant_learnings=[])

    async def _call_supabase_rpc(self, function_name: str, params: dict) -> list[dict]:
        """Executa uma função RPC no Supabase de forma assíncrona."""
        if not self.client:
            return []

        def _execute():
            response = self.client.rpc(function_name, params).execute()
            error = getattr(response, "error", None)
            if error:
                message = getattr(error, "message", str(error))
                raise RuntimeError(f"Erro ao executar RPC '{function_name}': {message}")
            return getattr(response, "data", []) or []

        return await asyncio.to_thread(_execute)

    def _parse_datetime(self, value) -> datetime | None:
        """Normaliza entrada potencialmente vinda do Supabase em datetime."""
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            normalized = value.replace("Z", "+00:00") if value.endswith("Z") else value
            try:
                return datetime.fromisoformat(normalized)
            except ValueError:
                return None
        return None

    def _combine_learning_score(
        self,
        *,
        similarity: float | int | None,
        relevance_weight: float | None,
        last_used_at: datetime | None,
    ) -> float:
        """Combina similaridade vetorial e peso dinâmico para ordenar aprendizados."""
        similarity_component = float(similarity) if similarity is not None else 0.0
        weight_component = relevance_weight if relevance_weight is not None else 0.7

        recency_bonus = 0.0
        if last_used_at:
            days_since_use = (datetime.utcnow() - last_used_at).days
            if days_since_use <= 7:
                recency_bonus = 0.1
            elif days_since_use <= 30:
                recency_bonus = 0.05
            elif days_since_use > 180:
                recency_bonus = -0.05

        combined = similarity_component * 0.6 + weight_component * 0.35 + recency_bonus
        return round(combined, 4)
