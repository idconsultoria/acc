import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, Artifact, ArtifactChunk, ArtifactContentResponse } from '@/api/client'
import { Loader2, Plus, Trash2, Check, X, Shield, FileText, MessageSquare, Bot } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { useCallback } from 'react'

function AdminView() {
  const queryClient = useQueryClient()
  const [showAddModal, setShowAddModal] = useState(false)
  const [addTitle, setAddTitle] = useState('')
  const [addText, setAddText] = useState('')
  const [addFile, setAddFile] = useState<File | null>(null)
  const [addType, setAddType] = useState<'text' | 'pdf'>('text')
  const [instructionText, setInstructionText] = useState('')
  const [artifactTags, setArtifactTags] = useState<string[]>([])
  const [newTag, setNewTag] = useState('')
  const [activeArtifact, setActiveArtifact] = useState<Artifact | null>(null)
  const [artifactModalTab, setArtifactModalTab] = useState<'edit' | 'chunks'>('edit')
  const [artifactContent, setArtifactContent] = useState<ArtifactContentResponse | null>(null)
  const [isLoadingArtifactContent, setIsLoadingArtifactContent] = useState(false)
  const [artifactChunks, setArtifactChunks] = useState<ArtifactChunk[]>([])
  const [isLoadingChunks, setIsLoadingChunks] = useState(false)
  const [chunksError, setChunksError] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [editDescription, setEditDescription] = useState('')
  const [editContent, setEditContent] = useState('')
  const [editColor, setEditColor] = useState<string | null>(null)
  const [editFile, setEditFile] = useState<File | null>(null)
  const [deletingArtifactId, setDeletingArtifactId] = useState<string | null>(null)
  const [feedbackAlert, setFeedbackAlert] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  // Busca artefatos
  const { data: artifacts = [] } = useQuery({
    queryKey: ['artifacts'],
    queryFn: api.listArtifacts,
  })

  // Busca instrução do agente
  const { data: agentInstructionData } = useQuery({
    queryKey: ['agent-instruction'],
    queryFn: api.getAgentInstruction,
  })

  // Atualiza o texto quando os dados chegam
  useEffect(() => {
    if (agentInstructionData?.instruction) {
      setInstructionText(agentInstructionData.instruction)
    }
  }, [agentInstructionData])

  // Busca feedbacks pendentes
  const { data: pendingFeedbacks = [] } = useQuery({
    queryKey: ['pending-feedbacks'],
    queryFn: api.listPendingFeedbacks,
  })

  // Atualiza instrução do agente
  const updateInstructionMutation = useMutation({
    mutationFn: api.updateAgentInstruction,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-instruction'] })
    },
  })

  // Cria artefato
  const createArtifactMutation = useMutation({
    mutationFn: async () => {
      const formData = new FormData()
      formData.append('title', addTitle)
      
      if (addType === 'text') {
        formData.append('text_content', addText)
      } else if (addFile) {
        formData.append('file', addFile)
      }
      
      return api.createArtifact(formData)
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['artifacts'] })
      setShowAddModal(false)
      setAddTitle('')
      setAddText('')
      setAddFile(null)
      setFeedbackAlert({ type: 'success', message: 'Artefato adicionado com sucesso.' })
    },
    onError: (error: unknown) => {
      let message = 'Não foi possível adicionar o artefato. Tente novamente.'
      if (typeof error === 'object' && error !== null) {
        const maybeAxios = error as { response?: { data?: { detail?: string } } ; message?: string }
        if (maybeAxios.response?.data?.detail) {
          message = maybeAxios.response.data.detail
        } else if (maybeAxios.message) {
          message = maybeAxios.message
        }
      } else if (typeof error === 'string') {
        message = error
      }
      setFeedbackAlert({ type: 'error', message })
    }
  })

  // Deleta artefato
  const deleteArtifactMutation = useMutation({
    mutationFn: api.deleteArtifact,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['artifacts'] })
    },
    onMutate: (artifactId: string) => {
      setDeletingArtifactId(artifactId)
    },
    onSettled: () => {
      setDeletingArtifactId(null)
    }
  })

  const handleCloseArtifactModal = () => {
    setActiveArtifact(null)
    setArtifactContent(null)
    setArtifactModalTab('edit')
    setArtifactChunks([])
    setChunksError(null)
    setIsLoadingChunks(false)
    setIsLoadingArtifactContent(false)
    setEditFile(null)
    setEditContent('')
    setEditDescription('')
    setEditTitle('')
    setEditColor(null)
    setArtifactTags([])
    setNewTag('')
  }

  const loadArtifactContent = async (artifact: Artifact) => {
    setIsLoadingArtifactContent(true)
    try {
      const response = await api.getArtifactContent(artifact.id)
      setArtifactContent(response)
      if (response.source_type === 'TEXT') {
        setEditContent(response.content)
      } else {
        setEditContent('')
      }
    } catch (error) {
      console.error('Erro ao carregar conteúdo do artefato:', error)
      setArtifactContent(null)
      setEditContent('')
    } finally {
      setIsLoadingArtifactContent(false)
    }
  }

  const loadArtifactChunks = async (artifact: Artifact) => {
    setIsLoadingChunks(true)
    setChunksError(null)
    try {
      const chunks = await api.getArtifactChunks(artifact.id)
      setArtifactChunks(chunks)
    } catch (error) {
      console.error('Erro ao carregar chunks:', error)
      setChunksError('Não foi possível carregar os chunks deste artefato.')
    } finally {
      setIsLoadingChunks(false)
    }
  }

  const handleOpenArtifactModal = async (artifact: Artifact) => {
    setActiveArtifact(artifact)
    setArtifactModalTab('edit')
    setArtifactTags(artifact.tags || [])
    setNewTag('')
    setEditTitle(artifact.title)
    setEditDescription(artifact.description || '')
    setEditColor(artifact.color || null)
    setEditContent('')
    setEditFile(null)
    await Promise.all([loadArtifactContent(artifact), loadArtifactChunks(artifact)])
  }

  const handleAddTag = () => {
    if (newTag.trim() && !artifactTags.includes(newTag.trim())) {
      setArtifactTags([...artifactTags, newTag.trim()])
      setNewTag('')
    }
  }

  const handleRemoveTag = (tagToRemove: string) => {
    setArtifactTags(artifactTags.filter(tag => tag !== tagToRemove))
  }

  const updateArtifactMutation = useMutation({
    mutationFn: ({ artifactId, formData }: { artifactId: string; formData: FormData }) =>
      api.updateArtifact(artifactId, formData),
    onSuccess: async (_, variables) => {
      await queryClient.invalidateQueries({ queryKey: ['artifacts'] })
      if (activeArtifact && variables.artifactId === activeArtifact.id) {
        const updatedArtifact = {
          ...activeArtifact,
          title: editTitle,
          description: editDescription || undefined,
          tags: artifactTags,
          color: editColor || undefined,
        }
        setActiveArtifact(updatedArtifact)
        await Promise.all([
          loadArtifactContent(updatedArtifact),
          loadArtifactChunks(updatedArtifact),
        ])
        setEditFile(null)
      }
    },
    onError: (error) => {
      console.error('Erro ao atualizar artefato:', error)
    }
  })

  const handleSaveArtifact = () => {
    if (!activeArtifact) {
      return
    }

    const formData = new FormData()
    formData.append('title', editTitle)
    formData.append('description', editDescription || '')
    formData.append('tags', JSON.stringify(artifactTags))
    if (editColor) {
      formData.append('color', editColor)
    }

    if (activeArtifact.source_type === 'TEXT') {
      formData.append('content', editContent)
    } else if (editFile) {
      formData.append('file', editFile)
    }

    updateArtifactMutation.mutate({ artifactId: activeArtifact.id, formData })
  }

  // Aprova feedback
  const approveFeedbackMutation = useMutation({
    mutationFn: api.approveFeedback,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-feedbacks'] })
      queryClient.invalidateQueries({ queryKey: ['learnings'] })
    },
  })

  // Rejeita feedback
  const rejectFeedbackMutation = useMutation({
    mutationFn: api.rejectFeedback,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-feedbacks'] })
    },
  })

  const handleSaveInstruction = () => {
    if (instructionText.trim()) {
      updateInstructionMutation.mutate(instructionText)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20 p-3 md:p-4 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-4 md:space-y-6">
        {/* Header */}
        <Card className="border-primary/20">
          <CardHeader>
            <div className="flex items-center gap-2 md:gap-3">
              <div className="p-2 rounded-lg bg-primary text-primary-foreground">
                <Shield className="h-4 w-4 md:h-5 md:w-5" />
              </div>
              <div>
                <CardTitle className="text-xl md:text-2xl lg:text-3xl bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                  Painel do Guardião Cultural
                </CardTitle>
                <CardDescription className="text-sm md:text-base mt-1">
                  Gerencie artefatos, instruções e feedbacks do agente cultural
                </CardDescription>
              </div>
            </div>
          </CardHeader>
        </Card>

        {feedbackAlert && (
          <Alert
            variant={feedbackAlert.type === 'error' ? 'destructive' : 'default'}
            className="border-l-4"
          >
            <AlertTitle>
              {feedbackAlert.type === 'error' ? 'Erro ao processar' : 'Tudo certo!'}
            </AlertTitle>
            <AlertDescription>{feedbackAlert.message}</AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="agent" className="space-y-4 md:space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="agent" className="gap-2">
              <Bot className="h-4 w-4" />
              Agente
            </TabsTrigger>
            <TabsTrigger value="artifacts" className="gap-2">
              <FileText className="h-4 w-4" />
              Artefatos
            </TabsTrigger>
            <TabsTrigger value="feedbacks" className="gap-2">
              <MessageSquare className="h-4 w-4" />
              Feedbacks
              {pendingFeedbacks.length > 0 && (
                <Badge variant="destructive" className="ml-1">
                  {pendingFeedbacks.length}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>

          {/* Tab: Instrução do Agente */}
          <TabsContent value="agent">
            <Card>
              <CardHeader>
                <CardTitle>Instrução Geral do Agente</CardTitle>
                <CardDescription>
                  Defina a personalidade e comportamento base do agente cultural
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="agent-instruction">Instrução</Label>
                  <Textarea
                    id="agent-instruction"
                    value={instructionText}
                    onChange={(e) => setInstructionText(e.target.value)}
                    placeholder="Digite a instrução geral do agente..."
                    className="min-h-[200px]"
                  />
                </div>
                <Button
                  onClick={handleSaveInstruction}
                  disabled={updateInstructionMutation.isPending}
                >
                  {updateInstructionMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Salvando...
                    </>
                  ) : (
                    <>
                      <Check className="h-4 w-4 mr-2" />
                      Salvar Instrução
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Tab: Artefatos */}
          <TabsContent value="artifacts">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle>Artefatos Culturais</CardTitle>
                    <CardDescription>
                      Gerencie os documentos e textos que alimentam o conhecimento do agente
                    </CardDescription>
                  </div>
                  <Button onClick={() => setShowAddModal(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Adicionar Artefato
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {artifacts.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Nenhum artefato cadastrado ainda.</p>
                    <p className="text-sm">Clique em "Adicionar Artefato" para começar.</p>
                  </div>
                ) : (
                  <div className="grid gap-3 md:gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                    {artifacts.map((artifact) => (
                      <Card
                        key={artifact.id}
                        className="relative cursor-pointer transition-colors hover:border-primary/40"
                        onClick={() => handleOpenArtifactModal(artifact)}
                      >
                        <CardHeader>
                          <div className="flex justify-between items-start gap-3">
                            <div className="flex-1 space-y-2">
                              <CardTitle className="text-lg">
                                {artifact.title}
                              </CardTitle>
                              <CardDescription className="flex items-center gap-2">
                                <Badge variant="secondary" className="uppercase tracking-wide text-[11px]">
                                  {artifact.source_type}
                                </Badge>
                                {artifact.color && (
                                  <span
                                    className="h-3 w-3 rounded-full border border-border"
                                    style={{ backgroundColor: artifact.color }}
                                  />
                                )}
                              </CardDescription>
                              <div className="flex flex-wrap gap-1">
                                {artifact.tags && artifact.tags.length > 0 ? (
                                  artifact.tags.slice(0, 3).map((tag, idx) => (
                                    <Badge key={idx} variant="outline" className="text-xs">
                                      {tag}
                                    </Badge>
                                  ))
                                ) : (
                                  <span className="text-xs text-muted-foreground">Sem tags</span>
                                )}
                                {artifact.tags && artifact.tags.length > 3 && (
                                  <Badge variant="outline" className="text-xs">
                                    +{artifact.tags.length - 3}
                                  </Badge>
                                )}
                              </div>
                            </div>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={(event) => {
                                event.stopPropagation()
                                deleteArtifactMutation.mutate(artifact.id)
                              }}
                              disabled={deleteArtifactMutation.isPending && deletingArtifactId !== null}
                              className="text-destructive hover:text-destructive"
                            >
                              {deleteArtifactMutation.isPending && deletingArtifactId === artifact.id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Trash2 className="h-4 w-4" />
                              )}
                            </Button>
                          </div>
                        </CardHeader>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Tab: Feedbacks */}
          <TabsContent value="feedbacks">
            <Card>
              <CardHeader>
                <CardTitle>Feedbacks Pendentes</CardTitle>
                <CardDescription>
                  Revise e modere os feedbacks enviados pelos usuários
                </CardDescription>
              </CardHeader>
              <CardContent>
                {pendingFeedbacks.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Nenhum feedback pendente no momento.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {pendingFeedbacks.map((feedback) => (
                      <Card key={feedback.id}>
                        <CardContent className="p-6 space-y-4">
                          {feedback.message_preview && (
                            <>
                              <div className="p-4 rounded-lg bg-muted border-l-4 border-primary">
                                <p className="text-xs font-semibold text-muted-foreground mb-2">
                                  Mensagem do Agente:
                                </p>
                                <p className="text-sm">{feedback.message_preview}</p>
                              </div>
                              <Separator />
                            </>
                          )}
                          <div>
                            <p className="text-xs font-semibold text-muted-foreground mb-2">
                              Feedback do Usuário:
                            </p>
                            <p className="text-sm">{feedback.feedback_text}</p>
                          </div>
                          <Separator />
                          <div className="flex gap-2">
                            <Button
                              onClick={() => approveFeedbackMutation.mutate(feedback.id)}
                              disabled={approveFeedbackMutation.isPending}
                              variant="default"
                              className="bg-green-600 hover:bg-green-700"
                            >
                              {approveFeedbackMutation.isPending ? (
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              ) : (
                                <Check className="h-4 w-4 mr-2" />
                              )}
                              Aprovar
                            </Button>
                            <Button
                              onClick={() => rejectFeedbackMutation.mutate(feedback.id)}
                              disabled={rejectFeedbackMutation.isPending}
                              variant="destructive"
                            >
                              {rejectFeedbackMutation.isPending ? (
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              ) : (
                                <X className="h-4 w-4 mr-2" />
                              )}
                              Rejeitar
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Modal Adicionar Artefato */}
        <Dialog open={showAddModal} onOpenChange={setShowAddModal}>
          <DialogContent className="w-[95vw] sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>Adicionar Novo Artefato</DialogTitle>
              <DialogDescription>
                Adicione um novo documento ou texto para enriquecer o conhecimento do agente
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="artifact-title">Título do Artefato</Label>
                <Input
                  id="artifact-title"
                  placeholder="Ex: Manual de Valores"
                  value={addTitle}
                  onChange={(e) => setAddTitle(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label>Tipo de Artefato</Label>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant={addType === 'text' ? 'default' : 'outline'}
                    className="flex-1"
                    onClick={() => setAddType('text')}
                  >
                    Texto
                  </Button>
                  <Button
                    type="button"
                    variant={addType === 'pdf' ? 'default' : 'outline'}
                    className="flex-1"
                    onClick={() => setAddType('pdf')}
                  >
                    PDF
                  </Button>
                </div>
              </div>

              {addType === 'text' ? (
                <div className="space-y-2">
                  <Label htmlFor="artifact-content">Conteúdo do Artefato</Label>
                  <Textarea
                    id="artifact-content"
                    placeholder="Digite o conteúdo do artefato aqui..."
                    value={addText}
                    onChange={(e) => setAddText(e.target.value)}
                    className="min-h-[200px]"
                  />
                </div>
              ) : (
                <div className="space-y-2">
                  <Label htmlFor="artifact-file">Arquivo PDF</Label>
                  <Input
                    id="artifact-file"
                    type="file"
                    accept=".pdf"
                    onChange={(e) => setAddFile(e.target.files?.[0] || null)}
                  />
                </div>
              )}
            </div>
            
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setShowAddModal(false)
                  setAddTitle('')
                  setAddText('')
                  setAddFile(null)
                }}
              >
                Cancelar
              </Button>
              <Button
                onClick={() => createArtifactMutation.mutate()}
                disabled={createArtifactMutation.isPending || !addTitle.trim()}
              >
                {createArtifactMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Enviando...
                  </>
                ) : (
                  <>
                    <Plus className="h-4 w-4 mr-2" />
                    Adicionar
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Modal de Artefato */}
        <Dialog open={!!activeArtifact} onOpenChange={(open) => !open && handleCloseArtifactModal()}>
          <DialogContent className="w-[95vw] sm:max-w-5xl max-h-[90vh]">
            <DialogHeader>
              <DialogTitle>{activeArtifact?.title ?? 'Artefato'}</DialogTitle>
              <DialogDescription>
                Gerencie o conteúdo original e a segmentação em chunks deste artefato.
              </DialogDescription>
            </DialogHeader>

            <Tabs value={artifactModalTab} onValueChange={(value) => setArtifactModalTab(value as 'edit' | 'chunks')} className="mt-2">
              <TabsList className="grid grid-cols-2 w-full">
                <TabsTrigger value="edit">Editar Artefato</TabsTrigger>
                <TabsTrigger value="chunks">Visualizar Chunks</TabsTrigger>
              </TabsList>

              <TabsContent value="edit" className="mt-4">
                <ScrollArea className="max-h-[55vh] pr-4">
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="artifact-title-edit">Título</Label>
                        <Input
                          id="artifact-title-edit"
                          value={editTitle}
                          onChange={(event) => setEditTitle(event.target.value)}
                          placeholder="Título do artefato"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="artifact-color-edit">Cor (opcional)</Label>
                        <Input
                          id="artifact-color-edit"
                          value={editColor ?? ''}
                          onChange={(event) => setEditColor(event.target.value || null)}
                          placeholder="Ex: #2563EB"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="artifact-description-edit">Descrição</Label>
                      <Textarea
                        id="artifact-description-edit"
                        value={editDescription}
                        onChange={(event) => setEditDescription(event.target.value)}
                        placeholder="Breve descrição do artefato"
                        className="min-h-[100px]"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Tags</Label>
                      <div className="flex flex-wrap gap-2 p-3 min-h-[48px] border rounded-md bg-muted/50">
                        {artifactTags.length === 0 ? (
                          <span className="text-sm text-muted-foreground">Nenhuma tag adicionada</span>
                        ) : (
                          artifactTags.map((tag) => (
                            <Badge key={tag} variant="secondary" className="flex items-center gap-1">
                              {tag}
                              <button
                                type="button"
                                onClick={() => handleRemoveTag(tag)}
                                className="ml-1 hover:text-destructive"
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </Badge>
                          ))
                        )}
                      </div>
                      <div className="flex gap-2">
                        <Input
                          placeholder="Adicionar nova tag"
                          value={newTag}
                          onChange={(event) => setNewTag(event.target.value)}
                          onKeyDown={(event) => {
                            if (event.key === 'Enter') {
                              event.preventDefault()
                              handleAddTag()
                            }
                          }}
                        />
                        <Button type="button" onClick={handleAddTag} disabled={!newTag.trim()}>
                          <Plus className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>

                    {activeArtifact?.source_type === 'TEXT' ? (
                      <div className="space-y-2">
                        <Label htmlFor="artifact-content-edit">Conteúdo Original (edite para reprocessar os chunks)</Label>
                        {isLoadingArtifactContent ? (
                          <div className="flex items-center justify-center py-8 text-muted-foreground">
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" /> Carregando conteúdo...
                          </div>
                        ) : (
                          <Textarea
                            id="artifact-content-edit"
                            value={editContent}
                            onChange={(event) => setEditContent(event.target.value)}
                            className="min-h-[220px] font-mono text-sm"
                            placeholder="Conteúdo original do artefato"
                          />
                        )}
                        <p className="text-xs text-muted-foreground">
                          Ao salvar, o texto será fracionado novamente com base no chunker inteligente.
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <Label>Arquivo PDF</Label>
                        {activeArtifact?.source_url ? (
                          <Button
                            type="button"
                            variant="outline"
                            asChild
                          >
                            <a href={activeArtifact.source_url} target="_blank" rel="noreferrer">
                              Abrir PDF atual em nova aba
                            </a>
                          </Button>
                        ) : (
                          <p className="text-sm text-muted-foreground">Não há link registrado para o PDF.</p>
                        )}
                        <div className="space-y-2">
                          <Label htmlFor="artifact-file-edit">Substituir arquivo PDF (opcional)</Label>
                          <Input
                            id="artifact-file-edit"
                            type="file"
                            accept=".pdf"
                            onChange={(event) => {
                              const file = event.target.files?.[0] || null
                              setEditFile(file)
                            }}
                          />
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Envie um novo PDF para reprocessar o artefato. O arquivo atual permanecerá caso nenhum novo seja selecionado.
                        </p>
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </TabsContent>

              <TabsContent value="chunks" className="mt-4">
                {isLoadingChunks ? (
                  <div className="flex items-center justify-center py-12 text-muted-foreground">
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" /> Processando chunking...
                  </div>
                ) : chunksError ? (
                  <div className="py-8 text-center text-sm text-destructive">{chunksError}</div>
                ) : artifactChunks.length === 0 ? (
                  <div className="py-8 text-center text-sm text-muted-foreground">
                    Nenhum chunk encontrado para este artefato.
                  </div>
                ) : (
                  <ScrollArea className="max-h-[55vh] pr-4">
                    <div className="space-y-3">
                      {artifactChunks.map((chunk) => {
                        const metadata = chunk.metadata
                        const depth = metadata?.breadcrumbs ? metadata.breadcrumbs.length : 0
                        return (
                          <div
                            key={chunk.id}
                            className="rounded-lg border border-border bg-card/60 p-4 space-y-3"
                            style={{ marginLeft: depth * 12 }}
                          >
                            <div className="flex flex-wrap items-center gap-2">
                              <Badge variant="outline">#{metadata?.position ?? 0}</Badge>
                              {metadata?.section_title ? (
                                <span className="font-semibold text-sm">
                                  {metadata.section_title}
                                </span>
                              ) : (
                                <span className="font-semibold text-sm text-muted-foreground">Chunk sem título</span>
                              )}
                              {metadata?.content_type && (
                                <Badge variant="secondary" className="uppercase text-[10px] tracking-wide">
                                  {metadata.content_type}
                                </Badge>
                              )}
                              {metadata?.token_count != null && (
                                <Badge variant="outline" className="text-[11px]">
                                  {metadata.token_count} tokens
                                </Badge>
                              )}
                            </div>
                            {metadata?.breadcrumbs && metadata.breadcrumbs.length > 0 && (
                              <p className="text-xs text-muted-foreground">
                                {metadata.breadcrumbs.join(' › ')}
                              </p>
                            )}
                            <p className="text-sm whitespace-pre-wrap leading-relaxed">
                              {chunk.content}
                            </p>
                          </div>
                        )
                      })}
                    </div>
                  </ScrollArea>
                )}
              </TabsContent>
            </Tabs>

            <DialogFooter className="mt-4">
              <Button variant="outline" onClick={handleCloseArtifactModal}>
                Fechar
              </Button>
              {artifactModalTab === 'edit' && (
                <Button
                  onClick={handleSaveArtifact}
                  disabled={updateArtifactMutation.isPending || !activeArtifact || (activeArtifact.source_type === 'TEXT' && isLoadingArtifactContent)}
                >
                  {updateArtifactMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" /> Salvando...
                    </>
                  ) : (
                    <>
                      <Check className="h-4 w-4 mr-2" /> Salvar alterações
                    </>
                  )}
                </Button>
              )}
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}

export default AdminView
