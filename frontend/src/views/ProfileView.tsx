import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import Sidebar from '@/components/shared/Sidebar'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { 
  User, 
  MessageSquare, 
  ThumbsUp, 
  ThumbsDown, 
  Clock, 
  TrendingUp,
  Calendar,
  Mail,
  Tag,
  BarChart3,
  Activity,
  Target,
  Award
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'

interface ProfileStats {
  totalConversations: number
  totalMessages: number
  userMessages: number
  agentMessages: number
  positiveFeedbacks: number
  negativeFeedbacks: number
  detailedFeedbacks: number
  averageResponseTime: string
  topTopic: string
  weeklyActivity: Array<{ day: string; messages: number }>
  topicDistribution: Array<{ name: string; count: number }>
  monthlyTrend: Array<{ month: string; conversations: number }>
}

function ProfileView() {
  const [agentBehavior, setAgentBehavior] = useState('supportive')
  const [sourceDisplay, setSourceDisplay] = useState('click')
  const [emailNotifications, setEmailNotifications] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [profileName, setProfileName] = useState('Colaborador Cultural')
  const [profileEmail, setProfileEmail] = useState('colaborador.nome@empresa.com')

  // Fetch conversations to calculate statistics
  const { data: conversations = [], isLoading: isLoadingConversations } = useQuery({
    queryKey: ['all-conversations'],
    queryFn: () => api.getConversationsByTopic(),
  })

  const { data: topics = [], isLoading: isLoadingTopics } = useQuery({
    queryKey: ['topics'],
    queryFn: () => api.listTopics(),
  })

  // Fetch feedbacks to calculate positive/negative counts
  const { data: pendingFeedbacks = [], isLoading: isLoadingPendingFeedbacks } = useQuery({
    queryKey: ['pending-feedbacks'],
    queryFn: () => api.listPendingFeedbacks(),
  })

  const { data: reviewedFeedbacks = [], isLoading: isLoadingReviewedFeedbacks } = useQuery({
    queryKey: ['reviewed-feedbacks'],
    queryFn: () => api.listReviewedFeedbacks(),
  })

  const isLoadingFeedbacks = isLoadingPendingFeedbacks || isLoadingReviewedFeedbacks

  // Calculate statistics from conversations and messages
  const stats: ProfileStats = useMemo(() => {
    const allFeedbacks = [...pendingFeedbacks, ...reviewedFeedbacks]
    
    const positiveFeedbacks = allFeedbacks.filter(f => f.feedback_type === 'POSITIVE').length
    const negativeFeedbacks = allFeedbacks.filter(f => f.feedback_type === 'NEGATIVE').length
    const detailedFeedbacks = allFeedbacks.filter(f => f.feedback_type !== 'POSITIVE' && f.feedback_type !== 'NEGATIVE').length

    // Calculate total conversations from topics
    const totalConversations = topics.reduce((sum, topic) => sum + topic.conversation_count, 0)

    // Find topic with highest conversation count
    const topTopic = topics.length > 0
      ? topics.reduce((prev, current) => 
          (current.conversation_count > prev.conversation_count) ? current : prev
        ).name
      : 'Nenhum tópico disponível'

    // Calculate weekly activity (mock data since we don't have created_at for each conversation)
    const now = new Date()
    const daysOfWeek = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
    const weeklyActivity = Array(7).fill(0).map((_, i) => {
      const date = new Date(now)
      date.setDate(date.getDate() - (6 - i))
      const dayName = daysOfWeek[date.getDay()]
      // Mock: distribute conversations across week
      const count = conversations.filter(conv => {
        const convDate = new Date(conv.created_at)
        return convDate.toDateString() === date.toDateString()
      }).length
      return { day: dayName, messages: count }
    })

    // Calculate monthly trend (mock data since we don't have detailed timeline)
    const monthNames = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    const monthlyTrend = Array(5).fill(0).map((_, i) => {
      const date = new Date(now)
      date.setMonth(date.getMonth() - (4 - i))
      const monthName = monthNames[date.getMonth()]
      // Mock: distribute conversations across months
      const count = conversations.filter(conv => {
        const convDate = new Date(conv.created_at)
        return convDate.getMonth() === date.getMonth() && 
               convDate.getFullYear() === date.getFullYear()
      }).length
      return { month: monthName, conversations: count }
    })

    return {
      totalConversations,
      totalMessages: 0, // Would need to fetch all messages from all conversations
      userMessages: 0,
      agentMessages: 0,
      positiveFeedbacks,
      negativeFeedbacks,
      detailedFeedbacks,
      averageResponseTime: '2.5s', // Mock - seria necessário calcular baseado em timestamps
      topTopic,
      weeklyActivity,
      topicDistribution: topics.slice(0, 5).map(topic => ({
        name: topic.name,
        count: topic.conversation_count,
      })),
      monthlyTrend,
    }
  }, [conversations, topics, pendingFeedbacks, reviewedFeedbacks])

  const handleSavePreferences = () => {
    // Implementar salvamento de preferências
    console.log('Saving preferences:', { agentBehavior, sourceDisplay, emailNotifications })
  }

  const handleSaveProfile = () => {
    // Implementar salvamento do perfil
    console.log('Saving profile:', { profileName, profileEmail })
    setIsEditDialogOpen(false)
  }

  return (
    <div className="flex h-screen w-full">
      <Sidebar />

      <main className="flex flex-1 flex-col h-screen overflow-y-auto bg-background md:ml-0">
        <div className="p-3 md:p-6 space-y-4 md:space-y-6 max-w-7xl mx-auto w-full">
          {/* Header */}
          <div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Painel de Perfil Personalizado</h1>
            <p className="text-muted-foreground mt-1 text-sm md:text-base">
              Gerencie suas preferências e acompanhe suas interações com o Agente Cultural
            </p>
          </div>

          {/* Profile Card */}
          <Card>
            <CardContent className="pt-4 md:pt-6">
              <div className="flex flex-col md:flex-row items-center md:items-start gap-4 md:gap-6">
                <Avatar className="h-20 w-20 md:h-24 md:w-24">
                  <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white text-xl md:text-2xl">
                    CC
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 text-center md:text-left space-y-2">
                  <h2 className="text-xl md:text-2xl font-bold">{profileName}</h2>
                  <p className="text-muted-foreground flex items-center gap-2 justify-center md:justify-start text-sm md:text-base">
                    <Mail className="h-4 w-4" />
                    {profileEmail}
                  </p>
                  <div className="flex flex-col md:flex-row flex-wrap gap-2 md:gap-4 text-xs md:text-sm text-muted-foreground justify-center md:justify-start">
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3 w-3 md:h-4 md:w-4" />
                      Ingressou em 15 de Janeiro, 2023
                    </span>
                    <span className="flex items-center gap-1">
                      <Activity className="h-3 w-3 md:h-4 md:w-4" />
                      Ativo hoje
                    </span>
                  </div>
                </div>
                <Button size="default" className="md:size-lg" onClick={() => setIsEditDialogOpen(true)}>
                  <User className="mr-2 h-4 w-4" />
                  Editar Perfil
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Statistics Grid */}
          <div className="grid gap-4 md:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Conversas Iniciadas</CardTitle>
                <MessageSquare className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                {isLoadingConversations || isLoadingTopics ? (
                  <>
                    <Skeleton className="h-8 w-16 mb-2" />
                    <Skeleton className="h-4 w-40" />
                  </>
                ) : (
                  <>
                    <div className="text-2xl font-bold">{stats.totalConversations}</div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Total de diálogos com o agente
                    </p>
                  </>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Feedback Dado</CardTitle>
                <Target className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                {isLoadingFeedbacks ? (
                  <>
                    <div className="flex items-center gap-2 mb-2">
                      <Skeleton className="h-8 w-12" />
                      <Skeleton className="h-5 w-5 rounded-full" />
                      <Skeleton className="h-8 w-12" />
                      <Skeleton className="h-5 w-5 rounded-full" />
                      <Skeleton className="h-8 w-12" />
                      <Skeleton className="h-5 w-5 rounded-full" />
                    </div>
                    <Skeleton className="h-4 w-48" />
                  </>
                ) : (
                  <>
                    <div className="flex items-center gap-6">
                      <div className="flex items-center gap-2">
                        <ThumbsUp className="h-5 w-5 text-green-600 fill-current" />
                        <span className="text-2xl font-bold">{stats.positiveFeedbacks}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <ThumbsDown className="h-5 w-5 text-red-600 fill-current" />
                        <span className="text-2xl font-bold">{stats.negativeFeedbacks}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Tag className="h-5 w-5 text-blue-600" />
                        <span className="text-2xl font-bold">{stats.detailedFeedbacks}</span>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Positivos, negativos e detalhados
                    </p>
                  </>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Tempo de Resposta</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                {isLoadingConversations ? (
                  <>
                    <Skeleton className="h-8 w-20 mb-2" />
                    <Skeleton className="h-4 w-44" />
                  </>
                ) : (
                  <>
                    <div className="text-2xl font-bold">{stats.averageResponseTime}</div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Tempo médio de resposta do agente
                    </p>
                  </>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Tópico Principal</CardTitle>
                <Tag className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                {isLoadingTopics ? (
                  <>
                    <Skeleton className="h-7 w-32 mb-2" />
                    <Skeleton className="h-4 w-36" />
                  </>
                ) : (
                  <>
                    <div className="text-lg font-bold truncate">{stats.topTopic}</div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Tema mais discutido
                    </p>
                  </>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Charts Section */}
          <div className="grid gap-4 md:gap-6 grid-cols-1 md:grid-cols-2">
            {/* Weekly Activity */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Atividade Semanal
                </CardTitle>
                <CardDescription>Suas interações nos últimos 7 dias</CardDescription>
              </CardHeader>
              <CardContent>
                {isLoadingConversations ? (
                  <div className="space-y-3">
                    <Skeleton className="h-[250px] w-full" />
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height={200} className="md:h-[250px]">
                    <BarChart data={stats.weeklyActivity}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                      <XAxis 
                        dataKey="day" 
                        className="text-xs"
                        tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
                      />
                      <YAxis 
                        className="text-xs"
                        tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
                      />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'hsl(var(--card))',
                          border: '1px solid hsl(var(--border))',
                          borderRadius: '0.5rem',
                          fontSize: '12px'
                        }}
                      />
                      <Bar dataKey="messages" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>

            {/* Monthly Trend */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Tendência Mensal
                </CardTitle>
                <CardDescription>Crescimento de conversas ao longo do tempo</CardDescription>
              </CardHeader>
              <CardContent>
                {isLoadingConversations ? (
                  <div className="space-y-3">
                    <Skeleton className="h-[250px] w-full" />
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height={200} className="md:h-[250px]">
                    <LineChart data={stats.monthlyTrend}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                      <XAxis 
                        dataKey="month" 
                        className="text-xs"
                        tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
                      />
                      <YAxis 
                        className="text-xs"
                        tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
                      />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'hsl(var(--card))',
                          border: '1px solid hsl(var(--border))',
                          borderRadius: '0.5rem',
                          fontSize: '12px'
                        }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="conversations" 
                        stroke="hsl(var(--primary))" 
                        strokeWidth={2}
                        dot={{ fill: 'hsl(var(--primary))' }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Topics Distribution */}
          {(isLoadingTopics || stats.topicDistribution.length > 0) && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Award className="h-5 w-5" />
                  Distribuição por Tópicos
                </CardTitle>
                <CardDescription>Suas conversas organizadas por tema</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {isLoadingTopics ? (
                  <>
                    {[...Array(5)].map((_, index) => (
                      <div key={index} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <Skeleton className="h-4 w-32" />
                          <Skeleton className="h-4 w-24" />
                        </div>
                        <Skeleton className="h-2 w-full" />
                      </div>
                    ))}
                  </>
                ) : (
                  stats.topicDistribution.map((topic, index) => {
                    const percentage = (topic.count / stats.totalConversations) * 100
                    return (
                      <div key={index} className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="font-medium">{topic.name}</span>
                          <span className="text-muted-foreground">
                            {topic.count} conversa{topic.count !== 1 ? 's' : ''} ({percentage.toFixed(0)}%)
                          </span>
                        </div>
                        <Progress value={percentage} className="h-2" />
                      </div>
                    )
                  })
                )}
              </CardContent>
            </Card>
          )}

          {/* Preferences */}
          <Card>
            <CardHeader>
              <CardTitle>Preferências</CardTitle>
              <CardDescription>Personalize sua experiência com o Agente Cultural</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="agent-behavior">Estilo de Comportamento do Agente</Label>
                <Select value={agentBehavior} onValueChange={setAgentBehavior}>
                  <SelectTrigger id="agent-behavior">
                    <SelectValue placeholder="Selecione um estilo" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="formal">Formal e Objetivo</SelectItem>
                    <SelectItem value="supportive">Apoiador e Empático</SelectItem>
                    <SelectItem value="direct">Direto e Orientado a Ação</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label htmlFor="source-display">Preferência de Exibição de Fontes</Label>
                <Select value={sourceDisplay} onValueChange={setSourceDisplay}>
                  <SelectTrigger id="source-display">
                    <SelectValue placeholder="Selecione uma opção" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="hover">Mostrar prévia ao passar o mouse</SelectItem>
                    <SelectItem value="click">Mostrar prévia ao clicar</SelectItem>
                    <SelectItem value="link">Apenas mostrar link</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="email-notifications" 
                  checked={emailNotifications}
                  onCheckedChange={(checked) => setEmailNotifications(checked as boolean)}
                />
                <Label 
                  htmlFor="email-notifications"
                  className="text-sm font-normal cursor-pointer"
                >
                  Receber resumos semanais do agente por e-mail
                </Label>
              </div>

              <Button onClick={handleSavePreferences} className="w-full">
                Salvar Preferências
              </Button>
            </CardContent>
          </Card>
        </div>
      </main>

      {/* Edit Profile Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="w-[95vw] sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Editar Perfil</DialogTitle>
            <DialogDescription>
              Faça alterações em seu perfil aqui. Clique em salvar quando terminar.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Nome</Label>
              <Input
                id="name"
                value={profileName}
                onChange={(e) => setProfileName(e.target.value)}
                placeholder="Seu nome completo"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={profileEmail}
                onChange={(e) => setProfileEmail(e.target.value)}
                placeholder="seu.email@empresa.com"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleSaveProfile}>
              Salvar Alterações
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default ProfileView

