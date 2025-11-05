# 🚀 Instruções de Deploy - Solução Final

## ⚠️ Problema Identificado

O backend Python excede o limite de 250 MB da Vercel mesmo após remover pymupdf (~60-90 MB).

**Dependências restantes ainda muito pesadas:**
- numpy + google-generativeai + psycopg + supabase + outras = ~110-175 MB
- Com overhead da Vercel = ultrapassa 250 MB ❌

---

## ✅ SOLUÇÃO: Deploy Separado

### **Frontend → Vercel** (já configurado)
### **Backend → Railway** (sem limite de tamanho)

---

## 📋 PASSO A PASSO

### **1️⃣ Frontend na Vercel (JÁ ESTÁ PRONTO!)**

O `vercel.json` já está configurado apenas para o frontend.

**Status:** ✅ Deploy do frontend deve funcionar agora

---

### **2️⃣ Backend no Railway**

#### **A. Criar conta no Railway**
1. Acesse: https://railway.app
2. Clique em **"Start a New Project"**
3. Faça login com GitHub

#### **B. Criar novo projeto**
1. Clique em **"Deploy from GitHub repo"**
2. Selecione: `idconsultoria/acc`
3. Railway detectará Python automaticamente

#### **C. Configurar Root Directory**
1. Vá em **Settings**
2. Em **"Root Directory"** digite: `backend`
3. Em **"Start Command"** digite: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

#### **D. Adicionar Variáveis de Ambiente**
Clique em **"Variables"** e adicione:

```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_service_role_key
GOOGLE_API_KEY=sua_chave_google_gemini
PORT=8000
```

#### **E. Deploy**
Railway fará deploy automaticamente!

Você receberá uma URL tipo:
```
https://acc-production.up.railway.app
```

---

### **3️⃣ Conectar Frontend ao Backend**

#### **A. Na Vercel**
1. Acesse: https://vercel.com/dashboard
2. Clique no projeto `acc`
3. Vá em **Settings** → **Environment Variables**
4. Adicione:

```env
VITE_API_BASE_URL=https://acc-production.up.railway.app/api/v1
```

5. Faça **Redeploy** do frontend

#### **B. No Backend (Railway)**
Atualize CORS no `backend/app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://seu-projeto.vercel.app",  # ← Sua URL da Vercel
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Commit e push:
```bash
git add backend/app/main.py
git commit -m "Update CORS for Vercel frontend"
git push origin main
```

Railway fará redeploy automaticamente.

---

## 🧪 Testar

### **Frontend (Vercel):**
```
https://seu-projeto.vercel.app
```

### **Backend (Railway):**
```
https://acc-production.up.railway.app/health
https://acc-production.up.railway.app/docs
```

---

## 💰 Custos

### **Vercel (Frontend)**
- ✅ **Gratuito** - 100 GB bandwidth/mês

### **Railway (Backend)**
- ✅ **$5/mês inclusos no plano gratuito**
- Depois: ~$10-15/mês para app pequeno

**Total estimado: $0-15/mês** 💰

---

## 🔄 CI/CD Automático

Ambas plataformas fazem deploy automático:

```bash
git push origin main
# ✅ Vercel detecta e faz redeploy do frontend
# ✅ Railway detecta e faz redeploy do backend
```

---

## 📊 Arquitetura Final

```
┌─────────────────────┐
│   User Browser      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Vercel (Frontend)  │  ← React + Vite
│  ✅ GRÁTIS          │
└──────────┬──────────┘
           │ API calls
           ▼
┌─────────────────────┐
│ Railway (Backend)   │  ← FastAPI + Python
│  💰 $5-15/mês       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Supabase (DB)      │
│  ✅ GRÁTIS (tier)   │
└─────────────────────┘
```

---

## 🆘 Problemas Comuns

### ❌ Frontend não conecta ao backend

**Solução:** Verifique se `VITE_API_BASE_URL` está configurado na Vercel

### ❌ CORS Error

**Solução:** Adicione URL do frontend Vercel no `allow_origins` do backend

### ❌ Railway build falha

**Solução:** Verifique se `Root Directory` está como `backend`

---

## ✅ Resumo Rápido

1. **Frontend na Vercel** - Configure `VITE_API_BASE_URL`
2. **Backend no Railway** - Configure variáveis de ambiente
3. **Atualize CORS** no backend
4. **Teste tudo** 🎉

---

**Documentação completa:** `DEPLOY_BACKEND_RAILWAY.md`

**Boa sorte! 🚀**

