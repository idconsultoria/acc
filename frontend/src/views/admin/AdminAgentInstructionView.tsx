import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import { Loader2, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import AdminSidebar from '@/components/shared/AdminSidebar'

function AdminAgentInstructionView() {
  const queryClient = useQueryClient()
  const [instructionText, setInstructionText] = useState('')

  // Busca instrução do agente
  const { data: agentInstruction, isLoading } = useQuery({
    queryKey: ['agent-instruction'],
    queryFn: api.getAgentInstruction,
  })

  // Garante que a instrução atual seja sempre carregada no campo de texto
  useEffect(() => {
    if (agentInstruction?.instruction !== undefined) {
      setInstructionText(agentInstruction.instruction)
    }
  }, [agentInstruction])

  // Atualiza instrução do agente
  const updateInstructionMutation = useMutation({
    mutationFn: api.updateAgentInstruction,
    onSuccess: (data) => {
      // Atualiza o estado local com a resposta do servidor para garantir sincronização
      if (data?.instruction) {
        setInstructionText(data.instruction)
      }
      queryClient.invalidateQueries({ queryKey: ['agent-instruction'] })
    },
  })

  const handleSaveInstruction = () => {
    if (instructionText.trim()) {
      updateInstructionMutation.mutate(instructionText)
    }
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
                  Instrução do Agente
                </h1>
              </div>
              
              <div className="relative">
                <div className="flex flex-col gap-3 md:gap-4">
                  <Label htmlFor="agent-instruction" className="text-sm md:text-base font-medium">
                    Diretiva Principal do Guardião
                  </Label>
                  <Textarea
                    id="agent-instruction"
                    value={instructionText}
                    onChange={(e) => setInstructionText(e.target.value)}
                    placeholder={isLoading ? "Carregando instrução..." : "Digite as instruções principais do agente aqui..."}
                    disabled={isLoading || updateInstructionMutation.isPending}
                    className="min-h-[300px] md:min-h-96 text-sm md:text-base font-normal leading-normal resize-none"
                  />
                </div>
                
                <div className="fixed bottom-4 right-4 md:bottom-8 md:right-10 z-30">
                  <Button
                    onClick={handleSaveInstruction}
                    disabled={updateInstructionMutation.isPending || !instructionText.trim()}
                    size="default"
                    className="md:size-lg shadow-2xl"
                  >
                    {updateInstructionMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        <span className="hidden sm:inline">Salvando...</span>
                      </>
                    ) : (
                      <>
                        <Check className="h-4 w-4 mr-2" />
                        <span className="hidden sm:inline">Salvar Alterações</span>
                        <span className="sm:hidden">Salvar</span>
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  )
}

export default AdminAgentInstructionView

