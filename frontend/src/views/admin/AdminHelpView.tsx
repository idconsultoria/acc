import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import AdminSidebar from '@/components/shared/AdminSidebar'
import { 
  BookOpen, 
  MessageCircle, 
  ExternalLink, 
  Mail, 
  FileText,
  HelpCircle,
  Info
} from 'lucide-react'

interface FAQItem {
  question: string
  answer: string
}

function AdminHelpView() {
  const faqs: FAQItem[] = [
    {
      question: 'Como adicionar um novo artefato cultural?',
      answer: 'Navegue até "Artefatos Culturais" no menu lateral, clique em "Adicionar Artefato" e preencha as informações necessárias incluindo título, descrição e arquivo PDF.'
    },
    {
      question: 'Como revisar feedbacks dos usuários?',
      answer: 'Acesse "Revisão de Feedback" no menu. Você pode filtrar feedbacks por tipo (positivo/negativo), revisar conversas completas e aprovar aprendizados sugeridos.'
    },
    {
      question: 'Como modificar a instrução principal do agente?',
      answer: 'Vá até "Instrução do Agente" e edite a diretiva principal. As mudanças serão aplicadas imediatamente após salvar.'
    },
    {
      question: 'Posso exportar os dados do sistema?',
      answer: 'Sim! Acesse "Configurações" e use a opção "Exportar Dados do Sistema" para baixar uma cópia de todos os artefatos, feedbacks e configurações.'
    },
    {
      question: 'Como organizar artefatos por tópicos?',
      answer: 'Ao criar ou editar um artefato, você pode atribuir tópicos através de tags. O sistema também sugere tópicos automaticamente baseado no conteúdo.'
    }
  ]

  const quickLinks = [
    {
      icon: BookOpen,
      title: 'Documentação Completa',
      description: 'Guia detalhado sobre todas as funcionalidades',
      href: '#'
    },
    {
      icon: FileText,
      title: 'Guia de Implementação',
      description: 'Como implementar e customizar o sistema',
      href: '#'
    },
    {
      icon: MessageCircle,
      title: 'Comunidade',
      description: 'Participe de discussões com outros usuários',
      href: '#'
    }
  ]

  return (
    <div className="flex h-screen w-full">
      <AdminSidebar />

      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-10 py-8">
            <section>
              <div className="flex flex-wrap justify-between gap-4 items-center mb-8">
                <div>
                  <h1 className="text-3xl sm:text-4xl font-black leading-tight tracking-tight text-foreground">
                    Ajuda e Suporte
                  </h1>
                  <p className="text-muted-foreground text-base mt-2">
                    Recursos e documentação para ajudá-lo a aproveitar ao máximo o sistema
                  </p>
                </div>
              </div>

              <div className="space-y-6">
                {/* Início Rápido */}
                <Card className="p-6 border-2 border-primary/20 bg-primary/5">
                  <div className="flex items-start gap-4">
                    <div className="p-3 rounded-lg bg-primary text-primary-foreground">
                      <Info className="h-5 w-5" />
                    </div>
                    <div className="flex-1">
                      <h2 className="text-xl font-bold text-foreground mb-2">Bem-vindo ao Guardião Cultural</h2>
                      <p className="text-sm text-muted-foreground mb-4">
                        Este painel permite gerenciar artefatos culturais, revisar feedbacks dos usuários e configurar 
                        o comportamento do agente de IA. Use o menu lateral para navegar entre as diferentes seções.
                      </p>
                      <div className="flex flex-wrap gap-2">
                        <Button size="sm" variant="default">
                          <BookOpen className="h-4 w-4 mr-2" />
                          Guia Inicial
                        </Button>
                        <Button size="sm" variant="outline">
                          <FileText className="h-4 w-4 mr-2" />
                          Tutorial em Vídeo
                        </Button>
                      </div>
                    </div>
                  </div>
                </Card>

                {/* FAQ */}
                <div>
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 rounded-lg bg-primary/10 text-primary">
                      <HelpCircle className="h-5 w-5" />
                    </div>
                    <h2 className="text-2xl font-bold text-foreground">Perguntas Frequentes</h2>
                  </div>
                  
                  <Accordion type="single" collapsible className="space-y-3">
                    {faqs.map((faq, index) => (
                      <AccordionItem 
                        key={index} 
                        value={`item-${index}`}
                        className="border rounded-lg px-4 bg-card"
                      >
                        <AccordionTrigger className="hover:no-underline">
                          <span className="font-medium text-foreground text-left">{faq.question}</span>
                        </AccordionTrigger>
                        <AccordionContent className="text-sm text-muted-foreground">
                          {faq.answer}
                        </AccordionContent>
                      </AccordionItem>
                    ))}
                  </Accordion>
                </div>

                {/* Links Rápidos */}
                <div>
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 rounded-lg bg-primary/10 text-primary">
                      <ExternalLink className="h-5 w-5" />
                    </div>
                    <h2 className="text-2xl font-bold text-foreground">Links Úteis</h2>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {quickLinks.map((link, index) => {
                      const Icon = link.icon
                      return (
                        <Card 
                          key={index}
                          className="p-5 hover:shadow-lg transition-all cursor-pointer group"
                          onClick={() => window.open(link.href, '_blank')}
                        >
                          <div className="flex flex-col gap-3">
                            <div className="p-2 rounded-lg bg-primary/10 text-primary w-fit group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                              <Icon className="h-5 w-5" />
                            </div>
                            <div>
                              <h3 className="font-semibold text-foreground mb-1 flex items-center gap-2">
                                {link.title}
                                <ExternalLink className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                              </h3>
                              <p className="text-sm text-muted-foreground">
                                {link.description}
                              </p>
                            </div>
                          </div>
                        </Card>
                      )
                    })}
                  </div>
                </div>

                {/* Suporte */}
                <Card className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="p-3 rounded-lg bg-primary/10 text-primary">
                      <Mail className="h-5 w-5" />
                    </div>
                    <div className="flex-1">
                      <h2 className="text-xl font-bold text-foreground mb-2">Precisa de Mais Ajuda?</h2>
                      <p className="text-sm text-muted-foreground mb-4">
                        Nossa equipe de suporte está pronta para ajudar você com qualquer dúvida ou problema.
                      </p>
                      <div className="flex flex-col sm:flex-row gap-3">
                        <Button variant="default">
                          <Mail className="h-4 w-4 mr-2" />
                          Entrar em Contato
                        </Button>
                        <Button variant="outline">
                          <MessageCircle className="h-4 w-4 mr-2" />
                          Chat ao Vivo
                        </Button>
                      </div>
                    </div>
                  </div>
                </Card>

                {/* Informações do Sistema */}
                <Card className="p-6 bg-muted/30">
                  <div className="flex flex-col gap-2 text-sm">
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Versão do Sistema</span>
                      <span className="font-mono font-medium text-foreground">v1.0.0</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Última Atualização</span>
                      <span className="font-medium text-foreground">Novembro 2025</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Documentação</span>
                      <Button variant="link" size="sm" className="h-auto p-0">
                        Ver Changelog
                        <ExternalLink className="h-3 w-3 ml-1" />
                      </Button>
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

export default AdminHelpView

