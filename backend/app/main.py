from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import artifacts, conversations, feedbacks, learnings, agent, topics, settings

app = FastAPI(
    title="API do Agente Cultural",
    description="API para gerenciar Artefatos Culturais e interagir com o Agente de IA",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(artifacts.router, prefix="/api/v1", tags=["Artefatos"])
app.include_router(conversations.router, prefix="/api/v1", tags=["Conversas"])
app.include_router(feedbacks.router, prefix="/api/v1", tags=["Feedbacks"])
app.include_router(learnings.router, prefix="/api/v1", tags=["Aprendizados"])
app.include_router(agent.router, prefix="/api/v1", tags=["Agente"])
app.include_router(topics.router, prefix="/api/v1", tags=["Tópicos"])
app.include_router(settings.router, prefix="/api/v1", tags=["Configurações"])


@app.get("/")
async def root():
    return {"message": "API do Agente Cultural"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

