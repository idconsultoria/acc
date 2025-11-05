# Visão, Domínio e Escopo do MVP

**Arquivo:** `design/1_visao_geral_dominio.md`

**Propósito:** Este é o documento fundamental do projeto. Ele serve como a fonte da verdade para o propósito, escopo, terminologia e princípios de design do sistema. Ele deve alinhar todos os envolvidos — desenvolvedores, designers e stakeholders — em uma visão compartilhada.

**Público-alvo:** Time de Desenvolvimento (Frontend e Backend), Product Owner, Stakeholders.

---

### 1. Visão do Produto

#### 1.1. A Dor: A Cultura que se Perde

Organizações são sistemas vivos com uma identidade única — sua cultura. No entanto, à medida que crescem, adotam o trabalho remoto ou passam por alta rotatividade, essa identidade se dilui. A cultura, que antes era transmitida organicamente, passa a depender de manuais estáticos ou da sobrecarga de "guardiões culturais" (líderes, fundadores, RH), gerando inconsistência, perda de coerência e dependência.

#### 1.2. A Solução: Uma Memória Cultural Conversacional e Coevolutiva

Para resolver essa dor, estamos construindo um **Agente Cultural de IA**. Ele é uma **memória viva e interativa**, treinada com o DNA da organização, que evolui junto com ela. Através de uma **interface de chat**, ele atua como um **conselheiro cultural**, ajudando qualquer colaborador a refletir sobre dilemas do dia a dia.

Crucialmente, o agente **cita suas fontes** (os artefatos culturais), trazendo transparência e permitindo que o usuário se aprofunde no conhecimento. Além disso, o sistema possui um **ciclo de aprendizado**, onde o feedback dos usuários, após validação, é sintetizado e incorporado à base de conhecimento do próprio agente, criando um sistema que aprende e se refina continuamente.

#### 1.3. O Valor Gerado
- **Autonomia com Alinhamento:** Empodera colaboradores a tomarem decisões coerentes.
- **Coerência Escalável:** Garante que a cultura permaneça consistente e acessível.
- **Rastreabilidade e Confiança:** As citações de fontes tornam as respostas da IA auditáveis e confiáveis.
- **Cultura Viva e Coevolutiva:** O ciclo de feedback transforma a cultura de algo estático em um organismo que aprende com a própria organização.

---

### 2. Escopo do MVP (Produto Mínimo Viável)

O objetivo do MVP é validar o ciclo completo: **Ingestão de conhecimento → Consulta conversacional com fontes → Aprendizado a partir de feedback.**

#### 2.1. Funcionalidades INCLUÍDAS no MVP

1.  **Tela de Administração (`/admin`)**:
    *   **CRUD de Artefatos Culturais:** Upload de PDFs e inserção de texto manual. O backend processará os PDFs para extrair texto, dividi-lo em *chunks* (pedaços) e gerar *embeddings* (vetores) para busca semântica.
    *   **Editor da Instrução Geral do Agente:** Uma área de texto destacada para o Guardião Cultural editar a "personalidade" base do agente.
    *   **Painel de Revisão de Feedbacks:** Uma lista de feedbacks pendentes enviados pelos colaboradores. O guardião poderá "Aprovar" ou "Rejeitar" um feedback. A aprovação acionará a síntese de um novo `Aprendizado`.

2.  **Tela de Chat (`/chat`)**:
    *   Interface de chat persistente que mantém o histórico da `Conversa`.
    *   Renderização de respostas do agente em formato **Markdown**.
    *   Exibição de **fontes citadas** junto às respostas, de forma interativa.
    *   Botão de **feedback** em cada mensagem do agente para que o usuário possa enviar comentários.

3.  **Backend e Persistência (Python & Supabase)**:
    *   **API REST** para servir as funcionalidades acima.
    *   **Tabelas no Supabase (PostgreSQL):**
        *   `artifacts`: Metadados dos documentos (título, tipo).
        *   `artifact_chunks`: Pedaços de texto dos artefatos, com seus vetores (`embedding`) para busca com `pgvector`.
        *   `conversations`: Histórico de chats.
        *   `messages`: Mensagens individuais, incluindo fontes citadas.
        *   `pending_feedbacks`: Feedbacks aguardando moderação.
        *   `learnings`: Aprendizados validados, também com vetores para busca.
        *   `agent_settings`: Para armazenar a `InstrucaoGeralAgente`.
    *   **Armazenamento de Arquivos (Supabase Storage):** Para os arquivos PDF originais.

