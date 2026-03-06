import { useState, useRef, useCallback } from 'react'
import { createDemoJob, getDemoJobStatus, type DemoPreviewResponseV2, type DemoJobStatusResponse } from '../api/client'
import { logger } from '../utils/logger'

export interface GenerationStageConfig {
  id: string
  progress: number
  time: number
  message: string
}

export const GENERATION_STAGES: GenerationStageConfig[] = [
  { id: 'capture', progress: 10, time: 4, message: 'Capturing page screenshot...' },
  { id: 'classify', progress: 18, time: 2, message: 'Classifying page type...' },
  { id: 'extract', progress: 35, time: 8, message: 'Extracting brand & content...' },
  { id: 'analyze', progress: 55, time: 10, message: 'Running AI analysis...' },
  { id: 'normalize', progress: 68, time: 2, message: 'Normalizing content...' },
  { id: 'compose', progress: 80, time: 5, message: 'Compositing preview image...' },
  { id: 'quality', progress: 90, time: 3, message: 'Validating quality...' },
  { id: 'finalize', progress: 95, time: 2, message: 'Finalizing result...' },
]

export interface DemoGenerationState {
  isGenerating: boolean
  preview: DemoPreviewResponseV2 | null
  error: string | null
  progress: number
  currentStage: number
  statusMessage: string
  estimatedTimeRemaining: number
  showCelebration: boolean
}

export interface DemoGenerationActions {
  generatePreview: (url: string) => Promise<void>
  cancelGeneration: () => void
  resetError: () => void
  resetAll: () => void
}

