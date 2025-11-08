"""Repositório de Aprendizados usando Supabase."""
from supabase import create_client, Client
from app.domain.learnings.types import Learning, LearningMergeCandidate
from app.domain.shared_kernel import LearningId, FeedbackId, Embedding
from app.infrastructure.persistence.config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime
import uuid
from typing import Iterable, Sequence


class LearningsRepository:
    """Repositório para persistência de aprendizados no Supabase."""
    
    def __init__(self):
        """Inicializa o repositório com cliente Supabase."""
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    async def save(self, learning: Learning) -> Learning:
        """Salva um aprendizado."""
        learning_data = {
            "id": str(learning.id),
            "content": learning.content,
            "embedding": learning.embedding.vector,
            "source_feedback_id": str(learning.source_feedback_id),
            "created_at": learning.created_at.isoformat(),
        }

        if learning.relevance_weight is not None:
            learning_data["relevance_weight"] = float(learning.relevance_weight)
        if learning.last_used_at is not None:
            learning_data["last_used_at"] = learning.last_used_at.isoformat()

        table = self.supabase.table("learnings")
        if hasattr(table, "upsert"):
            table.upsert(learning_data, on_conflict="id").execute()
        else:
            table.insert(learning_data).execute()

        return learning
    
    async def find_all(self) -> list[Learning]:
        """Busca todos os aprendizados."""
        result = (
            self.supabase.table("learnings")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        return [self._row_to_learning(row) for row in result.data or []]

    async def get_by_ids(self, learning_ids: Sequence[LearningId]) -> list[Learning]:
        """Busca aprendizados por uma lista de IDs."""
        if not learning_ids:
            return []

        id_list = [str(learning_id) for learning_id in learning_ids]
        result = (
            self.supabase.table("learnings")
            .select("*")
            .in_("id", id_list)
            .execute()
        )

        return [self._row_to_learning(row) for row in result.data or []]

    async def update_weights(self, updates: dict[LearningId, float]) -> None:
        """Atualiza pesos de relevância de múltiplos aprendizados."""
        if not updates:
            return

        if not getattr(self, "supabase", None):
            return

        table = self.supabase.table("learnings")
        for learning_id, weight in updates.items():
            table.update({"relevance_weight": float(weight)}).eq("id", str(learning_id)).execute()

    async def touch_last_used(self, learning_ids: Iterable[LearningId], when: datetime | None = None) -> None:
        """Atualiza o timestamp last_used_at para os aprendizados informados."""
        ids = list(learning_ids)
        if not ids:
            return

        if not getattr(self, "supabase", None):
            return

        timestamp = (when or datetime.utcnow()).isoformat()
        table = self.supabase.table("learnings")
        for learning_id in ids:
            table.update({"last_used_at": timestamp}).eq("id", str(learning_id)).execute()

    async def merge(
        self,
        learning_ids: Sequence[LearningId],
        merged_content: str,
        *,
        merged_embedding: list[float] | None = None,
        merged_weight: float | None = None,
    ) -> Learning:
        """
        Mescla aprendizados duplicados criando um novo registro e arquivando os antigos.
        """
        existing = await self.get_by_ids(learning_ids)
        if not existing:
            raise ValueError("Nenhum aprendizado encontrado para merge.")

        if not getattr(self, "supabase", None):
            raise RuntimeError("Repositório não inicializado com cliente Supabase.")

        base = existing[0]
        embedding_vector = merged_embedding or base.embedding.vector
        if not merged_embedding and len(existing) > 1:
            embedding_vector = self._average_embeddings([l.embedding.vector for l in existing])

        weight = merged_weight
        if weight is None:
            weights = [learning.relevance_weight for learning in existing if learning.relevance_weight is not None]
            weight = sum(weights) / len(weights) if weights else base.relevance_weight

        new_learning = Learning(
            id=LearningId(uuid.uuid4()),
            content=merged_content,
            embedding=Embedding(vector=embedding_vector),
            source_feedback_id=base.source_feedback_id,
            created_at=datetime.utcnow(),
            relevance_weight=weight,
            last_used_at=None,
        )

        await self.save(new_learning)

        table = self.supabase.table("learnings")
        archive_payload = {"is_archived": True, "archived_at": datetime.utcnow().isoformat()}
        for learning in existing:
            table.update(archive_payload).eq("id", str(learning.id)).execute()

        self._register_merge_history(new_learning, existing)
        return new_learning

    async def suggest_merge_candidates(
        self,
        similarity_threshold: float = 0.85,
        limit: int = 20,
    ) -> list[LearningMergeCandidate]:
        """
        Retorna candidatos a merge baseados em similaridade pré-calculada via RPC.
        """
        if not getattr(self, "supabase", None):
            return []

        response = (
            self.supabase.rpc(
                "learnings_find_duplicates",
                {"similarity_threshold": similarity_threshold, "candidate_limit": limit},
            ).execute()
        )

        candidates: list[LearningMergeCandidate] = []
        rows = response.data or []
        for row in rows:
            base_learning = self._row_to_learning(row["base"])
            duplicates = [self._row_to_learning(dup) for dup in row.get("duplicates", [])]
            candidates.append(
                LearningMergeCandidate(
                    base_learning=base_learning,
                    duplicate_learnings=duplicates,
                    similarity_score=row.get("similarity_score"),
                )
            )
        return candidates

    def _register_merge_history(self, merged_learning: Learning, originals: Sequence[Learning]) -> None:
        """Grava histórico de merge quando supabase tiver tabela configurada."""
        try:
            if not getattr(self, "supabase", None):
                return
            history_rows = [
                {
                    "merged_learning_id": str(merged_learning.id),
                    "source_learning_id": str(learning.id),
                    "created_at": datetime.utcnow().isoformat(),
                }
                for learning in originals
            ]
            if history_rows:
                self.supabase.table("learning_merge_history").insert(history_rows).execute()
        except Exception:
            # Ignora falhas silenciosamente quando tabela não existe
            pass

    def _row_to_learning(self, row: dict) -> Learning:
        """Converte linha do banco em entidade de domínio."""
        from app.domain.shared_kernel import Embedding

        created_at_raw = row.get("created_at")
        last_used_raw = row.get("last_used_at")

        created_at = self._parse_datetime(created_at_raw)
        last_used_at = self._parse_datetime(last_used_raw)
        weight = row.get("relevance_weight")
        try:
            weight = float(weight) if weight is not None else None
        except (TypeError, ValueError):
            weight = None

        return Learning(
            id=LearningId(uuid.UUID(row["id"])),
            content=row.get("content") or "",
            embedding=Embedding(vector=row.get("embedding") or []),
            source_feedback_id=FeedbackId(uuid.UUID(row["source_feedback_id"])),
            created_at=created_at,
            relevance_weight=weight,
            last_used_at=last_used_at,
        )

    def _parse_datetime(self, value) -> datetime | None:
        """Normaliza datas vindas do Supabase."""
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

    def _average_embeddings(self, vectors: Sequence[list[float]]) -> list[float]:
        """Calcula média simples de embeddings."""
        if not vectors:
            return []
        vector_length = len(vectors[0])
        if vector_length == 0:
            return []

        accumulator = [0.0] * vector_length
        for vector in vectors:
            for idx in range(min(vector_length, len(vector))):
                accumulator[idx] += float(vector[idx])
        count = len(vectors)
        return [value / count for value in accumulator]

