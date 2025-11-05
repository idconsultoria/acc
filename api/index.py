"""
Handler para Vercel Serverless Functions
Este arquivo expõe a aplicação FastAPI para a Vercel
"""
import sys
import os
import traceback

print("=" * 50)
print("INICIANDO API HANDLER")
print("=" * 50)

# Adiciona o diretório backend ao path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
print(f"Backend path: {backend_path}")
print(f"Backend path exists: {os.path.exists(backend_path)}")

sys.path.insert(0, backend_path)
print(f"sys.path: {sys.path[:3]}")

# Tenta importar passo a passo para identificar onde falha
print("\n--- Testando imports ---")

try:
    print("1. Importando FastAPI...")
    from fastapi import FastAPI
    print("   ✓ FastAPI OK")
except Exception as e:
    print(f"   ✗ FastAPI FALHOU: {e}")
    traceback.print_exc()

try:
    print("2. Importando módulo app...")
    import app
    print(f"   ✓ app OK - {app}")
except Exception as e:
    print(f"   ✗ app FALHOU: {e}")
    traceback.print_exc()

try:
    print("3. Importando app.main...")
    from app import main
    print(f"   ✓ app.main OK - {main}")
except Exception as e:
    print(f"   ✗ app.main FALHOU: {e}")
    traceback.print_exc()
    raise

try:
    print("4. Pegando app do main...")
    from app.main import app as application
    print(f"   ✓ application OK - {application}")
    print(f"   ✓ Routes: {[r.path for r in application.routes][:5]}")
except Exception as e:
    print(f"   ✗ application FALHOU: {e}")
    traceback.print_exc()
    raise

print("\n" + "=" * 50)
print("API HANDLER CARREGADO COM SUCESSO")
print("=" * 50)

# Expõe a aplicação para a Vercel
app = application
handler = application

