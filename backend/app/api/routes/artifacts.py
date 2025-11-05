"""Rotas para gerenciamento de Artefatos."""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from app.api.dto import ArtifactDTO, ErrorDTO, UpdateArtifactTagsPayload
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

# Valida configurações antes de inicializar
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY deve estar configurado no arquivo .env")
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY devem estar configurados")

# Inicializa serviços
pdf_processor = PDFProcessor()
embedding_generator = EmbeddingGenerator(GEMINI_API_KEY)
artifacts_repo = ArtifactsRepository()
supabase_storage = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


@router.get("/artifacts", response_model=list[ArtifactDTO])
async def list_artifacts():
    """Lista todos os Artefatos Culturais."""
    artifacts = await artifacts_repo.find_all()
    
    result = []
    for artifact in artifacts:
        # Busca description e tags do banco
        artifact_data = await artifacts_repo.get_artifact_data(artifact.id)
        
        result.append(ArtifactDTO(
            id=artifact.id,
            title=artifact.title,
            source_type=artifact.source_type.name,
            created_at=datetime.utcnow(),  # TODO: Buscar data real do banco
            description=artifact_data.get('description') if artifact_data else None,
            tags=artifact_data.get('tags', []) if artifact_data else []
        ))
    
    return result


@router.post("/artifacts", response_model=ArtifactDTO, status_code=201)
async def create_artifact(
    title: str = Form(...),
    text_content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """Cria um novo Artefato Cultural."""
    if not title:
        raise HTTPException(status_code=400, detail="Título é obrigatório")
    
    if not text_content and not file:
        raise HTTPException(status_code=400, detail="É necessário fornecer texto ou arquivo PDF")
    
    source_url = None
    
    if file:
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
        # Cria artefato a partir de texto
        artifact = create_artifact_from_text(
            title=title,
            text_content=text_content,
            embedding_generator=embedding_generator
        )
    
    # Salva no banco de dados
    await artifacts_repo.save(artifact, source_url)
    
    return ArtifactDTO(
        id=artifact.id,
        title=artifact.title,
        source_type=artifact.source_type.name,
        created_at=uuid.uuid4()  # Placeholder
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
    
    return ArtifactDTO(
        id=artifact.id,
        title=artifact.title,
        source_type=artifact.source_type.name,
        created_at=uuid.uuid4()  # Placeholder
    )


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
        tags=artifact_data.get('tags', []) if artifact_data else []
    )

