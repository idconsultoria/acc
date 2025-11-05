"""Repositório de Artefatos usando Supabase."""
from typing import Protocol
from supabase import create_client, Client
from app.domain.artifacts.types import Artifact, ArtifactChunk, ArtifactSourceType
from app.domain.shared_kernel import ArtifactId, ChunkId, Embedding
from app.infrastructure.persistence.config import SUPABASE_URL, SUPABASE_KEY
import uuid


class ArtifactsRepository:
    """Repositório para persistência de artefatos no Supabase."""
    
    def __init__(self):
        """Inicializa o repositório com cliente Supabase."""
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    async def save(self, artifact: Artifact, source_url: str | None = None) -> Artifact:
        """
        Salva um artefato e seus chunks no banco de dados.
        
        Args:
            artifact: Artefato a ser salvo
            source_url: URL do arquivo no Supabase Storage (se aplicável)
        
        Returns:
            Artefato salvo
        """
        # Salva o artefato
        artifact_data = {
            "id": str(artifact.id),
            "title": artifact.title,
            "source_type": artifact.source_type.name,
            "source_url": source_url,
            "created_at": "now()"
        }
        
        self.supabase.table("artifacts").insert(artifact_data).execute()
        
        # Salva os chunks com seus embeddings
        for chunk in artifact.chunks:
            chunk_data = {
                "id": str(chunk.id),
                "artifact_id": str(chunk.artifact_id),
                "content": chunk.content,
                "embedding": chunk.embedding.vector
            }
            
            self.supabase.table("artifact_chunks").insert(chunk_data).execute()
        
        return artifact
    
    async def find_by_id(self, artifact_id: ArtifactId) -> Artifact | None:
        """Busca um artefato por ID."""
        result = self.supabase.table("artifacts").select("*").eq("id", str(artifact_id)).execute()
        
        if not result.data:
            return None
        
        artifact_row = result.data[0]
        
        # Busca os chunks do artefato
        chunks_result = self.supabase.table("artifact_chunks").select("*").eq("artifact_id", str(artifact_id)).execute()
        
        # Converte os chunks (precisa dos embeddings)
        chunks = []
        for chunk_row in chunks_result.data:
            chunk = ArtifactChunk(
                id=ChunkId(uuid.UUID(chunk_row["id"])),
                artifact_id=ArtifactId(uuid.UUID(chunk_row["artifact_id"])),
                content=chunk_row["content"],
                embedding=Embedding(vector=chunk_row["embedding"])
            )
            chunks.append(chunk)
        
        source_type = ArtifactSourceType[artifact_row["source_type"]]
        
        return Artifact(
            id=ArtifactId(uuid.UUID(artifact_row["id"])),
            title=artifact_row["title"],
            source_type=source_type,
            chunks=chunks,
            source_url=artifact_row.get("source_url")
        )
    
    async def get_artifact_data(self, artifact_id: ArtifactId) -> dict | None:
        """Busca dados adicionais do artefato (description, tags)."""
        result = self.supabase.table("artifacts").select("description, tags").eq("id", str(artifact_id)).execute()
        
        if not result.data:
            return None
        
        return {
            "description": result.data[0].get("description"),
            "tags": result.data[0].get("tags", []) or []
        }
    
    async def update_artifact_tags(self, artifact_id: ArtifactId, tags: list[str]) -> None:
        """Atualiza as tags de um artefato."""
        self.supabase.table("artifacts").update({"tags": tags}).eq("id", str(artifact_id)).execute()
    
    async def update_artifact_description(self, artifact_id: ArtifactId, description: str | None) -> None:
        """Atualiza a descrição de um artefato."""
        self.supabase.table("artifacts").update({"description": description}).eq("id", str(artifact_id)).execute()
    
    async def find_all(self) -> list[Artifact]:
        """Busca todos os artefatos (sem chunks, apenas metadados)."""
        result = self.supabase.table("artifacts").select("*").order("created_at", desc=True).execute()
        
        artifacts = []
        for row in result.data:
            source_type = ArtifactSourceType[row["source_type"]]
            
            artifact = Artifact(
                id=ArtifactId(uuid.UUID(row["id"])),
                title=row["title"],
                source_type=source_type,
                chunks=[],  # Não carrega chunks na listagem
                source_url=row.get("source_url")
            )
            artifacts.append(artifact)
        
        return artifacts
    
    async def delete(self, artifact_id: ArtifactId) -> None:
        """Deleta um artefato e seus chunks."""
        # Deleta chunks primeiro
        self.supabase.table("artifact_chunks").delete().eq("artifact_id", str(artifact_id)).execute()
        
        # Deleta o artefato
        self.supabase.table("artifacts").delete().eq("id", str(artifact_id)).execute()
    
    async def find_chunks_by_embedding(self, embedding: list[float], limit: int = 5) -> list[ArtifactChunk]:
        """
        Busca chunks mais similares usando busca vetorial.
        
        Args:
            embedding: Vetor de embedding para busca
            limit: Número máximo de resultados
        
        Returns:
            Lista de chunks mais similares
        """
        # Usa pgvector para busca de similaridade
        # A query SQL seria algo como:
        # SELECT *, 1 - (embedding <=> $1::vector) AS similarity
        # FROM artifact_chunks
        # ORDER BY similarity DESC
        # LIMIT $2
        
        # Por enquanto, vamos usar uma abordagem simplificada
        # No Supabase, precisamos usar RPC (Remote Procedure Call) para busca vetorial
        # ou fazer a query diretamente no PostgreSQL
        
        # Para o MVP, vamos fazer uma busca simples e depois ordenar por similaridade
        # Isso requer uma função RPC no Supabase ou acesso direto ao PostgreSQL
        
        # Por enquanto, retornamos vazio - será implementado com acesso direto ao PostgreSQL
        # usando psycopg para queries vetoriais
        return []

