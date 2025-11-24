import { useState, useEffect, useCallback } from 'react'
import { fetchAnalyticsSummary } from '../api/client'
import type { AnalyticsSummary } from '../api/types'

interface UseAnalyticsSummaryReturn {
  summary: AnalyticsSummary | null
  loading: boolean
  error: string | null
  period: '7d' | '30d'
  setPeriod: (period: '7d' | '30d') => void
  refetch: () => Promise<void>
}

export function useAnalyticsSummary(
  initialPeriod: '7d' | '30d' = '7d'
): UseAnalyticsSummaryReturn {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [period, setPeriodState] = useState<'7d' | '30d'>(initialPeriod)

  const loadSummary = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await fetchAnalyticsSummary(period)
      setSummary(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics')
    } finally {
      setLoading(false)
    }
  }, [period])

  useEffect(() => {
    loadSummary()
  }, [loadSummary])

  const setPeriod = useCallback((newPeriod: '7d' | '30d') => {
    setPeriodState(newPeriod)
  }, [])

  return {
    summary,
    loading,
    error,
    period,
    setPeriod,
    refetch: loadSummary,
  }
}

