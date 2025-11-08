"""Repositório de Artefatos usando Supabase."""
from typing import Protocol
import json
from supabase import create_client, Client
from app.domain.artifacts.types import Artifact, ArtifactChunk, ArtifactSourceType, ChunkMetadata
from app.domain.shared_kernel import ArtifactId, ChunkId, Embedding
from app.infrastructure.persistence.config import SUPABASE_URL, SUPABASE_KEY
import uuid


class ArtifactsRepository:
    """Repositório para persistência de artefatos no Supabase."""
    
    def __init__(self):
        """Inicializa o repositório com cliente Supabase."""
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    async def save(self, artifact: Artifact, source_url: str | None = None, color: str | None = None) -> Artifact:
        """
        Salva um artefato e seus chunks no banco de dados.
        
        Args:
            artifact: Artefato a ser salvo
            source_url: URL do arquivo no Supabase Storage (se aplicável)
            color: Cor de fundo do card (se aplicável)
        
        Returns:
            Artefato salvo
        """
        # Salva o artefato
        artifact_data = {
            "id": str(artifact.id),
            "title": artifact.title,
            "source_type": artifact.source_type.name,
            "source_url": source_url,
            "color": color,
            "original_content": artifact.original_content,
            "created_at": "now()"
        }
        
        self.supabase.table("artifacts").insert(artifact_data).execute()
        
        # Salva os chunks com seus embeddings
        for chunk in artifact.chunks:
            metadata = chunk.metadata
            chunk_data = {
                "id": str(chunk.id),
                "artifact_id": str(chunk.artifact_id),
                "content": chunk.content,
                "embedding": chunk.embedding.vector,
                "section_title": metadata.section_title if metadata else None,
                "section_level": metadata.section_level if metadata else None,
                "content_type": metadata.content_type if metadata else None,
                "position": metadata.position if metadata else None,
                "token_count": metadata.token_count if metadata else None,
                "breadcrumbs": metadata.breadcrumbs if metadata else None,
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
            breadcrumbs = chunk_row.get("breadcrumbs") or []
            if isinstance(breadcrumbs, str):
                try:
                    breadcrumbs = json.loads(breadcrumbs)
                except json.JSONDecodeError:
                    breadcrumbs = []
            chunk = ArtifactChunk(
                id=ChunkId(uuid.UUID(chunk_row["id"])),
                artifact_id=ArtifactId(uuid.UUID(chunk_row["artifact_id"])),
                content=chunk_row["content"],
                embedding=Embedding(vector=chunk_row["embedding"]),
                metadata=None
            )
            if any(
                key in chunk_row
                for key in [
                    "section_title",
                    "section_level",
                    "content_type",
                    "position",
                    "token_count",
                    "breadcrumbs",
                ]
            ):
                metadata = ChunkMetadata(
                    section_title=chunk_row.get("section_title"),
                    section_level=chunk_row.get("section_level"),
                    content_type=chunk_row.get("content_type"),
                    position=chunk_row.get("position", 0),
                    token_count=chunk_row.get("token_count", 0),
                    breadcrumbs=breadcrumbs,
                )
                chunk = ArtifactChunk(
                    id=chunk.id,
                    artifact_id=chunk.artifact_id,
                    content=chunk.content,
                    embedding=chunk.embedding,
                    metadata=metadata,
                )
            chunks.append(chunk)

        chunks.sort(key=lambda c: c.metadata.position if c.metadata else 0)
        
        source_type = ArtifactSourceType[artifact_row["source_type"]]
        
        return Artifact(
            id=ArtifactId(uuid.UUID(artifact_row["id"])),
            title=artifact_row["title"],
            source_type=source_type,
            chunks=chunks,
            source_url=artifact_row.get("source_url"),
            original_content=artifact_row.get("original_content")
        )
    
    async def get_artifact_data(self, artifact_id: ArtifactId) -> dict | None:
        """Busca dados adicionais do artefato (description, tags, color)."""
        result = self.supabase.table("artifacts").select("description, tags, color").eq("id", str(artifact_id)).execute()
        
        if not result.data:
            return None
        
        return {
            "description": result.data[0].get("description"),
            "tags": result.data[0].get("tags", []) or [],
            "color": result.data[0].get("color"),
            "original_content": result.data[0].get("original_content")
        }
    
    async def update_artifact_tags(self, artifact_id: ArtifactId, tags: list[str]) -> None:
        """Atualiza as tags de um artefato."""
        self.supabase.table("artifacts").update({"tags": tags}).eq("id", str(artifact_id)).execute()
    
    async def update_artifact_title(self, artifact_id: ArtifactId, title: str) -> None:
        """Atualiza o título de um artefato."""
        self.supabase.table("artifacts").update({"title": title}).eq("id", str(artifact_id)).execute()
    
    async def update_artifact_description(self, artifact_id: ArtifactId, description: str | None) -> None:
        """Atualiza a descrição de um artefato."""
        self.supabase.table("artifacts").update({"description": description}).eq("id", str(artifact_id)).execute()
    
    async def update_artifact_color(self, artifact_id: ArtifactId, color: str | None) -> None:
        """Atualiza a cor de um artefato."""
        self.supabase.table("artifacts").update({"color": color}).eq("id", str(artifact_id)).execute()
    
    async def update_artifact_content(self, artifact_id: ArtifactId, new_content: str, embedding_generator) -> None:
        """Atualiza o conteúdo de um artefato TEXT re-processando os chunks."""
        from app.domain.artifacts.workflows import _generate_structured_chunks
        
        # Deleta chunks antigos
        self.supabase.table("artifact_chunks").delete().eq("artifact_id", str(artifact_id)).execute()
        
        # Cria novos chunks
        artifact_chunks = _generate_structured_chunks(
            text_content=new_content,
            artifact_id=artifact_id,
            embedding_generator=embedding_generator,
        )

        for chunk in artifact_chunks:
            metadata = chunk.metadata
            chunk_data = {
                "id": str(chunk.id),
                "artifact_id": str(artifact_id),
                "content": chunk.content,
                "embedding": chunk.embedding.vector,
                "section_title": metadata.section_title if metadata else None,
                "section_level": metadata.section_level if metadata else None,
                "content_type": metadata.content_type if metadata else None,
                "position": metadata.position if metadata else None,
                "token_count": metadata.token_count if metadata else None,
                "breadcrumbs": metadata.breadcrumbs if metadata else None,
            }

            self.supabase.table("artifact_chunks").insert(chunk_data).execute()
        # Atualiza o conteúdo original
        self.supabase.table("artifacts").update({"original_content": new_content}).eq("id", str(artifact_id)).execute()
    
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
                source_url=row.get("source_url"),
                original_content=row.get("original_content")
            )
            artifacts.append(artifact)
        
        return artifacts
    
    async def delete(self, artifact_id: ArtifactId) -> None:
        """Deleta um artefato e seus chunks."""
        # Deleta chunks primeiro
        self.supabase.table("artifact_chunks").delete().eq("artifact_id", str(artifact_id)).execute()
        
        # Deleta o artefato
        self.supabase.table("artifacts").delete().eq("id", str(artifact_id)).execute()
    
    async def delete_chunks(self, artifact_id: ArtifactId) -> None:
        """Deleta apenas os chunks de um artefato."""
        self.supabase.table("artifact_chunks").delete().eq("artifact_id", str(artifact_id)).execute()
    
    async def save_chunks(self, artifact_id: ArtifactId, chunks: list) -> None:
        """Salva chunks de um artefato."""
        for chunk in chunks:
            metadata = chunk.metadata
            chunk_data = {
                "id": str(chunk.id),
                "artifact_id": str(artifact_id),
                "content": chunk.content,
                "embedding": chunk.embedding.vector,
                "section_title": metadata.section_title if metadata else None,
                "section_level": metadata.section_level if metadata else None,
                "content_type": metadata.content_type if metadata else None,
                "position": metadata.position if metadata else None,
                "token_count": metadata.token_count if metadata else None,
                "breadcrumbs": metadata.breadcrumbs if metadata else None,
            }
            self.supabase.table("artifact_chunks").insert(chunk_data).execute()
    
    async def update_source_url(self, artifact_id: ArtifactId, source_url: str) -> None:
        """Atualiza a URL do source de um artefato."""
        self.supabase.table("artifacts").update({"source_url": source_url}).eq("id", str(artifact_id)).execute()
    
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

