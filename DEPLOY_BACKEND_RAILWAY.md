# 🚂 Deploy do Backend no Railway

O backend FastAPI é muito pesado para Vercel (>250 MB devido a numpy, pymupdf, etc).  
Use o **Railway** que é otimizado para backends Python.

---

## 🎯 Por que Railway?

- ✅ Gratuito (até $5/mês de uso)
- ✅ Deploy automático via GitHub
- ✅ Suporta Python/FastAPI nativamente
- ✅ Variáveis de ambiente fáceis
- ✅ Logs em tempo real
- ✅ Sem limite de tamanho de dependências

---

## 🚀 Passo a Passo

### 1. Criar Conta no Railway

1. Acesse: https://railway.app
2. Clique em **"Start a New Project"**
3. Faça login com GitHub

### 2. Importar Repositório

1. Clique em **"Deploy from GitHub repo"**
2. Selecione o repositório `idconsultoria/acc`
3. Railway detectará automaticamente o Python

### 3. Configurar Variáveis de Ambiente

No painel do Railway, vá em **"Variables"** e adicione:

```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_service_role_key
GOOGLE_API_KEY=sua_chave_google_gemini
DATABASE_URL=sua_url_database (se usar conexão direta)
PORT=8000
```

### 4. Configurar Root Directory

Como o backend está em `backend/`, configure:

1. Vá em **Settings**
2. Em **"Root Directory"** coloque: `backend`
3. Em **"Start Command"** coloque: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 5. Deploy

Railway fará deploy automaticamente!

Você receberá uma URL tipo:
```
https://acc-production.up.railway.app
```

---

## 🔧 Configurar Frontend para usar a API

Depois do deploy, configure o frontend na Vercel:

**Variável de Ambiente:**
```
VITE_API_BASE_URL=https://acc-production.up.railway.app/api/v1
```

---

## 📝 Arquivo Procfile (Opcional)

Se Railway não detectar automaticamente, crie `backend/Procfile`:

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## 🔍 Verificar Deploy

Após deploy, teste:

```
https://sua-api.railway.app/health
https://sua-api.railway.app/docs
```

---

## 💡 Alternativas ao Railway

Se preferir outras plataformas:

### **Render**
- URL: https://render.com
- Plano gratuito com limitações (spin down após inatividade)
- Deploy similar ao Railway

### **Fly.io**
- URL: https://fly.io
- Plano gratuito generoso
- Requer configuração de Docker

### **Google Cloud Run**
- URL: https://cloud.google.com/run
- Pay-as-you-go (muito barato para baixo tráfego)
- Escala automática para zero

---

## 📊 Custos Estimados

**Railway (Free Tier):**
- $5/mês de uso incluído
- Depois: $0.000231/minuto
- ~$10-15/mês para app pequeno

**Render (Free Tier):**
- Gratuito com limitações
- Spin down após 15min de inatividade
- Upgrade: $7/mês

---

## 🔄 CI/CD Automático

Railway faz deploy automático a cada push no GitHub!

```bash
git push origin main
# Railway detecta e faz deploy automático
```

---

## 🆘 Troubleshooting

### Build Falha

Verifique se `requirements.txt` está em `backend/requirements.txt`

### CORS Error

Configure no `backend/app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://seu-projeto.vercel.app",  # Frontend na Vercel
        "http://localhost:3000",            # Dev local
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Conexão com Supabase

Certifique-se que as variáveis `SUPABASE_URL` e `SUPABASE_KEY` estão configuradas.

---

## 📚 Documentação

- Railway Docs: https://docs.railway.app
- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/

---

**Agora você tem frontend na Vercel + backend no Railway = App completo!** 🎉

