# Documento 5: Guia de Implementação Frontend

**Arquivo:** `design/5_guia_implementacao_frontend.md`

**Propósito:** Fornecer um guia prático para o desenvolvedor frontend construir a interface do usuário (UI) do MVP. O documento detalha as telas, os componentes `shadcn/ui` recomendados, e como o estado da aplicação se conecta aos DTOs definidos no Contrato da API (OpenAPI).

**Público-alvo:** Desenvolvedor Frontend.

---

### 1. Visão Geral da Arquitetura Frontend

-   **Framework:** React com Vite
-   **Linguagem:** TypeScript
-   **Biblioteca de UI:** `shadcn/ui`
-   **Gerenciamento de Estado/Cache de API:** `TanStack Query` (React Query) para gerenciar o estado do servidor (chamadas à API), e `Zustand` para o estado global do cliente (ex: ID da conversa atual).
-   **Roteamento:** `React Router`.
-   **Renderização de Markdown:** `react-markdown` com plugins para GFM (GitHub Flavored Markdown).

### 2. Estrutura de Pastas (Proposta)

```
frontend/src/
├── api/
│   └── client.ts       # Cliente de API configurado (ex: com Axios), gerado a partir do OpenAPI.
├── components/
│   ├── ui/             # Componentes brutos do shadcn/ui.
│   └── shared/         # Componentes reutilizáveis da aplicação (ex: ArtifactCard, ChatMessage).
├── hooks/
│   └── useChat.ts      # Hook customizado para gerenciar a lógica do chat.
├── state/
│   └── store.ts        # Store global do Zustand.
└── views/
    ├── AdminView.tsx   # Tela de administração de artefatos.
    └── ChatView.tsx    # Tela principal de interação com o agente.
```

---

### 3. Detalhamento das Telas (Views)

#### 3.1. Tela de Administração (`/admin`) - `AdminView.tsx`

**Objetivo:** Permitir ao Guardião Cultural gerenciar os Artefatos Culturais.

**Wireframe de Baixa Fidelidade / Layout:**

```
+----------------------------------------------------------------------+
|  Header: "Painel do Guardião Cultural"                               |
+----------------------------------------------------------------------+
|                                                                      |
|  [Seção: Instrução Geral do Agente]                                  |
|  +------------------------------------------------------------------+ |
|  | Label: "Instrução Geral do Agente"                               | |
|  | +--------------------------------------------------------------+ | |
|  | | Textarea com a instrução atual...                            | | |
|  | +--------------------------------------------------------------+ | |
|  |                                                 [Salvar Botão] | |
|  +------------------------------------------------------------------+ |
|                                                                      |
|  [Seção: Artefatos Culturais]                                        |
|  +------------------------------------------------------------------+ |
|  | Título: "Artefatos"                             [Adicionar Botão]| |
|  +------------------------------------------------------------------+ |
|  |                                                                  | |
|  | [Card do Artefato 1]                                             | |
|  | +-----------------------+--------------------------------------+ | |
|  | | Título do Artefato 1  | [Ícone PDF] [Data] [Deletar Botão]   | | |
|  | +-----------------------+--------------------------------------+ | |
|  |                                                                  | |
|  | [Card do Artefato 2]                                             | |
|  | +-----------------------+--------------------------------------+ | |
|  | | Título do Artefato 2  | [Ícone Texto] [Data] [Deletar Botão] | | |
|  | +-----------------------+--------------------------------------+ | |
|  |                                                                  | |
|  +------------------------------------------------------------------+ |
|                                                                      |
+----------------------------------------------------------------------+

[Modal: Adicionar Novo Artefato] (Abre ao clicar em "Adicionar")
+----------------------------------------------------+
| Título do Modal: "Adicionar Novo Artefato"         |
+----------------------------------------------------+
|                                                    |
|  Input: "Título do Artefato"                       |
|                                                    |
|  [Toggle: Texto / Upload de PDF]                   |
|                                                    |
|  Se Texto:                                         |
|  +------------------------------------------------+ |
|  | Textarea: "Conteúdo do Artefato"               | |
|  +------------------------------------------------+ |
|                                                    |
|  Se PDF:                                           |
|  +------------------------------------------------+ |
|  | [Área de Drop de Arquivo ou Botão de Upload]   | |
|  +------------------------------------------------+ |
|                                                    |
|                       [Cancelar Botão] [Enviar Botão] |
+----------------------------------------------------+
```

