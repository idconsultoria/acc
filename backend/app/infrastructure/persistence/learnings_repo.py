"""Repositório de Aprendizados usando Supabase."""
from supabase import create_client, Client
from app.domain.learnings.types import Learning
from app.domain.shared_kernel import LearningId, FeedbackId
from app.infrastructure.persistence.config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime
import uuid


class LearningsRepository:
    """Repositório para persistência de aprendizados no Supabase."""
    
    def __init__(self):
        """Inicializa o repositório com cliente Supabase."""
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    async def save(self, learning: Learning) -> Learning:
        """Salva um aprendizado."""
        learning_data = {
            "id": str(learning.id),
            "content": learning.content,
            "embedding": learning.embedding.vector,
            "source_feedback_id": str(learning.source_feedback_id),
            "created_at": learning.created_at.isoformat()
        }
        
        self.supabase.table("learnings").insert(learning_data).execute()
        
        return learning
    
    async def find_all(self) -> list[Learning]:
        """Busca todos os aprendizados."""
        result = self.supabase.table("learnings").select("*").order("created_at", desc=True).execute()
        
        learnings = []
        for row in result.data:
            from app.domain.shared_kernel import Embedding
            
            learning = Learning(
                id=LearningId(uuid.UUID(row["id"])),
                content=row["content"],
                embedding=Embedding(vector=row["embedding"]),
                source_feedback_id=FeedbackId(uuid.UUID(row["source_feedback_id"])),
                created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
            )
            learnings.append(learning)
        
        return learnings

