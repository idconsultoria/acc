# Guia de Configuração - Google Cloud Run

Este guia detalha como implantar o backend do Agente Cultural no Google Cloud Run, permitindo que o serviço "durma" durante períodos de inatividade para reduzir custos.

## Visão Geral da Arquitetura

- **Frontend**: Implantado no Vercel (servindo apenas arquivos estáticos)
- **Backend**: Implantado no Google Cloud Run (com cold start automático)
- **Comportamento**: O Cloud Run coloca o serviço em "sleep" após períodos de inatividade e o "acorda" automaticamente quando há uma requisição

## Pré-requisitos

1. Conta no Google Cloud Platform (GCP)
2. Google Cloud SDK (gcloud) instalado
3. Docker instalado (para build local, opcional)
4. Projeto criado no GCP

## Passo 1: Configuração Inicial do GCP

### 1.1 Criar um Projeto no GCP

```bash
# Fazer login no GCP
gcloud auth login

# Criar um novo projeto (ou usar um existente)
gcloud projects create agente-cultural-backend --name="Agente Cultural Backend"

# Definir o projeto como padrão
gcloud config set project agente-cultural-backend
```

### 1.2 Habilitar APIs Necessárias

```bash
# Habilitar Cloud Run API
gcloud services enable run.googleapis.com

# Habilitar Cloud Build API (para build de imagens)
gcloud services enable cloudbuild.googleapis.com

# Habilitar Container Registry API (para armazenar imagens Docker)
gcloud services enable containerregistry.googleapis.com

# Habilitar Artifact Registry API (alternativa mais moderna)
gcloud services enable artifactregistry.googleapis.com
```

### 1.3 Configurar Autenticação

```bash
# Configurar Application Default Credentials
gcloud auth application-default login

# Configurar Docker para usar gcloud como helper
gcloud auth configure-docker
```

## Passo 2: Preparar o Backend para Cloud Run

### 2.1 Verificar Dockerfile

O Dockerfile já está configurado para Cloud Run:
- Usa a porta definida pela variável de ambiente `PORT` (padrão: 8080)
- Otimizado para cold start com `--workers 1`
- Usa `exec` para melhor gerenciamento de processos

### 2.2 Configurar Variáveis de Ambiente

Crie um arquivo `.env.yaml` (ou use variáveis de ambiente no Cloud Run):

```yaml
# .env.yaml (exemplo - não commitar no git)
SUPABASE_URL: "sua-url-supabase"
SUPABASE_KEY: "sua-chave-supabase"
GEMINI_API_KEY: "sua-chave-gemini"
DATABASE_URL: "sua-url-database"
```

**Importante**: Não commite arquivos `.env.yaml` com credenciais reais no repositório.

## Passo 3: Build e Deploy da Imagem Docker

### 3.1 Opção A: Build e Deploy via Cloud Build (Recomendado)

```bash
# Navegar para o diretório do backend
cd backend

# Fazer build e deploy em um comando
gcloud run deploy agente-cultural-backend \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars "SUPABASE_URL=sua-url,SUPABASE_KEY=sua-chave,GEMINI_API_KEY=sua-chave"
```

### 3.2 Opção B: Build Local e Push para Container Registry

```bash
# Definir variáveis
PROJECT_ID=$(gcloud config get-value project)
REGION=us-central1
SERVICE_NAME=agente-cultural-backend

# Build da imagem localmente
docker build -t gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest ./backend

# Push para Container Registry
docker push gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest

# Deploy no Cloud Run
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0
```

## Passo 4: Configuração Avançada do Cloud Run

### 4.1 Configurações de Cold Start

O Cloud Run automaticamente:
- Coloca o serviço em "sleep" após 15 minutos de inatividade
- "Acorda" o serviço quando há uma requisição (cold start)
- O cold start pode levar de 5 a 30 segundos dependendo do tamanho da aplicação

**Otimizações para reduzir cold start:**
- `--min-instances 0`: Permite que o serviço durma (padrão)
- `--memory 512Mi`: Memória mínima necessária
- `--cpu 1`: CPU mínima
- Dockerfile otimizado com `--workers 1`

### 4.2 Configurar Variáveis de Ambiente

```bash
# Atualizar variáveis de ambiente
gcloud run services update agente-cultural-backend \
  --region us-central1 \
  --update-env-vars "SUPABASE_URL=nova-url,SUPABASE_KEY=nova-chave"
```

### 4.3 Configurar Secrets (Recomendado para Produção)

```bash
# Criar secrets no Secret Manager
gcloud secrets create supabase-url --data-file=- <<< "sua-url-supabase"
gcloud secrets create supabase-key --data-file=- <<< "sua-chave-supabase"
gcloud secrets create gemini-api-key --data-file=- <<< "sua-chave-gemini"

# Conceder permissão ao Cloud Run
gcloud secrets add-iam-policy-binding supabase-url \
  --member serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role roles/secretmanager.secretAccessor

# Atualizar serviço para usar secrets
gcloud run services update agente-cultural-backend \
  --region us-central1 \
  --update-secrets "SUPABASE_URL=supabase-url:latest,SUPABASE_KEY=supabase-key:latest,GEMINI_API_KEY=gemini-api-key:latest"
```

## Passo 5: Configurar o Frontend

