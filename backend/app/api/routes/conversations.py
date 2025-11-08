"""Rotas para gerenciamento de Conversas."""
import asyncio
import contextlib
import json
import uuid
from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
from supabase import create_client

from app.api.dto import (
    CitedSourceDTO,
    ConversationTopicDTO,
    CreateMessagePayload,
    MessageDTO,
)
from app.domain.conversations.types import Conversation, Message as DomainMessage, Author
from app.domain.conversations.workflows import ProgressEmitter, continue_conversation
from app.domain.shared_kernel import ConversationId, MessageId, TopicId
from app.infrastructure.ai.embedding_service import EmbeddingGenerator
from app.infrastructure.ai.gemini_service import GeminiService, get_gemini_api_key
from app.infrastructure.ai.topic_classifier import TopicClassifier
from app.infrastructure.persistence.agent_settings_repo import AgentSettingsRepository
from app.infrastructure.persistence.config import GEMINI_API_KEY, SUPABASE_KEY, SUPABASE_URL
from app.infrastructure.persistence.conversations_repo import ConversationsRepository
from app.infrastructure.persistence.knowledge_repo import KnowledgeRepository
from app.infrastructure.persistence.topics_repo import TopicsRepository

router = APIRouter()

# Inicializa repositórios
conversations_repo = ConversationsRepository()
knowledge_repo = KnowledgeRepository()
agent_settings_repo = AgentSettingsRepository()
topics_repo = TopicsRepository()

# Validação de GEMINI_API_KEY será feita dentro das rotas quando necessário
# Não falha durante a importação para permitir que o servidor inicie


def _message_to_dto(message: DomainMessage) -> MessageDTO:
    """Converte uma mensagem de domínio para DTO."""
    return MessageDTO(
        id=message.id,
        conversation_id=message.conversation_id,
        author=message.author.name,
        content=message.content,
        cited_sources=[
            CitedSourceDTO(
                chunk_id=cited_source.chunk_id,
                artifact_id=cited_source.artifact_id,
                title=cited_source.title,
                chunk_content_preview=cited_source.chunk_content_preview,
                section_title=cited_source.section_title,
                section_level=cited_source.section_level,
                content_type=cited_source.content_type,
                breadcrumbs=cited_source.breadcrumbs,
            )
            for cited_source in message.cited_sources
        ],
        created_at=message.created_at,
    )


