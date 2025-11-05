"""Configuração do Supabase e banco de dados."""
import os
from dotenv import load_dotenv

load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Google Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# As validações serão feitas quando necessário, não na importação
# Isso permite que o servidor inicie mesmo sem todas as variáveis