export function useDemoGeneration(): [DemoGenerationState, DemoGenerationActions] {
  const [isGenerating, setIsGenerating] = useState(false)
  const [preview, setPreview] = useState<DemoPreviewResponseV2 | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const [currentStage, setCurrentStage] = useState(0)
  const [statusMessage, setStatusMessage] = useState('')
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState(0)
  const [showCelebration, setShowCelebration] = useState(false)

  const cancelRef = useRef(false)
  const lastProgressRef = useRef(0)

  const resetState = useCallback(() => {
    setProgress(0)
    setCurrentStage(0)
    setStatusMessage('')
    setEstimatedTimeRemaining(0)
    lastProgressRef.current = 0
  }, [])

  const cancelGeneration = useCallback(() => {
    cancelRef.current = true
    setIsGenerating(false)
    resetState()
  }, [resetState])

  const resetError = useCallback(() => {
    setError(null)
  }, [])

  const resetAll = useCallback(() => {
    setPreview(null)
    setError(null)
    setIsGenerating(false)
    setShowCelebration(false)
    resetState()
  }, [resetState])

  const generatePreview = useCallback(async (urlToProcess: string) => {
    setIsGenerating(true)
    setCurrentStage(0)
    setProgress(2)
    setStatusMessage('Initializing AI analysis...')
    setEstimatedTimeRemaining(30)
    setError(null)
    cancelRef.current = false
    lastProgressRef.current = 0

    try {
      // Validate URL
      try {
        new URL(urlToProcess)
      } catch {
        throw new Error('Invalid URL format. Please enter a valid URL (e.g., https://example.com)')
      }

      const jobResponse = await createDemoJob(urlToProcess)
      const jobId = jobResponse.job_id

      if (cancelRef.current) return

      logger.info(`[Demo] Job created: ${jobId}`)

      // Poll for job status
      const pollInterval = 2000
      const maxPollTime = 600000
      const startPollTime = Date.now()

      const pollJobStatus = async (): Promise<DemoPreviewResponseV2> => {
        let consecutiveErrors = 0
        const maxConsecutiveErrors = 5

        while (Date.now() - startPollTime < maxPollTime) {
          if (cancelRef.current) throw new Error('Generation cancelled')

          try {
            const statusResponse: DemoJobStatusResponse = await getDemoJobStatus(jobId)
            consecutiveErrors = 0

            if (statusResponse.status === 'failed') {
              const errorMsg = statusResponse.error || 'Job failed with unknown error'
              if (errorMsg.includes('Page load timeout') || errorMsg.includes('Timeout')) {
                throw new Error('The website took too long to load. Please try a different URL or try again later.')
              } else if (errorMsg.includes('Failed to capture')) {
                throw new Error('Unable to capture the website. The site may be blocking automated access.')
              }
              throw new Error(errorMsg)
            }

            if (statusResponse.status === 'finished') {
              setCurrentStage(GENERATION_STAGES.length)
              setProgress(100)
              setStatusMessage('Preview complete!')
              setEstimatedTimeRemaining(0)

              if (statusResponse.result) {
                return statusResponse.result
              }
              await new Promise(resolve => setTimeout(resolve, 1000))
              continue
            }

            // Update progress monotonically
            if (statusResponse.progress !== null) {
              const backendPercent = statusResponse.progress * 100
              if (backendPercent >= lastProgressRef.current) {
                lastProgressRef.current = backendPercent
                const capped = Math.min(95, backendPercent)
                setProgress(capped)
                setStatusMessage(statusResponse.message || 'Processing...')

                // Map progress to stage (matches backend pipeline stages)
                let stageIndex = 0
                if (capped >= 10) stageIndex = 1
                if (capped >= 18) stageIndex = 2
                if (capped >= 35) stageIndex = 3
                if (capped >= 55) stageIndex = 4
                if (capped >= 68) stageIndex = 5
                if (capped >= 80) stageIndex = 6
                if (capped >= 90) stageIndex = 7
                if (capped >= 95) stageIndex = 8
                setCurrentStage(Math.min(stageIndex, GENERATION_STAGES.length - 1))

                // Estimate remaining time
                const elapsed = (Date.now() - startPollTime) / 1000
                if (capped > 0 && capped < 95) {
                  const estimatedTotal = elapsed / (capped / 100)
                  setEstimatedTimeRemaining(Math.max(3, Math.ceil(estimatedTotal - elapsed)))
                } else if (capped >= 95) {
                  setEstimatedTimeRemaining(0)
                }
              }
            }

            await new Promise(resolve => setTimeout(resolve, pollInterval))
          } catch (err) {
            if (err instanceof Error && (
              err.message === 'Generation cancelled' ||
              err.message.includes('took too long') ||
              err.message.includes('Unable to capture') ||
              err.message.includes('not found') ||
              err.message.includes('404')
            )) {
              throw err
            }

            consecutiveErrors++
            if (consecutiveErrors >= maxConsecutiveErrors) {
              throw new Error(`Unable to check job status after ${maxConsecutiveErrors} attempts. Please try again.`)
            }
            await new Promise(resolve => setTimeout(resolve, pollInterval * Math.min(consecutiveErrors, 3)))
          }
        }
        throw new Error('Preview generation timed out after 10 minutes.')
      }

      const result = await pollJobStatus()
      if (cancelRef.current) return

      // Show celebration briefly
      setShowCelebration(true)
      await new Promise(resolve => setTimeout(resolve, 1200))

      setPreview(result)
      setShowCelebration(false)
      resetState()
    } catch (err) {
      if (cancelRef.current) return

      const errorStr = err instanceof Error ? err.message : String(err)
      let errorMessage = errorStr

      if (errorStr.includes('Invalid URL') || errorStr.includes('field required')) {
        errorMessage = 'Please enter a valid URL (e.g., https://example.com)'
      } else if (errorStr.includes('not found') || errorStr.includes('404')) {
        errorMessage = 'The preview job was not found. It may have expired. Please try again.'
      }

      setError(errorMessage)
      resetState()
    } finally {
      if (!cancelRef.current) {
        setIsGenerating(false)
      }
    }
  }, [resetState])

  const state: DemoGenerationState = {
    isGenerating,
    preview,
    error,
    progress,
    currentStage,
    statusMessage,
    estimatedTimeRemaining,
    showCelebration,
  }

  const actions: DemoGenerationActions = {
    generatePreview,
    cancelGeneration,
    resetError,
    resetAll,
  }

  return [state, actions]
}
