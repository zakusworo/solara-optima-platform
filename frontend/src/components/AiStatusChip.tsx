import { useState, useEffect } from 'react'
import { api } from '../utils/api'

export interface AiStatus {
  ollama_available: boolean
  model: string
  host: string
  capabilities: string[]
}

/**
 * Small badge showing whether the Ollama LLM backend is reachable.
 * Green = agent inference available; amber = endpoints fall back to
 * statistical / pvlib pass-through methods.
 */
export default function AiStatusChip({ onStatus }: { onStatus?: (s: AiStatus) => void }) {
  const [status, setStatus] = useState<AiStatus | null>(null)

  useEffect(() => {
    api.get('/api/v1/ai/status')
      .then((r) => {
        if (r.data.success) {
          setStatus(r.data.data)
          onStatus?.(r.data.data)
        }
      })
      .catch(() => setStatus(null))
  }, [])

  if (!status) return null

  return status.ollama_available ? (
    <span
      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs bg-[#E4EDD8] text-[#3A7010]"
      title={`Ollama at ${status.host}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-[#3A7010]" />
      AI: {status.model} ready
    </span>
  ) : (
    <span
      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs bg-[#F3EAD4] text-[#A07010]"
      title="Ollama offline — AI endpoints use statistical / pvlib fallbacks"
    >
      <span className="w-1.5 h-1.5 rounded-full bg-[#A07010]" />
      AI: fallback mode
    </span>
  )
}
