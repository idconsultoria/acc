import React, { useEffect, useState, useRef } from 'react'
import { checkBackendStatus } from '@/api/client'
import { useStore } from '@/state/store'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Loader2, CheckCircle2, AlertCircle, Zap, X } from 'lucide-react'

export function BackendStatusNotification() {
  const { backendStatusChecked, setBackendStatusChecked, backendStatus, setBackendStatus } = useStore()
  const [isChecking, setIsChecking] = useState(false)
  const [message, setMessage] = useState<string>('')
  const [showSuccess, setShowSuccess] = useState(false)
  const successTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const previousStatusRef = useRef<'unknown' | 'online' | 'waking' | 'offline'>('unknown')

  // Função para verificar status do backend
  const handleCheckStatus = async () => {
    setIsChecking(true)
    setBackendStatus('unknown')
    
    try {
      const result = await checkBackendStatus()
      const previousStatus = previousStatusRef.current
      
      setBackendStatus(result.status)
      setMessage(result.message || '')
      
      // Se estava offline e agora está online, mostra sucesso
      if (previousStatus === 'offline' && result.status === 'online') {
        setShowSuccess(true)
        // Remove o sucesso após 5 segundos
        if (successTimeoutRef.current) {
          clearTimeout(successTimeoutRef.current)
        }
        successTimeoutRef.current = setTimeout(() => {
          setShowSuccess(false)
        }, 5000)
      }
      
      previousStatusRef.current = result.status
      
      // Se o backend estiver acordando, tenta verificar novamente após alguns segundos
      if (result.status === 'waking') {
        setTimeout(() => {
          checkBackendStatus()
            .then((retryResult) => {
              const prevStatus = previousStatusRef.current
              setBackendStatus(retryResult.status)
              setMessage(retryResult.message || '')
              
              // Se estava offline/waking e agora está online, mostra sucesso
              if ((prevStatus === 'offline' || prevStatus === 'waking') && retryResult.status === 'online') {
                setShowSuccess(true)
                if (successTimeoutRef.current) {
                  clearTimeout(successTimeoutRef.current)
                }
                successTimeoutRef.current = setTimeout(() => {
                  setShowSuccess(false)
                }, 5000)
              }
              
              previousStatusRef.current = retryResult.status
            })
            .catch(() => {
              setBackendStatus('offline')
              setMessage('Não foi possível conectar ao backend')
              previousStatusRef.current = 'offline'
            })
        }, 5000) // Aguarda 5 segundos antes de verificar novamente
      }
      
      if (!backendStatusChecked) {
        setBackendStatusChecked(true)
      }
    } catch (error) {
      setBackendStatus('offline')
      setMessage('Erro ao verificar status do backend')
      previousStatusRef.current = 'offline'
      if (!backendStatusChecked) {
        setBackendStatusChecked(true)
      }
    } finally {
      setIsChecking(false)
    }
  }

  useEffect(() => {
    // Verifica o status do backend apenas na primeira vez que o app é carregado
    if (!backendStatusChecked && !isChecking) {
      previousStatusRef.current = 'unknown'
      handleCheckStatus()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [backendStatusChecked, isChecking])

  // Limpar timeout ao desmontar
  useEffect(() => {
    return () => {
      if (successTimeoutRef.current) {
        clearTimeout(successTimeoutRef.current)
      }
    }
  }, [])

  // Mostra aviso de sucesso se necessário
  if (showSuccess && backendStatus === 'online') {
    return (
      <div className="fixed bottom-4 right-4 z-50 max-w-md">
        <Alert variant="success">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="h-4 w-4" />
            <div className="flex-1">
              <AlertTitle>Conexão estabelecida</AlertTitle>
              <AlertDescription className="mt-1">
                O backend foi conectado com sucesso. O serviço está disponível.
              </AlertDescription>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 -mt-1 -mr-1"
              onClick={() => {
                setShowSuccess(false)
                if (successTimeoutRef.current) {
                  clearTimeout(successTimeoutRef.current)
                }
              }}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </Alert>
      </div>
    )
  }

  // Não mostra nada se já foi verificado e está online (e não está mostrando sucesso)
  if (backendStatusChecked && backendStatus === 'online' && !showSuccess) {
    return null
  }

  // Não mostra nada se ainda não começou a verificação
  if (!backendStatusChecked && !isChecking && backendStatus === 'unknown') {
    return null
  }

  const getAlertContent = (): {
    variant: 'default' | 'destructive'
    icon: React.ReactNode
    title: string
    description: string
    showRetryButton?: boolean
  } => {
    if (isChecking || backendStatus === 'unknown') {
      return {
        variant: 'default' as const,
        icon: <Loader2 className="h-4 w-4 animate-spin" />,
        title: 'Verificando status do backend...',
        description: 'Aguarde enquanto verificamos se o serviço está disponível.',
      }
    }

    if (backendStatus === 'waking') {
      return {
        variant: 'default' as const,
        icon: <Zap className="h-4 w-4 animate-pulse" />,
        title: 'Acordando o backend...',
        description: 'O serviço estava inativo e está sendo acordado. Isso pode levar alguns segundos. Por favor, aguarde.',
      }
    }

    if (backendStatus === 'offline') {
      return {
        variant: 'destructive' as const,
        icon: <AlertCircle className="h-4 w-4" />,
        title: 'Backend indisponível',
        description: message || 'Não foi possível conectar ao backend. Tente novamente em alguns instantes.',
        showRetryButton: true,
      }
    }

    return {
      variant: 'default' as const,
      icon: <CheckCircle2 className="h-4 w-4" />,
      title: 'Backend online',
      description: 'O serviço está disponível e pronto para uso.',
    }
  }

  const content = getAlertContent()

  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-md">
      <Alert variant={content.variant}>
        <div className="flex items-start gap-3">
          {content.icon}
          <div className="flex-1">
            <AlertTitle>{content.title}</AlertTitle>
            <AlertDescription className="mt-1">{content.description}</AlertDescription>
            {content.showRetryButton && (
              <Button
                variant="outline"
                size="sm"
                className="mt-3"
                onClick={() => {
                  previousStatusRef.current = backendStatus
                  handleCheckStatus()
                }}
                disabled={isChecking}
              >
                {isChecking ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Verificando...
                  </>
                ) : (
                  'Tentar novamente'
                )}
              </Button>
            )}
          </div>
        </div>
      </Alert>
    </div>
  )
}

