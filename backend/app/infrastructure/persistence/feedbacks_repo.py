"""Repositório de Feedbacks usando Supabase."""
from supabase import create_client, Client
from app.domain.feedbacks.types import PendingFeedback, FeedbackStatus
from app.domain.shared_kernel import FeedbackId, MessageId
from app.infrastructure.persistence.config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime
import uuid


class FeedbacksRepository:
    """Repositório para persistência de feedbacks no Supabase."""
    
    def __init__(self):
        """Inicializa o repositório com cliente Supabase."""
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    async def save(self, feedback: PendingFeedback) -> PendingFeedback:
        """Salva um feedback."""
        feedback_data = {
            "id": str(feedback.id),
            "message_id": str(feedback.message_id),
            "feedback_text": feedback.feedback_text,
            "status": feedback.status.name,
            "created_at": feedback.created_at.isoformat(),
            "feedback_type": feedback.feedback_type
        }
        
        self.supabase.table("pending_feedbacks").insert(feedback_data).execute()
        
        return feedback
    
    async def find_by_id(self, feedback_id: FeedbackId) -> PendingFeedback | None:
        """Busca um feedback por ID."""
        result = self.supabase.table("pending_feedbacks").select("*").eq("id", str(feedback_id)).execute()
        
        if not result.data:
            return None
        
        row = result.data[0]
        
        return PendingFeedback(
            id=FeedbackId(uuid.UUID(row["id"])),
            message_id=MessageId(uuid.UUID(row["message_id"])),
            feedback_text=row["feedback_text"],
            status=FeedbackStatus[row["status"]],
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
            feedback_type=row.get("feedback_type")
        )
    
    async def find_pending(self) -> list[PendingFeedback]:
        """Busca todos os feedbacks pendentes."""
        result = self.supabase.table("pending_feedbacks").select("*, messages(content)").eq("status", "PENDING").order("created_at", desc=True).execute()
        
        feedbacks = []
        for row in result.data:
            feedback = PendingFeedback(
                id=FeedbackId(uuid.UUID(row["id"])),
                message_id=MessageId(uuid.UUID(row["message_id"])),
                feedback_text=row["feedback_text"],
                status=FeedbackStatus[row["status"]],
                created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
                feedback_type=row.get("feedback_type")
            )
            feedbacks.append(feedback)
        
        return feedbacks
    
    async def find_reviewed(self) -> list[PendingFeedback]:
        """Busca todos os feedbacks revisados (aprovados ou rejeitados)."""
        result = self.supabase.table("pending_feedbacks").select("*").in_("status", ["APPROVED", "REJECTED"]).order("created_at", desc=True).execute()
        
        feedbacks = []
        for row in result.data:
            feedback = PendingFeedback(
                id=FeedbackId(uuid.UUID(row["id"])),
                message_id=MessageId(uuid.UUID(row["message_id"])),
                feedback_text=row["feedback_text"],
                status=FeedbackStatus[row["status"]],
                created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
                feedback_type=row.get("feedback_type")
            )
            feedbacks.append(feedback)
        
        return feedbacks
    
    async def get_conversation_id_by_message_id(self, message_id: MessageId) -> str | None:
        """Busca o conversation_id a partir de um message_id."""
        try:
            result = self.supabase.table("messages").select("conversation_id").eq("id", str(message_id)).execute()
            if result.data and result.data[0]:
                return result.data[0].get("conversation_id")
        except Exception:
            pass
        return None
    
    async def find_by_message_id(self, message_id: MessageId) -> PendingFeedback | None:
        """Busca um feedback por message_id."""
        result = self.supabase.table("pending_feedbacks").select("*").eq("message_id", str(message_id)).order("created_at", desc=True).limit(1).execute()
        
        if not result.data:
            return None
        
        row = result.data[0]
        
        return PendingFeedback(
            id=FeedbackId(uuid.UUID(row["id"])),
            message_id=MessageId(uuid.UUID(row["message_id"])),
            feedback_text=row["feedback_text"],
            status=FeedbackStatus[row["status"]],
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
            feedback_type=row.get("feedback_type")
        )
    
    async def update(self, feedback_id: FeedbackId, feedback_text: str, feedback_type: str | None = None) -> PendingFeedback:
        """Atualiza o texto e tipo de um feedback."""
        update_data = {"feedback_text": feedback_text}
        if feedback_type is not None:
            update_data["feedback_type"] = feedback_type
        
        self.supabase.table("pending_feedbacks").update(update_data).eq("id", str(feedback_id)).execute()
        
        return await self.find_by_id(feedback_id)
    
    async def delete(self, feedback_id: FeedbackId) -> None:
        """Deleta um feedback."""
        self.supabase.table("pending_feedbacks").delete().eq("id", str(feedback_id)).execute()
    
    async def update_status(self, feedback_id: FeedbackId, status: FeedbackStatus) -> PendingFeedback:
        """Atualiza o status de um feedback."""
        self.supabase.table("pending_feedbacks").update({"status": status.name}).eq("id", str(feedback_id)).execute()
        
        return await self.find_by_id(feedback_id)
    
    async def find_by_message_ids(self, message_ids: list[MessageId]) -> dict[str, PendingFeedback]:
        """
        Busca feedbacks por múltiplos message_ids de uma vez.
        Retorna um dicionário mapeando message_id (string) para PendingFeedback.
        """
        if not message_ids:
            return {}
        
        try:
            # Converte MessageIds para strings
            message_id_strings = [str(msg_id) for msg_id in message_ids]
            
            # Busca todos os feedbacks de uma vez usando in_
            # Nota: Supabase pode ter limites no número de itens no in_, então pode precisar fazer em batches
            result = self.supabase.table("pending_feedbacks").select("*").in_("message_id", message_id_strings).execute()
            
            # Cria dicionário de feedbacks por message_id
            feedbacks_dict = {}
            
            # Agrupa por message_id e pega apenas o mais recente de cada um
            for row in result.data:
                message_id_str = row["message_id"]
                
                # Se já existe um feedback para este message_id, verifica qual é mais recente
                if message_id_str not in feedbacks_dict:
                    feedbacks_dict[message_id_str] = PendingFeedback(
                        id=FeedbackId(uuid.UUID(row["id"])),
                        message_id=MessageId(uuid.UUID(row["message_id"])),
                        feedback_text=row["feedback_text"],
                        status=FeedbackStatus[row["status"]],
                        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
                        feedback_type=row.get("feedback_type")
                    )
                else:
                    # Compara datas e mantém o mais recente
                    existing_date = feedbacks_dict[message_id_str].created_at
                    current_date = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
                    if current_date > existing_date:
                        feedbacks_dict[message_id_str] = PendingFeedback(
                            id=FeedbackId(uuid.UUID(row["id"])),
                            message_id=MessageId(uuid.UUID(row["message_id"])),
                            feedback_text=row["feedback_text"],
                            status=FeedbackStatus[row["status"]],
                            created_at=current_date,
                            feedback_type=row.get("feedback_type")
                        )
            
            return feedbacks_dict
        except Exception:
            return {}

