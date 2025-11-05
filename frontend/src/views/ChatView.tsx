import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { api, ConversationTopic } from '../api/client'
import { useStore } from '../state/store'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Send, ThumbsUp, ThumbsDown, Bot, Loader2, Tag, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import Sidebar from '@/components/shared/Sidebar'
import SourceCitation from '@/components/shared/SourceCitation'
import { cn } from '@/lib/utils'

function ChatView() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { conversationId, setConversationId } = useStore()
  const [input, setInput] = useState('')
  const [showFeedbackModal, setShowFeedbackModal] = useState<string | null>(null)
  const [feedbackText, setFeedbackText] = useState('')
  const [existingFeedback, setExistingFeedback] = useState<{ id: string; text: string } | null>(null)
  const [pendingUserMessage, setPendingUserMessage] = useState<string | null>(null)
  const [messageFeedbacks, setMessageFeedbacks] = useState<Record<string, 'POSITIVE' | 'NEGATIVE'>>({})
  const [detailedFeedbacks, setDetailedFeedbacks] = useState<Record<string, string>>({}) // message_id -> feedback_id
  const [initializingFeedbacks, setInitializingFeedbacks] = useState<Set<string>>(new Set())
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()
  const isInitialLoadRef = useRef(true)
  const previousConversationIdRef = useRef<string | null>(null)

  // Verifica se há um parâmetro de conversa na URL
  useEffect(() => {
    const urlConversationId = searchParams.get('conversation')
    if (urlConversationId && urlConversationId !== conversationId) {
      // Atualiza o store com o ID da URL
      setConversationId(urlConversationId)
      // Remove o parâmetro da URL para limpar a barra de endereços
      setSearchParams({}, { replace: true })
      // Reseta o flag de carregamento inicial para rolar até o final
      isInitialLoadRef.current = true
    }
  }, [searchParams, conversationId, setConversationId, setSearchParams])

  // Detecta mudança de conversa e limpa estados
  useEffect(() => {
    if (conversationId && previousConversationIdRef.current !== conversationId) {
      // Limpa estados de feedback quando muda de conversa
      setMessageFeedbacks({})
      setDetailedFeedbacks({})
      setPendingUserMessage(null)
      setShowFeedbackModal(null)
      setFeedbackText('')
      setExistingFeedback(null)
      setInitializingFeedbacks(new Set())
    }
  }, [conversationId])


  // Cria ou busca conversa
  useEffect(() => {
    if (!conversationId) {
      api.createConversation().then((data) => {
        setConversationId(data.conversation_id)
      })
    }
  }, [conversationId, setConversationId])

  // Envia mensagem
  const sendMessageMutation = useMutation({
    mutationFn: async (content: string) => {
      if (!conversationId) throw new Error('Conversa não encontrada')
      // Adiciona a mensagem do usuário imediatamente (optimistic update)
      setPendingUserMessage(content)
      return api.postMessage(conversationId, content)
    },
    onSuccess: () => {
      // Remove a mensagem pendente e atualiza a lista de mensagens
      setPendingUserMessage(null)
      queryClient.invalidateQueries({ queryKey: ['conversation', conversationId] })
      // Invalida também a query do tópico para buscar novamente
      queryClient.invalidateQueries({ queryKey: ['conversation-topic', conversationId] })
      setInput('')
    },
    onError: () => {
      // Remove a mensagem pendente em caso de erro
      setPendingUserMessage(null)
    },
  })

  // Busca mensagens
  const { data: messages = [], isLoading: isLoadingMessages } = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => conversationId ? api.getConversationMessages(conversationId) : Promise.resolve([]),
    enabled: !!conversationId,
    refetchInterval: sendMessageMutation.isPending ? 1000 : false,
  })

  // Atualiza o ref quando as mensagens são carregadas ou na primeira montagem
  useEffect(() => {
    if (!isLoadingMessages && conversationId) {
      if (previousConversationIdRef.current !== conversationId) {
        previousConversationIdRef.current = conversationId
      }
    }
    // Inicializa o ref na primeira montagem se não houver conversa anterior
    if (conversationId && previousConversationIdRef.current === null && !isLoadingMessages) {
      previousConversationIdRef.current = conversationId
    }
  }, [isLoadingMessages, conversationId])

  // Busca feedbacks existentes para as mensagens do agente
  useEffect(() => {
    const agentMessages = messages.filter(msg => msg.author === 'AGENT')
    const fetchFeedbacks = async () => {
      const messagesToFetch = agentMessages.filter(msg => !detailedFeedbacks[msg.id] && !messageFeedbacks[msg.id])
      
      // Marca mensagens como inicializando
      if (messagesToFetch.length > 0) {
        setInitializingFeedbacks(prev => {
          const newSet = new Set(prev)
          messagesToFetch.forEach(msg => newSet.add(msg.id))
          return newSet
        })
      }
      
      const feedbackPromises = messagesToFetch.map(async (msg) => {
        try {
          const feedback = await api.getFeedbackByMessageId(msg.id)
          return { messageId: msg.id, feedback }
        } catch (error) {
          return { messageId: msg.id, feedback: null }
        }
      })
      
      const results = await Promise.all(feedbackPromises)
      results.forEach(({ messageId, feedback }) => {
        if (feedback) {
          if (feedback.feedback_type === 'POSITIVE' || feedback.feedback_type === 'NEGATIVE') {
            setMessageFeedbacks(prev => {
              if (prev[messageId]) return prev
              return { ...prev, [messageId]: feedback.feedback_type as 'POSITIVE' | 'NEGATIVE' }
            })
          } else {
            setDetailedFeedbacks(prev => {
              if (prev[messageId]) return prev
              return { ...prev, [messageId]: feedback.id }
            })
          }
        }
        // Remove da lista de inicialização
        setInitializingFeedbacks(prev => {
          const newSet = new Set(prev)
          newSet.delete(messageId)
          return newSet
        })
      })
    }
    
    if (agentMessages.length > 0) {
      fetchFeedbacks()
    }
  }, [messages, detailedFeedbacks, messageFeedbacks])

  // Verifica se há mensagens do agente (primeira resposta já foi dada)
  const hasAgentResponse = messages.some(msg => msg.author === 'AGENT')

  // Busca o tópico da conversa
  const { data: conversationTopic } = useQuery<ConversationTopic>({
    queryKey: ['conversation-topic', conversationId],
    queryFn: () => conversationId ? api.getConversationTopic(conversationId) : Promise.resolve({ topic: null, is_processing: false }),
    enabled: !!conversationId && hasAgentResponse,
    refetchInterval: (query) => {
      // Refaz a busca enquanto estiver processando
      const data = query.state?.data
      return data?.is_processing ? 2000 : false
    },
  })

  // Remove mensagem pendente se já existe no servidor
  useEffect(() => {
    if (pendingUserMessage && messages.length > 0) {
      // Verifica se a última mensagem do usuário do servidor corresponde à pendente
      const lastUserMessage = messages.filter(m => m.author === 'USER').pop()
      if (lastUserMessage && lastUserMessage.content === pendingUserMessage) {
        // Se a mensagem já chegou do servidor, remove a pendente
        setPendingUserMessage(null)
      }
    }
  }, [messages, pendingUserMessage])

  // Combina mensagens do servidor com mensagem pendente do usuário
  const displayMessages = [...messages]
  if (pendingUserMessage) {
    // Verifica se a mensagem pendente já não está nas mensagens do servidor
    const messageExists = messages.some(
      m => m.author === 'USER' && m.content === pendingUserMessage
    )
    if (!messageExists) {
      // Adiciona a mensagem pendente do usuário no final
      displayMessages.push({
        id: 'pending',
        conversation_id: conversationId || '',
        author: 'USER' as const,
        content: pendingUserMessage,
        cited_sources: [],
        created_at: new Date().toISOString(),
      })
    }
  }

  // Função para verificar se o usuário está no final do scroll
  const isAtBottom = (): boolean => {
    if (!scrollContainerRef.current) return true
    const container = scrollContainerRef.current
    const threshold = 100 // pixels de tolerância
    return container.scrollHeight - container.scrollTop - container.clientHeight < threshold
  }

  // Scroll automático - só rola se:
  // 1. É o carregamento inicial da conversa
  // 2. Uma mensagem do agente chegou E o usuário está no final
  useEffect(() => {
    if (!messagesEndRef.current || !scrollContainerRef.current) return

    // Sempre rola no carregamento inicial
    if (isInitialLoadRef.current && messages.length > 0) {
      messagesEndRef.current.scrollIntoView({ behavior: 'auto' })
      isInitialLoadRef.current = false
      return
    }

    // Verifica se há uma nova mensagem do agente
    const lastMessage = displayMessages[displayMessages.length - 1]
    const isNewAgentMessage = lastMessage?.author === 'AGENT'

    // Só rola se:
    // - É uma nova mensagem do agente E o usuário está no final
    // - Ou está enviando uma mensagem (para rolar quando a resposta do agente chegar)
    if (isNewAgentMessage && (isAtBottom() || sendMessageMutation.isPending)) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [displayMessages, sendMessageMutation.isPending])

  // Marca que é carregamento inicial quando a conversa muda
  useEffect(() => {
    if (conversationId) {
      isInitialLoadRef.current = true
    }
  }, [conversationId])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !conversationId || sendMessageMutation.isPending) return
    sendMessageMutation.mutate(input)
  }

  // Busca feedback existente quando abre o modal
  const { data: existingFeedbackData } = useQuery({
    queryKey: ['feedback-by-message', showFeedbackModal],
    queryFn: () => showFeedbackModal ? api.getFeedbackByMessageId(showFeedbackModal) : Promise.resolve(null),
    enabled: !!showFeedbackModal,
  })

  // Atualiza estado quando feedback existente é carregado
  useEffect(() => {
    if (existingFeedbackData && showFeedbackModal) {
      setExistingFeedback({ id: existingFeedbackData.id, text: existingFeedbackData.feedback_text })
      setFeedbackText(existingFeedbackData.feedback_text)
      setDetailedFeedbacks(prev => ({
        ...prev,
        [showFeedbackModal]: existingFeedbackData.id
      }))
    } else if (showFeedbackModal && !existingFeedbackData) {
      setExistingFeedback(null)
      setFeedbackText('')
    }
  }, [existingFeedbackData, showFeedbackModal])

  // Envia feedback
  const submitFeedbackMutation = useMutation({
    mutationFn: async ({ messageId, feedbackText, feedbackType }: { messageId: string; feedbackText: string; feedbackType?: 'POSITIVE' | 'NEGATIVE' | null }) => {
      return api.submitFeedback(messageId, feedbackText, feedbackType)
    },
    onSuccess: (data, variables) => {
      setShowFeedbackModal(null)
      setFeedbackText('')
      setExistingFeedback(null)
      // Estado já foi atualizado otimisticamente, apenas confirma
      if (variables.feedbackType !== 'POSITIVE' && variables.feedbackType !== 'NEGATIVE') {
        // Feedback detalhado - atualiza com ID real
        setDetailedFeedbacks(prev => ({
          ...prev,
          [variables.messageId]: data.id
        }))
      }
    },
    onError: (error: any, variables) => {
      // Reverte mudanças otimistas em caso de erro
      if (variables.feedbackType === 'POSITIVE' || variables.feedbackType === 'NEGATIVE') {
        setMessageFeedbacks(prev => {
          const newState = { ...prev }
          delete newState[variables.messageId]
          return newState
        })
      }
      console.error('Erro ao enviar feedback:', error)
    },
  })

  // Atualiza feedback
  const updateFeedbackMutation = useMutation({
    mutationFn: async ({ feedbackId, feedbackText }: { feedbackId: string; feedbackText: string }) => {
      return api.updateFeedback(feedbackId, feedbackText, null)
    },
    onSuccess: () => {
      setShowFeedbackModal(null)
      setFeedbackText('')
      setExistingFeedback(null)
    },
    onError: (error: any) => {
      console.error('Erro ao atualizar feedback:', error)
    },
  })

  // Deleta feedback
  const deleteFeedbackMutation = useMutation({
    mutationFn: async (feedbackId: string) => {
      return api.deleteFeedback(feedbackId)
    },
    onSuccess: (_, feedbackId) => {
      // Remove do estado de feedbacks detalhados
      const messageId = Object.keys(detailedFeedbacks).find(key => detailedFeedbacks[key] === feedbackId)
      if (messageId) {
        setDetailedFeedbacks(prev => {
          const newState = { ...prev }
          delete newState[messageId]
          return newState
        })
        // Também limpa feedbacks de thumbs se existir
        setMessageFeedbacks(prev => {
          const newState = { ...prev }
          delete newState[messageId]
          return newState
        })
      }
      setShowFeedbackModal(null)
      setFeedbackText('')
      setExistingFeedback(null)
    },
    onError: (error: any) => {
      console.error('Erro ao deletar feedback:', error)
    },
  })

  const handleFeedbackSubmit = async (messageId: string) => {
    if (existingFeedback) {
      // Atualiza feedback existente
      if (!feedbackText.trim()) {
        alert('Por favor, digite seu feedback antes de salvar.')
        return
      }
      updateFeedbackMutation.mutate({ feedbackId: existingFeedback.id, feedbackText })
    } else {
      // Cria novo feedback
      if (!feedbackText.trim()) {
        alert('Por favor, digite seu feedback antes de enviar.')
        return
      }
      // Remove feedback anterior se existir (thumbs up/down)
      await deleteExistingFeedback(messageId)
      submitFeedbackMutation.mutate({ messageId, feedbackText, feedbackType: null })
    }
  }

  const handleDeleteFeedback = () => {
    if (existingFeedback && confirm('Tem certeza que deseja excluir este feedback?')) {
      deleteFeedbackMutation.mutate(existingFeedback.id)
    }
  }

  // Função helper para deletar feedback existente de uma mensagem
  const deleteExistingFeedback = async (messageId: string): Promise<string | null> => {
    try {
      const feedback = await api.getFeedbackByMessageId(messageId)
      if (feedback) {
        await api.deleteFeedback(feedback.id)
        // Limpa estados
        setMessageFeedbacks(prev => {
          const newState = { ...prev }
          delete newState[messageId]
          return newState
        })
        setDetailedFeedbacks(prev => {
          const newState = { ...prev }
          delete newState[messageId]
          return newState
        })
        return feedback.id
      }
    } catch (error) {
      // Ignora erros (feedback pode não existir)
    }
    return null
  }

  const handleThumbsUp = async (messageId: string) => {
    // Se já está ativo, remove (toggle)
    if (messageFeedbacks[messageId] === 'POSITIVE') {
      await deleteExistingFeedback(messageId)
      return
    }
    
    // Remove feedback anterior se existir
    await deleteExistingFeedback(messageId)
    
    // Atualiza estado imediatamente (otimista)
    setMessageFeedbacks(prev => ({ ...prev, [messageId]: 'POSITIVE' }))
    setDetailedFeedbacks(prev => {
      const newState = { ...prev }
      delete newState[messageId]
      return newState
    })
    
    // Cria novo feedback positivo
    submitFeedbackMutation.mutate({ 
      messageId, 
      feedbackText: 'Feedback positivo (thumbs up)', 
      feedbackType: 'POSITIVE' 
    })
  }

  const handleThumbsDown = async (messageId: string) => {
    // Se já está ativo, remove (toggle)
    if (messageFeedbacks[messageId] === 'NEGATIVE') {
      await deleteExistingFeedback(messageId)
      return
    }
    
    // Remove feedback anterior se existir
    await deleteExistingFeedback(messageId)
    
    // Atualiza estado imediatamente (otimista)
    setMessageFeedbacks(prev => ({ ...prev, [messageId]: 'NEGATIVE' }))
    setDetailedFeedbacks(prev => {
      const newState = { ...prev }
      delete newState[messageId]
      return newState
    })
    
    // Cria novo feedback negativo
    submitFeedbackMutation.mutate({ 
      messageId, 
      feedbackText: 'Feedback negativo (thumbs down)', 
      feedbackType: 'NEGATIVE' 
    })
  }

  const handleOpenFeedbackModal = async (messageId: string) => {
    // Se já tem feedback detalhado, abre modal para editar (não remove)
    if (detailedFeedbacks[messageId]) {
      // Se o modal já está aberto para esta mensagem, fecha
      if (showFeedbackModal === messageId) {
        setShowFeedbackModal(null)
        setFeedbackText('')
        setExistingFeedback(null)
        return
      }
      // Abre modal para editar feedback existente
      setShowFeedbackModal(messageId)
      return
    }
    
    // Se o modal já está aberto para esta mensagem, fecha
    if (showFeedbackModal === messageId) {
      setShowFeedbackModal(null)
      setFeedbackText('')
      setExistingFeedback(null)
      return
    }
    
    // Remove feedback anterior se existir (thumbs up/down)
    await deleteExistingFeedback(messageId)
    
    // Abre modal para novo feedback
    setShowFeedbackModal(messageId)
  }

  // Função para formatar timestamp
  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })
  }

  // Função para renderizar conteúdo com citações inline
  const renderContentWithCitations = (content: string, citedSources: typeof messages[0]['cited_sources']) => {
    // Processa o conteúdo para encontrar referências a fontes
    // Por enquanto, renderiza o markdown normalmente e adiciona as citações no final
    return (
      <div className="text-gray-800 dark:text-gray-300 text-base font-normal leading-relaxed space-y-4">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            p: ({ children }) => <p className="mb-2">{children}</p>,
            ul: ({ children }) => <ul className="list-disc pl-5 space-y-2 mb-2">{children}</ul>,
            li: ({ children }) => <li className="mb-1">{children}</li>,
            strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
          }}
        >
          {content}
        </ReactMarkdown>
        {citedSources.length > 0 && (
          <div className="flex flex-wrap gap-1 items-center">
            {citedSources.map((source, idx) => (
              <SourceCitation key={idx} source={source} />
            ))}
          </div>
        )}
      </div>
    )
  }

  const hasWelcomeMessage = displayMessages.length === 0 && !pendingUserMessage && !isLoadingMessages
  const showTypingIndicator = sendMessageMutation.isPending
  // Detecta se está mudando de conversa (carregando mensagens de uma conversa diferente)
  // Só mostra skeletons se há uma conversa válida, está carregando, e mudou de conversa
  const isChangingConversation = isLoadingMessages && 
    conversationId && 
    previousConversationIdRef.current !== null && 
    previousConversationIdRef.current !== conversationId

  // Componente de skeleton para mensagens
  const MessageSkeleton = ({ isAgent }: { isAgent: boolean }) => (
    <div className={cn("flex gap-4", isAgent ? "" : "items-end justify-end")}>
      {isAgent ? (
        <>
          <Avatar className="size-10 shrink-0">
            <AvatarFallback className="bg-gradient-to-br from-blue-500 via-purple-500 to-blue-600 text-white shadow-lg ring-2 ring-blue-400/50">
              <Bot className="h-5 w-5 text-white" strokeWidth={2.5} />
            </AvatarFallback>
          </Avatar>
          <div className="flex flex-1 flex-col items-start gap-2">
            <div className="flex flex-col gap-2 rounded-lg bg-card p-4 border border-border w-full">
              <div className="flex flex-wrap items-center gap-3">
                <Skeleton className="h-5 w-40" />
                <Skeleton className="h-4 w-20" />
              </div>
              <div className="space-y-2 mt-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
                <Skeleton className="h-4 w-4/6" />
              </div>
            </div>
            <div className="flex flex-wrap gap-2 px-2">
              <Skeleton className="h-8 w-8 rounded" />
              <Skeleton className="h-8 w-8 rounded" />
              <Skeleton className="h-8 w-8 rounded" />
            </div>
          </div>
        </>
      ) : (
        <>
          <div className="flex flex-col gap-1 items-end">
            <Skeleton className="h-4 w-16" />
            <div className="flex flex-col gap-2 rounded-lg bg-card p-4 border border-border max-w-[80%]">
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
              </div>
            </div>
          </div>
          <Avatar className="size-10 shrink-0">
            <AvatarFallback className="bg-primary">
              <span className="text-sm font-medium">V</span>
            </AvatarFallback>
          </Avatar>
        </>
      )}
    </div>
  )

  return (
    <div className="flex h-screen w-full">
      <Sidebar />

      {/* Main Chat Area */}
      <main className="flex flex-1 flex-col h-screen">
        {/* Topic Badge */}
        {hasAgentResponse && (conversationTopic?.is_processing || conversationTopic?.topic) && (
          <div className="px-6 pt-4 pb-2 border-b border-border">
            <div className="mx-auto max-w-4xl">
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/50 border border-border">
                <Tag className="h-4 w-4 text-muted-foreground shrink-0" />
                {conversationTopic?.is_processing ? (
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-3 w-3 text-muted-foreground animate-spin" />
                    <span className="text-sm text-muted-foreground">Classificando conversa...</span>
                  </div>
                ) : conversationTopic?.topic ? (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">Tópico:</span>
                    <span className="text-sm font-medium text-foreground">{conversationTopic.topic}</span>
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        )}

        <div ref={scrollContainerRef} className="flex-1 overflow-y-auto p-6">
          <div className="mx-auto max-w-4xl space-y-8">
            {/* Loading Skeletons */}
            {isChangingConversation && (
              <>
                <MessageSkeleton isAgent={true} />
                <MessageSkeleton isAgent={false} />
                <MessageSkeleton isAgent={true} />
              </>
            )}

            {/* Agent's Welcome Message */}
            {hasWelcomeMessage && !isChangingConversation && (
              <div className="flex gap-4">
                <Avatar className="size-10 shrink-0">
                  <AvatarFallback className="bg-gradient-to-br from-blue-500 via-purple-500 to-blue-600 text-white shadow-lg ring-2 ring-blue-400/50">
                    <Bot className="h-5 w-5 text-white" strokeWidth={2.5} />
                  </AvatarFallback>
                </Avatar>
                <div className="flex flex-1 flex-col items-start gap-2">
                  <div className="flex flex-col gap-2 rounded-lg bg-card p-4 border border-border">
                    <div className="flex flex-wrap items-center gap-3">
                      <p className="text-foreground text-base font-bold leading-tight">Agente Cultural IA</p>
                      <p className="text-muted-foreground text-sm font-normal leading-normal">
                        {formatTime(new Date().toISOString())}
                      </p>
                    </div>
                    <p className="text-foreground text-base font-normal leading-relaxed">
                      Olá! Estou aqui para ajudá-lo a refletir sobre dilemas culturais que você enfrenta no trabalho. Sinta-se à vontade para descrever uma situação e eu fornecerei conselhos com fontes citadas. Você pode clicar em qualquer fonte para ver uma prévia. Seu feedback é valioso para meu aprendizado, então por favor use os ícones de polegar para cima ou para baixo.
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2 px-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled
                      className="h-8 text-muted-foreground opacity-50 cursor-not-allowed"
                      title="Feedback disponível apenas nas respostas do agente"
                    >
                      <ThumbsUp className="h-5 w-5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled
                      className="h-8 text-muted-foreground opacity-50 cursor-not-allowed"
                      title="Feedback disponível apenas nas respostas do agente"
                    >
                      <ThumbsDown className="h-5 w-5" />
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Messages */}
            {!isChangingConversation && displayMessages.map((message) => {
              const isAgent = message.author === 'AGENT'
              const isPending = message.id === 'pending'
              
              return (
                <div key={message.id} className={cn("flex gap-4", isAgent ? "" : "items-end justify-end", isPending && "opacity-70")}>
                  {isAgent ? (
                    <>
                      <Avatar className="size-10 shrink-0">
                        <AvatarFallback className="bg-gradient-to-br from-blue-500 via-purple-500 to-blue-600 text-white shadow-lg ring-2 ring-blue-400/50">
                          <Bot className="h-5 w-5 text-white" strokeWidth={2.5} />
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex flex-1 flex-col items-start gap-2">
                        <div className="flex flex-col gap-2 rounded-lg bg-card p-4 border border-border">
                          <div className="flex flex-wrap items-center gap-3">
                            <p className="text-foreground text-base font-bold leading-tight">Agente Cultural IA</p>
                            <p className="text-muted-foreground text-sm font-normal leading-normal">
                              {formatTime(message.created_at)}
                            </p>
                          </div>
                          {renderContentWithCitations(message.content, message.cited_sources)}
                        </div>
                        <div className="flex flex-wrap gap-2 px-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleThumbsUp(message.id)}
                            disabled={
                              (!!messageFeedbacks[message.id] && messageFeedbacks[message.id] !== 'POSITIVE')
                            }
                            className={cn(
                              "h-8",
                              messageFeedbacks[message.id] === 'POSITIVE'
                                ? "bg-green-500/20 text-green-600 hover:bg-green-500/30 border border-green-500/30"
                                : "text-muted-foreground hover:bg-muted dark:hover:bg-muted/50 hover:text-green-600"
                            )}
                            title={messageFeedbacks[message.id] === 'POSITIVE' ? "Clique para remover feedback" : "Feedback positivo"}
                          >
                            {initializingFeedbacks.has(message.id) && !messageFeedbacks[message.id] ? (
                              <Skeleton className="h-5 w-5 rounded" />
                            ) : (
                              <ThumbsUp className={cn("h-5 w-5", messageFeedbacks[message.id] === 'POSITIVE' && "fill-current")} />
                            )}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleThumbsDown(message.id)}
                            disabled={
                              (!!messageFeedbacks[message.id] && messageFeedbacks[message.id] !== 'NEGATIVE')
                            }
                            className={cn(
                              "h-8",
                              messageFeedbacks[message.id] === 'NEGATIVE'
                                ? "bg-red-500/20 text-red-600 hover:bg-red-500/30 border border-red-500/30"
                                : "text-muted-foreground hover:bg-muted dark:hover:bg-muted/50 hover:text-red-600"
                            )}
                            title={messageFeedbacks[message.id] === 'NEGATIVE' ? "Clique para remover feedback" : "Feedback negativo"}
                          >
                            {initializingFeedbacks.has(message.id) && !messageFeedbacks[message.id] ? (
                              <Skeleton className="h-5 w-5 rounded" />
                            ) : (
                              <ThumbsDown className={cn("h-5 w-5", messageFeedbacks[message.id] === 'NEGATIVE' && "fill-current")} />
                            )}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleOpenFeedbackModal(message.id)}
                            disabled={false}
                            className={cn(
                              "h-8",
                              detailedFeedbacks[message.id]
                                ? "bg-blue-500/20 text-blue-600 hover:bg-blue-500/30 border border-blue-500/30"
                                : "text-muted-foreground hover:bg-muted dark:hover:bg-muted/50"
                            )}
                            title={detailedFeedbacks[message.id] ? "Clique para editar feedback" : "Enviar feedback detalhado"}
                          >
                            {initializingFeedbacks.has(message.id) && !detailedFeedbacks[message.id] ? (
                              <Skeleton className="h-4 w-4 rounded" />
                            ) : (
                              <Tag className={cn("h-4 w-4", detailedFeedbacks[message.id] && "fill-current")} />
                            )}
                          </Button>
                        </div>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="flex flex-col gap-1 items-end">
                        <p className="text-muted-foreground text-[13px] font-normal leading-normal text-right">Você</p>
                        <p className="text-base font-normal leading-normal flex max-w-lg rounded-lg px-4 py-3 bg-primary text-primary-foreground">
                          {message.content}
                        </p>
                      </div>
                      <Avatar className="w-10 shrink-0">
                        <AvatarFallback className="bg-gradient-to-br from-purple-500 to-blue-500 text-white">
                          <span className="text-xs">U</span>
                        </AvatarFallback>
                      </Avatar>
                    </>
                  )}
                </div>
              )
            })}

            {/* Agent is Typing Indicator */}
            {showTypingIndicator && (
              <div className="flex gap-4">
                <Avatar className="size-10 shrink-0">
                  <AvatarFallback className="bg-gradient-to-br from-blue-500 via-purple-500 to-blue-600 text-white shadow-lg ring-2 ring-blue-400/50">
                    <Bot className="h-5 w-5 text-white" strokeWidth={2.5} />
                  </AvatarFallback>
                </Avatar>
                <div className="flex items-center space-x-2 rounded-lg bg-card px-4 py-3 border border-border">
                  <span className="text-muted-foreground">O agente está digitando...</span>
                  <div className="flex items-center space-x-1">
                    <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce"></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Message Input Area */}
        <div className="px-6 pb-6 pt-4 bg-background border-t">
          <div className="mx-auto max-w-4xl">
            <form onSubmit={handleSubmit} className="relative flex items-center">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Digite sua mensagem..."
                rows={1}
                className="w-full resize-none rounded-lg border-input bg-card text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary focus:border-primary pr-12 py-3 pl-4"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSubmit(e)
                  }
                }}
                disabled={sendMessageMutation.isPending}
              />
              <Button
                type="submit"
                disabled={!input.trim() || sendMessageMutation.isPending}
                className="absolute right-3 flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed p-0"
              >
                <Send className="h-5 w-5" />
              </Button>
            </form>
          </div>
        </div>
      </main>

      {/* Modal de Feedback */}
      <Dialog open={!!showFeedbackModal} onOpenChange={(open) => {
        if (!open) {
          setShowFeedbackModal(null)
          setFeedbackText('')
          setExistingFeedback(null)
        }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {existingFeedback ? 'Editar Feedback' : 'Enviar Feedback'}
            </DialogTitle>
            <DialogDescription>
              {existingFeedback 
                ? 'Visualize, edite ou exclua seu feedback sobre esta resposta do agente.'
                : 'Ajude-nos a melhorar! Compartilhe sua opinião sobre esta resposta do agente.'}
            </DialogDescription>
          </DialogHeader>
          
          <Textarea
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            placeholder="Digite seu feedback aqui..."
            className="min-h-[120px]"
          />
          
          <DialogFooter className="flex flex-row justify-between items-center">
            <div className="flex gap-2">
              {existingFeedback && (
                <Button
                  variant="destructive"
                  onClick={handleDeleteFeedback}
                  disabled={deleteFeedbackMutation.isPending}
                  className="flex items-center gap-2"
                >
                  {deleteFeedbackMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Trash2 className="h-4 w-4" />
                  )}
                  Excluir
                </Button>
              )}
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  setShowFeedbackModal(null)
                  setFeedbackText('')
                  setExistingFeedback(null)
                }}
                disabled={submitFeedbackMutation.isPending || updateFeedbackMutation.isPending || deleteFeedbackMutation.isPending}
              >
                Cancelar
              </Button>
              <Button
                onClick={() => showFeedbackModal && handleFeedbackSubmit(showFeedbackModal)}
                disabled={
                  (submitFeedbackMutation.isPending || updateFeedbackMutation.isPending || deleteFeedbackMutation.isPending) || 
                  !feedbackText.trim()
                }
              >
                {submitFeedbackMutation.isPending || updateFeedbackMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    {existingFeedback ? 'Salvando...' : 'Enviando...'}
                  </>
                ) : (
                  existingFeedback ? 'Salvar Alterações' : 'Enviar'
                )}
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default ChatView
