import { useEffect, useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  api,
  Learning,
  LearningWeightUpdate,
  LearningMergeCandidate,
} from '@/api/client'
import AdminSidebar from '@/components/shared/AdminSidebar'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Separator } from '@/components/ui/separator'
import { Loader2, RefreshCcw, Brain, Sparkles, GitMerge } from 'lucide-react'
import { cn } from '@/lib/utils'

type FeedbackState =
  | { type: 'success'; message: string }
  | { type: 'error'; message: string }
  | null

interface MergeDraft {
  base: Learning
  duplicates: Learning[]
  selectedDuplicateIds: string[]
  mergedContent: string
  mergedWeight: number
}

const formatDateTime = (value?: string | null) => {
  if (!value) return 'Nunca utilizado'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Data inválida'
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

const clampWeight = (value: number) => {
  if (Number.isNaN(value)) return 0
  return Math.min(2, Math.max(0, value))
}

const calculateDefaultMergeContent = (candidate: LearningMergeCandidate): string => {
  const parts = [
    candidate.base_learning.content.trim(),
    ...candidate.duplicate_learnings.map((learning) => learning.content.trim()),
  ].filter(Boolean)
  return Array.from(new Set(parts)).join('\n\n')
}

const calculateSuggestedWeight = (candidate: LearningMergeCandidate): number => {
  const weights = [
    candidate.base_learning.relevance_weight ?? 0.7,
    ...candidate.duplicate_learnings.map((learning) => learning.relevance_weight ?? 0.7),
  ]
  const sum = weights.reduce((acc, value) => acc + value, 0)
  return Number((sum / weights.length).toFixed(2))
}

function AdminLearningsView() {
  const queryClient = useQueryClient()

  const [feedback, setFeedback] = useState<FeedbackState>(null)
  const [draftWeights, setDraftWeights] = useState<Record<string, number>>({})
  const [isDedupModalOpen, setIsDedupModalOpen] = useState(false)
  const [mergeDraft, setMergeDraft] = useState<MergeDraft | null>(null)

  const {
    data: learnings = [],
    isLoading: isLoadingLearnings,
    isFetching: isFetchingLearnings,
  } = useQuery({
    queryKey: ['learnings'],
    queryFn: api.listLearnings,
  })

  useEffect(() => {
    if (learnings.length === 0) {
      setDraftWeights({})
      return
    }
    setDraftWeights((prev) => {
      const next: Record<string, number> = {}
      for (const learning of learnings) {
        next[learning.id] = prev[learning.id] ?? clampWeight(learning.relevance_weight ?? 0.7)
      }
      return next
    })
  }, [learnings])

  const originalWeights = useMemo(() => {
    const weights: Record<string, number> = {}
    for (const learning of learnings) {
      weights[learning.id] = clampWeight(learning.relevance_weight ?? 0.7)
    }
    return weights
  }, [learnings])

  const weightUpdates = useMemo<LearningWeightUpdate[]>(() => {
    return learnings
      .map((learning) => {
        const draft = draftWeights[learning.id]
        const original = originalWeights[learning.id]
        if (draft === undefined || Number.isNaN(draft) || Math.abs(draft - original) < 0.001) {
          return null
        }
        return {
          learning_id: learning.id,
          relevance_weight: Number(draft.toFixed(3)),
        }
      })
      .filter(Boolean) as LearningWeightUpdate[]
  }, [draftWeights, learnings, originalWeights])

  const hasPendingWeightUpdates = weightUpdates.length > 0

  const updateWeightsMutation = useMutation({
    mutationFn: (updates: LearningWeightUpdate[]) => api.updateLearningWeights(updates),
    onSuccess: () => {
      setFeedback({ type: 'success', message: 'Pesos atualizados com sucesso.' })
      queryClient.invalidateQueries({ queryKey: ['learnings'] })
      queryClient.invalidateQueries({ queryKey: ['learning-dedup-candidates'] })
    },
    onError: (error: unknown) => {
      console.error('Erro ao atualizar pesos de aprendizados:', error)
      setFeedback({
        type: 'error',
        message: 'Não foi possível atualizar os pesos. Tente novamente.',
      })
    },
  })

  const recalcWeightsMutation = useMutation({
    mutationFn: api.recalculateLearningWeights,
    onSuccess: () => {
      setFeedback({
        type: 'success',
        message: 'Recalibração solicitada. Pesos serão atualizados em instantes.',
      })
      queryClient.invalidateQueries({ queryKey: ['learnings'] })
      queryClient.invalidateQueries({ queryKey: ['learning-dedup-candidates'] })
    },
    onError: (error: unknown) => {
      console.error('Erro ao recalcular pesos:', error)
      setFeedback({
        type: 'error',
        message: 'Não foi possível recalcular os pesos automaticamente.',
      })
    },
  })

  const {
    data: dedupData,
    isLoading: isLoadingDedup,
    refetch: refetchDedup,
  } = useQuery({
    queryKey: ['learning-dedup-candidates'],
    queryFn: () => api.getLearningDedupCandidates(),
    enabled: isDedupModalOpen,
  })

  const mergeMutation = useMutation({
    mutationFn: ({
      baseId,
      duplicateIds,
      mergedContent,
      mergedWeight,
    }: {
      baseId: string
      duplicateIds: string[]
      mergedContent: string
      mergedWeight?: number
    }) => api.mergeLearnings([baseId, ...duplicateIds], mergedContent, mergedWeight),
    onSuccess: () => {
      setFeedback({ type: 'success', message: 'Aprendizados mesclados com sucesso.' })
      setMergeDraft(null)
      setIsDedupModalOpen(false)
      queryClient.invalidateQueries({ queryKey: ['learnings'] })
      queryClient.invalidateQueries({ queryKey: ['learning-dedup-candidates'] })
    },
    onError: (error: unknown) => {
      console.error('Erro ao mesclar aprendizados:', error)
      setFeedback({
        type: 'error',
        message: 'Falha ao mesclar aprendizados. Revise os dados e tente novamente.',
      })
    },
  })

  const handleWeightInputChange = (learningId: string, value: string) => {
    const parsed = parseFloat(value)
    if (Number.isNaN(parsed)) {
      setDraftWeights((prev) => ({ ...prev, [learningId]: 0 }))
      return
    }
    setDraftWeights((prev) => ({ ...prev, [learningId]: clampWeight(parsed) }))
  }

  const handleSaveWeights = () => {
    if (!hasPendingWeightUpdates || updateWeightsMutation.isPending) return
    updateWeightsMutation.mutate(weightUpdates)
  }

  const openDedupModal = () => {
    setIsDedupModalOpen(true)
    setMergeDraft(null)
    setTimeout(() => {
      refetchDedup()
    }, 0)
  }

  const handlePrepareMerge = (candidate: LearningMergeCandidate) => {
    setMergeDraft({
      base: candidate.base_learning,
      duplicates: candidate.duplicate_learnings,
      selectedDuplicateIds: candidate.duplicate_learnings.map((learning) => learning.id),
      mergedContent: calculateDefaultMergeContent(candidate),
      mergedWeight: calculateSuggestedWeight(candidate),
    })
  }

  const toggleDuplicateSelection = (learningId: string) => {
    if (!mergeDraft) return
    setMergeDraft((prev) => {
      if (!prev) return prev
      const alreadySelected = prev.selectedDuplicateIds.includes(learningId)
      const nextSelected = alreadySelected
        ? prev.selectedDuplicateIds.filter((id) => id !== learningId)
        : [...prev.selectedDuplicateIds, learningId]
      return { ...prev, selectedDuplicateIds: nextSelected }
    })
  }

  const handleConfirmMerge = () => {
    if (!mergeDraft || mergeDraft.selectedDuplicateIds.length === 0) {
      setFeedback({
        type: 'error',
        message: 'Selecione pelo menos um aprendizado duplicado para mesclar.',
      })
      return
    }
    mergeMutation.mutate({
      baseId: mergeDraft.base.id,
      duplicateIds: mergeDraft.selectedDuplicateIds,
      mergedContent: mergeDraft.mergedContent.trim(),
      mergedWeight: clampWeight(mergeDraft.mergedWeight),
    })
  }

  return (
    <div className="flex h-screen w-full">
      <AdminSidebar />

      <main className="flex-1 flex flex-col h-screen overflow-hidden md:ml-0">
        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-7xl px-3 sm:px-6 lg:px-10 py-4 md:py-8 pt-14 md:pt-8">
            <section className="space-y-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div className="space-y-2">
                  <h1 className="text-2xl md:text-3xl font-black tracking-tight text-foreground flex items-center gap-2">
                    <Brain className="h-6 w-6 text-primary" />
                    Aprendizados do Agente
                  </h1>
                  <p className="text-sm md:text-base text-muted-foreground max-w-2xl">
                    Ajuste pesos, acompanhe o uso recente e consolide aprendizados duplicados para
                    manter o repertório do agente enxuto e relevante.
                  </p>
                </div>

                <div className="flex flex-col sm:flex-row gap-2">
                  <Button
                    variant="outline"
                    onClick={openDedupModal}
                    disabled={isFetchingLearnings || isLoadingLearnings}
                  >
                    <GitMerge className="h-4 w-4 mr-2" />
                    Deduplicar Aprendizados
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => recalcWeightsMutation.mutate()}
                    disabled={recalcWeightsMutation.isPending || isFetchingLearnings}
                  >
                    {recalcWeightsMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Recalculando...
                      </>
                    ) : (
                      <>
                        <RefreshCcw className="h-4 w-4 mr-2" />
                        Recalibrar Automaticamente
                      </>
                    )}
                  </Button>
                </div>
              </div>

              {feedback && (
                <Alert
                  variant={feedback.type === 'error' ? 'destructive' : 'default'}
                  className="border-l-4"
                >
                  <AlertTitle>
                    {feedback.type === 'error' ? 'Algo deu errado' : 'Tudo certo!'}
                  </AlertTitle>
                  <AlertDescription>{feedback.message}</AlertDescription>
                </Alert>
              )}

              <Card>
                <CardHeader className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div className="space-y-1.5">
                    <CardTitle className="text-lg md:text-xl">Inventário de Aprendizados</CardTitle>
                    <CardDescription>
                      {isFetchingLearnings
                        ? 'Atualizando dados...'
                        : `Total atual: ${learnings.length} aprendizados aprovados.`}
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={handleSaveWeights}
                      disabled={!hasPendingWeightUpdates || updateWeightsMutation.isPending}
                    >
                      {updateWeightsMutation.isPending ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Salvando...
                        </>
                      ) : (
                        <>
                          <Sparkles className="h-4 w-4 mr-2" />
                          Salvar Pesos Atualizados
                        </>
                      )}
                    </Button>
                  </div>
                </CardHeader>

                <Separator />

                <CardContent className="p-0">
                  {isLoadingLearnings ? (
                    <div className="py-16 flex flex-col items-center justify-center text-muted-foreground gap-3">
                      <Loader2 className="h-6 w-6 animate-spin" />
                      <p className="text-sm">Carregando aprendizados...</p>
                    </div>
                  ) : learnings.length === 0 ? (
                    <div className="py-16 flex flex-col items-center justify-center text-muted-foreground gap-3">
                      <Brain className="h-10 w-10 opacity-50" />
                      <p className="text-sm text-center max-w-md">
                        Ainda não há aprendizados aprovados. Assim que feedbacks forem convertidos,
                        eles aparecerão aqui para revisão e ajustes.
                      </p>
                    </div>
                  ) : (
                    <ScrollArea className="max-h-[65vh]">
                      <div className="divide-y">
                        {learnings.map((learning) => {
                          const currentWeight = draftWeights[learning.id] ?? 0
                          const originalWeight = originalWeights[learning.id] ?? 0
                          const hasChanged =
                            Math.abs(currentWeight - originalWeight) >= 0.001 &&
                            !Number.isNaN(currentWeight)
                          return (
                            <div
                              key={learning.id}
                              className="p-4 md:p-6 hover:bg-muted/40 transition-colors"
                            >
                              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                                <div className="space-y-3">
                                  <div className="flex flex-wrap items-center gap-2">
                                    <Badge variant="outline" className="text-xs font-mono">
                                      {learning.id.slice(0, 8)}
                                    </Badge>
                                    {hasChanged && (
                                      <Badge variant="secondary" className="text-xs">
                                        Peso não salvo
                                      </Badge>
                                    )}
                                  </div>
                                  <p className="text-sm leading-relaxed whitespace-pre-wrap">
                                    {learning.content}
                                  </p>
                                  <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                                    <span>
                                      Criado em:{' '}
                                      <strong>{formatDateTime(learning.created_at)}</strong>
                                    </span>
                                    <span>
                                      Último uso:{' '}
                                      <strong>{formatDateTime(learning.last_used_at)}</strong>
                                    </span>
                                    <span>
                                      Feedback origem:{' '}
                                      <code className="font-mono">
                                        {learning.source_feedback_id.slice(0, 8)}
                                      </code>
                                    </span>
                                  </div>
                                </div>

                                <div className="w-full md:w-56 space-y-2">
                                  <Label className="text-xs uppercase tracking-wide text-muted-foreground">
                                    Peso de relevância
                                  </Label>
                                  <Input
                                    type="number"
                                    step={0.05}
                                    min={0}
                                    max={2}
                                    value={currentWeight.toString()}
                                    onChange={(event) =>
                                      handleWeightInputChange(learning.id, event.target.value)
                                    }
                                  />
                                  <div className="flex justify-between text-[11px] text-muted-foreground">
                                    <span>0 (neutralizado)</span>
                                    <span>2 (prioritário)</span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </ScrollArea>
                  )}
                </CardContent>
              </Card>
            </section>
          </div>
        </div>
      </main>

      <Dialog open={isDedupModalOpen} onOpenChange={setIsDedupModalOpen}>
        <DialogContent className="max-w-4xl w-[95vw]">
          <DialogHeader>
            <DialogTitle>Deduplicação de Aprendizados</DialogTitle>
            <DialogDescription>
              Analise sugestões automáticas de aprendizados similares e consolide aqueles que
              possuem mensagens redundantes ou complementares.
            </DialogDescription>
          </DialogHeader>

          {isLoadingDedup ? (
            <div className="py-12 flex flex-col items-center justify-center gap-3 text-muted-foreground">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span className="text-sm">Buscando candidatos...</span>
            </div>
          ) : dedupData?.candidates?.length ? (
            <div className="flex flex-col gap-4 max-h-[60vh] overflow-y-auto pr-1">
              {dedupData.candidates.map((candidate) => {
                const isActiveDraft =
                  mergeDraft?.base.id === candidate.base_learning.id &&
                  mergeDraft.duplicates.length === candidate.duplicate_learnings.length
                return (
                  <Card
                    key={candidate.base_learning.id}
                    className={cn(
                      'border-border',
                      isActiveDraft && 'border-primary/60 shadow-lg shadow-primary/10'
                    )}
                  >
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base flex items-center gap-2">
                        <Badge variant="outline">Base</Badge>
                        {candidate.base_learning.content.slice(0, 80)}
                        {candidate.base_learning.content.length > 80 && '…'}
                      </CardTitle>
                      <CardDescription>
                        {candidate.similarity_score != null && (
                          <span className="text-xs">
                            Similaridade média sugerida:{' '}
                            <strong>{Math.round(candidate.similarity_score * 100)}%</strong>
                          </span>
                        )}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="space-y-2">
                        <Label className="text-xs uppercase tracking-wide text-muted-foreground">
                          Possíveis duplicados ({candidate.duplicate_learnings.length})
                        </Label>
                        <div className="flex flex-col gap-2">
                          {candidate.duplicate_learnings.map((duplicate) => {
                            const isSelected =
                              mergeDraft?.selectedDuplicateIds.includes(duplicate.id) ?? true
                            return (
                              <label
                                key={duplicate.id}
                                className={cn(
                                  'flex gap-2 rounded-md border border-border/60 p-3 bg-muted/40 text-sm',
                                  mergeDraft?.base.id === candidate.base_learning.id &&
                                    'cursor-pointer hover:bg-muted'
                                )}
                              >
                                <Checkbox
                                  className="mt-1"
                                  checked={mergeDraft ? isSelected : true}
                                  onCheckedChange={() => toggleDuplicateSelection(duplicate.id)}
                                />
                                <span className="leading-relaxed">
                                  {duplicate.content}
                                  <span className="block text-[11px] text-muted-foreground mt-1">
                                    Peso atual:{' '}
                                    <strong>
                                      {(duplicate.relevance_weight ?? 0.7).toFixed(2)}
                                    </strong>{' '}
                                    • Criação: {formatDateTime(duplicate.created_at)}
                                  </span>
                                </span>
                              </label>
                            )
                          })}
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <Button
                          size="sm"
                          variant={isActiveDraft ? 'default' : 'outline'}
                          onClick={() => handlePrepareMerge(candidate)}
                        >
                          {isActiveDraft ? 'Preparando merge...' : 'Preparar merge manual'}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          ) : (
            <div className="py-8 text-sm text-muted-foreground text-center">
              Nenhum conjunto de aprendizados semelhantes foi encontrado neste momento.
            </div>
          )}

          {mergeDraft && (
            <div className="space-y-3 border rounded-lg border-primary/40 bg-primary/5 p-4">
              <h3 className="text-sm font-semibold text-primary flex items-center gap-2">
                <GitMerge className="h-4 w-4" />
                Consolidar aprendizados selecionados
              </h3>
              <div className="grid gap-3">
                <div className="space-y-1">
                  <Label className="text-xs uppercase tracking-wide text-muted-foreground">
                    Conteúdo resultante
                  </Label>
                  <Textarea
                    value={mergeDraft.mergedContent}
                    onChange={(event) =>
                      setMergeDraft((prev) =>
                        prev ? { ...prev, mergedContent: event.target.value } : prev
                      )
                    }
                    className="min-h-[160px] text-sm"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs uppercase tracking-wide text-muted-foreground">
                    Peso sugerido
                  </Label>
                  <Input
                    type="number"
                    min={0}
                    max={2}
                    step={0.05}
                    value={mergeDraft.mergedWeight.toString()}
                    onChange={(event) =>
                      setMergeDraft((prev) =>
                        prev
                          ? { ...prev, mergedWeight: clampWeight(parseFloat(event.target.value)) }
                          : prev
                      )
                    }
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  {mergeDraft.selectedDuplicateIds.length} duplicado(s) será(ão) arquivado(s) e o
                  novo aprendizado substituto herdará o feedback mais relevante.
                </p>
              </div>
            </div>
          )}

          <DialogFooter className="flex items-center justify-between">
            <Button variant="outline" onClick={() => setIsDedupModalOpen(false)}>
              Fechar
            </Button>
            <Button
              onClick={handleConfirmMerge}
              disabled={!mergeDraft || mergeMutation.isPending}
            >
              {mergeMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Consolidando...
                </>
              ) : (
                <>
                  <GitMerge className="h-4 w-4 mr-2" />
                  Confirmar Mesclagem
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default AdminLearningsView
