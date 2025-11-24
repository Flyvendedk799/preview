import { useState, useEffect, useCallback } from 'react'
import { fetchDomains, createDomain, deleteDomain } from '../api/client'
import type { Domain, DomainCreate } from '../api/types'

interface UseDomainsReturn {
  domains: Domain[]
  loading: boolean
  error: string | null
  addDomain: (payload: DomainCreate) => Promise<void>
  removeDomain: (id: number) => Promise<void>
  refetch: () => Promise<void>
}

export function useDomains(): UseDomainsReturn {
  const [domains, setDomains] = useState<Domain[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadDomains = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await fetchDomains()
      setDomains(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load domains')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDomains()
  }, [loadDomains])

  const addDomain = useCallback(async (payload: DomainCreate) => {
    try {
      setError(null)
      const newDomain = await createDomain(payload)
      setDomains((prev) => [...prev, newDomain])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create domain')
      throw err
    }
  }, [])

  const removeDomain = useCallback(async (id: number) => {
    try {
      setError(null)
      await deleteDomain(id)
      setDomains((prev) => prev.filter((d) => d.id !== id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete domain')
      throw err
    }
  }, [])

  return {
    domains,
    loading,
    error,
    addDomain,
    removeDomain,
    refetch: loadDomains,
  }
}