**Mapeamento de Componentes `shadcn/ui` e Lógica:**

| Elemento da UI | Componente `shadcn/ui` | Lógica / Chamada à API | DTO da API |
| :--- | :--- | :--- | :--- |
| **Header** | `<h1>` (customizado) | - | - |
| **Textarea da Instrução** | `Textarea` | `useQuery(['agent-instruction'], () => api.getAgentInstruction())` para popular. `useMutation(api.updateAgentInstruction)` para salvar. | `AgentInstructionDTO` |
| **Botão Adicionar Artefato**| `Button` | Abre o modal de criação. | - |
| **Lista de Artefatos** | `Card` para cada item | `useQuery(['artifacts'], () => api.listArtifacts())` do React Query. | `Artifact[]` |
| **Botão Deletar Artefato**| `Button` com `variant="destructive"` | `useMutation(api.deleteArtifact)` do React Query, seguido de invalidação do query `['artifacts']`. | - |                                                                
| **Modal de Adição** | `Dialog`, `Input`, `Textarea`, `Label` | `useMutation(api.createArtifact)` do React Query. O `onSubmit` do formulário montará um `FormData` para a requisição `multipart/form-data`. | FormData com `title`, `text_content` ou `file` |
| **[Seção: Painel de Revisão de Feedbacks]** | - | - | - |
| **Lista de Feedbacks Pendentes** | `Card` para cada feedback | `useQuery(['pending-feedbacks'], () => api.listPendingFeedbacks())` do React Query. | `PendingFeedback[]` |
| **Botão Aprovar Feedback** | `Button` com `variant="default"` | `useMutation(api.approveFeedback)` do React Query. Ao aprovar, invalida `['pending-feedbacks']` e `['learnings']`. | - |
| **Botão Rejeitar Feedback** | `Button` com `variant="destructive"` | `useMutation(api.rejectFeedback)` do React Query. Ao rejeitar, invalida `['pending-feedbacks']`. | - |

#### 3.2. Tela de Chat (`/chat`) - `ChatView.tsx`

**Objetivo:** Prover a interface de conversação entre o Colaborador e o Agente Cultural.

**Wireframe de Baixa Fidelidade / Layout:**

```
+----------------------------------------------------------------------+
|  Header: "Conselheiro Cultural" (Logo da Empresa)                    |
+----------------------------------------------------------------------+
|                                                                      |
|  [Área de Scroll com Mensagens]                                      |
|                                                                      |
|  +------------------------------------------------------------------+ |
|  | [Mensagem do Agente - Boas-vindas]                               | |
|  | "Olá! Como posso ajudar você a refletir sobre um dilema hoje?"   | |
|  +------------------------------------------------------------------+ |
|                                                                      |
|  +------------------------------------------------------------------+ |
|  | [Mensagem do Usuário]                                            | |
|  | "Estou com dificuldade em dar um feedback..."                   | |
|  +------------------------------------------------------------------+ |
|                                                                      |
|  +------------------------------------------------------------------+ |
|  | [Mensagem do Agente - Com Citações]                              | |
|  | "Ótima pergunta! Baseado no nosso valor de **'Comunicação...'**" | |
|  |                                                                  | |
|  | Fontes: [Chip: Guia de Valores] [Chip: Manual de Feedback]       | |
|  | [Botão de Feedback 👍 👎]                                        | |
|  +------------------------------------------------------------------+ |
|                                                                      |
|  [Indicador de "Agente está digitando..."]                          |
|                                                                      |
+----------------------------------------------------------------------+
|  [Input de Texto para a Mensagem]                     [Enviar Botão]  |
+----------------------------------------------------------------------+
```

