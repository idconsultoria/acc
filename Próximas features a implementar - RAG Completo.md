# Próximas features a implementar — RAG Completo

## Issue 1 — Chunking Inteligente e Extração de Metadados

**Objetivo**
- Evoluir o pipeline de ingestão (`backend/app/domain/artifacts/workflows.py`) para produzir chunks semanticamente coerentes, com metadados estruturais persistidos e disponíveis para busca.

**Contexto atual**
- `chunk_text` usa janelas fixas de caracteres e não entende hierarquia de documentos.
- `ArtifactChunk` armazena apenas `content` e `embedding`; os repositórios (`artifacts_repo`, `knowledge_repo`) não suportam metadados.
- A UI de artefatos em `frontend/src/views/AdminView.tsx` não expõe nenhuma visão granular dos chunks.

**Plano de implementação**
- *Modelagem de domínio*
  - Introduzir um novo value object `ChunkMetadata` em `backend/app/domain/artifacts/types.py` contendo campos como `section_title`, `section_level`, `content_type`, `position`, `token_count` e `breadcrumbs` (lista de títulos ancestrais).
  - Estender `ArtifactChunk` para incluir `metadata: ChunkMetadata | None` preservando compatibilidade retroativa (metadados opcionais quando não existentes).
- *Chunking adaptativo*
  - Criar módulo `backend/app/infrastructure/files/structured_chunker.py` com funções: `analyze_structure(text: str) -> list[StructuredBlock]` que identifica headings Markdown, listas numeradas e parágrafos, e `generate_chunks(blocks, max_tokens, overlap_tokens)` que combina blocos mantendo contexto.
  - Atualizar `create_artifact_from_text`/`create_artifact_from_pdf` para usar o novo chunker. Computar tokens via `tiktoken` (adicionar a dependência no `backend/requirements.txt`) ou fallback simples baseado em número de palavras se a lib não estiver disponível.
  - Implementar sobreposição inteligente: reutilizar `position` e garantir que o conteúdo concatenado inclua overlap via neighbors list.
- *Extração de metadados durante parsing*
  - Para PDFs, reabilitar `PDFProcessor.extract_text` com uso opcional de `pymupdf` quando disponível, mas garantir fallback para texto plano. Adicionar método `extract_with_metadata` que devolve pares `(text, attrs)` se o PDF contiver bookmarks.
  - Enriquecer cada chunk com: título da seção mais próxima, nível hierárquico (H1, H2 etc.), tipo (`paragraph`, `bullet`, `quote`, `table`), ordem global e contagem de tokens.
- *Persistência*
  - Adicionar colunas `section_title`, `section_level`, `content_type`, `position`, `token_count`, `breadcrumbs` (JSON) em `artifact_chunks` por nova migration SQL (seguir padrão de `backend/database/migrations`). Atualizar `schema.sql` e migrations auxiliares para Supabase.
  - Atualizar `ArtifactsRepository.save`, `find_by_id`, `save_chunks`, `update_artifact_content` para gravar/carregar `metadata`. Ajustar o tipo de retorno em `KnowledgeRepository` para popular `ArtifactChunk.metadata`.
- *API & UI*
  - Estender DTOs em `backend/app/api/dto.py` e rotas de artefatos para devolver metadados junto ao conteúdo.
  - Adicionar na view e no modal de artefatos a opção de visualizar o texto ou PDF original na íntegra e não remontado dos chunks (verificar alterações necessárias no database/backend)
  - Na UI admin (`AdminView`), adicionar drawer modal que liste chunks com seção, tipo e snippet, permitindo inspeção da segmentação.
  - Exibir breadcrumbs/metadados na visualização de citações (`frontend/src/components/shared/SourceCitation.tsx`).
- *Testes*
  - Cobrir `structured_chunker` com casos de headings aninhados e listas.
  - Ajustar testes em `backend/tests/test_domain_workflows.py` para validar geração de metadados e estabilidade do número de chunks.
  - Criar testes E2E simulando ingestão de texto e validando resposta da API (`tests/test_api_routes.py`).

**Dependências e riscos**
- Necessidade de sincronizar migrations com Supabase (executar manualmente após deploy).
- Tokernização depende de biblioteca externa; definir fallback claro.
- Volume adicional de metadados aumenta tamanho da janela de contexto — mitigado pela Issue 3.

## Issue 2 — Prompt Engineering Profissional

**Objetivo**
- Organizar prompts em templates versionados, inserir exemplos (few-shot), formatos diferenciados para artefatos/aprendizados e embutir metaprompt de autoavaliação antes da resposta final.

**Contexto atual**
- `GeminiService.generate_advice` monta string monolítica com regras fixas e sem exemplos.
- Não há separação entre system prompt, context prompt e user prompt; aprendizados não têm destaque.
- Não existe mecanismo de auto-reflexão ou checagem de citações.

