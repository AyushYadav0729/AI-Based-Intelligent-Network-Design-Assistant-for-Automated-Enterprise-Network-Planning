import React, { useEffect, useState } from 'react'
import { getHealth } from '../api/client'

/**
 * Polls /api/health once on mount and shows a colour-coded badge.
 * Green = backend up + LLM available
 * Yellow = backend up, no LLM key
 * Red = backend unreachable
 */
export default function HealthBadge() {
  const [health, setHealth] = useState(null)   // null = loading
  const [error, setError]   = useState(false)

  useEffect(() => {
    getHealth()
      .then(res => setHealth(res.data))
      .catch(() => setError(true))
  }, [])

  if (error) {
    return (
      <span className="inline-flex items-center gap-1 bg-red-600 text-white text-xs px-2 py-0.5 rounded-full">
        <span className="w-1.5 h-1.5 rounded-full bg-white" />
        Backend offline
      </span>
    )
  }

  if (!health) {
    return (
      <span className="inline-flex items-center gap-1 bg-gray-500 text-white text-xs px-2 py-0.5 rounded-full animate-pulse">
        <span className="w-1.5 h-1.5 rounded-full bg-white" />
        Checking…
      </span>
    )
  }

  const llm = health.llm_available
  return (
    <span
      className={`inline-flex items-center gap-1 text-white text-xs px-2 py-0.5 rounded-full ${
        llm ? 'bg-green-600' : 'bg-yellow-500'
      }`}
      title={llm ? `LLM: ${health.llm_model}` : 'No GEMINI_API_KEY — template fallback active'}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-white" />
      {llm ? 'LLM ready' : 'No LLM key'}
    </span>
  )
}