**Mapeamento de Componentes `shadcn/ui` e Lógica:**

| Elemento da UI | Componente `shadcn/ui` | Lógica / Chamada à API | DTO da API |
| :--- | :--- | :--- | :--- |
| **Área de Mensagens** | Componente customizado `ChatMessage` | Mapeia o array de mensagens do estado. Deve ter scroll automático para a última mensagem. | `Message[]` |
| **Mensagem do Agente** | `Card` ou `div` customizado, `Avatar` | Renderiza o `content` usando `react-markdown`. | `Message` |
| **Fontes Citadas** | `Badge` (para os chips), `Tooltip` ou `Popover` | Mapeia o array `cited_sources`. Ao passar o mouse ou clicar, um `Tooltip` pode mostrar o `chunk_content_preview`. | `CitedSource[]` |
| **Botão de Feedback** | `Button` com `variant="ghost"` | Abre um modal/popover para o usuário digitar o feedback sobre a mensagem específica. Ao enviar, usa `useMutation(api.submitFeedback)` com `message_id` e `feedback_text`. | `SubmitFeedbackPayload` |
| **Indicador "Digitando"**| Componente customizado | Fica visível quando a `mutation` de envio de mensagem está em estado `isLoading`. | - |
| **Input de Mensagem** | `Input` ou `Textarea` | Controlado pelo estado local do componente de chat. | - |
| **Botão Enviar** | `Button` | Aciona a `mutation` `useMutation(api.postMessage)`. Desabilitado enquanto uma mensagem está sendo enviada. | `CreateMessagePayload` |

**Gerenciamento do Estado do Chat (`useChat.ts` hook):**

Este hook customizado será o cérebro da tela de chat e encapsulará a lógica complexa:

1.  **Estado da Conversa:**
    *   Usará `Zustand` para armazenar o `conversation_id` atual.
    *   Ao montar a `ChatView`, verificará se já existe um `conversation_id`. Se não, chamará `api.createConversation()` para iniciar uma nova e salvará o ID.
    *   Usará `useQuery(['conversation', conversation_id], () => api.getConversationMessages(conversation_id))` para carregar o histórico de mensagens.

2.  **Envio de Mensagem:**
    *   Exporá uma função `sendMessage` que será chamada pelo componente.
    *   Esta função usará a `mutation` do React Query para chamar `POST /conversations/{id}/messages`.
    *   Gerenciará o estado "otimista": adiciona a mensagem do usuário à lista de mensagens imediatamente, antes mesmo da resposta da API, para uma UX fluida.
    *   Quando a API responder com a mensagem do agente, ela será adicionada à lista, e o query `['conversation', conversation_id]` será invalidado para garantir a consistência.

### 4. Guia para o Desenvolvedor Frontend

1.  **Setup Inicial:** Configure o projeto React/Vite com TypeScript. Instale e configure o `shadcn/ui`.
2.  **Gere o Cliente da API:** Use uma ferramenta como `openapi-typescript-codegen` para gerar um cliente de API TypeScript a partir do arquivo `3_contrato_api.yml`. Isso garantirá que todas as chamadas e tipos de dados estejam alinhados com o backend.
3.  **Construa a Tela de Administração (`/admin`):**
    *   Implemente a UI estática usando os componentes `shadcn/ui` listados.
    *   Integre com o cliente de API usando `TanStack Query` para buscar e deletar artefatos.
    *   Implemente o formulário de upload (lembre-se do `FormData`).
4.  **Construa a Tela de Chat (`/chat`):**
    *   Desenvolva o componente `ChatMessage` que renderiza o Markdown e as `CitedSource`.
    *   Implemente o hook `useChat.ts` para gerenciar todo o ciclo de vida da conversa.
    *   Monte a `ChatView` usando o hook e os componentes.
5.  **Mocking:** Durante o desenvolvimento, se o backend não estiver pronto, use `msw` (Mock Service Worker) ou uma ferramenta similar para interceptar as chamadas de API e retornar dados mockados baseados nos schemas do OpenAPI. Isso permite um desenvolvimento de UI totalmente independente.