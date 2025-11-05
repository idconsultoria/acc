# Agente Cultural - MVP

Sistema de Agente Cultural de IA para preservar e transmitir a cultura organizacional através de conversas interativas com RAG (Retrieval-Augmented Generation).

## 📊 Estado Atual do Projeto

### ✅ O que foi implementado

#### Backend (Python + FastAPI)
- ✅ **Domínio completo** com todos os módulos:
  - `shared_kernel`: Tipos base (IDs, Embedding)
  - `artifacts`: CRUD de artefatos culturais (PDF e texto)
  - `conversations`: Sistema de conversas e mensagens
  - `feedbacks`: Sistema de feedbacks pendentes
  - `learnings`: Aprendizados sintetizados
  - `agent`: Configuração da instrução geral do agente

- ✅ **Infraestrutura completa**:
  - Repositórios Supabase (Artifacts, Conversations, Feedbacks, Learnings, AgentSettings, Knowledge)
  - Serviço Gemini (geração de conselhos RAG e síntese de aprendizados)
  - Serviço de Embeddings (Gemini)
  - Processador de PDF (PyMuPDF)

- ✅ **API REST completa** conforme OpenAPI:
  - `/api/v1/artifacts` - CRUD de artefatos
  - `/api/v1/conversations` - Conversas e mensagens
  - `/api/v1/feedbacks` - Feedbacks pendentes e moderação
  - `/api/v1/learnings` - Listagem de aprendizados
  - `/api/v1/agent/instruction` - Configuração do agente

- ✅ **Schema SQL completo** (`backend/schema.sql`) com:
  - Todas as tabelas necessárias
  - Extensão pgvector habilitada
  - Índices vetoriais para busca RAG
  - Funções SQL para busca de similaridade

#### Frontend (React + TypeScript + Vite)
- ✅ **Tela de Chat** (`/chat`):
  - Interface conversacional completa
  - Renderização de Markdown com ReactMarkdown
  - Exibição de fontes citadas
  - Indicador de "digitando"
  - Scroll automático

- ✅ **Tela de Admin** (`/admin`):
  - CRUD de artefatos (texto e PDF)
  - Editor da instrução geral do agente
  - Painel de revisão de feedbacks pendentes
  - Aprovação/Rejeição de feedbacks

- ✅ **Integração completa**:
  - Cliente API configurado com Axios
  - React Query para estado do servidor
  - Zustand para estado global
  - React Router para navegação
  - Tailwind CSS para estilos

#### Ambiente
- ✅ Ambiente virtual Python (`.venv`) configurado na raiz
- ✅ Dependências instaladas (backend e frontend)
- ✅ Servidores testados e funcionando

### ⚠️ Limitações Identificadas

- Alguns endpoints podem retornar erro 500 se Supabase/Gemini não estiverem configurados
- O sistema funciona em modo degradado sem Supabase configurado
- O modelo de embedding `text-embedding-004` pode precisar de ajuste dependendo da disponibilidade no Gemini

## 🏗️ Arquitetura

- **Backend**: Python + FastAPI
- **Frontend**: React + TypeScript + Vite
- **Banco de Dados**: Supabase (PostgreSQL com pgvector)
- **Armazenamento**: Supabase Storage
- **IA**: Google Gemini 2.5 Flash

## 🚀 Como Iniciar

### Pré-requisitos
- Python 3.10+
- Node.js 18+
- Conta no Supabase
- Chave da API do Google Gemini

### 1. Configurar Backend

```bash
# Ativar o venv (já configurado na raiz)
.\.venv\Scripts\Activate.ps1

# Instalar dependências (se necessário)
cd backend
pip install -r requirements.txt
```

Crie o arquivo `backend/.env` com:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=postgresql://user:password@host:port/database
```

### 2. Configurar Supabase

1. Crie um projeto no [Supabase](https://supabase.com)
2. Execute o script SQL em `backend/schema.sql` no SQL Editor
3. Crie um bucket chamado `artifacts` no Storage
4. Configure as políticas de acesso do bucket

### 3. Configurar Frontend

```bash
cd frontend
npm install
```

### 4. Executar

**Backend (Terminal 1):**
```bash
.\.venv\Scripts\Activate.ps1
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

**Frontend (Terminal 2):**
```bash
cd frontend
npm run dev
```

