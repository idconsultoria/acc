# 🔍 Problemas Identificados e Soluções - Deploy no Vercel

## 📋 Resumo dos Problemas Encontrados

Foram identificados **3 problemas principais** que causavam falhas nas requisições ao backend no Vercel:

---

## ❌ Problema 1: Handler do FastAPI Incorreto

### **Descrição:**
O handler do FastAPI em `api/index.py` estava exportando o objeto `app` diretamente, mas o Vercel para Python serverless functions requer um adaptador específico (Mangum) para converter requisições do formato API Gateway/Lambda para ASGI (usado pelo FastAPI).

### **Solução Aplicada:**
- Adicionado `mangum==0.18.0` ao `requirements.txt`
- Modificado `api/index.py` para usar `Mangum` como adaptador:
  ```python
  from mangum import Mangum
  handler = Mangum(app, lifespan="off")
  ```

### **Arquivos Modificados:**
- ✅ `api/index.py` - Adicionado adaptador Mangum
- ✅ `requirements.txt` - Adicionado `mangum==0.18.0`

---

## ❌ Problema 2: URL da API no Frontend Usando Localhost

### **Descrição:**
O `frontend/src/api/client.ts` estava usando `http://localhost:8000/api/v1` como fallback quando a variável `VITE_API_BASE_URL` não estava definida. No Vercel, isso causava tentativas de requisição para localhost, que obviamente falhava.

### **Solução Aplicada:**
- Implementada detecção automática do ambiente:
  - **Se `VITE_API_BASE_URL` estiver definida**: usa ela (prioridade)
  - **Se estiver em produção (PROD)**: usa URL relativa `/api/v1` (mesma origem)
  - **Se estiver em desenvolvimento**: usa `http://localhost:8000/api/v1`

### **Arquivos Modificados:**
- ✅ `frontend/src/api/client.ts` - Adicionada função `getApiBaseUrl()` com detecção automática

### **Código Implementado:**
```typescript
const getApiBaseUrl = () => {
  // Se VITE_API_BASE_URL estiver definida, usa ela (prioridade)
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  
  // Se estiver em produção (Vercel), usa URL relativa
  if (import.meta.env.PROD) {
    return '/api/v1'
  }
  
  // Em desenvolvimento, usa localhost
  return 'http://localhost:8000/api/v1'
}
```

---

## ❌ Problema 3: Possível Problema com Duplicação de Prefixo

### **Descrição:**
Verificado o roteamento e confirmado que está correto:
- O `vercel.json` redireciona `/api/v1/:path*` para `/api/index.py`
- O FastAPI registra rotas com prefixo `/api/v1`
- O path completo é passado corretamente ao handler

**Status:** ✅ Confirmado que o roteamento está correto, não há duplicação de prefixo.

---

## ✅ Configuração Necessária no Vercel

### **Variáveis de Ambiente no Dashboard da Vercel:**

1. Acesse: **Dashboard Vercel → Seu Projeto → Settings → Environment Variables**

2. Adicione as seguintes variáveis (se ainda não estiverem configuradas):

#### **Variáveis do Backend (para serverless functions):**
```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_service_role_key_aqui
GOOGLE_API_KEY=sua_chave_google_gemini_aqui
```

#### **Variáveis do Frontend (opcional - só se quiser sobrescrever):**
```env
VITE_API_BASE_URL=/api/v1
```
**Nota:** Esta variável é **opcional**. Se não for definida, o frontend usará automaticamente `/api/v1` em produção.

### **Importante:**
- Marque as variáveis para **todos os ambientes** (Production, Preview, Development)
- Após adicionar variáveis, faça um **redeploy** do projeto

---

## 🧪 Como Testar

### **1. Testar Localmente (antes do deploy):**

```bash
# Frontend
cd frontend
npm run dev

# Backend (em outro terminal)
cd backend
uvicorn app.main:app --reload
```

### **2. Testar no Vercel após deploy:**

1. **Frontend:**
   - Acesse: `https://seu-projeto.vercel.app`
   - Abra o DevTools (F12) → aba Network
   - Faça uma requisição (ex: listar artefatos)
   - Verifique se as requisições vão para `/api/v1/...` (URL relativa)

2. **Backend (Health Check):**
   - Acesse: `https://seu-projeto.vercel.app/health`
   - Deve retornar: `{"status": "healthy"}`

3. **Backend (API):**
   - Acesse: `https://seu-projeto.vercel.app/api/v1/artifacts`
   - Deve retornar lista de artefatos (ou array vazio)

---

## 📝 Checklist de Verificação

Antes de fazer deploy, verifique:

- [ ] `mangum==0.18.0` está no `requirements.txt`
- [ ] `api/index.py` usa `Mangum` como adaptador
- [ ] `frontend/src/api/client.ts` tem detecção automática de ambiente
- [ ] Variáveis de ambiente configuradas no Vercel Dashboard
- [ ] Build local funciona: `cd frontend && npm run build`
- [ ] Backend local funciona: `uvicorn app.main:app --reload`

---

## 🔄 Próximos Passos

1. **Fazer commit das alterações:**
   ```bash
   git add .
   git commit -m "Corrige problemas de deploy no Vercel: adiciona Mangum, corrige URL da API"
   git push origin main
   ```

2. **Aguardar deploy automático no Vercel**

3. **Verificar logs no Dashboard da Vercel:**
   - Vá em **Deployments** → clique no último deployment → **Logs**
   - Procure por mensagens de erro ou confirmação de sucesso

4. **Testar a aplicação** conforme instruções acima

---

## 🐛 Se Ainda Houver Problemas

### **Erro: "ModuleNotFoundError: No module named 'mangum'"**
- Verifique se `mangum==0.18.0` está no `requirements.txt`
- Verifique se o `requirements.txt` está na raiz do projeto
- Faça redeploy

### **Erro: "404 Not Found" nas rotas da API**
- Verifique os logs do Vercel para ver se o handler está sendo carregado
- Verifique se o `vercel.json` está configurado corretamente
- Teste a rota `/health` primeiro

### **Erro: "CORS Error"**
- Verifique se o CORS está configurado no `backend/app/main.py`:
  ```python
  allow_origins=["*"]  # Para testes
  # Ou especifique: allow_origins=["https://seu-projeto.vercel.app"]
  ```

### **Erro: "Connection refused" ou "Failed to fetch"**
- Verifique se a URL da API está correta (deve ser `/api/v1` em produção)
- Verifique no DevTools do navegador qual URL está sendo usada
- Verifique se há variável `VITE_API_BASE_URL` configurada incorretamente

---

## 📚 Referências

- [Vercel Python Runtime](https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python)
- [Mangum Documentation](https://mangum.io/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

**Data da correção:** Novembro 2025

