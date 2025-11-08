"""Rotas para gerenciamento de Artefatos."""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from app.api.dto import (
    ArtifactDTO,
    ArtifactChunkDTO,
    ChunkMetadataDTO,
    ErrorDTO,
    UpdateArtifactTagsPayload,
    UpdateArtifactPayload,
)
from app.domain.artifacts.workflows import create_artifact_from_text, create_artifact_from_pdf
from app.domain.artifacts.types import ArtifactSourceType
from app.infrastructure.persistence.artifacts_repo import ArtifactsRepository
from app.infrastructure.files.pdf_processor import PDFProcessor
from app.infrastructure.ai.embedding_service import EmbeddingGenerator
from app.infrastructure.persistence.config import GEMINI_API_KEY
from app.infrastructure.persistence.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from supabase import create_client
from datetime import datetime
import uuid

router = APIRouter()

# Inicializa serviços (com tratamento de erros para variáveis não configuradas)
# As validações serão feitas dentro das rotas, não durante a importação
pdf_processor = PDFProcessor()
embedding_generator = EmbeddingGenerator(GEMINI_API_KEY) if GEMINI_API_KEY else None
artifacts_repo = ArtifactsRepository()
supabase_storage = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY) if (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY) else None


@router.get("/artifacts", response_model=list[ArtifactDTO])
async def list_artifacts():
    """Lista todos os Artefatos Culturais."""
    artifacts = await artifacts_repo.find_all()
    
    result = []
    for artifact in artifacts:
        # Busca description, tags e color do banco
        artifact_data = await artifacts_repo.get_artifact_data(artifact.id)
        
        result.append(ArtifactDTO(
            id=artifact.id,
            title=artifact.title,
            source_type=artifact.source_type.name,
            created_at=datetime.utcnow(),  # TODO: Buscar data real do banco
            description=artifact_data.get('description') if artifact_data else None,
            tags=artifact_data.get('tags', []) if artifact_data else [],
            color=artifact_data.get('color') if artifact_data else None,
            source_url=artifact.source_url
        ))
    
    return result


@router.post("/artifacts", response_model=ArtifactDTO, status_code=201)
async def create_artifact(
    title: str = Form(...),
    text_content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    color: Optional[str] = Form(None)
):
    """Cria um novo Artefato Cultural."""
    if not title:
        raise HTTPException(status_code=400, detail="Título é obrigatório")
    
    if not text_content and not file:
        raise HTTPException(status_code=400, detail="É necessário fornecer texto ou arquivo PDF")
    
    source_url = None
    
    if file:
        # Valida configurações necessárias
        if not embedding_generator:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY não configurada. Configure a variável de ambiente GOOGLE_API_KEY no Vercel.")
        if not supabase_storage:
            raise HTTPException(status_code=500, detail="Supabase não configurado. Configure SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY no Vercel.")
        
        # Processa PDF
        file_content = await file.read()
        
        # Verifica se é PDF
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos")
        
        # Cria artefato a partir do PDF
        artifact = create_artifact_from_pdf(
            title=title,
            pdf_content=file_content,
            pdf_processor=pdf_processor,
            embedding_generator=embedding_generator
        )
        
        # Salva o PDF no Supabase Storage
        storage_path = f"artifacts/{artifact.id}/{file.filename}"
        supabase_storage.storage.from_("artifacts").upload(storage_path, file_content)
        
        # Obtém URL pública
        source_url = supabase_storage.storage.from_("artifacts").get_public_url(storage_path)
    else:
        # Valida configurações necessárias
        if not embedding_generator:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY não configurada. Configure a variável de ambiente GOOGLE_API_KEY no Vercel.")
        
        # Cria artefato a partir de texto
        artifact = create_artifact_from_text(
            title=title,
            text_content=text_content,
            embedding_generator=embedding_generator
        )
    
    # Salva no banco de dados
    await artifacts_repo.save(artifact, source_url, color)
    
    # Busca dados completos do artefato
    artifact_data = await artifacts_repo.get_artifact_data(artifact.id)
    
    return ArtifactDTO(
        id=artifact.id,
        title=artifact.title,
        source_type=artifact.source_type.name,
        created_at=datetime.utcnow(),
        description=artifact_data.get('description') if artifact_data else None,
        tags=artifact_data.get('tags', []) if artifact_data else [],
        color=artifact_data.get('color') if artifact_data else None,
        source_url=artifact.source_url
    )


