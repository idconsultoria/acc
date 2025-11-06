# GitHub Actions Workflows

## Workflow de Testes (`tests.yml`)

Este workflow executa automaticamente a suíte completa de testes sempre que:

- Um **pull request** é aberto ou atualizado para as branches `main`, `master` ou `develop`
- Um **push** é feito para as branches `main`, `master` ou `develop`

### O que o workflow faz:

1. **Configura o ambiente**
   - Executa em Ubuntu Latest
   - Testa em Python 3.11 e 3.12 (usando matrix strategy)
   - Configura cache do pip para instalações mais rápidas

2. **Instala dependências**
   - Atualiza pip para a versão mais recente
   - Instala todas as dependências do `requirements.txt`

3. **Executa testes**
   - Roda pytest com cobertura completa
   - Gera relatórios em múltiplos formatos:
     - XML (para Codecov)
     - HTML (para visualização)
     - Terminal (para logs do GitHub Actions)

4. **Upload de resultados**
   - **Codecov**: Upload opcional de cobertura (não falha se Codecov não estiver configurado)
   - **Artifacts**: Upload do relatório HTML de cobertura (disponível por 7 dias)

5. **Verificação de cobertura**
   - Verifica se a cobertura mínima de 60% foi atingida
   - Falha o workflow se a cobertura estiver abaixo do mínimo

### Variáveis de Ambiente

O workflow usa variáveis de ambiente para configuração dos testes:

- `SUPABASE_URL`: URL do Supabase (usa valor padrão se não configurado)
- `SUPABASE_KEY`: Chave do Supabase (usa valor padrão se não configurado)
- `SUPABASE_SERVICE_ROLE_KEY`: Chave de serviço do Supabase (usa valor padrão se não configurado)
- `GEMINI_API_KEY`: Chave da API do Gemini (usa valor padrão se não configurado)

**Nota**: Os valores padrão são suficientes para os testes, mas você pode configurar secrets no GitHub para usar valores reais se necessário.

### Como visualizar os resultados:

1. **No GitHub Actions**:
   - Vá para a aba "Actions" no repositório
   - Clique no workflow que foi executado
   - Veja os logs detalhados de cada step

2. **Relatório HTML de Cobertura**:
   - No final do workflow, baixe o artifact "coverage-report-3.11" ou "coverage-report-3.12"
   - Extraia o arquivo e abra `htmlcov/index.html` no navegador

3. **Codecov** (se configurado):
   - Acesse o dashboard do Codecov
   - Veja gráficos de cobertura ao longo do tempo
   - Compare cobertura entre branches

### Configuração de Secrets (Opcional)

Se quiser usar valores reais para testes de integração, configure os seguintes secrets no GitHub:

1. Vá em **Settings** → **Secrets and variables** → **Actions**
2. Adicione os seguintes secrets:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `GEMINI_API_KEY`

**Importante**: Os valores padrão são suficientes para os testes unitários. Secrets são opcionais.

### Status Badge

Para adicionar um badge de status do workflow no README:

```markdown
![Testes](https://github.com/USERNAME/REPO/workflows/Testes/badge.svg)
```

Substitua `USERNAME` e `REPO` pelos valores corretos.
