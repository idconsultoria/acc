import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import { Loader2, Plus, Trash2, Check, X, Shield, FileText, MessageSquare, Bot, Tag, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

function AdminView() {
  const queryClient = useQueryClient()
  const [showAddModal, setShowAddModal] = useState(false)
  const [addTitle, setAddTitle] = useState('')
  const [addText, setAddText] = useState('')
  const [addFile, setAddFile] = useState<File | null>(null)
  const [addType, setAddType] = useState<'text' | 'pdf'>('text')
  const [instructionText, setInstructionText] = useState('')
  const [showTagsModal, setShowTagsModal] = useState<string | null>(null)
  const [artifactTags, setArtifactTags] = useState<string[]>([])
  const [newTag, setNewTag] = useState('')

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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['artifacts'] })
      setShowAddModal(false)
      setAddTitle('')
      setAddText('')
      setAddFile(null)
    },
  })

  // Deleta artefato
  const deleteArtifactMutation = useMutation({
    mutationFn: api.deleteArtifact,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['artifacts'] })
    },
  })

  // Atualiza tags do artefato
  const updateTagsMutation = useMutation({
    mutationFn: ({ artifactId, tags }: { artifactId: string; tags: string[] }) =>
      api.updateArtifactTags(artifactId, tags),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['artifacts'] })
      setShowTagsModal(null)
      setArtifactTags([])
      setNewTag('')
    },
  })

  // Abre modal de tags
  const handleOpenTagsModal = (artifact: typeof artifacts[0]) => {
    setArtifactTags(artifact.tags || [])
    setShowTagsModal(artifact.id)
    setNewTag('')
  }

  // Adiciona tag
  const handleAddTag = () => {
    if (newTag.trim() && !artifactTags.includes(newTag.trim())) {
      setArtifactTags([...artifactTags, newTag.trim()])
      setNewTag('')
    }
  }

  // Remove tag
  const handleRemoveTag = (tagToRemove: string) => {
    setArtifactTags(artifactTags.filter(tag => tag !== tagToRemove))
  }

  // Salva tags
  const handleSaveTags = () => {
    if (showTagsModal) {
      updateTagsMutation.mutate({ artifactId: showTagsModal, tags: artifactTags })
    }
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
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20 p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <Card className="border-primary/20">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary text-primary-foreground">
                <Shield className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-3xl bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                  Painel do Guardião Cultural
                </CardTitle>
                <CardDescription className="text-base mt-1">
                  Gerencie artefatos, instruções e feedbacks do agente cultural
                </CardDescription>
              </div>
            </div>
          </CardHeader>
        </Card>

        <Tabs defaultValue="agent" className="space-y-6">
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
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {artifacts.map((artifact) => (
                      <Card key={artifact.id} className="relative">
                        <CardHeader>
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <CardTitle className="text-lg">{artifact.title}</CardTitle>
                              <CardDescription className="mt-1">
                                <Badge variant="secondary">
                                  {artifact.source_type}
                                </Badge>
                              </CardDescription>
                              {/* Tags */}
                              <div className="flex flex-wrap gap-1 mt-2">
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
                            <div className="flex gap-1">
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleOpenTagsModal(artifact)}
                                className="text-primary hover:text-primary"
                              >
                                <Tag className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => deleteArtifactMutation.mutate(artifact.id)}
                                disabled={deleteArtifactMutation.isPending}
                                className="text-destructive hover:text-destructive"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
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
          <DialogContent>
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

        {/* Modal de Tags */}
        <Dialog open={!!showTagsModal} onOpenChange={(open) => !open && setShowTagsModal(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Gerenciar Tags do Artefato</DialogTitle>
              <DialogDescription>
                Adicione ou remova tags para categorizar este artefato cultural
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              {/* Tags atuais */}
              <div className="space-y-2">
                <Label>Tags Atuais</Label>
                <div className="flex flex-wrap gap-2 p-3 min-h-[60px] border rounded-md bg-muted/50">
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
                          <XCircle className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))
                  )}
                </div>
              </div>

              {/* Adicionar nova tag */}
              <div className="space-y-2">
                <Label htmlFor="new-tag">Adicionar Tag</Label>
                <div className="flex gap-2">
                  <Input
                    id="new-tag"
                    placeholder="Ex: Artigo, Comunicação, Política..."
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        handleAddTag()
                      }
                    }}
                  />
                  <Button type="button" onClick={handleAddTag} disabled={!newTag.trim()}>
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
            
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setShowTagsModal(null)
                  setArtifactTags([])
                  setNewTag('')
                }}
              >
                Cancelar
              </Button>
              <Button
                onClick={handleSaveTags}
                disabled={updateTagsMutation.isPending}
              >
                {updateTagsMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Salvando...
                  </>
                ) : (
                  <>
                    <Check className="h-4 w-4 mr-2" />
                    Salvar Tags
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}

export default AdminView