@router.get("/artifacts/{artifact_id}", response_model=ArtifactDTO)
async def get_artifact_by_id(artifact_id: str):
    """Obtém um Artefato Cultural por ID."""
    from app.domain.shared_kernel import ArtifactId
    
    try:
        artifact_id_uuid = ArtifactId(uuid.UUID(artifact_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    artifact = await artifacts_repo.find_by_id(artifact_id_uuid)
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artefato não encontrado")
    
    # Busca dados adicionais
    artifact_data = await artifacts_repo.get_artifact_data(artifact_id_uuid)
    
    return ArtifactDTO(
        id=artifact.id,
        title=artifact.title,
        source_type=artifact.source_type.name,
        created_at=datetime.utcnow(),
        description=artifact_data.get('description') if artifact_data else None,
        tags=artifact_data.get('tags', []) if artifact_data else [],
        color=artifact_data.get('color') if artifact_data else None,
        source_url=artifact.source_url
    )


@router.get("/artifacts/{artifact_id}/content")
async def get_artifact_content(artifact_id: str):
    """Obtém o conteúdo completo de um artefato (chunks concatenados)."""
    from app.domain.shared_kernel import ArtifactId
    
    try:
        artifact_id_uuid = ArtifactId(uuid.UUID(artifact_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    artifact = await artifacts_repo.find_by_id(artifact_id_uuid)
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artefato não encontrado")
    
    if artifact.source_type.name == "TEXT":
        if artifact.original_content:
            return {"source_type": "TEXT", "content": artifact.original_content}
        content = "\n".join([chunk.content for chunk in artifact.chunks])
        return {"source_type": "TEXT", "content": content}

    return {"source_type": "PDF", "source_url": artifact.source_url}


@router.get("/artifacts/{artifact_id}/chunks", response_model=list[ArtifactChunkDTO])
async def get_artifact_chunks(artifact_id: str):
    """Retorna os chunks de um artefato com metadados estruturados."""
    from app.domain.shared_kernel import ArtifactId

    try:
        artifact_id_uuid = ArtifactId(uuid.UUID(artifact_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")

    artifact = await artifacts_repo.find_by_id(artifact_id_uuid)

    if not artifact:
        raise HTTPException(status_code=404, detail="Artefato não encontrado")

    chunk_dtos: list[ArtifactChunkDTO] = []
    for chunk in sorted(artifact.chunks, key=lambda c: c.metadata.position if c.metadata else 0):
        metadata = chunk.metadata
        metadata_dto = None
        if metadata:
            metadata_dto = ChunkMetadataDTO(
                section_title=metadata.section_title,
                section_level=metadata.section_level,
                content_type=metadata.content_type,
                position=metadata.position,
                token_count=metadata.token_count,
                breadcrumbs=metadata.breadcrumbs,
            )
        chunk_dtos.append(
            ArtifactChunkDTO(
                id=chunk.id,
                artifact_id=chunk.artifact_id,
                content=chunk.content,
                metadata=metadata_dto,
            )
        )

    return chunk_dtos


@router.delete("/artifacts/{artifact_id}", status_code=204)
async def delete_artifact(artifact_id: str):
    """Deleta um Artefato Cultural."""
    from app.domain.shared_kernel import ArtifactId
    
    try:
        artifact_id_uuid = ArtifactId(uuid.UUID(artifact_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    artifact = await artifacts_repo.find_by_id(artifact_id_uuid)
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artefato não encontrado")
    
    # Deleta do banco de dados
    await artifacts_repo.delete(artifact_id_uuid)
    
    # Deleta do storage se houver
    if artifact.source_url:
        # Extrai o path do storage da URL
        # Por enquanto, apenas deleta do banco
        pass
    
    return JSONResponse(status_code=204, content=None)


@router.patch("/artifacts/{artifact_id}/tags", response_model=ArtifactDTO)
async def update_artifact_tags(artifact_id: str, payload: UpdateArtifactTagsPayload):
    """Atualiza as tags de um artefato."""
    from app.domain.shared_kernel import ArtifactId
    
    try:
        artifact_id_uuid = ArtifactId(uuid.UUID(artifact_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    artifact = await artifacts_repo.find_by_id(artifact_id_uuid)
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artefato não encontrado")
    
    # Atualiza as tags
    await artifacts_repo.update_artifact_tags(artifact_id_uuid, payload.tags)
    
    # Busca dados atualizados
    artifact_data = await artifacts_repo.get_artifact_data(artifact_id_uuid)
    
    return ArtifactDTO(
        id=artifact.id,
        title=artifact.title,
        source_type=artifact.source_type.name,
        created_at=datetime.utcnow(),
        description=artifact_data.get('description') if artifact_data else None,
        tags=artifact_data.get('tags', []) if artifact_data else [],
        color=artifact_data.get('color') if artifact_data else None,
        source_url=artifact.source_url
    )


@router.patch("/artifacts/{artifact_id}", response_model=ArtifactDTO)
async def update_artifact(
    artifact_id: str,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON string
    color: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """Atualiza um artefato (aceita form-data para suportar upload de arquivo)."""
    from app.domain.shared_kernel import ArtifactId
    import json
    
    try:
        artifact_id_uuid = ArtifactId(uuid.UUID(artifact_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    artifact = await artifacts_repo.find_by_id(artifact_id_uuid)
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artefato não encontrado")
    
    # Atualiza os campos fornecidos
    if title is not None:
        await artifacts_repo.update_artifact_title(artifact_id_uuid, title)
    
    if description is not None:
        await artifacts_repo.update_artifact_description(artifact_id_uuid, description)
    
    if tags is not None:
        tags_list = json.loads(tags) if tags else []
        await artifacts_repo.update_artifact_tags(artifact_id_uuid, tags_list)
    
    if color is not None:
        await artifacts_repo.update_artifact_color(artifact_id_uuid, color)
    
    # Atualiza conteúdo se for TEXT
    if content is not None and artifact.source_type.name == "TEXT":
        await artifacts_repo.update_artifact_content(artifact_id_uuid, content, embedding_generator)
    
    # Substitui PDF se um novo arquivo foi enviado
    if file and artifact.source_type.name == "PDF":
        file_content = await file.read()
        
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos")
        
        # Processa novo PDF
        from app.domain.artifacts.workflows import create_artifact_from_pdf
        temp_artifact = create_artifact_from_pdf(
            title=artifact.title,  # Mantém título atual
            pdf_content=file_content,
            pdf_processor=pdf_processor,
            embedding_generator=embedding_generator
        )
        
        # Deleta chunks antigos
        await artifacts_repo.delete_chunks(artifact_id_uuid)
        
        # Salva novos chunks
        await artifacts_repo.save_chunks(artifact_id_uuid, temp_artifact.chunks)
        
        # Atualiza URL do PDF no storage
        storage_path = f"artifacts/{artifact_id_uuid}/{file.filename}"
        supabase_storage.storage.from_("artifacts").upload(storage_path, file_content, {"upsert": "true"})
        source_url = supabase_storage.storage.from_("artifacts").get_public_url(storage_path)
        await artifacts_repo.update_source_url(artifact_id_uuid, source_url)
    
    # Busca dados atualizados
    artifact_data = await artifacts_repo.get_artifact_data(artifact_id_uuid)
    updated_artifact = await artifacts_repo.find_by_id(artifact_id_uuid)
    
    return ArtifactDTO(
        id=updated_artifact.id,
        title=updated_artifact.title,
        source_type=updated_artifact.source_type.name,
        created_at=datetime.utcnow(),
        description=artifact_data.get('description') if artifact_data else None,
        tags=artifact_data.get('tags', []) if artifact_data else [],
        color=artifact_data.get('color') if artifact_data else None,
        source_url=updated_artifact.source_url
    )

