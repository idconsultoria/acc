import { cn } from '@/lib/utils'

export type RagPhaseStatus = 'pending' | 'running' | 'complete'

export interface RagPhaseState {
  id: string
  label: string
  status: RagPhaseStatus
  metadata?: Record<string, unknown>
}

interface RagPipelineTimelineProps {
  phases: RagPhaseState[]
  isStreaming: boolean
}

const statusLabels: Record<RagPhaseStatus, string> = {
  pending: 'Pendente',
  running: 'Em andamento',
  complete: 'Concluída',
}

const statusStyles: Record<RagPhaseStatus, string> = {
  pending: 'text-muted-foreground',
  running: 'text-primary',
  complete: 'text-emerald-600 dark:text-emerald-400',
}

const formatValue = (value: unknown): string | null => {
  if (value === null || value === undefined) {
    return null
  }

  if (typeof value === 'number') {
    return value.toString()
  }

  if (typeof value === 'boolean') {
    return value ? 'Sim' : 'Não'
  }

  if (typeof value === 'string') {
    return value
  }

  return null
}

const formatKey = (key: string): string => {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

const RagPipelineTimeline = ({ phases, isStreaming }: RagPipelineTimelineProps) => {
  if (!phases.length) {
    return null
  }

  return (
    <div className="rounded-lg border border-border bg-card/70 p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">Pipeline RAG</h3>
        <span
          className={cn(
            'text-xs font-medium',
            isStreaming ? 'text-primary animate-pulse' : 'text-muted-foreground'
          )}
        >
          {isStreaming ? 'Transmitindo resposta' : 'Última execução concluída'}
        </span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {phases.map((phase) => {
          const metadataEntries = Object.entries(phase.metadata ?? {}).reduce<string[][]>(
            (acc, [key, value]) => {
              if (key === 'status' || key === 'phase') {
                return acc
              }
              const formatted = formatValue(value)
              if (formatted) {
                acc.push([formatKey(key), formatted])
              }
              return acc
            },
            []
          )

          return (
            <div
              key={phase.id}
              className="rounded-md border border-border/60 bg-background/90 p-3"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-foreground">{phase.label}</span>
                <span
                  className={cn(
                    'text-xs font-semibold uppercase tracking-wide',
                    statusStyles[phase.status]
                  )}
                >
                  {statusLabels[phase.status]}
                </span>
              </div>

              {metadataEntries.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {metadataEntries.slice(0, 3).map(([keyLabel, value]) => (
                    <li key={keyLabel} className="text-xs text-muted-foreground">
                      <span className="font-medium text-foreground">{keyLabel}:</span>{' '}
                      {value}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default RagPipelineTimeline
