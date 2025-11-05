"""
Handler para Vercel Serverless Functions
Este arquivo expõe a aplicação FastAPI para a Vercel
"""
import sys
import os

# Adiciona o diretório backend ao path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

try:
    from app.main import app as application
    
    # Para debug - mostra que a importação funcionou
    print(f"✓ FastAPI app loaded successfully from {backend_path}")
    print(f"✓ Routes available: {[route.path for route in application.routes]}")
    
except Exception as e:
    print(f"✗ Error loading FastAPI app: {e}")
    print(f"✗ sys.path: {sys.path}")
    raise

# Expõe a aplicação para a Vercel
# A Vercel espera 'app' ou 'handler'
app = application
handler = application