**Acessar:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📋 Próximos Passos

### Prioridade Alta

1. **Configurar Supabase e Gemini**
   - [ ] Criar projeto no Supabase
   - [ ] Executar schema SQL
   - [ ] Configurar bucket de storage
   - [ ] Obter chave da API do Gemini
   - [ ] Criar arquivo `.env` no backend com todas as credenciais

2. **Testar Fluxo Completo**
   - [ ] Adicionar artefato no admin (texto e PDF)
   - [ ] Testar chat com pergunta sobre artefato
   - [ ] Verificar se RAG retorna citações corretas
   - [ ] Enviar feedback sobre resposta do agente
   - [ ] Aprovar feedback e verificar criação de aprendizado
   - [ ] Verificar se aprendizado é usado em próximas conversas

3. **Validação e Ajustes**
   - [ ] Validar modelo de embedding (ajustar se necessário)
   - [ ] Verificar dimensões dos embeddings no schema
   - [ ] Testar com múltiplos artefatos
   - [ ] Testar performance com PDFs grandes

### Prioridade Média

4. **Melhorias de UX**
   - [ ] Adicionar loading states mais informativos
   - [ ] Melhorar tratamento de erros na UI
   - [ ] Adicionar feedback visual para ações do usuário
   - [ ] Otimizar renderização de markdown

5. **Validações e Tratamento de Erros**
   - [ ] Adicionar validações de entrada mais robustas
   - [ ] Melhorar mensagens de erro
   - [ ] Adicionar logging estruturado
   - [ ] Implementar retry logic para chamadas de API

6. **Testes**
   - [ ] Adicionar testes unitários para domínio
   - [ ] Adicionar testes de integração para API
   - [ ] Adicionar testes E2E para fluxos principais

### Prioridade Baixa (Pós-MVP)

7. **Melhorias de Performance**
   - [ ] Implementar processamento assíncrono para PDFs grandes
   - [ ] Adicionar cache para embeddings
   - [ ] Otimizar queries de busca vetorial

8. **Funcionalidades Adicionais**
   - [ ] Sistema de autenticação
   - [ ] Dashboard analítico
   - [ ] Busca por filtros no chat
   - [ ] Edição/exclusão de mensagens

## 📁 Estrutura do Projeto

```
/
├── .venv/                    # Ambiente virtual Python (configurado)
├── backend/
│   ├── app/
│   │   ├── api/              # Rotas da API
│   │   ├── domain/           # Lógica de negócio
│   │   └── infrastructure/   # Implementações (Supabase, Gemini)
│   ├── schema.sql            # Schema do banco de dados
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/              # Cliente da API
│   │   ├── views/            # Telas (Chat, Admin)
│   │   └── state/            # Estado global
│   └── package.json
└── design/                   # Documentação de design
```

## 🔧 Troubleshooting

**Backend não inicia:**
- Verifique se o `.env` está na pasta `backend/`
- Verifique se o venv está ativado
- Verifique os logs do terminal

**Frontend não conecta:**
- Verifique se o backend está rodando na porta 8000
- Verifique o console do navegador (F12)
- Verifique o proxy no `vite.config.ts`

**Erro ao criar artefato:**
- Verifique credenciais do Supabase no `.env`
- Verifique se o schema SQL foi executado
- Verifique se o bucket `artifacts` existe

**Erro ao gerar embeddings:**
- Verifique a chave da API do Gemini
- Verifique se o modelo de embedding está disponível
- Consulte logs do backend

## 📚 Documentação

A documentação completa de design está na pasta `design/`:
- `1_visao_geral_dominio.md` - Visão e escopo
- `2_arquitetura_alto_nivel.md` - Arquitetura
- `3_contrato_api.yml` - Contrato da API (OpenAPI)
- `4_modelagem_tatica_backend.md` - Modelagem do backend
- `5_guia_implementacao_frontend.md` - Guia do frontend

## 📝 Notas Importantes

- O MVP não inclui sistema de autenticação (simulado por URLs diretas)
- A ingestão de PDF é síncrona (processa na requisição)
- O sistema usa busca vetorial com pgvector para RAG
- O código segue arquitetura em camadas (domínio/infraestrutura)
- O sistema pode funcionar parcialmente sem Supabase configurado (modo degradado)
