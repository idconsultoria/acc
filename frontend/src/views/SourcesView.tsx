import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, ChevronLeft, ChevronRight, FileText } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import Sidebar from '@/components/shared/Sidebar'
import { api, Artifact } from '../api/client'
import { cn } from '@/lib/utils'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

function SourcesView() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedFilter, setSelectedFilter] = useState<string>('Todos')
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null)
  const itemsPerPage = 6

  // Busca artefatos
  const { 
    data: artifacts = [], 
    isLoading: isLoadingArtifacts
  } = useQuery({
    queryKey: ['artifacts'],
    queryFn: api.listArtifacts,
    staleTime: 1000 * 30,
    refetchOnMount: 'always',
    placeholderData: (previousData) => previousData,
  })

  // Busca conteúdo do artefato selecionado
  const { 
    data: artifactContent,
    isLoading: isLoadingContent
  } = useQuery({
    queryKey: ['artifact-content', selectedArtifact?.id],
    queryFn: () => selectedArtifact ? api.getArtifactContent(selectedArtifact.id) : Promise.resolve({ content: '' }),
    enabled: !!selectedArtifact && selectedArtifact.source_type === 'TEXT',
  })

  // Filtra artefatos
  const filteredArtifacts = artifacts.filter((artifact) => {
    const matchesSearch = artifact.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (artifact.tags || []).some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    
    if (selectedFilter === 'Todos') return matchesSearch
    
    // Mapeia filtros para tipos/categorias (tags em português)
    const filterMap: Record<string, string[]> = {
      'Valores da Empresa': ['Valores', 'Política', 'Valores da Empresa'],
      'Estudos de Caso': ['Estudo de Caso', 'Estudos de Caso'],
      'Boas Práticas': ['Boas Práticas', 'Artigo', 'Práticas'],
      'Documentos de Política': ['Política', 'Segurança', 'Documento'],
    }
    
    const filterTags = filterMap[selectedFilter] || []
    const matchesFilter = filterTags.some(filterTag => 
      artifact.tags?.some(tag => tag.includes(filterTag))
    )
    
    return matchesSearch && matchesFilter
  })

  // Paginação
  const totalPages = Math.ceil(filteredArtifacts.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const paginatedArtifacts = filteredArtifacts.slice(startIndex, startIndex + itemsPerPage)

  // Função para gerar imagem placeholder baseada no título
  const getPlaceholderImage = (title: string) => {
    // Usa um hash simples do título para gerar uma cor consistente
    let hash = 0
    for (let i = 0; i < title.length; i++) {
      hash = title.charCodeAt(i) + ((hash << 5) - hash)
    }
    const hue = hash % 360
    return `linear-gradient(135deg, hsl(${hue}, 70%, 60%), hsl(${(hue + 60) % 360}, 70%, 60%))`
  }

  const filters = ['Todos', 'Valores da Empresa', 'Estudos de Caso', 'Boas Práticas', 'Documentos de Política']

  // Handler para abrir visualização do artefato
  const handleArtifactClick = (artifact: Artifact) => {
    setSelectedArtifact(artifact)
  }

  // Handler para fechar o dialog
  const handleCloseDialog = () => {
    setSelectedArtifact(null)
  }

  return (
    <div className="flex h-screen w-full">
      <Sidebar />

      <main className="flex flex-1 flex-col h-screen overflow-hidden">
        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-6xl px-4 sm:px-8 md:px-16 lg:px-24 xl:px-40 py-5">
            {/* Header */}
            <div className="flex flex-wrap justify-between gap-3 pt-10 pb-6">
              <div className="flex min-w-72 flex-col gap-3">
                <h1 className="text-4xl font-black leading-tight tracking-tight text-foreground">
                  Base de Conhecimento
                </h1>
                <p className="text-base font-normal leading-normal text-muted-foreground">
                  Pesquise e navegue por todos os artefatos culturais e aprendizados usados pelo agente.
                </p>
              </div>
            </div>

            {/* Search Bar */}
            <div className="py-3">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="Pesquise por artigos, estudos de caso, valores..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value)
                    setCurrentPage(1) // Reset para primeira página ao buscar
                  }}
                  className="pl-10 h-12 rounded-xl bg-muted border-none focus-ring-2 focus-ring-primary/50"
                />
              </div>
            </div>

            {/* Filter Chips */}
            <div className="flex gap-2 p-3 overflow-x-auto pb-4">
              {filters.map((filter) => (
                <Button
                  key={filter}
                  onClick={() => {
                    setSelectedFilter(filter)
                    setCurrentPage(1) // Reset para primeira página ao filtrar
                  }}
                  variant={selectedFilter === filter ? 'default' : 'outline'}
                  className={cn(
                    'h-8 rounded-full px-4 shrink-0',
                    selectedFilter === filter
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted hover:bg-muted/80 text-foreground'
                  )}
                >
                  {filter}
                </Button>
              ))}
            </div>

            {/* Content Grid */}
            {isLoadingArtifacts ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
                {[...Array(6)].map((_, i) => (
                  <Card key={i} className="border border-border">
                    <CardContent className="p-3 flex flex-col gap-3">
                      <Skeleton className="w-full aspect-video rounded-lg" />
                      <Skeleton className="h-5 w-3/4" />
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-2/3" />
                      <Skeleton className="h-3 w-1/2" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : paginatedArtifacts.length === 0 ? (
              <Card className="border border-border">
                <CardContent className="p-6 text-center text-muted-foreground">
                  Nenhum artefato encontrado para os filtros selecionados.
                </CardContent>
              </Card>
            ) : (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
                  {paginatedArtifacts.map((artifact) => (
                    <Card
                      key={artifact.id}
                      className="border border-border bg-card/50 hover:bg-card transition-colors cursor-pointer"
                      onClick={() => handleArtifactClick(artifact)}
                    >
                      <CardContent className="p-3 flex flex-col gap-3">
                        {/* Image Placeholder */}
                        <div
                          className="w-full aspect-video rounded-lg bg-cover bg-center"
                          style={{
                            backgroundImage: getPlaceholderImage(artifact.title),
                          }}
                        />

                        {/* Title and Description */}
                        <div>
                          <h3 className="text-base font-medium leading-normal text-foreground">
                            {artifact.title}
                          </h3>
                          <p className="text-sm font-normal leading-normal text-muted-foreground mt-1">
                            {artifact.description || 'Artefato cultural da base de conhecimento.'}
                          </p>
                          {/* Tags */}
                          <div className="flex flex-wrap gap-1 mt-2">
                            {artifact.tags && artifact.tags.length > 0 ? (
                              artifact.tags.slice(0, 2).map((tag, idx) => (
                                <Badge
                                  key={idx}
                                  variant="secondary"
                                  className="text-xs font-normal text-muted-foreground bg-muted/50"
                                >
                                  {tag}
                                </Badge>
                              ))
                              ) : (
                                <Badge
                                  variant="secondary"
                                  className="text-xs font-normal text-muted-foreground bg-muted/50"
                                >
                                  {artifact.source_type === 'PDF' ? 'Documento' : 'Artigo'}
                                </Badge>
                              )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-center p-6 mt-4">
                    <nav className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                        className="h-9 w-9 rounded-lg"
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      
                      {/* Page Numbers */}
                      {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                        let pageNum
                        if (totalPages <= 5) {
                          pageNum = i + 1
                        } else if (currentPage <= 3) {
                          pageNum = i + 1
                        } else if (currentPage >= totalPages - 2) {
                          pageNum = totalPages - 4 + i
                        } else {
                          pageNum = currentPage - 2 + i
                        }
                        
                        return (
                          <Button
                            key={pageNum}
                            variant={currentPage === pageNum ? 'default' : 'outline'}
                            size="icon"
                            onClick={() => setCurrentPage(pageNum)}
                            className={cn(
                              'h-9 w-9 rounded-lg',
                              currentPage === pageNum
                                ? 'bg-primary text-primary-foreground'
                                : 'bg-muted hover:bg-muted/80'
                            )}
                          >
                            {pageNum}
                          </Button>
                        )
                      })}
                      
                      {totalPages > 5 && (
                        <>
                          <span className="text-muted-foreground">...</span>
                          <Button
                            variant="outline"
                            size="icon"
                            onClick={() => setCurrentPage(totalPages)}
                            className="h-9 w-9 rounded-lg bg-muted hover:bg-muted/80"
                          >
                            {totalPages}
                          </Button>
                        </>
                      )}
                      
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                        disabled={currentPage === totalPages}
                        className="h-9 w-9 rounded-lg"
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </nav>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </main>

      {/* Dialog para visualização do conteúdo */}
      <Dialog open={!!selectedArtifact} onOpenChange={(open) => !open && handleCloseDialog()}>
        <DialogContent className="max-w-4xl h-[85vh] flex flex-col p-0">
          <DialogHeader className="px-6 pt-6 pb-4 border-b shrink-0">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <DialogTitle className="text-2xl font-bold text-foreground pr-8">
                  {selectedArtifact?.title}
                </DialogTitle>
                {selectedArtifact?.description && (
                  <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                    {selectedArtifact.description}
                  </p>
                )}
                {selectedArtifact?.tags && selectedArtifact.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {selectedArtifact.tags.map((tag, idx) => (
                      <Badge
                        key={idx}
                        variant="secondary"
                        className="text-xs font-normal"
                      >
                        {tag}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </DialogHeader>

          <ScrollArea className="flex-1 overflow-auto">
            <div className="px-6 py-4">
            {selectedArtifact?.source_type === 'PDF' ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <FileText className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  Documento PDF
                </h3>
                <p className="text-sm text-muted-foreground max-w-md">
                  Este é um documento PDF. A visualização completa de PDFs não está disponível no momento.
                  O conteúdo deste documento é utilizado pelo agente durante as conversas.
                </p>
              </div>
            ) : isLoadingContent ? (
              <div className="space-y-3 py-4">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
                <Skeleton className="h-4 w-4/6" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            ) : (
              <div className="prose prose-slate dark:prose-invert max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ children }) => (
                      <h1 className="text-3xl font-bold text-foreground mt-6 mb-4">
                        {children}
                      </h1>
                    ),
                    h2: ({ children }) => (
                      <h2 className="text-2xl font-bold text-foreground mt-5 mb-3">
                        {children}
                      </h2>
                    ),
                    h3: ({ children }) => (
                      <h3 className="text-xl font-semibold text-foreground mt-4 mb-2">
                        {children}
                      </h3>
                    ),
                    h4: ({ children }) => (
                      <h4 className="text-lg font-semibold text-foreground mt-3 mb-2">
                        {children}
                      </h4>
                    ),
                    p: ({ children }) => (
                      <p className="text-base text-foreground leading-relaxed mb-4">
                        {children}
                      </p>
                    ),
                    ul: ({ children }) => (
                      <ul className="list-disc pl-6 space-y-2 mb-4 text-foreground">
                        {children}
                      </ul>
                    ),
                    ol: ({ children }) => (
                      <ol className="list-decimal pl-6 space-y-2 mb-4 text-foreground">
                        {children}
                      </ol>
                    ),
                    li: ({ children }) => (
                      <li className="text-base leading-relaxed">
                        {children}
                      </li>
                    ),
                    blockquote: ({ children }) => (
                      <blockquote className="border-l-4 border-primary pl-4 italic text-muted-foreground my-4">
                        {children}
                      </blockquote>
                    ),
                    code: ({ inline, children }: { inline?: boolean; children?: React.ReactNode }) => 
                      inline ? (
                        <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono text-foreground">
                          {children}
                        </code>
                      ) : (
                        <code className="block bg-muted p-4 rounded-lg text-sm font-mono text-foreground overflow-x-auto my-4">
                          {children}
                        </code>
                      ),
                    pre: ({ children }) => (
                      <pre className="bg-muted p-4 rounded-lg overflow-x-auto my-4">
                        {children}
                      </pre>
                    ),
                    strong: ({ children }) => (
                      <strong className="font-semibold text-foreground">
                        {children}
                      </strong>
                    ),
                    em: ({ children }) => (
                      <em className="italic text-foreground">
                        {children}
                      </em>
                    ),
                    a: ({ children, href }) => (
                      <a 
                        href={href} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-primary hover:underline"
                      >
                        {children}
                      </a>
                    ),
                    table: ({ children }) => (
                      <div className="overflow-x-auto my-4">
                        <table className="min-w-full divide-y divide-border">
                          {children}
                        </table>
                      </div>
                    ),
                    thead: ({ children }) => (
                      <thead className="bg-muted">
                        {children}
                      </thead>
                    ),
                    tbody: ({ children }) => (
                      <tbody className="divide-y divide-border">
                        {children}
                      </tbody>
                    ),
                    tr: ({ children }) => (
                      <tr>{children}</tr>
                    ),
                    th: ({ children }) => (
                      <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">
                        {children}
                      </th>
                    ),
                    td: ({ children }) => (
                      <td className="px-4 py-2 text-sm text-foreground">
                        {children}
                      </td>
                    ),
                    hr: () => (
                      <hr className="border-border my-6" />
                    ),
                  }}
                >
                  {artifactContent?.content || ''}
                </ReactMarkdown>
              </div>
            )}
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default SourcesView

