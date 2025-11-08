import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, Artifact, ArtifactChunk, ArtifactContentResponse } from '@/api/client'
import { Loader2, Plus, Trash2, FileText, File, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import AdminSidebar from '@/components/shared/AdminSidebar'

// Paleta de cores inspirada no shadcn-ui com bordas e fundos sutis
const COLOR_PALETTE = [
  { 
    name: 'Padrão', 
    value: null, 
    styles: '', 
    preview: 'bg-background border-2 border-dashed border-muted-foreground/25',
    description: 'Sem destaque'
  },
  { 
    name: 'Slate', 
    value: 'slate', 
    styles: 'bg-slate-50/50 border-slate-200 dark:bg-slate-950/50 dark:border-slate-800', 
    preview: 'bg-slate-100 border-2 border-slate-300',
    description: 'Neutro e profissional'
  },
  { 
    name: 'Zinc', 
    value: 'zinc', 
    styles: 'bg-zinc-50/50 border-zinc-200 dark:bg-zinc-950/50 dark:border-zinc-800', 
    preview: 'bg-zinc-100 border-2 border-zinc-300',
    description: 'Moderno e elegante'
  },
  { 
    name: 'Rose', 
    value: 'rose', 
    styles: 'bg-rose-50/50 border-rose-200 dark:bg-rose-950/50 dark:border-rose-800', 
    preview: 'bg-rose-100 border-2 border-rose-300',
    description: 'Delicado e acolhedor'
  },
  { 
    name: 'Blue', 
    value: 'blue', 
    styles: 'bg-blue-50/50 border-blue-200 dark:bg-blue-950/50 dark:border-blue-800', 
    preview: 'bg-blue-100 border-2 border-blue-300',
    description: 'Confiável e calmo'
  },
  { 
    name: 'Green', 
    value: 'green', 
    styles: 'bg-green-50/50 border-green-200 dark:bg-green-950/50 dark:border-green-800', 
    preview: 'bg-green-100 border-2 border-green-300',
    description: 'Natural e positivo'
  },
  { 
    name: 'Violet', 
    value: 'violet', 
    styles: 'bg-violet-50/50 border-violet-200 dark:bg-violet-950/50 dark:border-violet-800', 
    preview: 'bg-violet-100 border-2 border-violet-300',
    description: 'Criativo e único'
  },
  { 
    name: 'Amber', 
    value: 'amber', 
    styles: 'bg-amber-50/50 border-amber-200 dark:bg-amber-950/50 dark:border-amber-800', 
    preview: 'bg-amber-100 border-2 border-amber-300',
    description: 'Caloroso e energético'
  },
  { 
    name: 'Orange', 
    value: 'orange', 
    styles: 'bg-orange-50/50 border-orange-200 dark:bg-orange-950/50 dark:border-orange-800', 
    preview: 'bg-orange-100 border-2 border-orange-300',
    description: 'Vibrante e atencioso'
  },
  { 
    name: 'Emerald', 
    value: 'emerald', 
    styles: 'bg-emerald-50/50 border-emerald-200 dark:bg-emerald-950/50 dark:border-emerald-800', 
    preview: 'bg-emerald-100 border-2 border-emerald-300',
    description: 'Fresco e renovador'
  },
]

// Função para obter cor aleatória da paleta
const getRandomColor = () => {
  const colorsWithValue = COLOR_PALETTE.filter(c => c.value !== null)
  const randomIndex = Math.floor(Math.random() * colorsWithValue.length)
  return colorsWithValue[randomIndex].value
}

function AdminArtifactsView() {
  const queryClient = useQueryClient()

  // Estado para criação de artefatos
  const [showAddModal, setShowAddModal] = useState(false)
  const [addTitle, setAddTitle] = useState('')
  const [addText, setAddText] = useState('')
  const [addFile, setAddFile] = useState<File | null>(null)
  const [addType, setAddType] = useState<'text' | 'pdf'>('text')
  const [addColor, setAddColor] = useState<string | null>(getRandomColor())

  // Estado para edição/visualização
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
  const [originalTextContent, setOriginalTextContent] = useState('')
  const [editColor, setEditColor] = useState<string | null>(null)
  const [artifactTags, setArtifactTags] = useState<string[]>([])
  const [newTag, setNewTag] = useState('')
  const [editFile, setEditFile] = useState<File | null>(null)
  const [feedbackAlert, setFeedbackAlert] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [isDeleting, setIsDeleting] = useState<string | null>(null)

  // Busca artefatos
  const { data: artifacts = [], isLoading: isLoadingArtifacts } = useQuery({
    queryKey: ['artifacts'],
    queryFn: api.listArtifacts,
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
      
      if (addColor) {
        formData.append('color', addColor)
      }
      
      return api.createArtifact(formData)
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['artifacts'] })
      setShowAddModal(false)
      setAddTitle('')
      setAddText('')
      setAddFile(null)
      setAddType('text')
      setAddColor(getRandomColor())
      setFeedbackAlert({ type: 'success', message: 'Artefato adicionado com sucesso.' })
    },
    onError: (error: unknown) => {
      let message = 'Não foi possível adicionar o artefato. Tente novamente.'
      if (typeof error === 'object' && error !== null) {
        const maybeAxios = error as { response?: { data?: { detail?: string } }; message?: string }
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

  const loadArtifactContent = async (artifact: Artifact) => {
    setIsLoadingArtifactContent(true)
    try {
      const contentResponse = await api.getArtifactContent(artifact.id)
      setArtifactContent(contentResponse)
      if (contentResponse.source_type === 'TEXT') {
        setEditContent(contentResponse.content)
        setOriginalTextContent(contentResponse.content)
      } else {
        setEditContent('')
        setOriginalTextContent('')
      }
    } catch (error) {
      console.error('Erro ao carregar conteúdo do artefato:', error)
      setArtifactContent(null)
      setEditContent('')
      setOriginalTextContent('')
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
      console.error('Erro ao carregar chunks do artefato:', error)
      setArtifactChunks([])
      setChunksError('Não foi possível carregar os chunks deste artefato.')
    } finally {
      setIsLoadingChunks(false)
    }
  }

  // Edita artefato
  const updateArtifactMutation = useMutation({
    mutationFn: async () => {
      if (!activeArtifact) return

      const formData = new FormData()
      formData.append('title', editTitle)
      formData.append('description', editDescription || '')
      formData.append('tags', JSON.stringify(artifactTags))
      formData.append('color', editColor ?? '')

      const shouldRechunk =
        activeArtifact.source_type === 'TEXT' && editContent !== originalTextContent

      if (shouldRechunk) {
        formData.append('content', editContent)
      }

      if (activeArtifact.source_type === 'PDF' && editFile) {
        formData.append('file', editFile)
      }

      return api.updateArtifact(activeArtifact.id, formData)
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['artifacts'] })
      if (activeArtifact) {
        const updatedArtifact: Artifact = {
          ...activeArtifact,
          title: editTitle,
          description: editDescription || undefined,
          tags: artifactTags,
          color: editColor || undefined,
        }
        setActiveArtifact(updatedArtifact)
        await Promise.all([loadArtifactContent(updatedArtifact), loadArtifactChunks(updatedArtifact)])
      }
      setFeedbackAlert({ type: 'success', message: 'Artefato atualizado com sucesso.' })
      setEditFile(null)
    },
    onError: (error: unknown) => {
      let message = 'Não foi possível atualizar o artefato. Tente novamente.'
      if (typeof error === 'object' && error !== null) {
        const maybeAxios = error as { response?: { data?: { detail?: string } }; message?: string }
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
    mutationFn: (artifactId: string) => api.deleteArtifact(artifactId),
    onMutate: (artifactId: string) => {
      setIsDeleting(artifactId)
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['artifacts'] })
      setFeedbackAlert({ type: 'success', message: 'Artefato excluído com sucesso.' })
      if (activeArtifact) {
        handleCloseArtifactModal()
      }
    },
    onError: (error: unknown) => {
      let message = 'Não foi possível excluir o artefato. Tente novamente.'
      if (typeof error === 'object' && error !== null) {
        const maybeAxios = error as { response?: { data?: { detail?: string } }; message?: string }
        if (maybeAxios.response?.data?.detail) {
          message = maybeAxios.response.data.detail
        } else if (maybeAxios.message) {
          message = maybeAxios.message
        }
      } else if (typeof error === 'string') {
        message = error
      }
      setFeedbackAlert({ type: 'error', message })
    },
    onSettled: () => {
      setIsDeleting(null)
    }
  })

  function handleAddTag() {
    if (newTag.trim() && !artifactTags.includes(newTag.trim())) {
      setArtifactTags([...artifactTags, newTag.trim()])
      setNewTag('')
    }
  }

  function handleRemoveTag(tagToRemove: string) {
    setArtifactTags(artifactTags.filter(tag => tag !== tagToRemove))
  }

  async function handleOpenArtifactModal(artifact: Artifact) {
    setActiveArtifact(artifact)
    setArtifactModalTab('edit')
    setEditTitle(artifact.title)
    setEditDescription(artifact.description || '')
    setEditColor(artifact.color || null)
    setArtifactTags(artifact.tags || [])
    setNewTag('')
    setEditFile(null)
    await Promise.all([loadArtifactContent(artifact), loadArtifactChunks(artifact)])
  }

  function handleCloseArtifactModal() {
    setActiveArtifact(null)
    setArtifactModalTab('edit')
    setArtifactContent(null)
    setArtifactChunks([])
    setChunksError(null)
    setEditTitle('')
    setEditDescription('')
    setEditContent('')
    setOriginalTextContent('')
    setEditColor(null)
    setArtifactTags([])
    setNewTag('')
    setEditFile(null)
  }

  // Função para formatar data
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    return `${months[date.getMonth()]} ${date.getDate().toString().padStart(2, '0')}, ${date.getFullYear()}`
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
                  Artefatos Culturais
                </h1>
              </div>

              {feedbackAlert && (
                <Alert
                  variant={feedbackAlert.type === 'error' ? 'destructive' : 'default'}
                  className="mb-6 border-l-4"
                >
                  <AlertTitle>
                    {feedbackAlert.type === 'error' ? 'Erro ao processar' : 'Tudo certo!'}
                  </AlertTitle>
                  <AlertDescription>{feedbackAlert.message}</AlertDescription>
                </Alert>
              )}
              
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
                {/* Card Adicionar Novo */}
                <Card
                  className="border-2 border-dashed border-border hover:border-primary hover:bg-primary/5 transition-colors cursor-pointer group"
                  onClick={() => {
                    setAddColor(getRandomColor())
                    setShowAddModal(true)
                  }}
                >
                  <CardContent className="flex flex-col items-center justify-center p-6 text-center">
                    <Plus className="h-12 w-12 text-primary mb-2" />
                    <p className="text-sm font-semibold text-primary">Adicionar Novo Artefato</p>
                  </CardContent>
                </Card>

                {/* Skeleton Loading */}
                {isLoadingArtifacts ? (
                  <>
                    {[...Array(6)].map((_, i) => (
                      <Card key={`skeleton-${i}`} className="relative">
                        <CardContent className="p-4 flex flex-col">
                          <div className="flex-1">
                            <Skeleton className="h-10 w-10 mb-3" />
                            <Skeleton className="h-5 w-3/4 mb-2" />
                            <Skeleton className="h-3 w-1/2 mb-2" />
                            <div className="flex flex-wrap gap-1 mt-2">
                              <Skeleton className="h-5 w-16 rounded-full" />
                              <Skeleton className="h-5 w-20 rounded-full" />
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </>
                ) : (
                  /* Cards de Artefatos */
                  artifacts.map((artifact) => {
                  const colorConfig = COLOR_PALETTE.find(c => c.value === artifact.color)
                  const colorStyles = colorConfig?.styles || ''
                  
                  return (
                  <Card
                    key={artifact.id}
                    className={`relative group hover:shadow-lg transition-all duration-200 cursor-pointer ${colorStyles}`}
                    onClick={() => handleOpenArtifactModal(artifact)}
                  >
                    <CardContent className="p-4 flex flex-col">
                      <div className="absolute top-3 right-3 flex gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteArtifactMutation.mutate(artifact.id)
                          }}
                          disabled={isDeleting === artifact.id}
                          className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                        >
                          {isDeleting === artifact.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </Button>
                      </div>

                      <div className="flex-1">
                        {artifact.source_type === 'PDF' ? (
                          <File className="h-10 w-10 text-destructive mb-3" />
                        ) : (
                          <FileText className="h-10 w-10 text-primary mb-3" />
                        )}
                        <h3 className="font-bold text-foreground mb-1 line-clamp-2 min-h-[44px]">{artifact.title}</h3>
                        <p className="text-xs text-muted-foreground">
                          Adicionado {formatDate(artifact.created_at)}
                        </p>
                        {artifact.source_type === 'PDF' && artifact.source_url && (
                          <p className="mt-1 text-xs text-muted-foreground line-clamp-1">
                            PDF original disponível
                          </p>
                        )}
                        {artifact.tags && artifact.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {artifact.tags.slice(0, 2).map((tag, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                            {artifact.tags.length > 2 && (
                              <Badge variant="outline" className="text-xs">
                                +{artifact.tags.length - 2}
                              </Badge>
                            )}
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                  )
                  })
                )}
              </div>
            </section>
          </div>
        </div>
      </main>

      {/* Modal Adicionar Artefato */}
      <Dialog open={showAddModal} onOpenChange={setShowAddModal}>
        <DialogContent className="w-[95vw] max-w-4xl max-h-[90vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>Adicionar Novo Artefato</DialogTitle>
            <DialogDescription>
              Adicione um novo documento ou texto para enriquecer o conhecimento do agente
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 overflow-y-auto pr-2 flex-1">
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
                <Label htmlFor="artifact-text">Conteúdo do Texto</Label>
                <Textarea
                  id="artifact-text"
                  placeholder="Digite o conteúdo do artefato..."
                  value={addText}
                  onChange={(e) => setAddText(e.target.value)}
                  className="min-h-[300px] font-mono text-sm"
                />
                <p className="text-xs text-muted-foreground">
                  O texto será processado automaticamente em chunks para busca semântica
                </p>
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
                <p className="text-xs text-muted-foreground">
                  O PDF será extraído, processado em chunks e indexado para busca
                </p>
              </div>
            )}

            <div className="space-y-3">
              <Label>Tema do Card (opcional)</Label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 md:gap-3">
                {COLOR_PALETTE.map((color) => (
                  <button
                    key={color.value || 'none'}
                    type="button"
                    onClick={() => setAddColor(color.value)}
                    className={`group flex flex-col items-center gap-2 p-3 rounded-lg border-2 transition-all ${
                      addColor === color.value
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50 hover:bg-accent'
                    }`}
                  >
                    <div className={`w-full h-10 rounded-md ${color.preview}`} />
                    <div className="text-center">
                      <p className="text-xs font-medium">{color.name}</p>
                      <p className="text-[10px] text-muted-foreground line-clamp-1">{color.description}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
          
          <DialogFooter className="flex-shrink-0">
            <Button
              variant="outline"
              onClick={() => {
                setShowAddModal(false)
                setAddTitle('')
                setAddText('')
                setAddFile(null)
                setAddColor(getRandomColor())
              }}
            >
              Cancelar
            </Button>
            <Button
              onClick={() => createArtifactMutation.mutate()}
              disabled={
                createArtifactMutation.isPending || 
                !addTitle.trim() || 
                (addType === 'text' ? !addText.trim() : !addFile)
              }
            >
              {createArtifactMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Processando...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4 mr-2" />
                  Adicionar Artefato
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!activeArtifact} onOpenChange={(open) => {
        if (!open) {
          handleCloseArtifactModal()
        }
      }}>
        <DialogContent className="w-[95vw] max-w-5xl max-h-[90vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>{activeArtifact ? `Gerenciar ${activeArtifact.title}` : 'Gerenciar Artefato'}</DialogTitle>
            <DialogDescription>
              Revise os dados originais, atualize informações e visualize os chunks estruturados.
            </DialogDescription>
          </DialogHeader>

          {activeArtifact && (
            <>
              <Tabs value={artifactModalTab} onValueChange={(value) => setArtifactModalTab(value as 'edit' | 'chunks')} className="flex-1 flex flex-col">
                <TabsList className="grid grid-cols-2 w-full">
                  <TabsTrigger value="edit">Detalhes e Edição</TabsTrigger>
                  <TabsTrigger value="chunks">Visualização de Chunks</TabsTrigger>
                </TabsList>

                <TabsContent value="edit" className="flex-1 focus:outline-none">
                  <ScrollArea className="h-[55vh] pr-4">
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="edit-title">Título do Artefato</Label>
                        <Input
                          id="edit-title"
                          placeholder="Ex: Manual de Valores"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="edit-description">Descrição (opcional)</Label>
                        <Textarea
                          id="edit-description"
                          placeholder="Adicione uma descrição do artefato..."
                          value={editDescription}
                          onChange={(e) => setEditDescription(e.target.value)}
                          className="min-h-[80px]"
                        />
                        <p className="text-xs text-muted-foreground">
                          Esta descrição ajuda a contextualizar o artefato para outros administradores.
                        </p>
                      </div>

                      {activeArtifact.source_type === 'TEXT' && (
                        <div className="space-y-2">
                          <Label htmlFor="edit-content">Conteúdo Original</Label>
                          {isLoadingArtifactContent ? (
                            <div className="flex items-center justify-center p-8 border rounded-md bg-muted/50">
                              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                              <span className="ml-2 text-sm text-muted-foreground">Carregando conteúdo...</span>
                            </div>
                          ) : (
                            <Textarea
                              id="edit-content"
                              placeholder="Edite o conteúdo do artefato..."
                              value={editContent}
                              onChange={(e) => setEditContent(e.target.value)}
                              className="min-h-[300px] font-mono text-sm"
                            />
                          )}
                          <p className="text-xs text-muted-foreground">
                            Alterações neste texto irão disparar uma nova etapa de chunking inteligente ao salvar.
                          </p>
                        </div>
                      )}

                      {activeArtifact.source_type === 'PDF' && (
                        <div className="space-y-3 p-4 border rounded-lg bg-muted/50">
                          <div>
                            <Label>Arquivo PDF Original</Label>
                            <p className="text-sm text-muted-foreground mb-2">
                              Visualize o arquivo original ou envie uma nova versão para reprocessar os chunks.
                            </p>
                            {(() => {
                              const pdfSourceUrl =
                                artifactContent?.source_type === 'PDF'
                                  ? artifactContent.source_url
                                  : activeArtifact.source_url || undefined
                              return pdfSourceUrl ? (
                                <Button variant="link" className="px-0" asChild>
                                  <a href={pdfSourceUrl} target="_blank" rel="noopener noreferrer">
                                    Abrir PDF original em nova aba
                                  </a>
                                </Button>
                              ) : (
                                <p className="text-xs text-muted-foreground">Nenhum link direto disponível para este PDF.</p>
                              )
                            })()}
                          </div>
                          <div className="space-y-2 pt-2">
                            <Label htmlFor="replace-pdf">Substituir PDF</Label>
                            <Input
                              id="replace-pdf"
                              type="file"
                              accept=".pdf"
                              onChange={(e) => setEditFile(e.target.files?.[0] || null)}
                            />
                            {editFile && (
                              <p className="text-xs text-muted-foreground">Arquivo selecionado: {editFile.name}</p>
                            )}
                            <p className="text-xs text-muted-foreground">
                              Ao salvar, o novo PDF será processado e todos os chunks serão atualizados.
                            </p>
                          </div>
                        </div>
                      )}

                      <div className="space-y-2">
                        <Label>Tags</Label>
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
                                  x
                                </button>
                              </Badge>
                            ))
                          )}
                        </div>
                        <div className="flex gap-2">
                          <Input
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
                          <Button type="button" size="icon" onClick={handleAddTag} disabled={!newTag.trim()}>
                            <Plus className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>

                      <div className="space-y-3">
                        <Label>Tema do Card (opcional)</Label>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 md:gap-3">
                          {COLOR_PALETTE.map((color) => (
                            <button
                              key={color.value || 'none'}
                              type="button"
                              onClick={() => setEditColor(color.value)}
                              className={`group flex flex-col items-center gap-2 p-3 rounded-lg border-2 transition-all ${
                                editColor === color.value
                                  ? 'border-primary bg-primary/5'
                                  : 'border-border hover:border-primary/50 hover:bg-accent'
                              }`}
                            >
                              <div className={`w-full h-10 rounded-md ${color.preview}`} />
                              <div className="text-center">
                                <p className="text-xs font-medium">{color.name}</p>
                                <p className="text-[10px] text-muted-foreground line-clamp-1">{color.description}</p>
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </ScrollArea>
                </TabsContent>

                <TabsContent value="chunks" className="flex-1 focus:outline-none">
                  <ScrollArea className="h-[55vh] pr-4">
                    <div className="space-y-4">
                      <div>
                        <h3 className="text-sm font-semibold text-foreground">Estrutura do Artefato</h3>
                        <p className="text-xs text-muted-foreground">
                          Visualize os chunks gerados, incluindo hierarquia e metadados estruturais.
                        </p>
                      </div>

                      {isLoadingChunks ? (
                        <div className="flex items-center justify-center p-8 border rounded-md bg-muted/50">
                          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                          <span className="ml-2 text-sm text-muted-foreground">Carregando chunks...</span>
                        </div>
                      ) : chunksError ? (
                        <Alert variant="destructive">
                          <AlertTitle>Não foi possível carregar os chunks</AlertTitle>
                          <AlertDescription>{chunksError}</AlertDescription>
                        </Alert>
                      ) : artifactChunks.length === 0 ? (
                        <p className="text-sm text-muted-foreground">
                          Nenhum chunk encontrado para este artefato ainda.
                        </p>
                      ) : (
                        <div className="space-y-3">
                          {artifactChunks.map((chunk) => {
                            const metadata = chunk.metadata
                            const breadcrumbs = metadata?.breadcrumbs ?? []
                            const indentation = breadcrumbs.length * 12
                            return (
                              <div
                                key={chunk.id}
                                className="rounded-lg border bg-background p-4 shadow-sm"
                                style={{ marginLeft: indentation ? `${indentation}px` : undefined }}
                              >
                                <div className="flex flex-wrap items-center justify-between gap-2">
                                  <div className="flex flex-col">
                                    <span className="text-xs font-semibold text-muted-foreground">
                                      Chunk {metadata?.position ?? 'N/A'} • {metadata?.token_count ?? 0} tokens
                                    </span>
                                    {metadata?.section_title && (
                                      <span className="text-sm font-medium text-foreground">
                                        {metadata.section_title}
                                      </span>
                                    )}
                                  </div>
                                  {metadata?.content_type && (
                                    <Badge variant="outline" className="text-[11px] uppercase tracking-wide">
                                      {metadata.content_type}
                                    </Badge>
                                  )}
                                </div>
                                {breadcrumbs.length > 0 && (
                                  <p className="mt-1 text-xs text-muted-foreground">
                                    {breadcrumbs.join(' > ')}
                                  </p>
                                )}
                                <p className="mt-3 text-sm leading-relaxed whitespace-pre-line text-foreground/90">
                                  {chunk.content}
                                </p>
                              </div>
                            )
                          })}
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                </TabsContent>
              </Tabs>

              <DialogFooter className="flex-shrink-0 pt-4">
                <Button variant="outline" onClick={handleCloseArtifactModal}>
                  Fechar
                </Button>
                <Button
                  onClick={() => updateArtifactMutation.mutate()}
                  disabled={artifactModalTab !== 'edit' || updateArtifactMutation.isPending || !editTitle.trim()}
                >
                  {updateArtifactMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Salvando...
                    </>
                  ) : (
                    <>
                      <Check className="h-4 w-4 mr-2" />
                      Salvar
                    </>
                  )}
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default AdminArtifactsView

