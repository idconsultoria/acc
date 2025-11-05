"""Repositório para busca de conhecimento relevante (RAG)."""
import psycopg
import json
from typing import Protocol
from app.domain.artifacts.types import ArtifactChunk
from app.domain.learnings.types import Learning
from app.domain.shared_kernel import ChunkId, LearningId, ArtifactId, FeedbackId
from app.infrastructure.persistence.config import DATABASE_URL
import uuid


class RelevantKnowledge:
    """Representa o conhecimento relevante encontrado."""
    def __init__(
        self,
        relevant_artifacts: list[ArtifactChunk],
        relevant_learnings: list[Learning]
    ):
        self.relevant_artifacts = relevant_artifacts
        self.relevant_learnings = relevant_learnings


class KnowledgeRepository:
    """Repositório para busca vetorial de conhecimento relevante."""
    
    def __init__(self):
        """Inicializa o repositório com conexão PostgreSQL."""
        self.conn_string = DATABASE_URL
    
    async def find_relevant_knowledge(self, user_query: str, embedding: list[float]) -> RelevantKnowledge:
        """
        Busca conhecimento relevante usando busca vetorial.
        
        Args:
            user_query: Consulta do usuário
            embedding: Vetor de embedding da consulta
        
        Returns:
            Conhecimento relevante encontrado
        """
        # Se não houver DATABASE_URL configurado, retorna conhecimento vazio
        if not self.conn_string:
            return RelevantKnowledge(relevant_artifacts=[], relevant_learnings=[])

        try:
            # Conecta ao PostgreSQL
            async with await psycopg.AsyncConnection.connect(self.conn_string) as conn:
                async with conn.cursor() as cur:
                                        # Busca chunks de artefatos mais similares
                    # Converte o embedding para formato do pgvector (array de floats)
                    # O psycopg aceita arrays Python diretamente para vetores
                    artifact_chunks_query = """
                        SELECT
                            ac.id,
                            ac.artifact_id,
                            ac.content,
                            ac.embedding,
                            a.title
                        FROM artifact_chunks ac
                        JOIN artifacts a ON ac.artifact_id = a.id
                        ORDER BY ac.embedding <=> %s::vector
                        LIMIT 5
                    """

                    # Passa o embedding como array para o pgvector
                    await cur.execute(artifact_chunks_query, (embedding,))
                    artifact_rows = await cur.fetchall()

                    # Converte para ArtifactChunk
                    from app.domain.artifacts.types import ArtifactChunk
                    from app.domain.shared_kernel import Embedding

                    artifact_chunks = []
                    for row in artifact_rows:
                        chunk_id, artifact_id, content, embedding_vec, title = row
                        chunk = ArtifactChunk(
                            id=ChunkId(uuid.UUID(chunk_id)),
                            artifact_id=ArtifactId(uuid.UUID(artifact_id)),
                            content=content,
                            embedding=Embedding(vector=embedding_vec)
                        )
                        artifact_chunks.append(chunk)

                                                                                # Busca aprendizados mais similares
                    learnings_query = """
                        SELECT 
                            l.id,
                            l.content,
                            l.embedding,
                            l.source_feedback_id,
                            l.created_at
                        FROM learnings l
                        ORDER BY l.embedding <=> %s::vector
                        LIMIT 3
                    """

                    await cur.execute(learnings_query, (embedding,))
                    learning_rows = await cur.fetchall()

                    # Converte para Learning
                    from app.domain.learnings.types import Learning
                    from datetime import datetime

                    learnings = []
                    for row in learning_rows:
                        learning_id, content, embedding_vec, source_feedback_id, created_at = row
                        learning = Learning(
                            id=LearningId(uuid.UUID(learning_id)),
                            content=content,
                            embedding=Embedding(vector=embedding_vec),
                            source_feedback_id=FeedbackId(uuid.UUID(source_feedback_id)),
                            created_at=created_at if isinstance(created_at, datetime) else datetime.fromisoformat(str(created_at))
                                                )
                        learnings.append(learning)

                    return RelevantKnowledge(
                        relevant_artifacts=artifact_chunks,
                        relevant_learnings=learnings
                    )
        except Exception as e:
            # Se houver erro na busca vetorial, retorna conhecimento vazio
            # Isso permite que o sistema funcione mesmo sem busca vetorial configurada
            return RelevantKnowledge(relevant_artifacts=[], relevant_learnings=[])

