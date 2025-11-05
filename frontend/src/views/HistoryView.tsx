import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { Search, Loader2 } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import Sidebar from '@/components/shared/Sidebar'
import { cn } from '@/lib/utils.ts'

function HistoryView() {
  const navigate = useNavigate()
  const [selectedTopicId, setSelectedTopicId] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  // Busca tópicos
  const { 
    data: topics = [], 
    isLoading: isLoadingTopics,
    isFetching: isFetchingTopics
  } = useQuery({
    queryKey: ['topics'],
    queryFn: api.listTopics,
    staleTime: 1000 * 30, // 30 segundos - dados permanecem válidos por pouco tempo
    refetchOnMount: 'always', // Sempre refaz a busca ao montar
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
    staleTime: 1000 * 30, // 30 segundos - dados permanecem válidos por pouco tempo
    refetchOnMount: 'always', // Sempre refaz a busca ao montar
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

      <main className="flex flex-1 flex-col h-screen overflow-hidden">
        <div className="flex flex-1 overflow-hidden">
          {/* Painel de Tópicos */}
          <div className="w-64 border-r border-border bg-background p-6 flex flex-col gap-4">
            <h2 className="text-xl font-semibold text-foreground">Tópicos</h2>
            
            {/* Barra de busca */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Filtrar tópicos..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
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
                    onClick={() => setSelectedTopicId(null)}
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
                      onClick={() => setSelectedTopicId(topic.id)}
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
          <div className="flex-1 p-6 overflow-y-auto relative">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-foreground">Resumos de Conversas</h2>
              {/* Indicador de atualização em background */}
              {isFetchingConversations && !isLoadingConversations && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Atualizando...</span>
                </div>
              )}
            </div>
            
            <div className="flex flex-col gap-3 relative">
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
                    <CardContent className="p-4 flex flex-col gap-3">
                      <div className="flex items-center justify-between">
                        <h3 className="text-lg font-medium text-foreground">{conversation.title}</h3>
                        <p className="text-sm text-muted-foreground">{formatRelativeTime(conversation.created_at)}</p>
                      </div>
                      
                      <p className="text-sm text-foreground leading-relaxed">{conversation.summary}</p>
                      
                      {conversation.topic && (
                        <div className="flex flex-wrap gap-2 pt-2">
                          <span className="bg-muted text-muted-foreground px-3 py-1 rounded-full text-xs font-medium">
                            #{conversation.topic.replace(/\s+/g, '')}
                          </span>
                        </div>
                      )}
                      
                      <div className="flex justify-end pt-2">
                        <Button
                          variant="link"
                          className="text-primary dark:text-white hover:underline text-sm font-medium p-0 h-auto"
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

