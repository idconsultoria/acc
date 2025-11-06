# 🔧 Solução para Erro 500 no Vercel

## 🔍 Problema Identificado

O erro **500: INTERNAL_SERVER_ERROR** estava ocorrendo porque:

1. **Validações durante a importação**: Os arquivos de rotas (`artifacts.py` e `conversations.py`) estavam fazendo validações de variáveis de ambiente durante a importação do módulo, causando `ValueError` se as variáveis não estivessem configuradas.

2. **Handler não exportado corretamente**: O handler precisava ser exportado de forma explícita para o Vercel.

## ✅ Correções Aplicadas

### 1. **Handler do FastAPI (`api/index.py`)**
- ✅ Adicionado tratamento de erros melhorado
- ✅ Melhorado logs de debug
- ✅ Mantido uso do Mangum como adaptador

### 2. **Validações Tolerantes (`backend/app/api/routes/artifacts.py`)**
- ✅ Removidas validações que causavam erro durante a importação
- ✅ Inicialização condicional de serviços (apenas se variáveis existirem)
- ✅ Validações serão feitas dentro das rotas quando necessário

### 3. **Validações Tolerantes (`backend/app/api/routes/conversations.py`)**
- ✅ Removida validação que causava erro durante a importação
- ✅ Permite que o servidor inicie mesmo sem `GEMINI_API_KEY`

## 📋 Checklist de Variáveis de Ambiente no Vercel

**IMPORTANTE:** As seguintes variáveis de ambiente DEVEM estar configuradas no Dashboard da Vercel:

1. Acesse: **Dashboard Vercel → Seu Projeto → Settings → Environment Variables**

2. Adicione/Verifique estas variáveis:

```env
# Supabase (obrigatórias)
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_service_role_key_aqui
SUPABASE_SERVICE_ROLE_KEY=sua_service_role_key_aqui

# Google Gemini (obrigatória)
GOOGLE_API_KEY=sua_chave_google_gemini_aqui

# Frontend (opcional - usa /api/v1 automaticamente se não definida)
VITE_API_BASE_URL=/api/v1
```

3. **Marque para todos os ambientes**: Production, Preview, Development

4. **Após adicionar variáveis**: Faça um **redeploy** do projeto

## 🧪 Como Testar Após Correções

### 1. **Teste a Rota `/health`**
Esta rota não precisa de variáveis de ambiente e deve funcionar:

```bash
curl https://seu-projeto.vercel.app/health
```

**Resposta esperada:**
```json
{"status": "healthy"}
```

### 2. **Teste a Rota `/api/v1/artifacts`**
Esta rota precisa de variáveis de ambiente:

```bash
curl https://seu-projeto.vercel.app/api/v1/artifacts
```

**Resposta esperada:**
```json
[]
```

Ou uma lista de artefatos se houver dados.

### 3. **Verificar Logs no Vercel**
1. Acesse: **Dashboard Vercel → Seu Projeto → Deployments**
2. Clique no último deployment
3. Clique em **"Logs"**
4. Procure por:
   - ✅ `✓ SUCCESS: FastAPI app imported`
   - ✅ `✓ Using Mangum adapter for Vercel`
   - ⚠️ Qualquer mensagem de erro

## 🐛 Se Ainda Houver Erro 500

### **Passo 1: Verificar Logs**
- Acesse os logs no Dashboard da Vercel
- Procure pela mensagem de erro específica
- Copie o erro completo

### **Passo 2: Verificar Variáveis de Ambiente**
- Confirme que TODAS as variáveis estão configuradas
- Confirme que estão marcadas para o ambiente correto (Production)
- Faça redeploy após adicionar variáveis

### **Passo 3: Verificar Dependências**
- Confirme que `mangum==0.18.0` está no `requirements.txt`
- Confirme que o `requirements.txt` está na raiz do projeto

### **Passo 4: Verificar Estrutura de Arquivos**
- Confirme que `api/index.py` existe
- Confirme que `backend/app/main.py` existe
- Confirme que `vercel.json` está configurado corretamente

## 📝 Arquivos Modificados

- ✅ `api/index.py` - Melhorado tratamento de erros
- ✅ `backend/app/api/routes/artifacts.py` - Removidas validações durante importação
- ✅ `backend/app/api/routes/conversations.py` - Removida validação durante importação

## 🔄 Próximos Passos

1. **Fazer commit das alterações:**
   ```bash
   git add .
   git commit -m "Corrige erro 500: remove validações durante importação"
   git push origin main
   ```

2. **Aguardar deploy automático no Vercel**

3. **Testar a rota `/health`** primeiro (deve funcionar sem variáveis)

4. **Configurar variáveis de ambiente no Vercel** (se ainda não estiverem)

5. **Testar rotas da API** (`/api/v1/artifacts`, etc.)

---

## 💡 Explicação Técnica

### Por que estava dando erro 500?

O problema ocorria porque:

1. Quando o Vercel carrega a função serverless, ele importa o módulo `api/index.py`
2. O `api/index.py` importa `app.main`
3. O `app.main` importa os routers (`artifacts`, `conversations`, etc.)
4. Durante a importação dos routers, havia código que validava variáveis de ambiente:
   ```python
   if not GEMINI_API_KEY:
       raise ValueError("GEMINI_API_KEY deve estar configurado")
   ```
5. Se as variáveis não estivessem configuradas, o `ValueError` era lançado durante a importação
6. Isso impedia que o handler fosse criado, causando erro 500

### Solução

Removemos as validações durante a importação e as movemos para dentro das rotas, onde podem ser tratadas graciosamente com `HTTPException` em vez de `ValueError`.

---

**Data da correção:** Novembro 2025

