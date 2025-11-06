import { Card } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import AdminSidebar from '@/components/shared/AdminSidebar'
import { Bell, Database, Globe, Palette, Download } from 'lucide-react'
import { useState } from 'react'

function AdminSettingsView() {
  const [notifications, setNotifications] = useState(true)
  const [language, setLanguage] = useState('pt-BR')
  const [theme, setTheme] = useState('system')

  const handleExportData = () => {
    // Placeholder para exportação de dados
    console.log('Exportando dados...')
  }

  return (
    <div className="flex h-screen w-full">
      <AdminSidebar />

      <main className="flex-1 flex flex-col h-screen overflow-hidden md:ml-0">
        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-5xl px-3 md:px-4 sm:px-6 lg:px-10 py-4 md:py-8 pt-14 md:pt-8">
            <section>
              <div className="flex flex-wrap justify-between gap-4 items-center mb-6 md:mb-8">
                <div>
                  <h1 className="text-2xl md:text-3xl sm:text-4xl font-black leading-tight tracking-tight text-foreground">
                    Configurações
                  </h1>
                  <p className="text-muted-foreground text-sm md:text-base mt-2">
                    Personalize o comportamento e a aparência do painel administrativo
                  </p>
                </div>
              </div>

              <div className="space-y-4 md:space-y-6">
                {/* Aparência */}
                <Card className="p-4 md:p-6">
                  <div className="flex items-start gap-3 md:gap-4">
                    <div className="p-2 md:p-3 rounded-lg bg-primary/10 text-primary shrink-0">
                      <Palette className="h-4 w-4 md:h-5 md:w-5" />
                    </div>
                    <div className="flex-1 space-y-3 md:space-y-4">
                      <div>
                        <h2 className="text-lg md:text-xl font-bold text-foreground">Aparência</h2>
                        <p className="text-xs md:text-sm text-muted-foreground mt-1">
                          Customize a interface visual do sistema
                        </p>
                      </div>
                      
                      <div className="space-y-2">
                        <Label htmlFor="theme" className="text-sm font-medium">
                          Tema da Interface
                        </Label>
                        <Select value={theme} onValueChange={setTheme}>
                          <SelectTrigger id="theme" className="w-full max-w-xs">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="light">Claro</SelectItem>
                            <SelectItem value="dark">Escuro</SelectItem>
                            <SelectItem value="system">Sistema</SelectItem>
                          </SelectContent>
                        </Select>
                        <p className="text-xs text-muted-foreground">
                          O tema "Sistema" segue as preferências do seu dispositivo
                        </p>
                      </div>
                    </div>
                  </div>
                </Card>

                {/* Notificações */}
                <Card className="p-4 md:p-6">
                  <div className="flex items-start gap-3 md:gap-4">
                    <div className="p-2 md:p-3 rounded-lg bg-primary/10 text-primary shrink-0">
                      <Bell className="h-4 w-4 md:h-5 md:w-5" />
                    </div>
                    <div className="flex-1 space-y-3 md:space-y-4">
                      <div>
                        <h2 className="text-lg md:text-xl font-bold text-foreground">Notificações</h2>
                        <p className="text-xs md:text-sm text-muted-foreground mt-1">
                          Gerencie como você recebe alertas e atualizações
                        </p>
                      </div>
                      
                      <div className="flex items-center justify-between py-2 gap-4">
                        <div className="space-y-0.5 flex-1">
                          <Label htmlFor="notifications" className="text-sm font-medium">
                            Notificações do Sistema
                          </Label>
                          <p className="text-xs text-muted-foreground">
                            Receba alertas sobre novos feedbacks e atualizações
                          </p>
                        </div>
                        <Switch
                          id="notifications"
                          checked={notifications}
                          onCheckedChange={setNotifications}
                        />
                      </div>
                    </div>
                  </div>
                </Card>

                {/* Idioma e Região */}
                <Card className="p-4 md:p-6">
                  <div className="flex items-start gap-3 md:gap-4">
                    <div className="p-2 md:p-3 rounded-lg bg-primary/10 text-primary shrink-0">
                      <Globe className="h-4 w-4 md:h-5 md:w-5" />
                    </div>
                    <div className="flex-1 space-y-3 md:space-y-4">
                      <div>
                        <h2 className="text-lg md:text-xl font-bold text-foreground">Idioma e Região</h2>
                        <p className="text-xs md:text-sm text-muted-foreground mt-1">
                          Configure o idioma da interface
                        </p>
                      </div>
                      
                      <div className="space-y-2">
                        <Label htmlFor="language" className="text-sm font-medium">
                          Idioma
                        </Label>
                        <Select value={language} onValueChange={setLanguage}>
                          <SelectTrigger id="language" className="w-full max-w-xs">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="pt-BR">Português (Brasil)</SelectItem>
                            <SelectItem value="en-US">English (US)</SelectItem>
                            <SelectItem value="es-ES">Español</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </div>
                </Card>

                {/* Dados e Backup */}
                <Card className="p-4 md:p-6">
                  <div className="flex items-start gap-3 md:gap-4">
                    <div className="p-2 md:p-3 rounded-lg bg-primary/10 text-primary shrink-0">
                      <Database className="h-4 w-4 md:h-5 md:w-5" />
                    </div>
                    <div className="flex-1 space-y-3 md:space-y-4">
                      <div>
                        <h2 className="text-lg md:text-xl font-bold text-foreground">Dados e Backup</h2>
                        <p className="text-xs md:text-sm text-muted-foreground mt-1">
                          Gerencie seus dados e crie backups
                        </p>
                      </div>
                      
                      <div className="space-y-3">
                        <Button 
                          variant="outline" 
                          onClick={handleExportData}
                          className="w-full sm:w-auto max-w-xs justify-start"
                        >
                          <Download className="h-4 w-4 mr-2" />
                          Exportar Dados do Sistema
                        </Button>
                        <p className="text-xs text-muted-foreground">
                          Baixe uma cópia de todos os artefatos, feedbacks e configurações
                        </p>
                      </div>
                    </div>
                  </div>
                </Card>
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  )
}

export default AdminSettingsView