**Plano de implementação**
- *Arquitetura de prompts*
  - Criar módulo `backend/app/domain/agent/prompt_templates.py` com classes `PromptSection` e `PromptTemplate`. Incluir template base com placeholders para instrução, artefatos, aprendizados, histórico, consulta e instruções de metaavaliação.
  - Armazenar exemplos few-shot em JSON (`backend/app/domain/agent/prompt_examples.py`) com estrutura `{user, agent, cited_sources}` para reuso.
  - Definir `PromptRenderer` responsável por aplicar formatação Markdown (ex: `### Fonte 1 — {section_title}`) e por incluir aprendizados com destaque (blockquote, emoji, etc.).
- *Integração com LLM*
  - Refatorar `GeminiService.generate_advice` para usar o builder: `PromptTemplate.build_prompt(...)`. Utilizar streaming nativo (preparação para Issue 4) e separar system prompt (persona + regras), context prompt (artefatos/aprendizados formatados) e user prompt.
  - Inserir few-shots no array `contents` da API Gemini (`model.generate_content` com `messages=[system, example1_user, example1_model, ..., user]`).
  - Acrescentar metaprompt: após gerar a primeira resposta, executar chamada curta `generate_content` com prompt de auto-checagem que valide aderência às fontes e sinalize problemas; se houver ajustes, reescrever resposta final destacando correções.
- *Formatação especial*
  - Implementar função `format_artifact_chunk(chunk)` que inclui título, tipo, resumo (primeiras N frases) e ID da fonte.
  - Diferenciar aprendizados: agrupar por peso (Issue 5) e prefixar com `🧠 Insight Relevante`.
- *Persistência / Configuração*
  - Permitir versionamento do prompt (coluna `prompt_version` em `agent_settings`). Atualizar `AgentSettingsRepository` para salvar versão corrente e expor via API.
- *Testes*
  - Criar testes unitários para `PromptTemplate` validando presença de seções e placeholders.
  - Adicionar teste de integração (mock Gemini) verificando que `generate_advice` envia mensagens com few-shots e aplica metaprompt.
- *Documentação*
  - Atualizar `design/5_guia_implementacao_frontend.md` com novo contrato de system prompt.

**Dependências e riscos**
- Chamadas adicionais ao Gemini (auto-reflexão) aumentam latência e custo; configurar flag `ENABLE_SELF_REFLECTION` para desligar quando necessário.
- Precisamos confirmar limites de tokens do modelo para acomodar few-shots + contexto.

## Issue 3 — Gestão de Janela de Contexto

**Objetivo**
- Permitir fixar artefatos/aprendizados na janela, visualizar contexto ativo e gerenciar orçamento de tokens por conversa, persistindo preferências do usuário.

**Contexto atual**
- `continue_conversation` recebe todos os chunks retornados pela busca sem distinção.
- Não existe UI para o usuário priorizar fontes.
- As configurações por conversa não são persistidas (`ConversationsRepository` só grava mensagens/tópico).

**Plano de implementação**
- *Modelagem*
  - Criar entidade `ContextSlot` com campos `conversation_id`, `item_type` (`CHUNK` | `LEARNING`), `item_id`, `is_pinned`, `manual_weight`, `created_at`.
  - Adicionar tabela `conversation_context_slots` via migration PostgreSQL e Supabase.
- *Backend*
  - Implementar workflow `manage_context_window` em `backend/app/domain/conversations/workflows.py` (ou novo módulo) que receba: chunks candidatos, aprendizados, slots persistidos e orçamento de tokens. Função deve ordenar itens (`pinned` > `re-ranking score`) e retornar subconjunto dentro do limite.
  - Atualizar `KnowledgeRepository.find_relevant_knowledge` para aceitar parâmetro opcional `exclude_ids` (evitar duplicar itens já pinados) e retornar score bruto para combinação.
  - Adicionar novo repositório `ConversationContextRepository` em `backend/app/infrastructure/persistence` para CRUD dos slots.
  - Expor rotas REST (`/conversations/{id}/context`) em `backend/app/api/routes/conversations.py` para listar itens ativos, fixar/desfixar, definir pesos manuais e atualizar orçamento máximo (armazenar em nova coluna `context_token_budget` na tabela `conversations`).
  - Integrar `continue_conversation`: antes da chamada ao LLM, compor contexto com `ContextManager`, garantindo que itens pinados entrem primeiro e registrando o conjunto usado (salvar log em `conversation_context_slots` ou tabela auxiliar `context_usage_history`).
