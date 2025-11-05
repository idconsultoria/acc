import { Link, useLocation, useNavigate } from 'react-router-dom'
import { MessageSquare, Clock, Book, User, Settings, Bot, Plus } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useStore } from '@/state/store'
import { api } from '@/api/client'

const Sidebar = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const { setConversationId } = useStore()

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
    } catch (error) {
      console.error('Erro ao criar nova conversa:', error)
    }
  }

  return (
    <aside className="flex flex-col w-64 bg-background border-r border-border">
      <div className="flex flex-col h-full justify-between p-4">
        <div className="flex flex-col gap-4">
          <div className="flex gap-3 items-center">
            <div className="bg-gradient-to-br from-blue-500 via-purple-500 to-blue-600 text-white rounded-full size-10 flex items-center justify-center shrink-0 shadow-lg ring-2 ring-blue-400/50">
              <Bot className="h-5 w-5 text-white" strokeWidth={2.5} />
            </div>
            <div className="flex flex-col">
              <h1 className="text-foreground text-base font-medium leading-normal">Agente Cultural IA</h1>
              <p className="text-muted-foreground text-sm font-normal leading-normal">Seu parceiro de reflexão</p>
            </div>
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
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:bg-muted dark:hover:bg-muted/50 transition-colors"
          >
            <Settings className="h-5 w-5" />
            <p className="leading-normal">Configurações</p>
          </Link>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar

