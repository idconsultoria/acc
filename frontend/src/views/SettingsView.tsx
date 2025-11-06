import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Save, Key, Eye, EyeOff } from 'lucide-react'
import { api } from '@/api/client'
import Sidebar from '@/components/shared/Sidebar'

export default function SettingsView() {
  const [apiKey, setApiKey] = useState('')
  const [showApiKey, setShowApiKey] = useState(false)
  const queryClient = useQueryClient()

  // Fetch current API key (masked)
  const { data: settings } = useQuery({
    queryKey: ['settings'],
    queryFn: () => api.getSettings(),
  })

  // Mutation to save API key
  const saveApiKeyMutation = useMutation({
    mutationFn: (key: string) => api.saveGeminiApiKey(key),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      setApiKey('')
      alert('Chave de API salva com sucesso!')
    },
    onError: () => {
      alert('Erro ao salvar chave de API')
    },
  })

  const handleSave = () => {
    if (apiKey.trim()) {
      saveApiKeyMutation.mutate(apiKey)
    }
  }

  const handleRemove = () => {
    if (confirm('Deseja remover a chave de API personalizada?')) {
      saveApiKeyMutation.mutate('')
    }
  }

  return (
    <div className="flex h-screen w-full">
      <Sidebar />

      {/* Main Content Area */}
      <main className="flex flex-1 flex-col h-screen md:ml-0">
        {/* Header */}
        <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 pt-14 md:pt-0">
          <div className="flex h-14 items-center px-3 md:px-6">
            <h1 className="text-base md:text-lg font-semibold">Configurações</h1>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-3 md:p-6">
        <div className="max-w-2xl mx-auto space-y-4 md:space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                <CardTitle>Chave de API do Gemini</CardTitle>
              </div>
              <CardDescription>
                Configure uma chave de API personalizada do Google Gemini (opcional).
                Se não fornecida, será usada a chave padrão do sistema.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Current API Key Status */}
              {settings?.hasCustomApiKey && (
                <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-md">
                  <p className="text-sm text-green-600 dark:text-green-400">
                    ✓ Chave de API personalizada configurada
                  </p>
                </div>
              )}

              {/* API Key Input */}
              <div className="space-y-2">
                <Label htmlFor="apiKey">Chave de API</Label>
                <div className="flex flex-col sm:flex-row gap-2">
                  <div className="relative flex-1">
                    <Input
                      id="apiKey"
                      type={showApiKey ? 'text' : 'password'}
                      placeholder="AIzaSy..."
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      className="pr-10 text-sm md:text-base"
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiKey(!showApiKey)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-accent rounded"
                    >
                      {showApiKey ? (
                        <EyeOff className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <Eye className="h-4 w-4 text-muted-foreground" />
                      )}
                    </button>
                  </div>
                  <Button
                    onClick={handleSave}
                    disabled={!apiKey.trim() || saveApiKeyMutation.isPending}
                    className="w-full sm:w-auto"
                  >
                    <Save className="h-4 w-4 mr-2" />
                    Salvar
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Obtenha sua chave em:{' '}
                  <a
                    href="https://aistudio.google.com/app/apikey"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    Google AI Studio
                  </a>
                </p>
              </div>

              {/* Remove Button */}
              {settings?.hasCustomApiKey && (
                <Button
                  variant="destructive"
                  onClick={handleRemove}
                  disabled={saveApiKeyMutation.isPending}
                >
                  Remover Chave Personalizada
                </Button>
              )}
            </CardContent>
          </Card>
        </div>
        </div>
      </main>
    </div>
  )
}