class SSEProgressEmitter(ProgressEmitter):
    """Implementação de ProgressEmitter para envio via SSE."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[dict[str, str] | None] = asyncio.Queue()
        self._closed = False

    async def phase_start(self, phases: list[dict[str, str]]) -> None:
        await self._enqueue("phase:start", {"phases": phases})

    async def phase_update(self, phase: str, data: dict[str, object] | None = None) -> None:
        payload = {"phase": phase}
        if data:
            payload.update(data)
        await self._enqueue("phase:update", payload)

    async def phase_complete(self, phase: str, data: dict[str, object] | None = None) -> None:
        payload = {"phase": phase}
        if data:
            payload.update(data)
        await self._enqueue("phase:complete", payload)

    async def emit_token(self, token: str) -> None:
        if token:
            await self._enqueue("token", {"value": token})

    async def message_complete(self, message: MessageDTO) -> None:
        await self._enqueue("message:complete", message.model_dump(mode="json"))

    async def error(self, detail: str) -> None:
        await self._enqueue("error", {"detail": detail})

    async def finish(self) -> None:
        if not self._closed:
            self._closed = True
            await self._queue.put(None)

    async def listen(self) -> AsyncGenerator[dict[str, str], None]:
        while True:
            event = await self._queue.get()
            if event is None:
                break
            yield event

    async def _enqueue(self, event_type: str, payload: dict[str, object]) -> None:
        await self._queue.put(
            {
                "event": event_type,
                "data": json.dumps(payload, ensure_ascii=False),
            }
        )


async def _classify_conversation_if_needed(
    previous_conversation: Conversation,
    updated_conversation: Conversation,
    conversation_id_uuid: ConversationId,
    api_key: str,
) -> None:
    """Executa classificação de tópico quando necessário."""
    old_agent_messages = [msg for msg in previous_conversation.messages if msg.author == Author.AGENT]
    if old_agent_messages:
        return

    print(f"[TOPIC] Primeira resposta do agente detectada para conversa {conversation_id_uuid}")

    user_messages = [msg for msg in updated_conversation.messages if msg.author == Author.USER]
    agent_messages = [msg for msg in updated_conversation.messages if msg.author == Author.AGENT]

    print(f"[TOPIC] Mensagens encontradas: {len(user_messages)} do usuário, {len(agent_messages)} do agente")

    if not user_messages or not agent_messages:
        return

    existing_topics = await topics_repo.find_all()
    existing_topic_names = [topic.name for topic in existing_topics]
    print(f"[TOPIC] Tópicos existentes: {existing_topic_names}")

    user_query = user_messages[0].content
    agent_response = agent_messages[0].content
    print(f"[TOPIC] Classificando conversa. Query: {user_query[:100]}...")

    topic_classifier = TopicClassifier(api_key)

    try:
        topic_name = await topic_classifier.classify_conversation(
            user_query=user_query,
            agent_response=agent_response,
            existing_topics=existing_topic_names,
        )
        print(f"[TOPIC] Tópico classificado: '{topic_name}'")

        topic = await topics_repo.find_by_name(topic_name)
        if not topic:
            print(f"[TOPIC] Criando novo tópico: '{topic_name}'")
            topic = await topics_repo.create(topic_name)
            print(f"[TOPIC] Tópico criado com ID: {topic.id}")
        else:
            print(f"[TOPIC] Tópico já existe: {topic.name} (ID: {topic.id})")

        print(f"[TOPIC] Atualizando conversa {conversation_id_uuid} com tópico {topic.id}")
        await conversations_repo.update_topic(conversation_id_uuid, topic.id)
        print(f"[TOPIC] Conversa atualizada com sucesso")

        title = user_query.split("\n")[0][:100]
        summary = agent_response[:300] + ("..." if len(agent_response) > 300 else "")
        await conversations_repo.update_summary_and_title(
            conversation_id_uuid,
            summary=summary,
            title=title,
        )
        print(f"[TOPIC] Título e resumo atualizados")
    except Exception as exc:
        print(f"[TOPIC] Erro ao classificar conversa por tópico: {exc}")
        import traceback

        traceback.print_exc()


@router.post("/conversations")
async def create_conversation():
    """Inicia uma nova conversa."""
    conversation = await conversations_repo.create()
    
    return {"conversation_id": str(conversation.id)}


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageDTO])
async def get_conversation_messages(conversation_id: str):
    """Lista as mensagens de uma conversa."""
    try:
        conversation_id_uuid = ConversationId(uuid.UUID(conversation_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    conversation = await conversations_repo.find_by_id(conversation_id_uuid)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    
    return [_message_to_dto(msg) for msg in conversation.messages]


@router.post("/conversations/{conversation_id}/messages", response_model=MessageDTO)
async def post_message(conversation_id: str, payload: CreateMessagePayload):
    """Envia uma nova mensagem para o agente."""
    try:
        conversation_id_uuid = ConversationId(uuid.UUID(conversation_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    # Busca a conversa
    conversation = await conversations_repo.find_by_id(conversation_id_uuid)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    
    # Obtém a instrução do agente
    agent_instruction = await agent_settings_repo.get_instruction()
    
    # Obtém a chave de API (personalizada ou padrão)
    api_key = await get_gemini_api_key()
    gemini_service = GeminiService(api_key)
    embedding_generator = EmbeddingGenerator(api_key)
    
    # Continua a conversa (gera resposta do agente)
    previous_conversation = conversation
    updated_conversation = await continue_conversation(
        conversation=conversation,
        user_query=payload.content,
        embedding_generator=embedding_generator,
        knowledge_repo=knowledge_repo,
        llm_service=gemini_service,
        agent_instruction=agent_instruction
    )
    
    # Salva as mensagens
    await conversations_repo.save_messages(updated_conversation)
    

    await _classify_conversation_if_needed(
        previous_conversation=previous_conversation,
        updated_conversation=updated_conversation,
        conversation_id_uuid=conversation_id_uuid,
        api_key=api_key,
    )
    
    # Retorna a última mensagem (do agente)
    agent_message = updated_conversation.messages[-1]
    
    return _message_to_dto(agent_message)


@router.post("/conversations/{conversation_id}/messages/stream")
async def post_message_stream(conversation_id: str, payload: CreateMessagePayload):
    """Envia uma nova mensagem para o agente usando streaming SSE."""
    try:
        conversation_id_uuid = ConversationId(uuid.UUID(conversation_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")

    conversation = await conversations_repo.find_by_id(conversation_id_uuid)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    agent_instruction = await agent_settings_repo.get_instruction()
    api_key = await get_gemini_api_key()
    gemini_service = GeminiService(api_key)
    embedding_generator = EmbeddingGenerator(api_key)

    progress_emitter = SSEProgressEmitter()

    async def workflow() -> None:
        try:
            updated_conversation = await continue_conversation(
                conversation=conversation,
                user_query=payload.content,
                embedding_generator=embedding_generator,
                knowledge_repo=knowledge_repo,
                llm_service=gemini_service,
                agent_instruction=agent_instruction,
                progress_emitter=progress_emitter,
            )

            await conversations_repo.save_messages(updated_conversation)
            await _classify_conversation_if_needed(
                previous_conversation=conversation,
                updated_conversation=updated_conversation,
                conversation_id_uuid=conversation_id_uuid,
                api_key=api_key,
            )

            agent_message = updated_conversation.messages[-1]
            await progress_emitter.message_complete(_message_to_dto(agent_message))
        except Exception as exc:
            await progress_emitter.error(str(exc))
        finally:
            await progress_emitter.finish()

    workflow_task = asyncio.create_task(workflow())

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        try:
            async for event in progress_emitter.listen():
                yield event
        except asyncio.CancelledError:
            workflow_task.cancel()
            raise
        finally:
            with contextlib.suppress(asyncio.CancelledError):
                await workflow_task

    return EventSourceResponse(event_generator())


@router.get("/conversations/{conversation_id}/topic", response_model=ConversationTopicDTO)
async def get_conversation_topic(conversation_id: str):
    """Busca o tópico de uma conversa."""
    try:
        conversation_id_uuid = ConversationId(uuid.UUID(conversation_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    # Busca a conversa para verificar se tem mensagens do agente
    conversation = await conversations_repo.find_by_id(conversation_id_uuid)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    
    # Verifica se tem mensagens do agente (primeira resposta já foi dada)
    agent_messages = [msg for msg in conversation.messages if msg.author.value == 2]
    has_agent_response = len(agent_messages) > 0
    
    if not has_agent_response:
        # Se ainda não tem resposta do agente, não tem tópico ainda
        return ConversationTopicDTO(topic=None, is_processing=False)
    
    # Busca o tópico no banco
    topic = None
    is_processing = False
    
    try:
        if SUPABASE_URL and SUPABASE_KEY:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            conv_row = supabase.table("conversations").select("topic_id").eq("id", str(conversation_id_uuid)).execute()
            
            if conv_row.data and conv_row.data[0]:
                topic_id_from_db = conv_row.data[0].get("topic_id")
                
                if topic_id_from_db:
                    # Tópico já foi definido
                    topic_id_uuid = TopicId(uuid.UUID(topic_id_from_db))
                    topic_obj = await topics_repo.find_by_id(topic_id_uuid)
                    if topic_obj:
                        topic = topic_obj.name
                else:
                    # Tópico ainda não foi definido (processando)
                    is_processing = True
    except Exception:
        # Em caso de erro, assume que está processando
        is_processing = True
    
    return ConversationTopicDTO(topic=topic, is_processing=is_processing)

