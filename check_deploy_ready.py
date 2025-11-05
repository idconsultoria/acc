#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Verificação Pré-Deploy
Verifica se o projeto está pronto para deploy na Vercel
"""

import os
import sys
import json
from pathlib import Path

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Cores para terminal (simplificadas para Windows)
GREEN = '[OK]'
RED = '[X]'
YELLOW = '[!]'
BLUE = '[-]'
RESET = ''

def print_header(text):
    """Imprime cabeçalho colorido"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text.center(60)}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def check_file(filepath, description):
    """Verifica se um arquivo existe"""
    exists = os.path.exists(filepath)
    status = f"{GREEN}✓{RESET}" if exists else f"{RED}✗{RESET}"
    print(f"{status} {description}: {filepath}")
    return exists

def check_directory(dirpath, description):
    """Verifica se um diretório existe"""
    exists = os.path.isdir(dirpath)
    status = f"{GREEN}✓{RESET}" if exists else f"{RED}✗{RESET}"
    print(f"{status} {description}: {dirpath}")
    return exists

def check_json_file(filepath, key_path=None):
    """Verifica se arquivo JSON existe e opcionalmente valida uma chave"""
    if not os.path.exists(filepath):
        return False, "Arquivo não encontrado"
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if key_path:
            keys = key_path.split('.')
            current = data
            for key in keys:
                if key not in current:
                    return False, f"Chave '{key_path}' não encontrada"
                current = current[key]
        
        return True, "OK"
    except json.JSONDecodeError:
        return False, "JSON inválido"
    except Exception as e:
        return False, str(e)

def check_requirements():
    """Verifica se requirements.txt tem todas as dependências necessárias"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'supabase',
        'google-generativeai'
    ]
    
    if not os.path.exists('requirements.txt'):
        return False, []
    
    with open('requirements.txt', 'r') as f:
        content = f.read().lower()
    
    missing = [pkg for pkg in required_packages if pkg not in content]
    
    return len(missing) == 0, missing

def main():
    """Executa todas as verificações"""
    print_header("Verificacao Pre-Deploy - Vercel")
    
    all_checks_passed = True
    
    # 1. Arquivos de Configuração
    print(f"\n{YELLOW}1. Arquivos de Configuração{RESET}")
    checks = [
        ('vercel.json', 'Configuração Vercel'),
        ('requirements.txt', 'Dependências Python (raiz)'),
        ('.gitignore', 'Arquivo gitignore'),
    ]
    
    for filepath, description in checks:
        if not check_file(filepath, description):
            all_checks_passed = False
    
    # 2. Estrutura de Diretórios
    print(f"\n{YELLOW}2. Estrutura de Diretórios{RESET}")
    dirs = [
        ('backend', 'Diretório do Backend'),
        ('frontend', 'Diretório do Frontend'),
        ('api', 'Diretório API (Vercel Handler)'),
    ]
    
    for dirpath, description in dirs:
        if not check_directory(dirpath, description):
            all_checks_passed = False
    
    # 3. Backend
    print(f"\n{YELLOW}3. Backend (Python/FastAPI){RESET}")
    backend_files = [
        ('backend/app/main.py', 'FastAPI Main'),
        ('backend/requirements.txt', 'Requirements Backend'),
        ('api/index.py', 'Vercel Handler'),
    ]
    
    for filepath, description in backend_files:
        if not check_file(filepath, description):
            all_checks_passed = False
    
    # 4. Frontend
    print(f"\n{YELLOW}4. Frontend (React/Vite){RESET}")
    frontend_files = [
        ('frontend/package.json', 'Package.json'),
        ('frontend/vite.config.ts', 'Vite Config'),
        ('frontend/src/main.tsx', 'Main React'),
    ]
    
    for filepath, description in frontend_files:
        if not check_file(filepath, description):
            all_checks_passed = False
    
    # 5. Validar package.json
    print(f"\n{YELLOW}5. Validar Scripts{RESET}")
    pkg_path = 'frontend/package.json'
    valid, msg = check_json_file(pkg_path, 'scripts.build')
    status = f"{GREEN}✓{RESET}" if valid else f"{RED}✗{RESET}"
    print(f"{status} Script 'build' no package.json: {msg}")
    if not valid:
        all_checks_passed = False
    
    # 6. Validar vercel.json
    print(f"\n{YELLOW}6. Validar vercel.json{RESET}")
    vercel_checks = [
        ('builds', 'Seção builds'),
        ('routes', 'Seção routes'),
    ]
    
    for key, description in vercel_checks:
        valid, msg = check_json_file('vercel.json', key)
        status = f"{GREEN}✓{RESET}" if valid else f"{RED}✗{RESET}"
        print(f"{status} {description}: {msg}")
        if not valid:
            all_checks_passed = False
    
    # 7. Requirements.txt
    print(f"\n{YELLOW}7. Dependências Python{RESET}")
    has_all, missing = check_requirements()
    if has_all:
        print(f"{GREEN}✓{RESET} Todas as dependências essenciais estão presentes")
    else:
        print(f"{RED}✗{RESET} Dependências faltando: {', '.join(missing)}")
        all_checks_passed = False
    
    # 8. Git
    print(f"\n{YELLOW}8. Controle de Versão{RESET}")
    is_git_repo = os.path.isdir('.git')
    status = f"{GREEN}✓{RESET}" if is_git_repo else f"{RED}✗{RESET}"
    print(f"{status} Repositório Git inicializado")
    if not is_git_repo:
        print(f"{YELLOW}   ⚠️  Execute: git init{RESET}")
        all_checks_passed = False
    
    # 9. Documentação
    print(f"\n{YELLOW}9. Documentação de Deploy{RESET}")
    docs = [
        ('GUIA_IMPLANTACAO_VERCEL.md', 'Guia completo'),
        ('DEPLOY_CHECKLIST.md', 'Checklist rápido'),
        ('DEPLOY_README.md', 'README visual'),
    ]
    
    for filepath, description in docs:
        check_file(filepath, description)
    
    # Resultado Final
    print_header("Resultado da Verificacao")
    
    if all_checks_passed:
        print(f"{GREEN} TUDO PRONTO PARA DEPLOY!{RESET}\n")
        print("Proximos passos:")
        print(f"  1. {BLUE}git add .{RESET}")
        print(f"  2. {BLUE}git commit -m 'Pronto para deploy'{RESET}")
        print(f"  3. {BLUE}git push origin main{RESET}")
        print(f"  4. {BLUE}Acesse: https://vercel.com/new{RESET}")
        print(f"\nConsulte: {YELLOW}DEPLOY_README.md{RESET} para instrucoes detalhadas\n")
        return 0
    else:
        print(f"{RED} ATENCAO: Alguns itens precisam ser corrigidos{RESET}\n")
        print(f"Por favor, revise os itens marcados com {RED} acima.")
        print(f"\nConsulte: {YELLOW}GUIA_IMPLANTACAO_VERCEL.md{RESET} para ajuda\n")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Verificacao cancelada pelo usuario{RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{RED}Erro durante verificacao: {e}{RESET}")
        sys.exit(1)

