"""
Handler para Vercel Serverless Functions
Configurado especificamente para a estrutura de paths da Vercel
"""
import sys
import os

print("=" * 60)
print("VERCEL SERVERLESS FUNCTION - STARTING")
print("=" * 60)

# Determina paths absolutos
current_file = os.path.abspath(__file__)
api_dir = os.path.dirname(current_file)
root_dir = os.path.dirname(api_dir)
backend_dir = os.path.join(root_dir, 'backend')

print(f"Current file: {current_file}")
print(f"API directory: {api_dir}")
print(f"Root directory: {root_dir}")
print(f"Backend directory: {backend_dir}")
print(f"Backend exists: {os.path.exists(backend_dir)}")

if os.path.exists(backend_dir):
    print(f"Backend contents: {os.listdir(backend_dir)[:5]}")
else:
    print("ERROR: Backend directory NOT FOUND!")
    print(f"Root contents: {os.listdir(root_dir)}")

# Adiciona backend ao sys.path
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
    print(f"✓ Added backend to sys.path")

print(f"sys.path[0]: {sys.path[0]}")
print(f"sys.path[1]: {sys.path[1] if len(sys.path) > 1 else 'N/A'}")

# Tenta importar
print("\n--- Importing FastAPI app ---")
try:
    from app.main import app
    print(f"✓ SUCCESS: FastAPI app imported")
    print(f"✓ App type: {type(app)}")
    print(f"✓ Routes count: {len(app.routes)}")
    print("=" * 60)
    
    # Para Vercel Serverless Functions Python, precisamos usar Mangum
    # Mangum adapta FastAPI (ASGI) para o formato Lambda/API Gateway que o Vercel usa
    try:
        from mangum import Mangum
        handler = Mangum(app, lifespan="off")
        print("✓ Using Mangum adapter for Vercel")
    except ImportError as e:
        print(f"⚠ Mangum import error: {e}")
        print("⚠ Trying to use app directly (may not work)")
        # Fallback: tenta usar app diretamente
        handler = app
    
except ImportError as e:
    print(f"✗ IMPORT ERROR: {e}")
    print(f"✗ Trying to import 'app' from: {backend_dir}")
    if os.path.exists(os.path.join(backend_dir, 'app')):
        print(f"✓ 'app' directory exists")
        app_contents = os.listdir(os.path.join(backend_dir, 'app'))
        print(f"  Contents: {app_contents}")
    else:
        print(f"✗ 'app' directory does NOT exist")
    import traceback
    traceback.print_exc()
    raise
except Exception as e:
    print(f"✗ UNEXPECTED ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    raise

# Export handler - Vercel espera que o handler seja exportado no nível do módulo
# O handler será chamado automaticamente pelo Vercel quando a função for invocada