- *Frontend*
  - Criar componente `ContextPanel` exibido em `ChatView` (coluna lateral ou drawer) com: lista de artefatos relevantes, indicadores de token, botões de `Pin`/`Unpin`, slider para orçamento de tokens e reorder por drag-and-drop (biblioteca `@dnd-kit/core`).
  - Atualizar `api/client.ts` com novos métodos (`getConversationContext`, `pinContextItem`, `updateContextBudget`).
- *Persistência cliente*
  - `zustand` store (`frontend/src/state/store.ts`) precisa guardar `contextSettings` por conversa para resposta otimista.
- *Testes*
  - Novos testes backend validando priorização de slots e respeito ao orçamento.
  - Testes de integração na API (mock) assegurando que pinar um item reflete na próxima resposta.
  - Testes de interface (React Testing Library) para `ContextPanel`.

**Dependências e riscos**
- UI mais complexa aumenta superfície de estados; garantir loaders e mensagens quando SSE (Issue 4) estiver ativo.
- Precisamos controlar concorrência: múltiplos clientes alterando o mesmo contexto simultaneamente.

## Issue 4 — Streaming de Respostas + Visualização de Etapas

**Objetivo**
- Entregar respostas em tempo real (token por token) e expor progresso das fases do RAG no backend e frontend.

**Contexto atual**
- A rota `POST /conversations/{id}/messages` aguarda todo o processamento e retorna uma única `MessageDTO`.
- `ChatView` simula typing indicator com estado local, sem eventos de backend.
- `GeminiService` usa `generate_content` síncrono.

**Plano de implementação**
- *Backend — SSE*
  - Adicionar dependência `sse-starlette`. Criar rota `POST /conversations/{id}/messages/stream` que retorne `EventSourceResponse` emitindo eventos:
    1. `phase:start` (payload com fases: `embedding`, `retrieval`, `prompt_build`, `llm_stream`, `post_process`).
    2. `phase:update` com percentuais e metadados (ex: número de chunks selecionados).
    3. `token` emitido a cada fragmento do LLM.
    4. `phase:complete` para cada etapa.
    5. `message:complete` com payload final (mensagem, citações, IDs).
  - Refatorar `continue_conversation` para aceitar callback assíncrono de progresso (`ProgressEmitter`) e retornar gerador assíncrono quando streaming estiver habilitado. Manter versão atual para compatibilidade.
  - Atualizar `GeminiService` para usar `self.model.generate_content_async(..., stream=True)`, iterar sobre `response` e emitir tokens via callback. Realizar buffering para reconstruir texto final.
  - Garantir persistência incremental: salvar mensagens somente após evento `message:complete` para evitar registros parciais.
- *Frontend — consumo de SSE*
  - Adicionar utilitário `createEventSource` em `frontend/src/api/client.ts` que usa `EventSource` (browser) ou `fetch` com `ReadableStream` (fallback).
  - Em `ChatView`, criar estado `streamingMessage` atualizado com tokens recebidos. Substituir `useMutation` atual por hook custom `useStreamedMessage` que abre SSE, lida com reconexões e normaliza eventos.
  - Implementar componente `RagPipelineTimeline` (cards horizontais) mostrando status de cada fase com base nos eventos `phase:*`.
  - Permitir que usuário acompanhe progressão no chat (exibir tokens gradualmente no balão do agente).
- *Observabilidade*
  - Acrescentar logs estruturados (JSON) por fase em `GeminiService` e `KnowledgeRepository` para facilitar troubleshooting (incluindo tempos).
- *Testes*
  - Testes unitários simulando `ProgressEmitter` (mocks) para garantir ordem correta dos eventos.
  - Teste end-to-end com `pytest` usando `asyncio` e `httpx.AsyncClient` validando SSE.
  - Testes front-end (Cypress ou Playwright) para garantir que timeline reage aos eventos.

**Dependências e riscos**
- Streaming do Gemini requer quota/comportamento específico; validar limites e timeouts.
- SSE não é suportado por todos os ambientes serverless; avaliar se Cloud Run/Supabase Edge suportam e documentar fallback (exibir mensagem se streaming desabilitado).

## Issue 5 — Sistema de Aprendizados Aprimorado

**Objetivo**
- Refinar a gestão dos aprendizados aprovados, com pesos dinâmicos (recência, relevância), formatação no prompt e ferramentas de administração para merge/deduplicação.

**Contexto atual**
- `synthesize_learning_from_feedback` salva aprendizados sem pesos.
- `KnowledgeRepository` retorna os três mais próximos apenas por similaridade de embedding.
- Não há interface dedicada para revisar/mesclar aprendizados; UI depende da aba de feedbacks.

**Plano de implementação**
- *Modelagem*
  - Estender `Learning` com campos opcionais `relevance_weight: float` e `last_used_at: datetime`. Ajustar dataclass e migrations (`learnings` table).
  - Criar entidade `LearningMergeCandidate` para facilitar deduplicação.