### 5.1 Obter URL do Cloud Run

Após o deploy, você receberá uma URL como:
```
https://agente-cultural-backend-xxxxx.run.app
```

### 5.2 Configurar Variável de Ambiente no Vercel

1. Acesse o painel do Vercel
2. Vá em Settings > Environment Variables
3. Adicione a variável:
   - **Nome**: `VITE_API_BASE_URL`
   - **Valor**: `https://agente-cultural-backend-xxxxx.run.app/api/v1`
   - **Ambiente**: Production, Preview, Development

### 5.3 Rebuild do Frontend

Após adicionar a variável de ambiente, faça um novo deploy no Vercel para que a variável seja incluída no build.

## Passo 6: Testar o Deploy

### 6.1 Testar Health Check

```bash
# Obter URL do serviço
SERVICE_URL=$(gcloud run services describe agente-cultural-backend \
  --region us-central1 \
  --format 'value(status.url)')

# Testar health check
curl ${SERVICE_URL}/health
```

Deve retornar:
```json
{"status": "healthy"}
```

### 6.2 Testar Cold Start

1. Aguarde 15 minutos sem fazer requisições
2. Faça uma requisição ao endpoint `/health`
3. Observe o tempo de resposta (pode levar alguns segundos na primeira requisição)
4. O frontend deve mostrar a notificação "Acordando o backend..."

## Passo 7: Monitoramento e Logs

### 7.1 Ver Logs em Tempo Real

```bash
gcloud run services logs tail agente-cultural-backend \
  --region us-central1
```

### 7.2 Ver Métricas no Console

1. Acesse o [Cloud Run Console](https://console.cloud.google.com/run)
2. Selecione o serviço `agente-cultural-backend`
3. Veja métricas de:
   - Requisições por segundo
   - Latência
   - Instâncias ativas
   - Cold starts

## Passo 8: Otimizações e Boas Práticas

### 8.1 Reduzir Cold Start

- **Minimize dependências**: Remova bibliotecas não utilizadas
- **Use imagens base menores**: `python:3.12-slim` já é otimizado
- **Cache de dependências**: Use multi-stage builds se necessário
- **Warm-up requests**: Configure um cron job para manter o serviço ativo (opcional)

### 8.2 Configurar CORS

O backend já está configurado para aceitar requisições de qualquer origem. Em produção, você pode restringir:

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://seu-dominio.vercel.app"],  # Especifique domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 8.3 Configurar Timeout

O Cloud Run tem um timeout máximo de 300 segundos (5 minutos). Para requisições longas (como processamento de PDFs), considere usar tarefas assíncronas.

## Passo 9: Custos e Limites

### 9.1 Modelo de Cobrança

- **CPU**: Cobrado apenas quando há requisições
- **Memória**: Cobrado apenas quando há requisições
- **Requisições**: Primeiros 2 milhões/mês são gratuitos
- **Cold start**: Não há cobrança adicional

### 9.2 Limites Gratuitos

- 2 milhões de requisições/mês
- 360.000 GB-segundos de memória/mês
- 180.000 vCPU-segundos/mês

### 9.3 Estimativa de Custos

Para um serviço com:
- 10.000 requisições/mês
- 512MB de memória
- 1 vCPU
- Tempo médio de resposta: 2 segundos

**Custo estimado**: ~$0 (dentro do tier gratuito)

## Passo 10: Troubleshooting

### 10.1 Erro: "Service not found"

```bash
# Verificar se o serviço existe
gcloud run services list --region us-central1

# Verificar permissões
gcloud projects get-iam-policy $(gcloud config get-value project)
```

### 10.2 Erro: "Connection refused"

- Verifique se o serviço está rodando na porta correta (8080)
- Verifique se o Dockerfile expõe a porta 8080
- Verifique logs: `gcloud run services logs read agente-cultural-backend --region us-central1`

### 10.3 Cold Start Muito Lento

- Reduza o tamanho da imagem Docker
- Remova dependências desnecessárias
- Use `--min-instances 1` para manter sempre uma instância ativa (aumenta custos)

### 10.4 Erro de CORS

- Verifique se o frontend está usando a URL correta do Cloud Run
- Verifique configuração de CORS no backend
- Verifique se o Cloud Run permite requisições não autenticadas

## Passo 11: CI/CD (Opcional)

### 11.1 GitHub Actions

Crie `.github/workflows/deploy-cloud-run.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - id: 'auth'
        uses: 'google-github-actions/auth@v1'
        with:
          credentials_json: '${{ secrets.GCP_SA_KEY }}'
      
      - name: 'Set up Cloud SDK'
        uses: 'google-github-actions/setup-gcloud@v1'
      
      - name: 'Deploy to Cloud Run'
        run: |
          gcloud run deploy agente-cultural-backend \
            --source ./backend \
            --region us-central1 \
            --platform managed \
            --allow-unauthenticated
```

## Conclusão

Com este guia, você deve ter:
- ✅ Backend implantado no Cloud Run
- ✅ Serviço configurado para "dormir" em inatividade
- ✅ Frontend configurado para apontar para o Cloud Run
- ✅ Sistema de notificação de cold start funcionando
- ✅ Monitoramento e logs configurados

Para mais informações, consulte a [documentação oficial do Cloud Run](https://cloud.google.com/run/docs).

