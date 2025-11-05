import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import { Loader2, Plus, Trash2, Tag, XCircle, FileText, File, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import AdminSidebar from '@/components/shared/AdminSidebar'

function AdminArtifactsView() {
  const queryClient = useQueryClient()
  const [showAddModal, setShowAddModal] = useState(false)
  const [addTitle, setAddTitle] = useState('')
  const [addText, setAddText] = useState('')
  const [addFile, setAddFile] = useState<File | null>(null)
  const [addType, setAddType] = useState<'text' | 'pdf'>('text')
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

  // Função para formatar data
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    return `${months[date.getMonth()]} ${date.getDate().toString().padStart(2, '0')}, ${date.getFullYear()}`
  }

  return (
    <div className="flex h-screen w-full">
      <AdminSidebar />

      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-10 py-8">
            <section>
              <div className="flex flex-wrap justify-between gap-4 items-center mb-6">
                <h1 className="text-3xl sm:text-4xl font-black leading-tight tracking-tight text-foreground">
                  Artefatos Culturais
                </h1>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {/* Card Adicionar Novo */}
                <Card
                  className="border-2 border-dashed border-border hover:border-primary hover:bg-primary/5 transition-colors cursor-pointer group"
                  onClick={() => setShowAddModal(true)}
                >
                  <CardContent className="flex flex-col items-center justify-center p-6 text-center">
                    <Plus className="h-12 w-12 text-primary mb-2" />
                    <p className="text-sm font-semibold text-primary">Adicionar Novo Artefato</p>
                  </CardContent>
                </Card>

                {/* Cards de Artefatos */}
                {artifacts.map((artifact) => (
                  <Card
                    key={artifact.id}
                    className="relative group border border-border hover:shadow-md transition-all"
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
                ))}
              </div>
            </section>
          </div>
        </div>
      </main>

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
                <Label htmlFor="artifact-text">Conteúdo do Texto</Label>
                <Textarea
                  id="artifact-text"
                  placeholder="Digite o conteúdo do artefato..."
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
                'Adicionar'
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
    </div>
  )
}

export default AdminArtifactsView

