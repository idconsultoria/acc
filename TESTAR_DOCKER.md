# 🐳 Testar Backend com Docker

## 📋 Pré-requisitos

- ✅ Docker Desktop rodando
- ✅ Credenciais Supabase e Google Gemini

---

## 🚀 Passo a Passo

### 1. Criar arquivo .env

Crie o arquivo `backend/.env` com suas credenciais:

```bash
# Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_service_role_key

# Google Gemini
GOOGLE_API_KEY=sua_chave_google_api
```

---

### 2. Build e Rodar com Docker Compose

```powershell
# Build da imagem
docker-compose build

# Rodar o container
docker-compose up
```

Ou tudo de uma vez:
```powershell
docker-compose up --build
```

---

### 3. Testar os Endpoints

Abra outro terminal e teste:

#### Health Check
```powershell
curl http://localhost:8000/health
```

Ou no navegador:
```
http://localhost:8000/health
```

#### Documentação Interativa
```
http://localhost:8000/docs
```

#### API Artifacts
```
http://localhost:8000/api/v1/artifacts
```

---

## 🔍 Ver Logs

```powershell
# Ver logs em tempo real
docker-compose logs -f

# Ver logs apenas do backend
docker-compose logs -f backend
```

---

## 🛑 Parar o Container

```powershell
# Parar (Ctrl+C ou)
docker-compose down

# Parar e remover volumes
docker-compose down -v
```

---

## 🐛 Troubleshooting

### Erro: "no configuration file provided"
- Certifique-se que está na raiz do projeto

### Erro: Port 8000 already in use
```powershell
# Parar containers existentes
docker-compose down

# Ou mude a porta no docker-compose.yml
ports:
  - "8001:8000"
```

### Erro: Cannot connect to database
- Verifique se `SUPABASE_URL` e `SUPABASE_KEY` estão corretos no `.env`

---

## ✅ Se Funcionar no Docker

Se funcionar no Docker mas não na Vercel, o problema é:
1. **Configuração da Vercel** (vercel.json)
2. **Path dos arquivos** na Vercel
3. **Variáveis de ambiente** não configuradas na Vercel

Se **NÃO funcionar** no Docker:
1. **Dependências faltando**
2. **Erro no código Python**
3. **Credenciais inválidas**

---

## 📊 Comandos Úteis

```powershell
# Rebuild forçado (sem cache)
docker-compose build --no-cache

# Ver containers rodando
docker ps

# Entrar no container
docker-compose exec backend bash

# Ver tamanho da imagem
docker images | findstr backend
```

---

**Boa sorte! 🚀**

