import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { MessageSquare, Clock, Book, User, Settings, Bot, Plus, Menu, X, Shield, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'
import { useStore } from '@/state/store'
import { api } from '@/api/client'

const Sidebar = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const { setConversationId } = useStore()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const isInAdminArea = location.pathname.startsWith('/admin')
  const isInChatArea = location.pathname === '/' || location.pathname.startsWith('/chat')

  const navItems = [
    { icon: MessageSquare, label: 'Chat', path: '/chat' },
    { icon: Clock, label: 'Histórico', path: '/history' },
    { icon: Book, label: 'Fontes', path: '/sources' },
    { icon: User, label: 'Perfil', path: '/profile' },
  ]

  const handleNewChat = async () => {
    try {
      // Cria uma nova conversa
      const data = await api.createConversation()
      setConversationId(data.conversation_id)
      // Navega para o chat
      navigate('/chat')
      setIsMobileMenuOpen(false)
    } catch (error) {
      console.error('Erro ao criar nova conversa:', error)
    }
  }

  const handleNavClick = () => {
    setIsMobileMenuOpen(false)
  }

  return (
    <>
      {/* Botão Hamburger para Mobile */}
      <button
        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        className="md:hidden fixed top-3 left-3 z-20 p-2 rounded-lg bg-background border border-border shadow-lg hover:bg-muted transition-colors"
        aria-label="Toggle menu"
      >
        {isMobileMenuOpen ? (
          <X className="h-5 w-5" />
        ) : (
          <Menu className="h-5 w-5" />
        )}
      </button>

      {/* Overlay para Mobile */}
      {isMobileMenuOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'flex flex-col w-64 bg-background border-r border-border fixed md:static h-full z-40 transition-transform duration-300',
          'md:translate-x-0',
          isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        )}
      >
          <div className="flex flex-col h-full justify-between p-4">
            <div className="flex flex-col gap-4">
              <div className="flex gap-3 items-center pr-8 md:pr-0 relative">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button
                      type="button"
                      className={cn(
                        "bg-gradient-to-br from-blue-500 via-purple-500 to-blue-600 text-white rounded-full size-10 flex items-center justify-center shrink-0 shadow-lg ring-2 ring-blue-400/50",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary"
                      )}
                      aria-label="Trocar de tela"
                    >
                      <Bot className="h-5 w-5 text-white" strokeWidth={2.5} />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" side="right" className="w-64">
                    <DropdownMenuLabel>Trocar de tela</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onSelect={() => {
                        navigate('/chat')
                        setIsMobileMenuOpen(false)
                      }}
                      className={cn(
                        "flex items-center gap-3",
                        isInChatArea && "bg-accent/40 text-foreground"
                      )}
                    >
                      <Bot className="h-4 w-4 text-primary" />
                      <div className="flex flex-col">
                        <span className="text-sm font-medium leading-tight">Espaço do Colaborador</span>
                        <span className="text-xs text-muted-foreground leading-tight">Conversas e histórico pessoal</span>
                      </div>
                      {isInChatArea ? (
                        <Check className="ml-auto h-4 w-4 text-primary" />
                      ) : null}
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onSelect={() => {
                        navigate('/admin/instruction')
                        setIsMobileMenuOpen(false)
                      }}
                      className={cn(
                        "flex items-center gap-3",
                        isInAdminArea && "bg-accent/40 text-foreground"
                      )}
                    >
                      <Shield className="h-4 w-4 text-foreground" />
                      <div className="flex flex-col">
                        <span className="text-sm font-medium leading-tight">Painel do Guardião</span>
                        <span className="text-xs text-muted-foreground leading-tight">Configurações e curadoria do agente</span>
                      </div>
                      {isInAdminArea ? (
                        <Check className="ml-auto h-4 w-4 text-primary" />
                      ) : null}
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
                <div className="flex flex-col flex-1 min-w-0">
                  <h1 className="text-foreground text-base font-medium leading-normal">Agente Cultural IA</h1>
                  <p className="text-muted-foreground text-sm font-normal leading-normal">Seu parceiro de reflexão</p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="md:hidden absolute top-0 right-0 h-8 w-8 shrink-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>

            <nav className="flex flex-col gap-2 mt-4">
              {/* Botão Novo Chat */}
              <button
                onClick={handleNewChat}
                className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors bg-primary text-primary-foreground hover:bg-primary/90"
              >
                <Plus className="h-5 w-5" />
                <p className="leading-normal">Novo Chat</p>
              </button>

              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.path || (item.path === '/chat' && location.pathname === '/')
                
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={handleNavClick}
                    className={cn(
                      'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary/20 text-primary dark:bg-[#243047] dark:text-white'
                        : 'text-muted-foreground hover:bg-muted dark:hover:bg-muted/50'
                    )}
                  >
                    <Icon className="h-5 w-5" />
                    <p className="leading-normal">{item.label}</p>
                  </Link>
                )
              })}
            </nav>
          </div>

          <div className="flex flex-col gap-1">
            <Link
              to="/settings"
              onClick={handleNavClick}
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:bg-muted dark:hover:bg-muted/50 transition-colors"
            >
              <Settings className="h-5 w-5" />
              <p className="leading-normal">Configurações</p>
            </Link>
          </div>
        </div>
      </aside>
    </>
  )
}

export default Sidebar

