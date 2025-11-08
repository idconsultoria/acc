"""Repositório de Conversas usando Supabase."""
import json
from supabase import create_client, Client
from app.domain.conversations.types import Conversation, Message, Author, CitedSource
from app.domain.shared_kernel import ConversationId, MessageId, ArtifactId, TopicId, ChunkId
from app.infrastructure.persistence.config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime
import uuid


class ConversationsRepository:
    """Repositório para persistência de conversas no Supabase."""
    
    def __init__(self):
        """Inicializa o repositório com cliente Supabase."""
        try:
            if SUPABASE_URL and SUPABASE_KEY:
                self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            else:
                self.supabase = None
        except Exception:
            self.supabase = None
    
    async def create(self) -> Conversation:
        """Cria uma nova conversa."""
        conversation_id = ConversationId(uuid.uuid4())
        
        try:
            conversation_data = {
                "id": str(conversation_id),
                "created_at": "now()"
            }
            
            self.supabase.table("conversations").insert(conversation_data).execute()
        except Exception as e:
            # Se não conseguir salvar no Supabase, ainda retorna a conversa
            # para que o sistema possa funcionar
            pass
        
        return Conversation(
            id=conversation_id,
            messages=[],
            created_at=datetime.utcnow()
        )
    
    async def update_topic(
        self,
        conversation_id: ConversationId,
        topic_id: TopicId | None
    ) -> None:
        """Atualiza o tópico de uma conversa."""
        if not self.supabase:
            return
        
        try:
            update_data = {"topic_id": str(topic_id) if topic_id else None}
            self.supabase.table("conversations").update(update_data).eq("id", str(conversation_id)).execute()
        except Exception:
            pass
    
    async def update_summary_and_title(
        self,
        conversation_id: ConversationId,
        summary: str | None = None,
        title: str | None = None
    ) -> None:
        """Atualiza o resumo e título de uma conversa."""
        if not self.supabase:
            return
        
        try:
            update_data = {}
            if summary is not None:
                update_data["summary"] = summary
            if title is not None:
                update_data["title"] = title
            
            if update_data:
                self.supabase.table("conversations").update(update_data).eq("id", str(conversation_id)).execute()
        except Exception:
            pass
    
    async def find_by_topic(self, topic_id: TopicId | None) -> list[Conversation]:
        """Busca conversas por tópico (None para todas)."""
        # Otimizado: busca apenas IDs das conversas, não carrega todas as mensagens
        # Isso é usado apenas para contar conversas, então não precisamos das mensagens completas
        if not self.supabase:
            return []
        
        try:
            query = self.supabase.table("conversations").select("id, created_at")
            if topic_id is not None:
                query = query.eq("topic_id", str(topic_id))
            query = query.order("created_at", desc=True)
            
            result = query.execute()
            
            # Cria objetos Conversation mínimos (sem mensagens) apenas para contar
            conversations = []
            for row in result.data:
                conv_id = ConversationId(uuid.UUID(row["id"]))
                created_at = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
                conversation = Conversation(
                    id=conv_id,
                    messages=[],  # Não carrega mensagens para contagem
                    created_at=created_at
                )
                conversations.append(conversation)
            
            return conversations
        except Exception:
            return []
    
    async def find_by_id(self, conversation_id: ConversationId) -> Conversation | None:
        """Busca uma conversa por ID."""
        if not self.supabase:
            # Se não houver Supabase, retorna conversa vazia
            return Conversation(
                id=conversation_id,
                messages=[],
                created_at=datetime.utcnow()
            )
        
        try:
            # Busca a conversa
            result = self.supabase.table("conversations").select("*").eq("id", str(conversation_id)).execute()
            
            if not result.data:
                return None
        except Exception:
            # Se houver erro, retorna conversa vazia
            return Conversation(
                id=conversation_id,
                messages=[],
                created_at=datetime.utcnow()
            )
        
        conversation_row = result.data[0]
        
        # Busca as mensagens
        try:
            messages_result = self.supabase.table("messages").select("*").eq("conversation_id", str(conversation_id)).order("created_at").execute()
        except Exception:
            messages_result = type('obj', (object,), {'data': []})()
        
        # Converte as mensagens
        messages = []
        if not messages_result.data:
            messages_result.data = []
        
        # Otimização: coleta todos os chunk_ids de todas as mensagens primeiro
        all_chunk_ids = []
        chunk_id_to_message_index = {}  # Mapeia chunk_id -> lista de índices de mensagens
        
        for idx, msg_row in enumerate(messages_result.data):
            if msg_row.get("cited_artifact_chunk_ids"):
                for chunk_id in msg_row["cited_artifact_chunk_ids"]:
                    if chunk_id not in chunk_id_to_message_index:
                        chunk_id_to_message_index[chunk_id] = []
                        all_chunk_ids.append(chunk_id)
                    chunk_id_to_message_index[chunk_id].append(idx)
        
        # Busca todos os chunks de uma vez
        chunks_data = {}
        if all_chunk_ids:
            try:
                # Busca chunks com join em artifacts de uma vez
                # Supabase não suporta IN() direto, então fazemos queries em batch
                # ou uma query por chunk (ainda melhor que N queries por mensagem)
                for chunk_id in all_chunk_ids:
                    try:
                        chunk_result = (
                            self.supabase
                            .table("artifact_chunks")
                            .select(
                                "id, artifact_id, content, section_title, section_level, content_type, position, token_count, breadcrumbs, artifacts(title)"
                            )
                            .eq("id", chunk_id)
                            .limit(1)
                            .execute()
                        )
                        if chunk_result.data:
                            chunks_data[chunk_id] = chunk_result.data[0]
                    except Exception:
                        pass
            except Exception:
                pass
        
        # Agora processa as mensagens usando os chunks já carregados
        for idx, msg_row in enumerate(messages_result.data):
            # Converte cited_artifact_chunk_ids para CitedSource
            cited_sources = []
            
            # Busca informações dos chunks citados do cache
            if msg_row.get("cited_artifact_chunk_ids"):
                for chunk_id in msg_row["cited_artifact_chunk_ids"]:
                    chunk_data = chunks_data.get(chunk_id)
                    if chunk_data:
                        # Extrai título do artefato
                        artifact_title = ""
                        if chunk_data.get("artifacts"):
                            if isinstance(chunk_data["artifacts"], dict):
                                artifact_title = chunk_data["artifacts"].get("title", "")
                            elif isinstance(chunk_data["artifacts"], list) and chunk_data["artifacts"]:
                                artifact_title = chunk_data["artifacts"][0].get("title", "")
                        breadcrumbs = chunk_data.get("breadcrumbs") or []
                        if isinstance(breadcrumbs, str):
                            try:
                                breadcrumbs = json.loads(breadcrumbs)
                            except json.JSONDecodeError:
                                breadcrumbs = []
                        cited_source = CitedSource(
                            chunk_id=ChunkId(uuid.UUID(chunk_data["id"])),
                            artifact_id=ArtifactId(uuid.UUID(chunk_data["artifact_id"])),
                            title=artifact_title,
                            chunk_content_preview=chunk_data.get("content", "")[:200],
                            section_title=chunk_data.get("section_title"),
                            section_level=chunk_data.get("section_level"),
                            content_type=chunk_data.get("content_type"),
                            breadcrumbs=breadcrumbs,
                        )
                        cited_sources.append(cited_source)
            
            author = Author.USER if msg_row["author"] == "USER" else Author.AGENT
            
            message = Message(
                id=MessageId(uuid.UUID(msg_row["id"])),
                conversation_id=ConversationId(uuid.UUID(msg_row["conversation_id"])),
                author=author,
                content=msg_row["content"],
                cited_sources=cited_sources,
                created_at=datetime.fromisoformat(msg_row["created_at"].replace("Z", "+00:00"))
            )
            messages.append(message)
        
        created_at = datetime.fromisoformat(conversation_row["created_at"].replace("Z", "+00:00"))
        
        return Conversation(
            id=ConversationId(uuid.UUID(conversation_row["id"])),
            messages=messages,
            created_at=created_at
        )
    
    async def save_messages(self, conversation: Conversation) -> Conversation:
        """Salva as mensagens de uma conversa."""
        if not self.supabase:
            # Se não houver Supabase, apenas retorna a conversa
            return conversation
        
        try:
            # Salva apenas as novas mensagens (as que ainda não têm ID no banco)
            # Por simplicidade, vamos salvar todas as mensagens
            
            for msg in conversation.messages:
                # Verifica se a mensagem já existe
                try:
                    existing = self.supabase.table("messages").select("*").eq("id", str(msg.id)).execute()
                except Exception:
                    existing = type('obj', (object,), {'data': []})()
                
                if not existing.data:
                    # Prepara cited_artifact_chunk_ids
                    cited_chunk_ids = [str(cs.chunk_id) for cs in msg.cited_sources if cs.chunk_id]
                    
                    message_data = {
                        "id": str(msg.id),
                        "conversation_id": str(msg.conversation_id),
                        "author": msg.author.name,
                        "content": msg.content,
                        "cited_artifact_chunk_ids": cited_chunk_ids,
                        "created_at": msg.created_at.isoformat()
                    }
                    
                    try:
                        self.supabase.table("messages").insert(message_data).execute()
                    except Exception:
                        # Se não conseguir salvar, continua
                        pass
        except Exception:
            # Se houver erro, apenas retorna a conversa
            pass
        
        return conversation

