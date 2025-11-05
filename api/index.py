"""
Handler para Vercel Serverless Functions
Este arquivo expõe a aplicação FastAPI para a Vercel
"""
import sys
import os

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.main import app

# Expõe a aplicação para a Vercel
handler = app

