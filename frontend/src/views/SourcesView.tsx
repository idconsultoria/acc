import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, ChevronLeft, ChevronRight } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import Sidebar from '@/components/shared/Sidebar'
import { api } from '../api/client'
import { cn } from '@/lib/utils'

function SourcesView() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedFilter, setSelectedFilter] = useState<string>('Todos')
  const [currentPage, setCurrentPage] = useState(1)
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
    </div>
  )
}

export default SourcesView

