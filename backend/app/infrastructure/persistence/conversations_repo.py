"""Repositório de Conversas usando Supabase."""
from supabase import create_client, Client
from app.domain.conversations.types import Conversation, Message, Author, CitedSource
from app.domain.shared_kernel import ConversationId, MessageId, ArtifactId, TopicId
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
        if not self.supabase:
            return []
        
        try:
            query = self.supabase.table("conversations").select("*")
            if topic_id is not None:
                query = query.eq("topic_id", str(topic_id))
            # Se topic_id é None, busca todas as conversas (não filtra)
            query = query.order("created_at", desc=True)
            
            result = query.execute()
            
            conversations = []
            for row in result.data:
                # Busca mensagens para cada conversa
                conv_id = ConversationId(uuid.UUID(row["id"]))
                conversation = await self.find_by_id(conv_id)
                if conversation:
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
        
        for msg_row in messages_result.data:
            # Converte cited_artifact_chunk_ids para CitedSource
            cited_sources = []
            
            # Busca informações dos chunks citados
            if msg_row.get("cited_artifact_chunk_ids"):
                for chunk_id in msg_row["cited_artifact_chunk_ids"]:
                    # Busca o chunk e o artefato
                    try:
                        chunk_result = self.supabase.table("artifact_chunks").select("*, artifacts!inner(title)").eq("id", chunk_id).execute()
                        
                        if chunk_result.data:
                            chunk_data = chunk_result.data[0]
                            # O Supabase retorna o join de forma diferente
                            if isinstance(chunk_data.get("artifacts"), dict):
                                artifact_title = chunk_data["artifacts"].get("title", "")
                            elif isinstance(chunk_data.get("artifacts"), list) and chunk_data["artifacts"]:
                                artifact_title = chunk_data["artifacts"][0].get("title", "")
                            else:
                                artifact_title = ""
                            
                            cited_source = CitedSource(
                                artifact_id=ArtifactId(uuid.UUID(chunk_data["artifact_id"])),
                                title=artifact_title,
                                chunk_content_preview=chunk_data.get("content", "")[:200]
                            )
                            cited_sources.append(cited_source)
                    except Exception as e:
                        # Se não conseguir buscar o chunk, continua sem a citação
                        pass
            
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
                    cited_chunk_ids = [str(cs.artifact_id) for cs in msg.cited_sources]
                    
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

