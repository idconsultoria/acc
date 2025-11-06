# Agente Cultural de IA

Sistema de conselheiro cultural baseado em IA que utiliza RAG (Retrieval-Augmented Generation) para fornecer orientações baseadas em artefatos culturais da organização.

---

## 🏗️ Arquitetura

```
┌─────────────────┐
│   VERCEL        │  Frontend (React + TypeScript + Vite)
│   (Frontend)    │  https://seu-projeto.vercel.app
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│  CLOUD RUN      │  Backend (FastAPI + Python)
│  (Backend)      │  https://agente-cultural-backend-538302265670.us-central1.run.app
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   SUPABASE      │  PostgreSQL + pgvector + Storage
│   (Database)    │
└─────────────────┘
```

---

## 📁 Estrutura do Projeto

```
acc/
├── frontend/              # Frontend React (Vercel)
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/               # Backend FastAPI (Cloud Run)
│   ├── app/
│   ├── Dockerfile
│   └── requirements.txt
│
├── design/                # Documentação de design e arquitetura
│   ├── 1_visao_geral_dominio.md
│   ├── 2_arquitetura_alto_nivel.md
│   ├── 3_contrato_api.yml
│   ├── 4_modelagem_tatica_backend.md
│   ├── 5_guia_implementacao_frontend.md
│   └── telas/            # Mockups das telas
│
├── .vercelignore          # Ignora backend no deploy Vercel
├── vercel.json            # Config Vercel (frontend)
└── README.md              # Este arquivo
```

---

## 🚀 Deploy

### Frontend (Vercel)

1. Configure a variável de ambiente no Vercel:
```
VITE_API_BASE_URL = https://agente-cultural-backend-538302265670.us-central1.run.app/api/v1
```

2. O deploy é automático via Git push, ou manualmente:
```bash
cd frontend
npm run build
vercel --prod
```

---

### Backend (Cloud Run)

1. Configure as variáveis de ambiente:
```bash
SUPABASE_URL=sua-url
SUPABASE_KEY=sua-chave
GEMINI_API_KEY=sua-chave
```

2. Faça o deploy:
```bash
cd backend
gcloud run deploy agente-cultural-backend \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated
```

---

## 🛠️ Desenvolvimento Local

### Pré-requisitos

- Node.js 18+ (para frontend)
- Python 3.12+ (para backend)
- Supabase account (banco de dados)
- Google Cloud account (para Gemini API)

### Setup

1. **Clone o repositório**
```bash
git clone <seu-repo>
cd acc
```

2. **Configure o Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Crie um arquivo .env
cp .env.example .env
# Edite .env com suas credenciais
```

3. **Configure o Frontend**
```bash
cd frontend
npm install

# Crie um arquivo .env.local
echo "VITE_API_BASE_URL=http://localhost:8000/api/v1" > .env.local
```

4. **Inicie o Banco de Dados**
   - Acesse [Supabase](https://supabase.com)
   - Crie um novo projeto
   - Execute o script `backend/schema.sql` no SQL Editor

### Executar Localmente

Terminal 1 (Backend):
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
# Backend rodando em http://localhost:8000
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
# Frontend rodando em http://localhost:3000
```

---

## 🔑 Funcionalidades Principais

### Para o Usuário Final
- 💬 **Chat Interativo** - Converse com o agente cultural
- 📚 **Fontes Citadas** - Veja quais artefatos embasaram cada resposta
- 👍👎 **Feedback** - Avalie as respostas (thumbs up/down)
- 📝 **Feedback Detalhado** - Forneça feedback textual
- 📊 **Histórico** - Acesse conversas anteriores
- 🏷️ **Tópicos** - Conversas organizadas automaticamente por tema

### Para o Guardião Cultural (Admin)
- 📄 **Gestão de Artefatos** - Upload de PDFs e texto
- ✏️ **Editor de Artefatos** - Edite conteúdo e metadata
- 🏷️ **Tags** - Organize artefatos com tags
- 🤖 **Configuração do Agente** - Edite a instrução geral
- 📋 **Revisão de Feedbacks** - Aprove ou rejeite feedbacks
- 🧠 **Aprendizados** - Feedbacks aprovados viram aprendizados

---

## 🛠️ Stack Tecnológico

### Frontend
- React 18
- TypeScript
- Vite
- TailwindCSS
- shadcn/ui
- TanStack Query (React Query)
- Axios
- React Router

### Backend
- FastAPI
- Python 3.12
- Pydantic
- Google Gemini (LLM + Embeddings)
- Supabase (PostgreSQL + pgvector)
- Docker

### Infraestrutura
- **Frontend:** Vercel (CDN global)
- **Backend:** Google Cloud Run (auto-scaling)
- **Database:** Supabase (PostgreSQL com pgvector)
- **Storage:** Supabase Storage (PDFs)

---

## 🎯 Configuração Rápida

### 1. Variável de Ambiente no Vercel

```
Vercel Dashboard → Settings → Environment Variables

Nome: VITE_API_BASE_URL
Valor: https://agente-cultural-backend-538302265670.us-central1.run.app/api/v1
Ambientes: ✅ Production ✅ Preview ✅ Development
```

### 2. CORS no Backend (Opcional)

Edite `backend/app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://seu-projeto.vercel.app",  # Sua URL do Vercel
        "http://localhost:3000",            # Desenvolvimento local
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Redeploy:
```bash
cd backend
gcloud run deploy agente-cultural-backend \
  --source . \
  --region us-central1
```

---

## 🐛 Troubleshooting

### Erro de CORS
```
Access to fetch has been blocked by CORS policy
```
**Solução:** Adicione a URL do Vercel no `allow_origins` do backend

### Frontend não encontra backend
```
Network Error: ERR_NAME_NOT_RESOLVED
```
**Solução:** Verifique se `VITE_API_BASE_URL` está configurada no Vercel

### Timeout
```
timeout of 30000ms exceeded
```
**Solução:** Pode ser cold start (normal na primeira requisição após 15 min de inatividade)

### Vercel instala Python
**Solução:** Verifique se `.vercelignore` foi commitado corretamente

---

## 📄 Licença

[Definir licença]

---

## 📞 Suporte

Para questões técnicas:
- Verifique os logs do Cloud Run: `gcloud run services logs tail agente-cultural-backend --region us-central1`
- Verifique os logs do Vercel: Dashboard → Deployments → [seu deploy] → Logs
- Console do navegador (F12) para erros de frontend

---

**Status:** ✅ MVP em produção  
**Backend:** https://agente-cultural-backend-538302265670.us-central1.run.app  
**Última atualização:** 6 de novembro de 2025
