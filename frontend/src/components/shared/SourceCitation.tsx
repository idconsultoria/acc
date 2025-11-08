import { useState } from 'react'
import { CitedSource } from '@/api/client'
import { cn } from '@/lib/utils'

interface SourceCitationProps {
  source: CitedSource
}

const SourceCitation = ({ source }: SourceCitationProps) => {
  const [isHovered, setIsHovered] = useState(false)

  return (
    <span className="inline-block relative group mx-1">
      <div
        className="flex h-7 shrink-0 items-center justify-center gap-x-2 rounded-lg bg-primary/20 dark:bg-[#243047] px-3 cursor-pointer"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <p className="text-primary dark:text-white text-sm font-medium leading-normal">
          {source.title || 'Fonte'}
        </p>
      </div>
      <div
        className={cn(
          'absolute bottom-full mb-2 w-72 left-1/2 -translate-x-1/2 transition-opacity duration-200 pointer-events-none z-50',
          isHovered ? 'opacity-100 pointer-events-auto' : 'opacity-0'
        )}
      >
        <div className="bg-white dark:bg-gray-900 p-4 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 space-y-2">
          <div>
            <h4 className="font-bold text-gray-900 dark:text-white text-base">
              Fonte: {source.title || 'Artefato'}
            </h4>
            {source.section_title && (
              <p className="text-xs uppercase tracking-wide text-muted-foreground">
                Seção: {source.section_title}
              </p>
            )}
            {source.breadcrumbs && source.breadcrumbs.length > 0 && (
              <p className="text-xs text-muted-foreground">
                {source.breadcrumbs.join(' › ')}
              </p>
            )}
          </div>
          <div>
            <p className="text-[11px] font-semibold text-muted-foreground uppercase">
              Trecho
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 whitespace-pre-line">
              {source.chunk_content_preview}
            </p>
          </div>
          {source.content_type && (
            <div className="text-xs text-muted-foreground flex gap-2">
              <span className="px-2 py-1 rounded bg-muted/50 border border-muted">
                Tipo: {source.content_type}
              </span>
            </div>
          )}
        </div>
      </div>
    </span>
  )
}

export default SourceCitation

