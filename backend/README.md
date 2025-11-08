# Backend - Agente Cultural

Backend FastAPI para o Agente Cultural de IA.

## 🚀 Início Rápido

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Configure as variáveis de ambiente no arquivo `.env`:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=postgresql://user:password@host:port/database
```

3. Execute o schema SQL (`schema.sql`) ou as migrações numeradas em `database/migrations/` no Supabase.  
   - As funções RPC `rag_get_relevant_chunks` e `rag_get_relevant_learnings` são necessárias para o RAG via REST.  
   - Marque essas funções como *exposed* no painel do Supabase para permitir chamadas via `rpc`.

4. Execute o servidor:
```bash
uvicorn app.main:app --reload --port 8000
```

### ℹ️ Sobre credenciais do Supabase

- `SUPABASE_KEY` deve ser a chave pública (anon key) usada pelo frontend.
- `SUPABASE_SERVICE_ROLE_KEY` precisa ser mantida apenas no backend; ela é usada agora para a busca vetorial (RAG) via `supabase-py`.  
- Se estiver rodando localmente, crie um arquivo `.env` com esses valores; em produção, configure variáveis de ambiente seguras.

## 📁 Estrutura

- `app/api/` - Rotas da API (FastAPI routers)
- `app/domain/` - Lógica de negócio pura (tipos e workflows)
- `app/infrastructure/` - Implementações (Supabase, Gemini, PDF)

## 🔍 Endpoints Principais

- `GET /api/v1/artifacts` - Lista artefatos
- `POST /api/v1/artifacts` - Cria artefato (PDF ou texto)
- `POST /api/v1/conversations` - Cria conversa
- `POST /api/v1/conversations/{id}/messages` - Envia mensagem
- `GET /api/v1/feedbacks/pending` - Lista feedbacks pendentes
- `POST /api/v1/feedbacks/{id}/approve` - Aprova feedback

Veja a documentação completa em `/docs` quando o servidor estiver rodando.

