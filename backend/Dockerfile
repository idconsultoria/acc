FROM python:3.12-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY . .

# Expõe porta (Cloud Run usa a variável de ambiente PORT)
EXPOSE 8080

# Comando para rodar no Cloud Run
# Cloud Run define a variável PORT automaticamente
# Usa --workers 1 para otimizar para cold start
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1

