import { useState, useEffect, useCallback } from 'react'
import { fetchBrandSettings, updateBrandSettings } from '../api/client'
import type { BrandSettings, BrandSettingsUpdate } from '../api/types'

interface UseBrandSettingsReturn {
  settings: BrandSettings | null
  loading: boolean
  error: string | null
  updateSettings: (payload: BrandSettingsUpdate) => Promise<void>
  refetch: () => Promise<void>
}

export function useBrandSettings(): UseBrandSettingsReturn {
  const [settings, setSettings] = useState<BrandSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadSettings = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await fetchBrandSettings()
      setSettings(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load brand settings')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSettings()
  }, [loadSettings])

  const updateSettings = useCallback(async (payload: BrandSettingsUpdate) => {
    try {
      setError(null)
      const updated = await updateBrandSettings(payload)
      setSettings(updated)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update brand settings')
      throw err
    }
  }, [])

  return {
    settings,
    loading,
    error,
    updateSettings,
    refetch: loadSettings,
  }
}

