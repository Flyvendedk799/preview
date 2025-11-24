import { useState, useEffect, useCallback } from 'react'
import { fetchPreviews, createOrUpdatePreview, updatePreview, deletePreview, generatePreviewWithAI, createPreviewJob, getJobStatus } from '../api/client'
import type { Preview, PreviewCreate, PreviewUpdate } from '../api/types'

interface UsePreviewsReturn {
  previews: Preview[]
  loading: boolean
  error: string | null
  createOrUpdatePreview: (input: PreviewCreate) => Promise<Preview>
  updatePreview: (id: number, input: PreviewUpdate) => Promise<void>
  deletePreview: (id: number) => Promise<void>
  generateWithAI: (url: string, domain: string) => Promise<Preview>
  generatePreviewAsync: (url: string, domain: string) => Promise<string>
  refetch: (type?: string) => Promise<void>
}

export function usePreviews(type?: string): UsePreviewsReturn {
  const [previews, setPreviews] = useState<Preview[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadPreviews = useCallback(
    async (filterType?: string) => {
      try {
        setLoading(true)
        setError(null)
        const data = await fetchPreviews(filterType)
        setPreviews(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load previews')
      } finally {
        setLoading(false)
      }
    },
    []
  )

  useEffect(() => {
    loadPreviews(type)
  }, [loadPreviews, type])

  const handleCreateOrUpdate = useCallback(
    async (input: PreviewCreate): Promise<Preview> => {
      try {
        setError(null)
        const newPreview = await createOrUpdatePreview(input)
        await loadPreviews(type)
        return newPreview
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to create/update preview')
        throw err
      }
    },
    [loadPreviews, type]
  )

  const handleUpdate = useCallback(
    async (id: number, input: PreviewUpdate): Promise<void> => {
      try {
        setError(null)
        await updatePreview(id, input)
        await loadPreviews(type)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to update preview')
        throw err
      }
    },
    [loadPreviews, type]
  )

  const handleDelete = useCallback(
    async (id: number): Promise<void> => {
      try {
        setError(null)
        await deletePreview(id)
        setPreviews((prev) => prev.filter((p) => p.id !== id))
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete preview')
        throw err
      }
    },
    []
  )

  const handleGenerateWithAI = useCallback(
    async (url: string, domain: string): Promise<Preview> => {
      try {
        setError(null)
        const newPreview = await generatePreviewWithAI({ url, domain })
        await loadPreviews(type)
        return newPreview
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to generate preview with AI')
        throw err
      }
    },
    [loadPreviews, type]
  )

  const handleGeneratePreviewAsync = useCallback(
    async (url: string, domain: string): Promise<string> => {
      try {
        setError(null)
        // Create job
        const { job_id } = await createPreviewJob({ url, domain })
        
        // Poll job status until finished
        return new Promise((resolve, reject) => {
          const pollInterval = setInterval(async () => {
            try {
              const status = await getJobStatus(job_id)
              
              if (status.status === 'finished') {
                clearInterval(pollInterval)
                // Reload previews
                await loadPreviews(type)
                resolve(job_id)
              } else if (status.status === 'failed') {
                clearInterval(pollInterval)
                const errorMsg = status.error || 'Job failed'
                setError(errorMsg)
                reject(new Error(errorMsg))
              }
              // Continue polling for 'queued' and 'started' statuses
            } catch (err) {
              clearInterval(pollInterval)
              setError(err instanceof Error ? err.message : 'Failed to poll job status')
              reject(err)
            }
          }, 1500) // Poll every 1.5 seconds
          
          // Timeout after 2 minutes
          setTimeout(() => {
            clearInterval(pollInterval)
            reject(new Error('Job timeout: Preview generation took too long'))
          }, 120000)
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to create preview job')
        throw err
      }
    },
    [loadPreviews, type]
  )

  return {
    previews,
    loading,
    error,
    createOrUpdatePreview: handleCreateOrUpdate,
    updatePreview: handleUpdate,
    deletePreview: handleDelete,
    generateWithAI: handleGenerateWithAI,
    generatePreviewAsync: handleGeneratePreviewAsync,
    refetch: loadPreviews,
  }
}

