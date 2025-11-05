import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import Sidebar from '@/components/shared/Sidebar'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
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

  // Fetch conversations to calculate statistics
  const { data: conversations = [] } = useQuery({
    queryKey: ['all-conversations'],
    queryFn: () => api.getConversationsByTopic(),
  })

  const { data: topics = [] } = useQuery({
    queryKey: ['topics'],
    queryFn: () => api.listTopics(),
  })

  // Calculate statistics from conversations and messages
  const stats: ProfileStats = {
    totalConversations: conversations.length,
    totalMessages: 0,
    userMessages: 0,
    agentMessages: 0,
    positiveFeedbacks: 15, // Mock data - seria necessário endpoint específico
    negativeFeedbacks: 3,  // Mock data
    averageResponseTime: '3s',
    topTopic: topics[0]?.name || 'Colaboração em Equipe',
    weeklyActivity: [
      { day: 'Seg', messages: 12 },
      { day: 'Ter', messages: 18 },
      { day: 'Qua', messages: 15 },
      { day: 'Qui', messages: 22 },
      { day: 'Sex', messages: 20 },
      { day: 'Sáb', messages: 8 },
      { day: 'Dom', messages: 5 },
    ],
    topicDistribution: topics.slice(0, 5).map(topic => ({
      name: topic.name,
      count: topic.conversation_count,
    })),
    monthlyTrend: [
      { month: 'Jul', conversations: 8 },
      { month: 'Ago', conversations: 12 },
      { month: 'Set', conversations: 15 },
      { month: 'Out', conversations: 18 },
      { month: 'Nov', conversations: 22 },
    ],
  }

  const handleSavePreferences = () => {
    // Implementar salvamento de preferências
    console.log('Saving preferences:', { agentBehavior, sourceDisplay, emailNotifications })
  }

  return (
    <div className="flex h-screen w-full">
      <Sidebar />

      <main className="flex flex-1 flex-col h-screen overflow-y-auto bg-background">
        <div className="p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header */}
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Painel de Perfil Personalizado</h1>
            <p className="text-muted-foreground mt-1">
              Gerencie suas preferências e acompanhe suas interações com o Agente Cultural
            </p>
          </div>

          {/* Profile Card */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col md:flex-row items-center md:items-start gap-6">
                <Avatar className="h-24 w-24">
                  <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white text-2xl">
                    CC
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 text-center md:text-left space-y-2">
                  <h2 className="text-2xl font-bold">Colaborador Cultural</h2>
                  <p className="text-muted-foreground flex items-center gap-2 justify-center md:justify-start">
                    <Mail className="h-4 w-4" />
                    colaborador.nome@empresa.com
                  </p>
                  <div className="flex flex-wrap gap-4 text-sm text-muted-foreground justify-center md:justify-start">
                    <span className="flex items-center gap-1">
                      <Calendar className="h-4 w-4" />
                      Ingressou em 15 de Janeiro, 2023
                    </span>
                    <span className="flex items-center gap-1">
                      <Activity className="h-4 w-4" />
                      Ativo hoje
                    </span>
                  </div>
                </div>
                <Button size="lg">
                  <User className="mr-2 h-4 w-4" />
                  Editar Perfil
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Statistics Grid */}
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Conversas Iniciadas</CardTitle>
                <MessageSquare className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.totalConversations}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  Total de diálogos com o agente
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Feedback Dado</CardTitle>
                <Target className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <span className="text-2xl font-bold">{stats.positiveFeedbacks}</span>
                  <ThumbsUp className="h-5 w-5 text-green-600" />
                  <span className="text-2xl font-bold">{stats.negativeFeedbacks}</span>
                  <ThumbsDown className="h-5 w-5 text-red-600" />
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Avaliações positivas e negativas
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Tempo de Resposta</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.averageResponseTime}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  Tempo médio de resposta do agente
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Tópico Principal</CardTitle>
                <Tag className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-lg font-bold truncate">{stats.topTopic}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  Tema mais discutido
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Charts Section */}
          <div className="grid gap-6 md:grid-cols-2">
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
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={stats.weeklyActivity}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis 
                      dataKey="day" 
                      className="text-xs"
                      tick={{ fill: 'hsl(var(--muted-foreground))' }}
                    />
                    <YAxis 
                      className="text-xs"
                      tick={{ fill: 'hsl(var(--muted-foreground))' }}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '0.5rem'
                      }}
                    />
                    <Bar dataKey="messages" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
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
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={stats.monthlyTrend}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis 
                      dataKey="month" 
                      className="text-xs"
                      tick={{ fill: 'hsl(var(--muted-foreground))' }}
                    />
                    <YAxis 
                      className="text-xs"
                      tick={{ fill: 'hsl(var(--muted-foreground))' }}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '0.5rem'
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
              </CardContent>
            </Card>
          </div>

          {/* Topics Distribution */}
          {stats.topicDistribution.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Award className="h-5 w-5" />
                  Distribuição por Tópicos
                </CardTitle>
                <CardDescription>Suas conversas organizadas por tema</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {stats.topicDistribution.map((topic, index) => {
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
                })}
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
    </div>
  )
}

export default ProfileView

