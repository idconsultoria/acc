import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '@/api/client'
import { Search, Loader2, X } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import Sidebar from '@/components/shared/Sidebar'
import { cn } from '@/lib/utils'

function HistoryView() {
  const navigate = useNavigate()
  const [selectedTopicId, setSelectedTopicId] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [isTopicsPanelOpen, setIsTopicsPanelOpen] = useState(false)

  // Busca tópicos
  const { 
    data: topics = [], 
    isLoading: isLoadingTopics,
    isFetching: isFetchingTopics
  } = useQuery({
    queryKey: ['topics'],
    queryFn: api.listTopics,
    staleTime: 1000 * 60 * 5, // 5 minutos - dados permanecem válidos por mais tempo
    refetchOnMount: false, // Não refaz a busca automaticamente ao montar se os dados estão frescos
    refetchOnWindowFocus: true, // Apenas refaz quando a janela recebe foco
    placeholderData: (previousData) => previousData, // Mantém dados anteriores enquanto busca
  })

  // Busca conversas por tópico
  const { 
    data: conversations = [], 
    isLoading: isLoadingConversations,
    isFetching: isFetchingConversations
  } = useQuery({
    queryKey: ['conversations', selectedTopicId],
    queryFn: () => api.getConversationsByTopic(selectedTopicId || undefined),
    staleTime: 1000 * 60 * 2, // 2 minutos - dados permanecem válidos
    refetchOnMount: false, // Não refaz a busca automaticamente ao montar se os dados estão frescos
    refetchOnWindowFocus: true, // Apenas refaz quando a janela recebe foco
    placeholderData: (previousData) => previousData, // Mantém dados anteriores enquanto busca
  })

  // Filtra tópicos pela busca
  const filteredTopics = topics.filter((topic) =>
    topic.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Função para formatar data relativa
  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)
    
    if (diffInSeconds < 60) return 'Agora'
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutos atrás`
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} horas atrás`
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} dias atrás`
    if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 604800)} semanas atrás`
    return `${Math.floor(diffInSeconds / 2592000)} meses atrás`
  }

  // Calcula total de conversas
  const totalConversations = topics.reduce((sum, topic) => sum + topic.conversation_count, 0)

  return (
    <div className="flex h-screen w-full">
      <Sidebar />

      <main className="flex flex-1 flex-col h-screen overflow-hidden md:ml-0">
        {/* Botão para abrir painel de tópicos em mobile */}
        <div className="md:hidden px-4 py-3 border-b border-border bg-background">
          <Button
            variant="outline"
            onClick={() => setIsTopicsPanelOpen(true)}
            className="w-full justify-start"
          >
            <Search className="h-4 w-4 mr-2" />
            {selectedTopicId 
              ? topics.find(t => t.id === selectedTopicId)?.name || 'Filtrar tópicos...'
              : 'Todos os Dilemas'}
          </Button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Overlay para mobile */}
          {isTopicsPanelOpen && (
            <div
              className="md:hidden fixed inset-0 bg-black/50 z-40"
              onClick={() => setIsTopicsPanelOpen(false)}
            />
          )}

          {/* Painel de Tópicos */}
          <div className={cn(
            "w-64 border-r border-border bg-background p-4 md:p-6 flex flex-col gap-4",
            "fixed md:static h-full z-50 transition-transform duration-300",
            "md:translate-x-0",
            isTopicsPanelOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
          )}>
            <div className="flex items-center justify-between">
              <h2 className="text-lg md:text-xl font-semibold text-foreground">Tópicos</h2>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsTopicsPanelOpen(false)}
                className="md:hidden"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            
            {/* Barra de busca */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Filtrar tópicos..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 text-sm md:text-base"
              />
            </div>

            {/* Lista de tópicos */}
            <div className="flex flex-col gap-2 overflow-y-auto relative">
              {/* Indicador de atualização em background */}
              {isFetchingTopics && !isLoadingTopics && (
                <div className="absolute top-0 right-0 z-10 flex items-center gap-1 text-xs text-muted-foreground bg-background/80 backdrop-blur-sm px-2 py-1 rounded">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  <span>Atualizando</span>
                </div>
              )}
              {isLoadingTopics ? (
                <>
                  {/* Skeleton para "Todos os Dilemas" */}
                  <div className="flex items-center justify-between px-3 py-2 rounded-lg">
                    <Skeleton className="h-5 w-32" />
                    <Skeleton className="h-4 w-6" />
                  </div>
                  {/* Skeletons para tópicos */}
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="flex items-center justify-between px-3 py-2 rounded-lg">
                      <Skeleton className="h-5 w-40" />
                      <Skeleton className="h-4 w-6" />
                    </div>
                  ))}
                </>
              ) : (
                <>
                  <button
                    onClick={() => {
                      setSelectedTopicId(null)
                      setIsTopicsPanelOpen(false)
                    }}
                    className={cn(
                      'flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                      selectedTopicId === null
                        ? 'bg-primary/20 text-primary dark:bg-[#243047] dark:text-white'
                        : 'text-muted-foreground hover:bg-muted dark:hover:bg-muted/50'
                    )}
                  >
                    <span>Todos os Dilemas</span>
                    <span className="text-xs text-muted-foreground">{totalConversations}</span>
                  </button>

                  {filteredTopics.map((topic) => (
                    <button
                      key={topic.id}
                      onClick={() => {
                        setSelectedTopicId(topic.id)
                        setIsTopicsPanelOpen(false)
                      }}
                      className={cn(
                        'flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors',
                        selectedTopicId === topic.id
                          ? 'bg-primary/20 text-primary dark:bg-[#243047] dark:text-white font-medium'
                          : 'text-muted-foreground hover:bg-muted dark:hover:bg-muted/50 font-normal'
                      )}
                    >
                      <span>{topic.name}</span>
                      <span className="text-xs text-muted-foreground">{topic.conversation_count}</span>
                    </button>
                  ))}
                </>
              )}
            </div>
          </div>

          {/* Painel de Resumos */}
          <div className="flex-1 p-3 md:p-6 overflow-y-auto relative">
            <div className="flex items-center justify-between mb-4 md:mb-6">
              <h2 className="text-lg md:text-xl font-semibold text-foreground">Resumos de Conversas</h2>
              {/* Indicador de atualização em background */}
              {isFetchingConversations && !isLoadingConversations && (
                <div className="flex items-center gap-2 text-xs md:text-sm text-muted-foreground">
                  <Loader2 className="h-3 w-3 md:h-4 md:w-4 animate-spin" />
                  <span className="hidden md:inline">Atualizando...</span>
                </div>
              )}
            </div>
            
            <div className="flex flex-col gap-2 md:gap-3 relative">
              {/* Overlay sutil durante atualização em background */}
              {isFetchingConversations && !isLoadingConversations && conversations.length > 0 && (
                <div className="absolute inset-0 bg-background/20 backdrop-blur-[1px] z-10 pointer-events-none rounded-lg" />
              )}
              {isLoadingConversations ? (
                <>
                  {/* Skeletons para cards de conversas */}
                  {[...Array(3)].map((_, i) => (
                    <Card key={i} className="border border-border">
                      <CardContent className="p-4 flex flex-col gap-3">
                        <div className="flex items-center justify-between">
                          <Skeleton className="h-6 w-64" />
                          <Skeleton className="h-4 w-24" />
                        </div>
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-5/6" />
                        <Skeleton className="h-4 w-4/6" />
                        <div className="flex gap-2 pt-2">
                          <Skeleton className="h-5 w-24 rounded-full" />
                        </div>
                        <div className="flex justify-end pt-2">
                          <Skeleton className="h-5 w-32" />
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </>
              ) : conversations.length === 0 ? (
                <Card>
                  <CardContent className="p-6 text-center text-muted-foreground">
                    Nenhuma conversa encontrada para este tópico.
                  </CardContent>
                </Card>
              ) : (
                conversations.map((conversation) => (
                  <Card key={conversation.id} className="border border-border">
                    <CardContent className="p-3 md:p-4 flex flex-col gap-2 md:gap-3">
                      <div className="flex items-start justify-between gap-2">
                        <h3 className="text-base md:text-lg font-medium text-foreground flex-1">{conversation.title}</h3>
                        <p className="text-xs md:text-sm text-muted-foreground shrink-0">{formatRelativeTime(conversation.created_at)}</p>
                      </div>
                      
                      <p className="text-xs md:text-sm text-foreground leading-relaxed">{conversation.summary}</p>
                      
                      {conversation.topic && (
                        <div className="flex flex-wrap gap-2 pt-1 md:pt-2">
                          <span className="bg-muted text-muted-foreground px-2 md:px-3 py-1 rounded-full text-xs font-medium">
                            #{conversation.topic.replace(/\s+/g, '')}
                          </span>
                        </div>
                      )}
                      
                      <div className="flex justify-end pt-1 md:pt-2">
                        <Button
                          variant="link"
                          className="text-primary dark:text-white hover:underline text-xs md:text-sm font-medium p-0 h-auto"
                          onClick={() => navigate(`/chat?conversation=${conversation.id}`)}
                        >
                          Revisitar Conversa
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default HistoryView

