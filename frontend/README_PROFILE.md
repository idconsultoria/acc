# 📊 Perfil do Usuário - Guia Rápido

## 🎯 O que foi implementado

Uma view completa de perfil com estatísticas, gráficos e preferências personalizáveis.

## ✨ Recursos Principais

### 1. Informações do Perfil
- Avatar com gradiente
- Nome e email
- Data de ingresso e última atividade
- Botão de edição de perfil

### 2. Estatísticas em Cards
- **Conversas Iniciadas**: Total de diálogos
- **Feedback Dado**: 👍 positivos e 👎 negativos
- **Tempo de Resposta**: Média do agente
- **Tópico Principal**: Tema mais discutido

### 3. Visualizações Gráficas

#### Atividade Semanal 📊
Gráfico de barras mostrando suas interações nos últimos 7 dias

#### Tendência Mensal 📈
Gráfico de linha exibindo o crescimento de conversas ao longo dos meses

#### Distribuição por Tópicos 🎯
Barras de progresso mostrando a porcentagem de conversas por tema

### 4. Preferências ⚙️

**Estilo de Comportamento do Agente:**
- Formal e Objetivo
- Apoiador e Empático ⭐ (padrão)
- Direto e Orientado a Ação

**Exibição de Fontes:**
- Mostrar prévia ao passar o mouse
- Mostrar prévia ao clicar ⭐ (padrão)
- Apenas mostrar link

**Notificações:**
- ✅ Receber resumos semanais por e-mail

## 🎨 Design Responsivo

O layout se adapta automaticamente:

- **📱 Mobile**: Cards empilhados verticalmente
- **💻 Tablet**: Grid de 2 colunas
- **🖥️ Desktop**: Grid de até 4 colunas

## 🚀 Como Acessar

1. Inicie o servidor:
```bash
cd frontend
npm run dev
```

2. Acesse: `http://localhost:5173/profile`

Ou clique em **"Perfil"** no menu lateral da aplicação.

## 📦 Componentes Utilizados

### Shadcn/UI
- ✅ Card
- ✅ Button
- ✅ Avatar
- ✅ Select (novo)
- ✅ Checkbox (novo)
- ✅ Progress (novo)
- ✅ Label
- ✅ Separator

### Recharts
- ✅ BarChart (atividade semanal)
- ✅ LineChart (tendência mensal)

### Lucide Icons
- User, MessageSquare, ThumbsUp, ThumbsDown
- Clock, TrendingUp, Calendar, Mail
- Tag, BarChart3, Activity, Target, Award

## 🎯 Características de Design

✅ **Sem gráficos de pizza** (conforme requisito)  
✅ **Ícones modernos** (lucide-react)  
✅ **Layout responsivo** (mobile-first)  
✅ **Cores consistentes** (tema do projeto)  
✅ **Animações suaves** (transitions CSS)  

## 🔧 Estrutura de Arquivos

```
frontend/src/
├── components/ui/
│   ├── select.tsx        # ✨ Novo
│   ├── checkbox.tsx      # ✨ Novo
│   └── progress.tsx      # ✨ Novo
│
└── views/
    └── ProfileView.tsx   # ✨ Novo
```

## 🌟 Próximos Passos

Para melhorar ainda mais:

1. **Backend**: Criar endpoints de estatísticas agregadas
2. **Edição**: Implementar funcionalidade de editar perfil
3. **Exportação**: Adicionar export de relatórios em PDF
4. **Conquistas**: Sistema de badges e conquistas
5. **Filtros**: Adicionar filtros por período nos gráficos

## 💡 Dicas de Uso

- **Estatísticas**: Atualizadas em tempo real conforme você usa o sistema
- **Gráficos**: Hover nos gráficos para ver valores exatos
- **Preferências**: As mudanças são salvas ao clicar em "Salvar Preferências"
- **Responsivo**: Experimente em diferentes tamanhos de tela!

## 🐛 Troubleshooting

### Servidor não inicia?
```bash
npm install  # Reinstale as dependências
npm run dev  # Inicie novamente
```

### Gráficos não aparecem?
Verifique se a biblioteca `recharts` foi instalada:
```bash
npm list recharts
```

### Erros de TypeScript?
```bash
npm run build  # Compile para verificar erros
```

---

**Desenvolvido com ❤️ usando React, TypeScript, Tailwind CSS, e Shadcn/UI**

