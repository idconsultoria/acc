"""
Handler para Vercel Serverless Functions
Simula o ambiente do Docker para garantir compatibilidade
"""
import sys
import os

# CRITICAL: Adiciona backend ao path ANTES de qualquer import
# Isso simula o WORKDIR /app do Docker
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(root_dir, 'backend')

# Adiciona backend como PRIMEIRO item do path
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Agora importa normalmente como no Docker
from app.main import app

# Para Vercel Serverless
handler = app

