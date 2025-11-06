import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import { Check, X, Loader2, MessageSquare } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import AdminSidebar from '@/components/shared/AdminSidebar'
import { cn } from '@/lib/utils'
import ReactMarkdown from 'react-markdown'

function AdminFeedbackView() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'pending' | 'reviewed'>('pending')
  const [selectedFeedback, setSelectedFeedback] = useState<string | null>(null)

  // Busca feedbacks pendentes
  const { data: pendingFeedbacks = [], isLoading: isLoadingPending } = useQuery({
    queryKey: ['pending-feedbacks'],
    queryFn: api.listPendingFeedbacks,
  })

  // Busca feedbacks revisados
  const { data: reviewedFeedbacks = [], isLoading: isLoadingReviewed } = useQuery({
    queryKey: ['reviewed-feedbacks'],
    queryFn: api.listReviewedFeedbacks,
  })

  // Busca conversation_id a partir de message_id
  const { data: conversationIdData, isLoading: isLoadingConversationId } = useQuery({
    queryKey: ['conversation-id', selectedFeedback],
    queryFn: async () => {
      if (!selectedFeedback) return null
      const feedback = [...pendingFeedbacks, ...reviewedFeedbacks].find(f => f.id === selectedFeedback)
      if (!feedback) return null
      const data = await api.getConversationIdByMessageId(feedback.message_id)
      return data.conversation_id
    },
    enabled: !!selectedFeedback,
  })

  // Busca mensagens da conversa
  const { data: conversationMessages = [], isLoading: isLoadingMessages } = useQuery({
    queryKey: ['conversation-messages', conversationIdData],
    queryFn: async () => {
      if (!conversationIdData) return []
      return await api.getConversationMessages(conversationIdData)
    },
    enabled: !!conversationIdData && !!selectedFeedback,
  })

  // Aprova feedback
  const approveFeedbackMutation = useMutation({
    mutationFn: api.approveFeedback,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-feedbacks'] })
      queryClient.invalidateQueries({ queryKey: ['reviewed-feedbacks'] })
      queryClient.invalidateQueries({ queryKey: ['learnings'] })
    },
  })

  // Rejeita feedback
  const rejectFeedbackMutation = useMutation({
    mutationFn: api.rejectFeedback,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-feedbacks'] })
      queryClient.invalidateQueries({ queryKey: ['reviewed-feedbacks'] })
    },
  })

  const handleOpenConversationModal = (feedbackId: string) => {
    setSelectedFeedback(feedbackId)
  }

  const isLoadingConversation = isLoadingConversationId || isLoadingMessages

  const renderFeedbackCard = (feedback: typeof pendingFeedbacks[0], showActions: boolean = true) => {
    const isApproved = feedback.status === 'APPROVED'
    const isRejected = feedback.status === 'REJECTED'
    const isPending = feedback.status === 'PENDING'

    return (
      <Card 
        key={feedback.id} 
        className={cn(
          "border border-border cursor-pointer hover:bg-muted/50 transition-colors",
          isApproved && "border-green-500/20 bg-green-500/5",
          isRejected && "border-destructive/20 bg-destructive/5"
        )}
        onClick={() => handleOpenConversationModal(feedback.id)}
      >
        <CardContent className="p-4 flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              {/* Não mostra o badge "Pendente" na aba de pendentes (showActions = true) */}
              {(!showActions || !isPending) && (
                <Badge 
                  variant={isApproved ? "default" : isRejected ? "destructive" : "secondary"}
                  className={cn(
                    isApproved && "bg-green-500/20 text-green-600 border-green-500/20",
                    isRejected && "bg-destructive/20 text-destructive border-destructive/20"
                  )}
                >
                  {isApproved ? 'Aprovado' : isRejected ? 'Rejeitado' : 'Pendente'}
                </Badge>
              )}
              {feedback.feedback_type === 'POSITIVE' && (
                <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
                  Thumbs Up
                </Badge>
              )}
              {feedback.feedback_type === 'NEGATIVE' && (
                <Badge variant="outline" className="bg-red-500/10 text-red-600 border-red-500/20">
                  Thumbs Down
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground">
              Sobre o dilema: "{feedback.message_preview || 'Dilema não especificado'}"
            </p>
            <p className="text-foreground font-medium mt-1">
              "{feedback.feedback_text}"
            </p>
            <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
              <MessageSquare className="h-3 w-3" />
              Clique para ver histórico completo da conversa
            </p>
          </div>
          {showActions && isPending && (
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3 self-end sm:self-center">
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation()
                  approveFeedbackMutation.mutate(feedback.id)
                }}
                disabled={approveFeedbackMutation.isPending || rejectFeedbackMutation.isPending}
                className="bg-green-500/10 text-green-600 hover:bg-green-500/20 border-green-500/20 w-full sm:w-auto"
              >
                {approveFeedbackMutation.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Check className="h-4 w-4 mr-2" />
                )}
                Aprovar
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation()
                  rejectFeedbackMutation.mutate(feedback.id)
                }}
                disabled={approveFeedbackMutation.isPending || rejectFeedbackMutation.isPending}
                className="bg-destructive/10 text-destructive hover:bg-destructive/20 border-destructive/20 w-full sm:w-auto"
              >
                {rejectFeedbackMutation.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <X className="h-4 w-4 mr-2" />
                )}
                Rejeitar
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="flex h-screen w-full">
      <AdminSidebar />

      <main className="flex-1 flex flex-col h-screen overflow-hidden md:ml-0">
        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-7xl px-3 md:px-4 sm:px-6 lg:px-10 py-4 md:py-8 pt-14 md:pt-8">
            <section>
              <div className="flex flex-wrap justify-between gap-4 items-center mb-4 md:mb-6">
                <h1 className="text-2xl md:text-3xl sm:text-4xl font-black leading-tight tracking-tight text-foreground">
                  Revisão de Feedback
                </h1>
              </div>
              
              <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'pending' | 'reviewed')} className="w-full">
                <TabsList className="border-b border-border bg-transparent p-0 h-auto mb-4 md:mb-6">
                  <TabsTrigger
                    value="pending"
                    className="pb-2 md:pb-3 text-sm md:text-base border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:text-primary rounded-none"
                  >
                    Pendentes {pendingFeedbacks.length > 0 && `(${pendingFeedbacks.length})`}
                  </TabsTrigger>
                  <TabsTrigger
                    value="reviewed"
                    className="pb-2 md:pb-3 text-sm md:text-base border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:text-primary rounded-none"
                  >
                    Revisados {reviewedFeedbacks.length > 0 && `(${reviewedFeedbacks.length})`}
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="pending" className="mt-0">
                  <div className="flex flex-col gap-4">
                    {isLoadingPending ? (
                      <>
                        {[...Array(3)].map((_, i) => (
                          <Card key={i} className="border border-border">
                            <CardContent className="p-4 flex flex-col sm:flex-row sm:items-center gap-4">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2 flex-wrap">
                                  <Skeleton className="h-5 w-20 rounded-full" />
                                  <Skeleton className="h-5 w-24 rounded-full" />
                                </div>
                                <Skeleton className="h-4 w-full mb-1" />
                                <Skeleton className="h-4 w-5/6 mb-1" />
                                <Skeleton className="h-4 w-4/6 mb-2" />
                                <Skeleton className="h-3 w-48" />
                              </div>
                              <div className="flex items-center gap-3 self-end sm:self-center">
                                <Skeleton className="h-9 w-24" />
                                <Skeleton className="h-9 w-24" />
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </>
                    ) : pendingFeedbacks.length === 0 ? (
                      <Card>
                        <CardContent className="p-6 text-center text-muted-foreground">
                          Nenhum feedback pendente no momento.
                        </CardContent>
                      </Card>
                    ) : (
                      pendingFeedbacks.map((feedback) => renderFeedbackCard(feedback, true))
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="reviewed" className="mt-0">
                  <div className="flex flex-col gap-4">
                    {isLoadingReviewed ? (
                      <>
                        {[...Array(3)].map((_, i) => (
                          <Card key={i} className="border border-border">
                            <CardContent className="p-4 flex flex-col sm:flex-row sm:items-center gap-4">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2 flex-wrap">
                                  <Skeleton className="h-5 w-20 rounded-full" />
                                  <Skeleton className="h-5 w-24 rounded-full" />
                                </div>
                                <Skeleton className="h-4 w-full mb-1" />
                                <Skeleton className="h-4 w-5/6 mb-1" />
                                <Skeleton className="h-4 w-4/6 mb-2" />
                                <Skeleton className="h-3 w-48" />
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </>
                    ) : reviewedFeedbacks.length === 0 ? (
                      <Card>
                        <CardContent className="p-6 text-center text-muted-foreground">
                          Nenhum feedback revisado ainda.
                        </CardContent>
                      </Card>
                    ) : (
                      reviewedFeedbacks.map((feedback) => renderFeedbackCard(feedback, false))
                    )}
                  </div>
                </TabsContent>
              </Tabs>
            </section>
          </div>
        </div>
      </main>

      {/* Modal de Histórico da Conversa */}
      <Dialog open={!!selectedFeedback} onOpenChange={(open) => !open && setSelectedFeedback(null)}>
        <DialogContent className="w-[95vw] max-w-4xl max-h-[85vh] md:max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Histórico Completo da Conversa</DialogTitle>
            <DialogDescription>
              Visualize todas as mensagens da conversa relacionada a este feedback.
            </DialogDescription>
          </DialogHeader>

          <div className="mt-4">
            {isLoadingConversation ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                <span className="ml-2 text-muted-foreground">Carregando histórico...</span>
              </div>
            ) : conversationMessages.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                Nenhuma mensagem encontrada.
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                {conversationMessages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      "flex gap-2 md:gap-3 p-3 md:p-4 rounded-lg",
                      message.author === 'USER' 
                        ? "bg-muted/50 ml-auto max-w-[90%] md:max-w-[80%]"
                        : "bg-primary/5 mr-auto max-w-[90%] md:max-w-[80%]"
                    )}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={cn(
                          "text-sm font-semibold",
                          message.author === 'USER' ? "text-primary" : "text-muted-foreground"
                        )}>
                          {message.author === 'USER' ? 'Você' : 'Agente'}
                        </span>
                      </div>
                      <div className="prose prose-sm dark:prose-invert max-w-none">
                        <ReactMarkdown>{message.content}</ReactMarkdown>
                      </div>
                      {message.cited_sources && message.cited_sources.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-border">
                          <p className="text-xs text-muted-foreground mb-2">Fontes citadas:</p>
                          <div className="flex flex-wrap gap-2">
                            {message.cited_sources.map((source, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                {source.title}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedFeedback(null)}>
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default AdminFeedbackView
