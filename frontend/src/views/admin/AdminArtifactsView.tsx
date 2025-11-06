import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, Artifact } from '@/api/client'
import { Loader2, Plus, Trash2, Tag, XCircle, FileText, File, Check, Pencil } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
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
  const [showAddModal, setShowAddModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingArtifact, setEditingArtifact] = useState<Artifact | null>(null)
  const [addTitle, setAddTitle] = useState('')
  const [addText, setAddText] = useState('')
  const [addFile, setAddFile] = useState<File | null>(null)
  const [addType, setAddType] = useState<'text' | 'pdf'>('text')
  const [addColor, setAddColor] = useState<string | null>(getRandomColor())
  const [editContent, setEditContent] = useState('')
  const [loadingContent, setLoadingContent] = useState(false)
  const [replaceFile, setReplaceFile] = useState(false)
  const [showTagsModal, setShowTagsModal] = useState<string | null>(null)
  const [artifactTags, setArtifactTags] = useState<string[]>([])
  const [newTag, setNewTag] = useState('')

  // Busca artefatos
  const { data: artifacts = [] } = useQuery({
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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['artifacts'] })
      setShowAddModal(false)
      setAddTitle('')
      setAddText('')
      setAddFile(null)
      setAddColor(getRandomColor())
    },
  })

  // Edita artefato
  const updateArtifactMutation = useMutation({
    mutationFn: async () => {
      if (!editingArtifact) return
      
      const formData = new FormData()
      formData.append('title', addTitle)
      
      if (addText) {
        formData.append('description', addText)
      }
      
      if (artifactTags.length > 0) {
        formData.append('tags', JSON.stringify(artifactTags))
      }
      
      if (addColor) {
        formData.append('color', addColor)
      }
      
      // Se for TEXT e o conteúdo foi alterado
      if (editingArtifact.source_type === 'TEXT' && editContent) {
        formData.append('content', editContent)
      }
      
      // Se for PDF e um novo arquivo foi selecionado
      if (editingArtifact.source_type === 'PDF' && addFile) {
        formData.append('file', addFile)
      }
      
      return api.updateArtifact(editingArtifact.id, formData)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['artifacts'] })
      setShowEditModal(false)
      setEditingArtifact(null)
      setAddTitle('')
      setAddText('')
      setArtifactTags([])
      setAddColor(null)
      setEditContent('')
      setAddFile(null)
      setReplaceFile(false)
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

  // Abre modal de edição
  const handleOpenEditModal = async (artifact: typeof artifacts[0]) => {
    setEditingArtifact(artifact)
    setAddTitle(artifact.title)
    setAddText(artifact.description || '')
    setArtifactTags(artifact.tags || [])
    setAddColor(artifact.color || null)
    setReplaceFile(false)
    setAddFile(null)
    
    // Carrega o conteúdo se for TEXT
    if (artifact.source_type === 'TEXT') {
      setLoadingContent(true)
      try {
        const { content } = await api.getArtifactContent(artifact.id)
        setEditContent(content)
      } catch (error) {
        console.error('Erro ao carregar conteúdo:', error)
        setEditContent('')
      } finally {
        setLoadingContent(false)
      }
    } else {
      setEditContent('')
    }
    
    setShowEditModal(true)
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
          <div className="mx-auto max-w-7xl px-3 md:px-4 sm:px-6 lg:px-10 py-4 md:py-8 pt-16 md:pt-8">
            <section>
              <div className="flex flex-wrap justify-between gap-4 items-center mb-4 md:mb-6">
                <h1 className="text-2xl md:text-3xl sm:text-4xl font-black leading-tight tracking-tight text-foreground">
                  Artefatos Culturais
                </h1>
              </div>
              
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

                {/* Cards de Artefatos */}
                {artifacts.map((artifact) => {
                  const colorConfig = COLOR_PALETTE.find(c => c.value === artifact.color)
                  const colorStyles = colorConfig?.styles || ''
                  
                  return (
                  <Card
                    key={artifact.id}
                    className={`relative group hover:shadow-lg transition-all duration-200 ${colorStyles}`}
                  >
                    <CardContent className="p-4 flex flex-col">
                      <div className="flex-1">
                        {artifact.source_type === 'PDF' ? (
                          <File className="h-10 w-10 text-destructive mb-3" />
                        ) : (
                          <FileText className="h-10 w-10 text-primary mb-3" />
                        )}
                        <h3 className="font-bold text-foreground mb-1">{artifact.title}</h3>
                        <p className="text-xs text-muted-foreground">
                          Adicionado {formatDate(artifact.created_at)}
                        </p>
                        {/* Tags */}
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
                      
                      {/* Botões de ação (aparecem no hover) */}
                      <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleOpenEditModal(artifact)
                          }}
                          className="h-8 w-8 text-blue-600 hover:text-blue-600 hover:bg-blue-600/10"
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleOpenTagsModal(artifact)
                          }}
                          className="h-8 w-8 text-primary hover:text-primary hover:bg-primary/10"
                        >
                          <Tag className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteArtifactMutation.mutate(artifact.id)
                          }}
                          disabled={deleteArtifactMutation.isPending}
                          className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                  )
                })}
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

      {/* Modal de Tags */}
      <Dialog open={!!showTagsModal} onOpenChange={(open) => !open && setShowTagsModal(null)}>
        <DialogContent className="w-[95vw] sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Gerenciar Tags do Artefato</DialogTitle>
            <DialogDescription>
              Adicione ou remova tags para categorizar este artefato cultural
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
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

      {/* Modal de Edição */}
      <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
        <DialogContent className="w-[95vw] max-w-4xl max-h-[90vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>Editar Artefato</DialogTitle>
            <DialogDescription>
              Atualize as informações do artefato cultural
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 overflow-y-auto pr-2 flex-1">
            <div className="space-y-2">
              <Label htmlFor="edit-title">Título do Artefato</Label>
              <Input
                id="edit-title"
                placeholder="Ex: Manual de Valores"
                value={addTitle}
                onChange={(e) => setAddTitle(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-description">Descrição (opcional)</Label>
              <Textarea
                id="edit-description"
                placeholder="Adicione uma descrição do artefato..."
                value={addText}
                onChange={(e) => setAddText(e.target.value)}
                className="min-h-[80px]"
              />
            </div>

            {/* Conteúdo do Artefato */}
            {editingArtifact && editingArtifact.source_type === 'TEXT' && (
              <div className="space-y-2">
                <Label htmlFor="edit-content">Conteúdo do Artefato</Label>
                {loadingContent ? (
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
              </div>
            )}

            {/* Substituir PDF */}
            {editingArtifact && editingArtifact.source_type === 'PDF' && (
              <div className="space-y-3 p-4 border rounded-lg bg-muted/50">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Arquivo PDF Atual</Label>
                    <p className="text-sm text-muted-foreground">Este artefato foi criado a partir de um PDF</p>
                  </div>
                  <Button
                    type="button"
                    variant={replaceFile ? "default" : "outline"}
                    size="sm"
                    onClick={() => setReplaceFile(!replaceFile)}
                  >
                    {replaceFile ? 'Cancelar substituição' : 'Substituir PDF'}
                  </Button>
                </div>
                
                {replaceFile && (
                  <div className="space-y-2 pt-2">
                    <Label htmlFor="replace-pdf">Novo Arquivo PDF</Label>
                    <Input
                      id="replace-pdf"
                      type="file"
                      accept=".pdf"
                      onChange={(e) => setAddFile(e.target.files?.[0] || null)}
                    />
                    <p className="text-xs text-muted-foreground">
                      O arquivo será reprocessado e os chunks atualizados automaticamente
                    </p>
                  </div>
                )}
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
                        <XCircle className="h-3 w-3" />
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
                setShowEditModal(false)
                setEditingArtifact(null)
                setAddTitle('')
                setAddText('')
                setArtifactTags([])
                setAddColor(null)
                setNewTag('')
                setEditContent('')
                setReplaceFile(false)
                setAddFile(null)
              }}
            >
              Cancelar
            </Button>
            <Button
              onClick={() => updateArtifactMutation.mutate()}
              disabled={updateArtifactMutation.isPending || !addTitle.trim()}
            >
              {updateArtifactMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Salvando...
                </>
              ) : (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  Salvar Alterações
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default AdminArtifactsView

