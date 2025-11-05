# 🚀 Guia Completo de Implantação na Vercel

Este guia detalha todos os passos para implantar seu **Agente Cultural** (app fullstack) na Vercel.

## 📋 Índice
1. [Pré-requisitos](#pré-requisitos)
2. [Preparar o Repositório](#preparar-o-repositório)
3. [Configurar Variáveis de Ambiente](#configurar-variáveis-de-ambiente)
4. [Implantar na Vercel](#implantar-na-vercel)
5. [Verificar a Implantação](#verificar-a-implantação)
6. [Solução de Problemas](#solução-de-problemas)

---

## 🔧 Pré-requisitos

### 1. Conta na Vercel
- Acesse [vercel.com](https://vercel.com)
- Crie uma conta gratuita (pode usar GitHub, GitLab ou email)

### 2. Repositório Git
- Seu código deve estar em um repositório Git (GitHub, GitLab ou Bitbucket)
- Se ainda não estiver no Git, execute:

```bash
git init
git add .
git commit -m "Initial commit"
```

### 3. Criar repositório no GitHub (recomendado)
- Acesse [github.com/new](https://github.com/new)
- Crie um novo repositório (pode ser público ou privado)
- Conecte seu repositório local:

```bash
git remote add origin https://github.com/seu-usuario/seu-repositorio.git
git branch -M main
git push -u origin main
```

### 4. Credenciais Necessárias
Você precisará ter em mãos:
- ✅ URL do Supabase
- ✅ Chave do Supabase (Service Key)
- ✅ Chave da API do Google Gemini
- ✅ URL do banco de dados (se aplicável)

---

## 📦 Preparar o Repositório

### Passo 1: Criar arquivo .gitignore (se não existir)

Crie ou atualize o arquivo `.gitignore` na raiz do projeto:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
*.egg-info/

# Node
node_modules/
dist/
build/
.cache/

# Environment variables
.env
.env.local
.env.production

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Vercel
.vercel
```

### Passo 2: Criar arquivo de variáveis de ambiente de exemplo

Crie o arquivo `.env.example` na raiz do projeto:

```env
# Configurações do Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_chave_service_key_aqui

# Configurações do Google Gemini
GOOGLE_API_KEY=sua_chave_google_api_aqui

# Configurações do Banco de Dados (opcional)
DATABASE_URL=postgresql://usuario:senha@host:5432/database
```

### Passo 3: Verificar arquivos criados

Os seguintes arquivos foram criados automaticamente:
- ✅ `vercel.json` - Configuração da Vercel
- ✅ `api/index.py` - Handler para serverless functions
- ✅ `frontend/package.json` - Com script `vercel-build` adicionado

### Passo 4: Commit das alterações

```bash
git add .
git commit -m "Adiciona configuração para Vercel"
git push origin main
```

---

## 🔐 Configurar Variáveis de Ambiente

### Onde encontrar suas credenciais:

#### **Supabase**
1. Acesse [supabase.com](https://supabase.com)
2. Faça login e selecione seu projeto
3. Vá em **Settings** → **API**
4. Copie:
   - **URL**: `Project URL`
   - **Key**: `service_role key` (não use a anon key para produção)

#### **Google Gemini**
1. Acesse [ai.google.dev](https://ai.google.dev)
2. Clique em **Get API Key**
3. Crie ou selecione um projeto
4. Copie a chave gerada

---

## 🌐 Implantar na Vercel

### Método 1: Via Dashboard da Vercel (Recomendado)

#### Passo 1: Acessar Vercel Dashboard
1. Acesse [vercel.com/dashboard](https://vercel.com/dashboard)
2. Clique em **"Add New..."** → **"Project"**

#### Passo 2: Importar Repositório
1. Clique em **"Import Git Repository"**
2. Selecione seu repositório do GitHub/GitLab/Bitbucket
3. Se não aparecer, clique em **"Adjust GitHub App Permissions"** e autorize

#### Passo 3: Configurar o Projeto
1. **Framework Preset**: Selecione **"Other"** ou **"Vite"**
2. **Root Directory**: Deixe em branco (`.`)
3. **Build Command**: `cd frontend && npm install && npm run build`
4. **Output Directory**: `frontend/dist`

#### Passo 4: Adicionar Variáveis de Ambiente
Clique em **"Environment Variables"** e adicione:

| Nome | Valor |
|------|-------|
| `SUPABASE_URL` | sua_url_do_supabase |
| `SUPABASE_KEY` | sua_chave_do_supabase |
| `GOOGLE_API_KEY` | sua_chave_do_google |
| `DATABASE_URL` | sua_url_do_banco (opcional) |

**Importante:** Marque as variáveis para todos os ambientes (Production, Preview, Development)

#### Passo 5: Deploy
1. Clique em **"Deploy"**
2. Aguarde o build (pode levar 2-5 minutos)
3. ✅ Quando concluído, você verá a mensagem de sucesso!

---

### Método 2: Via Vercel CLI

#### Passo 1: Instalar Vercel CLI

```bash
npm install -g vercel
```

#### Passo 2: Login na Vercel

```bash
vercel login
```

#### Passo 3: Deploy

```bash
# Na raiz do projeto
vercel
```

Siga as instruções no terminal:
- Link to existing project? **No**
- Project name: **[nome-do-seu-projeto]**
- Directory: **. (ponto)**
- Override settings? **No**

#### Passo 4: Adicionar Variáveis de Ambiente

```bash
vercel env add SUPABASE_URL
vercel env add SUPABASE_KEY
vercel env add GOOGLE_API_KEY
```

#### Passo 5: Deploy para Produção

```bash
vercel --prod
```

---

## ✅ Verificar a Implantação

### Passo 1: Acessar o Dashboard da Vercel
1. Acesse [vercel.com/dashboard](https://vercel.com/dashboard)
2. Clique no seu projeto
3. Você verá o status do deployment

### Passo 2: Testar a Aplicação
A Vercel fornecerá uma URL, algo como:
```
https://seu-projeto.vercel.app
```

#### Testar o Frontend:
1. Acesse `https://seu-projeto.vercel.app`
2. Você deve ver a interface do Agente Cultural

#### Testar o Backend:
1. Acesse `https://seu-projeto.vercel.app/health`
2. Deve retornar: `{"status": "healthy"}`

3. Acesse `https://seu-projeto.vercel.app/api/v1/artifacts`
4. Deve retornar a lista de artefatos (ou array vazio se não houver dados)

### Passo 3: Verificar Logs
1. No Dashboard da Vercel, clique na aba **"Logs"**
2. Veja os logs em tempo real da sua aplicação
3. Se houver erros, eles aparecerão aqui

---

## 🔧 Solução de Problemas

### Problema 1: Build Falha no Frontend

**Erro comum:**
```
Error: Cannot find module '@/...'
```

**Solução:**
Verifique se o `tsconfig.json` do frontend tem:
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

---

### Problema 2: API não responde (404)

**Erro comum:**
```
404 - Not Found
```

**Solução:**
1. Verifique se o arquivo `api/index.py` existe
2. Verifique se `vercel.json` está configurado corretamente
3. Verifique os logs no Dashboard da Vercel

---

### Problema 3: Erro de Variáveis de Ambiente

**Erro comum:**
```
KeyError: 'SUPABASE_URL'
```

**Solução:**
1. Acesse o Dashboard da Vercel
2. Vá em **Settings** → **Environment Variables**
3. Adicione todas as variáveis necessárias
4. Faça um novo deploy:
   ```bash
   vercel --prod
   ```

---

### Problema 4: CORS Error

**Erro comum:**
```
Access to fetch has been blocked by CORS policy
```

**Solução:**
Verifique se o `backend/app/main.py` tem a configuração de CORS correta:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://seu-projeto.vercel.app"],  # URL do seu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Ou, temporariamente para teste:
```python
allow_origins=["*"]
```

---

### Problema 5: Dependências Python não instaladas

**Erro comum:**
```
ModuleNotFoundError: No module named '...'
```

**Solução:**
1. Verifique se `requirements.txt` está na raiz ou no diretório `backend/`
2. Se estiver em `backend/`, mova para a raiz:
   ```bash
   cp backend/requirements.txt ./requirements.txt
   ```
3. Faça commit e push:
   ```bash
   git add requirements.txt
   git commit -m "Move requirements.txt para raiz"
   git push
   ```

---

## 🎯 Próximos Passos

### 1. Configurar Domínio Customizado (Opcional)
1. No Dashboard da Vercel, vá em **Settings** → **Domains**
2. Adicione seu domínio customizado
3. Siga as instruções para configurar DNS

### 2. Configurar Preview Deployments
- Cada push para branches além de `main` criará um preview deployment
- Útil para testar mudanças antes de ir para produção

### 3. Monitoramento
- Use a aba **Analytics** no Dashboard da Vercel
- Configure alertas para erros
- Monitore performance e uso

### 4. CI/CD Automático
- A Vercel automaticamente faz deploy a cada push para `main`
- Configure GitHub Actions para testes antes do deploy (opcional)

---

## 📚 Recursos Adicionais

- [Documentação da Vercel](https://vercel.com/docs)
- [Vercel + Python](https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python)
- [Vercel + Vite](https://vercel.com/docs/frameworks/vite)
- [Supabase Documentation](https://supabase.com/docs)

---

## 💡 Dicas Importantes

1. **Sempre teste localmente antes de fazer deploy**
   ```bash
   # Frontend
   cd frontend && npm run dev
   
   # Backend (em outro terminal)
   cd backend && uvicorn app.main:app --reload
   ```

2. **Use branches para features**
   - Crie uma branch para cada feature
   - Teste no preview deployment
   - Faça merge para main quando estiver pronto

3. **Monitore custos**
   - A Vercel tem um plano gratuito generoso
   - Monitore uso em **Settings** → **Usage**

4. **Backups do Banco de Dados**
   - Configure backups automáticos no Supabase
   - Faça backups manuais antes de mudanças grandes

---

## ✅ Checklist Final

Antes de fazer o deploy, verifique:

- [ ] Código está no GitHub/GitLab/Bitbucket
- [ ] Arquivo `vercel.json` está configurado
- [ ] Arquivo `api/index.py` existe
- [ ] Arquivo `.gitignore` está atualizado
- [ ] Variáveis de ambiente estão documentadas em `.env.example`
- [ ] Build local funciona (`cd frontend && npm run build`)
- [ ] Backend local funciona (`uvicorn app.main:app --reload`)
- [ ] Todas as credenciais (Supabase, Gemini) estão disponíveis
- [ ] CORS está configurado corretamente

---

## 🎉 Sucesso!

Se você seguiu todos os passos, seu **Agente Cultural** agora está rodando na Vercel!

Acesse sua aplicação em: `https://seu-projeto.vercel.app`

**Qualquer dúvida, consulte os logs no Dashboard da Vercel ou a documentação oficial.**

---

*Guia criado em: Novembro 2025*
*Última atualização: Novembro 2025*

