"""Workflows do domínio de Artefatos."""
from typing import Protocol
from app.domain.artifacts.types import Artifact, ArtifactChunk, ArtifactSourceType
from app.domain.shared_kernel import ArtifactId, ChunkId, Embedding
import uuid


# --- Interfaces de Dependência (Protocolos) ---
# Definem o "contrato" que a infraestrutura deve implementar

class PDFProcessor(Protocol):
    """Interface para processamento de PDFs."""
    def extract_text(self, file_content: bytes) -> str:
        """Extrai texto de um arquivo PDF."""
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
    # Divide o texto em chunks
    text_chunks = chunk_text(text_content)
    
    # Gera chunks com embeddings
    artifact_chunks = []
    artifact_id = ArtifactId(uuid.uuid4())
    
    for i, text_chunk in enumerate(text_chunks):
        chunk_id = ChunkId(uuid.uuid4())
        embedding_vector = embedding_generator.generate(text_chunk)
        embedding = Embedding(vector=embedding_vector)
        
        chunk = ArtifactChunk(
            id=chunk_id,
            artifact_id=artifact_id,
            content=text_chunk,
            embedding=embedding
        )
        artifact_chunks.append(chunk)
    
    # Cria o artefato
    artifact = Artifact(
        id=artifact_id,
        title=title,
        source_type=ArtifactSourceType.TEXT,
        chunks=artifact_chunks
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
    extracted_text = pdf_processor.extract_text(pdf_content)
    
    # Divide o texto em chunks
    text_chunks = chunk_text(extracted_text)
    
    # Gera chunks com embeddings
    artifact_chunks = []
    artifact_id = ArtifactId(uuid.uuid4())
    
    for i, text_chunk in enumerate(text_chunks):
        chunk_id = ChunkId(uuid.uuid4())
        embedding_vector = embedding_generator.generate(text_chunk)
        embedding = Embedding(vector=embedding_vector)
        
        chunk = ArtifactChunk(
            id=chunk_id,
            artifact_id=artifact_id,
            content=text_chunk,
            embedding=embedding
        )
        artifact_chunks.append(chunk)
    
    # Cria o artefato
    artifact = Artifact(
        id=artifact_id,
        title=title,
        source_type=ArtifactSourceType.PDF,
        chunks=artifact_chunks
    )
    
    return artifact

