"""Tipos de dados do domínio de Artefatos."""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional
from app.domain.shared_kernel import ArtifactId, ChunkId, Embedding


@dataclass(frozen=True)
class ChunkMetadata:
    """Metadados estruturais e contextuais para um chunk."""
    section_title: Optional[str]
    section_level: Optional[int]
    content_type: Optional[str]
    position: int
    token_count: int
    breadcrumbs: list[str]


class ArtifactSourceType(Enum):
    """Tipo de origem do artefato."""
    PDF = auto()
    TEXT = auto()


# Value Object que representa um pedaço de um artefato
@dataclass(frozen=True)
class ArtifactChunk:
    """Um pedaço de texto indexável de um artefato, com seu vetor."""
    id: ChunkId
    artifact_id: ArtifactId
    content: str
    embedding: Embedding
    metadata: Optional[ChunkMetadata] = None


# Entidade principal/Aggregate Root deste domínio
@dataclass(frozen=True)
class Artifact:
    """Artefato Cultural - fonte primária de conhecimento."""
    id: ArtifactId
    title: str
    source_type: ArtifactSourceType
    chunks: list[ArtifactChunk]
    source_url: Optional[str] = None  # Link para o PDF no Supabase Storage
    original_content: Optional[str] = None  # Conteúdo original quando texto puro

