"""Repositório de Tópicos usando Supabase."""
from supabase import create_client, Client
from app.domain.topics.types import Topic
from app.domain.shared_kernel import TopicId
from app.infrastructure.persistence.config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime
import uuid


class TopicsRepository:
    """Repositório para persistência de tópicos no Supabase."""
    
    def __init__(self):
        """Inicializa o repositório com cliente Supabase."""
        try:
            if SUPABASE_URL and SUPABASE_KEY:
                self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            else:
                self.supabase = None
        except Exception:
            self.supabase = None
    
    async def find_all(self) -> list[Topic]:
        """Busca todos os tópicos."""
        if not self.supabase:
            return []
        
        try:
            response = self.supabase.table("topics").select("*").order("name").execute()
            topics = []
            for row in response.data:
                topics.append(Topic(
                    id=TopicId(uuid.UUID(row["id"])),
                    name=row["name"],
                    created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
                ))
            return topics
        except Exception:
            return []
    
    async def find_by_name(self, name: str) -> Topic | None:
        """Busca um tópico pelo nome."""
        if not self.supabase:
            return None
        
        try:
            response = self.supabase.table("topics").select("*").eq("name", name).limit(1).execute()
            if response.data:
                row = response.data[0]
                return Topic(
                    id=TopicId(uuid.UUID(row["id"])),
                    name=row["name"],
                    created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
                )
            return None
        except Exception:
            return None
    
    async def create(self, name: str) -> Topic:
        """Cria um novo tópico."""
        topic_id = TopicId(uuid.uuid4())
        
        try:
            if self.supabase:
                topic_data = {
                    "id": str(topic_id),
                    "name": name,
                    "created_at": "now()"
                }
                result = self.supabase.table("topics").insert(topic_data).execute()
                print(f"Tópico criado com sucesso: {name} (ID: {topic_id})")
                if result.data:
                    print(f"Dados retornados: {result.data}")
        except Exception as e:
            # Se já existir, busca o existente
            print(f"Erro ao criar tópico '{name}': {e}")
            import traceback
            traceback.print_exc()
            existing = await self.find_by_name(name)
            if existing:
                print(f"Tópico já existe, retornando existente: {existing.name}")
                return existing
        
        return Topic(
            id=topic_id,
            name=name,
            created_at=datetime.utcnow()
        )
    
    async def find_by_id(self, topic_id: TopicId) -> Topic | None:
        """Busca um tópico pelo ID."""
        if not self.supabase:
            return None
        
        try:
            response = self.supabase.table("topics").select("*").eq("id", str(topic_id)).limit(1).execute()
            if response.data:
                row = response.data[0]
                return Topic(
                    id=TopicId(uuid.UUID(row["id"])),
                    name=row["name"],
                    created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
                )
            return None
        except Exception:
            return None