- *Backend*
  - Atualizar `LearningsRepository` para persistir novos campos e expor métodos `update_weights` e `merge(learnings_ids, merged_content)` (executa soft-delete + criação de novo registro).
  - Em `synthesize_learning_from_feedback`, calcular peso inicial com base em tipo de feedback (`POSITIVE` vs `NEGATIVE`) e similaridade com aprendizados existentes (reuso do re-ranking da Issue 6).
  - Implementar serviço `LearningWeighter` que periodicamente (cron/worker) recalcula pesos usando fórmula: `weight = base + recency_decay + feedback_signal`. Para esta fase, expor endpoint manual `/learnings/recalculate` protegido via API Key.
  - Atualizar `KnowledgeRepository.find_relevant_knowledge` para ordenar aprendizados pela pontuação combinada (embedding + `relevance_weight`) e atualizar `last_used_at` após uso.
- *Frontend Admin*
  - Criar nova tela `AdminLearningsView.tsx` (link no `AdminSidebar`) listando aprendizados com peso, data, fonte. Incluir botões para `Editar`, `Mesclar`, `Remover duplicados`.
  - Implementar modais para merge: selecionar múltiplos aprendizados, editar texto resultante e enviar para endpoint `/learnings/merge`.
  - Ajustar `PromptTemplate` (Issue 2) para exibir aprendizados ordenados por peso e com formatação diferenciada.
- *Deduplicação*
  - Adicionar endpoint `POST /learnings/deduplicate` que usa embeddings + similaridade coseno > threshold para sugerir merges; retornar candidatos para UI confirmar.
- *Testes*
  - Expandir `backend/tests/test_domain_workflows.py` com cenários de pesos.
  - Testes para `LearningsRepository` garantindo que merges preservem `source_feedback_id` em histórico (armazenar em tabela `learning_merge_history`).
  - Tests React para `AdminLearningsView` (renderização e ações principais).

**Dependências e riscos**
- Ajustar políticas de Supabase para permitir updates de colunas adicionais.
- Merge manual exige auditoria; manter histórico e permitir rollback.

## Issue 6 — Melhorias de Qualidade do RAG

**Objetivo**
- Aumentar precisão das respostas via re-ranking, citações corretas e estratégia de fallback quando a busca vetorial não retornar contexto útil.

**Contexto atual**
- `KnowledgeRepository` retorna top-N por similaridade bruta sem re-ranking contextual.
- `GeminiService` assume que todos os chunks retornados foram usados e cita tudo indiscriminadamente.
- Não há fallback quando a busca falha; modelo responde sem referências.

**Plano de implementação**
- *Re-ranking*
  - Introduzir serviço `CrossEncoderReRanker` (`backend/app/infrastructure/ai/reranker.py`) usando modelo leve (ex: `voyageai` ou `sentence-transformers` via API). Interface `ReRanker.score(query, candidates)`.
  - Atualizar `KnowledgeRepository` para chamar re-ranker após busca vetorial, combinando score de similaridade com score cross-encoder. Retornar campo `relevance_score` em `RelevantKnowledge` para uso posterior.
- *Citação inteligente*
  - Modificar `GeminiService.generate_advice` para acompanhar `chunk_index` em tempo real: durante streaming, analisar tokens e procurar padrão `Fonte X`. Após completar resposta, mapear marcadores às fontes corretas (usando regex e ordem de menção). Retornar apenas chunks realmente citados.
  - Atualizar `continue_conversation` para preencher `CitedSource.title` com título real do artefato (usar `ArtifactsRepository.get_artifact_data`).
  - No front, alterar `SourceCitation` para exibir número da fonte e tooltip com seção/tipo (Issue 1).
- *Fallback strategy*
  - Implementar verificação de confiança: se `relevance_score` médio < threshold ou não houver chunks, enviar prompt alternativo para Gemini enfatizando que não há fontes suficientes e solicitando resposta genérica com disclaimers.
  - Registrar evento `knowledge:fallback` em logs e retornar flag `used_fallback` para exibirmos aviso na UI.
  - Na UI (`ChatView`), se fallback for usado, mostrar `Alert` informando que não houve fontes citadas.
- *Testes*
  - Criar casos de teste para re-ranking (mock re-ranker) garantindo ordenação correta.
  - Testar citação inteligente com resposta que não cita todos os chunks.
  - Testar fallback (mock `KnowledgeRepository` retornando vazio) e validar mensagem de alerta no front.

**Dependências e riscos**
- Re-ranker externo pode aumentar latência; prever cache na aplicação e opção de desativação (`settings_repo`).
- Parsing de citações precisa ser robusto a variações (usar regex flexível e fallback manual).