4.  **Lógica de Geração de Conselho (RAG com Gemini 2.5 Flash)**:
    *   O workflow de `ContinuarConversa` irá:
        1.  Receber a nova mensagem do usuário e o ID da conversa.
        2.  Buscar o histórico da conversa.
        3.  Realizar uma busca vetorial nos `artifact_chunks` e `learnings` para encontrar o contexto mais relevante.
        4.  Montar um *System Prompt* dinâmico contendo: a `InstrucaoGeralAgente`, o contexto de artefatos e aprendizados, o histórico da conversa e a nova pergunta.
        5.  Invocar o Gemini 2.5 Flash.
        6.  Processar a resposta para extrair o texto em Markdown e os IDs das fontes citadas.
        7.  Persistir a nova mensagem (do usuário e do agente) no histórico da conversa e retorná-la ao frontend.

#### 2.2. Funcionalidades EXCLUÍDAS do MVP
-   **Sistema de Login e Papéis:** (Simulado por URLs diretas).
-   **Dashboard Analítico Avançado:** (Análise de padrões de uso, métricas de engajamento).
-   **Busca por Filtros na Tela de Chat:** (Filtrar conversas, buscar em chats antigos).
-   **Edição/Exclusão de Mensagens pelo Usuário.**
-   **Processamento Assíncrono em Larga Escala:** (Para o MVP, a ingestão de PDF será síncrona na requisição de upload).

---

### 3. Linguagem Ubíqua (Glossário do Domínio)

| Termo | Definição | Implicações de Implementação | Exemplo (Código/API) |
| :--- | :--- | :--- | :--- |
| **Artefato Cultural** | Fonte primária de conhecimento cultural (documento, texto). | Tabela `artifacts`. A ingestão gera múltiplos `ArtifactChunks`. | `Artifact`, `ArtifactDTO` |
| **Artifact Chunk** | Um pedaço de texto indexável de um Artefato, com seu vetor. | Tabela `artifact_chunks` com coluna `embedding` (tipo `vector`). | `ArtifactChunk`, `chunk_content` |
| **Conversa** | Uma sequência de trocas entre um usuário e o agente. Uma entidade com ciclo de vida. | Tabela `conversations`. Cada `POST /chat/{id}/messages` opera dentro de uma conversa. | `Conversation`, `conversation_id` |
| **Mensagem** | Um único turno em uma `Conversa`. | Tabela `messages` com `conversation_id`, `author` (`'USER'` ou `'AGENT'`), `content`, `cited_artifact_chunk_ids` (array de IDs). | `Message`, `MessageDTO` |
| **Dilema** | A intenção do usuário expressa em uma ou mais `Mensagens`. | O conteúdo das mensagens do usuário. | `dilemma_text` |
| **Conselho Cultural**| A `Mensagem` gerada pelo agente em resposta a um dilema. | O conteúdo da mensagem do agente. O frontend deve renderizar o Markdown e as citações. | `CulturalAdvice`, `advice_content` |
| **Feedback** | Comentário de um usuário sobre uma `Mensagem` específica do agente. | Tabela `pending_feedbacks` com `message_id`, `feedback_text`, `status` (`'PENDING'`). | `Feedback`, `SubmitFeedbackCmd` |
| **Aprendizado** | Um insight conciso e reutilizável, sintetizado a partir de um `Feedback` aprovado. | Tabela `learnings` com `content` e `embedding`. Funciona como um "artefato gerado pelo sistema". | `Learning`, `SynthesizeLearning` |
| **Instrução Geral do Agente**| O prompt de sistema base que define a persona e o comportamento geral do agente. | Tabela `agent_settings` (ou um registro específico). Editável na tela de admin. | `AgentInstruction`, `update_instruction` |
| **Guardião Cultural**| O usuário administrador. | Acessa `/admin`. | `Guardian` |
| **Colaborador** | O usuário final. | Acessa `/chat`. | `Collaborator` |

---

### 4. Princípios Guias do MVP

-   **API First:** O [Contrato da API (OpenAPI)](./3_contrato_api.md) é a fonte da verdade para a comunicação cliente-servidor.
-   **Domínio no Centro (Backend):** A lógica de negócio será implementada em Python puro (funções, `dataclasses`). O I/O (Supabase, Gemini) será isolado nas "bordas" da aplicação, injetado como dependências nos workflows, permitindo testes puros da lógica de domínio.
-   **Rastreabilidade é Confiança:** Cada `Conselho Cultural` deve, sempre que possível, ser rastreável a `Artefatos` ou `Aprendizados` específicos. A UI deve refletir isso.
-   **Coevolução Contínua:** O ciclo de feedback-síntese-aprendizado é uma feature de primeira classe, não um "nice to have". A arquitetura deve suportar este loop desde o início.
-   **Interface Reflexiva:** O design da UI e a `Instrução Geral do Agente` devem sempre guiar o usuário a pensar, não a obedecer. O agente é um copiloto para a reflexão, não um piloto automático para decisões.