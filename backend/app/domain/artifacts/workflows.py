"""Workflows do domínio de Artefatos."""
from typing import Protocol
from app.domain.artifacts.types import Artifact, ArtifactChunk, ArtifactSourceType, ChunkMetadata
from app.domain.shared_kernel import ArtifactId, ChunkId, Embedding
from app.infrastructure.files.structured_chunker import analyze_structure, generate_chunks
import uuid


# --- Interfaces de Dependência (Protocolos) ---
# Definem o "contrato" que a infraestrutura deve implementar

class PDFProcessor(Protocol):
    """Interface para processamento de PDFs."""
    def extract_text(self, file_content: bytes) -> str:
        """Extrai texto de um arquivo PDF."""
        ...

    def extract_with_metadata(self, file_content: bytes) -> list[tuple[str, dict]]:
        """Extrai texto com metadados estruturais do PDF."""
        ...


class EmbeddingGenerator(Protocol):
    """Interface para geração de embeddings."""
    def generate(self, text: str) -> list[float]:
        """Gera um embedding para um texto."""
        ...


# --- Assinaturas dos Workflows ---

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """
    Divide um texto em chunks com sobreposição.
    
    Args:
        text: Texto a ser dividido
        chunk_size: Tamanho de cada chunk em caracteres
        overlap: Quantidade de caracteres de sobreposição entre chunks
    
    Returns:
        Lista de chunks de texto
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        
        # Tenta quebrar em um ponto apropriado (espaço, quebra de linha)
        if end < text_length:
            # Procura por quebra de linha ou espaço próximo ao final
            last_newline = chunk.rfind('\n')
            last_space = chunk.rfind(' ')
            
            if last_newline > chunk_size * 0.7:
                chunk = chunk[:last_newline + 1]
                end = start + last_newline + 1
            elif last_space > chunk_size * 0.7:
                chunk = chunk[:last_space + 1]
                end = start + last_space + 1
        
        chunks.append(chunk.strip())
        
        # Move o início considerando o overlap
        start = end - overlap if end < text_length else end
    
    return chunks


def create_artifact_from_text(
    title: str,
    text_content: str,
    embedding_generator: EmbeddingGenerator
) -> Artifact:
    """
    Workflow para criar um artefato a partir de texto.
    Ele é responsável por dividir o texto em chunks e gerar os embeddings.
    """
    artifact_id = ArtifactId(uuid.uuid4())
    artifact_chunks = _generate_structured_chunks(
        text_content=text_content,
        artifact_id=artifact_id,
        embedding_generator=embedding_generator,
    )
    
    # Cria o artefato
    artifact = Artifact(
        id=artifact_id,
        title=title,
        source_type=ArtifactSourceType.TEXT,
        chunks=artifact_chunks,
        original_content=text_content
    )
    
    return artifact


def create_artifact_from_pdf(
    title: str,
    pdf_content: bytes,
    pdf_processor: PDFProcessor,
    embedding_generator: EmbeddingGenerator
) -> Artifact:
    """
    Workflow para criar um artefato a partir de um PDF.
    Extrai o texto, faz o chunking e gera embeddings.
    """
    # Extrai o texto do PDF
    artifact_id = ArtifactId(uuid.uuid4())

    # Tenta extrair com metadados estruturados
    structured_segments: list[tuple[str, dict]] = []
    try:
        structured_segments = pdf_processor.extract_with_metadata(pdf_content)
    except AttributeError:
        structured_segments = []
    except NotImplementedError:
        structured_segments = []

    if structured_segments:
        enriched_text_parts: list[str] = []
        for segment_text, attrs in structured_segments:
            segment_text = segment_text.strip()
            if not segment_text:
                continue
            section_title = attrs.get("section_title") if isinstance(attrs, dict) else None
            section_level = attrs.get("section_level") if isinstance(attrs, dict) else None
            content_type = attrs.get("content_type") if isinstance(attrs, dict) else None

            if section_title:
                level = section_level if isinstance(section_level, int) and 1 <= section_level <= 6 else 2
                enriched_text_parts.append(f"{'#' * level} {section_title}")
            if content_type == "bullet":
                lines = [line.strip() for line in segment_text.splitlines() if line.strip()]
                enriched_text_parts.extend([f"- {line}" for line in lines])
            else:
                enriched_text_parts.append(segment_text)
        processed_text = "\n\n".join(enriched_text_parts)
    else:
        processed_text = pdf_processor.extract_text(pdf_content)

    artifact_chunks = _generate_structured_chunks(
        text_content=processed_text,
        artifact_id=artifact_id,
        embedding_generator=embedding_generator,
    )
    
    # Cria o artefato
    artifact = Artifact(
        id=artifact_id,
        title=title,
        source_type=ArtifactSourceType.PDF,
        chunks=artifact_chunks
    )
    
    return artifact


def _generate_structured_chunks(
    text_content: str,
    artifact_id: ArtifactId,
    embedding_generator: EmbeddingGenerator,
) -> list[ArtifactChunk]:
    """Gera chunks estruturados com metadados e embeddings."""
    if not text_content:
        return []

    blocks = analyze_structure(text_content)
    structured_chunks = generate_chunks(blocks)

    artifact_chunks: list[ArtifactChunk] = []
    for position, (content, metadata) in enumerate(structured_chunks):
        clean_content = content.strip()
        if not clean_content:
            continue
        chunk_id = ChunkId(uuid.uuid4())
        embedding_vector = embedding_generator.generate(clean_content)
        embedding = Embedding(vector=embedding_vector)

        normalized_metadata = ChunkMetadata(
            section_title=metadata.section_title,
            section_level=metadata.section_level,
            content_type=metadata.content_type,
            position=position,
            token_count=metadata.token_count,
            breadcrumbs=metadata.breadcrumbs,
        )

        artifact_chunks.append(
            ArtifactChunk(
                id=chunk_id,
                artifact_id=artifact_id,
                content=clean_content,
                embedding=embedding,
                metadata=normalized_metadata,
            )
        )

    return artifact_chunks

