/**
 * GenerationProgress Component
 * 
 * A premium, multi-stage progress indicator for AI preview generation.
 * Shows real-time status updates aligned with the AI workflow stages.
 * 
 * Design principles:
 * - Transparent: Users see exactly what's happening
 * - Trustworthy: Each stage has clear purpose
 * - Intentional: Animations and transitions feel designed
 * - Premium: Worthy of a high-ticket SaaS product
 */

import { useEffect, useState } from 'react'
import {
  CheckCircleIcon,
  CameraIcon,
  EyeIcon,
  SparklesIcon,
  AdjustmentsHorizontalIcon,
  DocumentCheckIcon,
  RocketLaunchIcon,
} from '@heroicons/react/24/outline'
import { CheckCircleIcon as CheckCircleSolidIcon } from '@heroicons/react/24/solid'

export interface GenerationStage {
  id: string
  name: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  status: 'pending' | 'active' | 'completed'
  detail?: string
}

const DEFAULT_STAGES: GenerationStage[] = [
  {
    id: 'capture',
    name: 'Capturing Page',
    description: 'Taking a high-resolution screenshot',
    icon: CameraIcon,
    status: 'pending',
  },
  {
    id: 'analyze',
    name: 'Visual Analysis',
    description: 'Identifying UI regions and content',
    icon: EyeIcon,
    status: 'pending',
  },
  {
    id: 'prioritize',
    name: 'Smart Prioritization',
    description: 'Ranking elements by importance',
    icon: AdjustmentsHorizontalIcon,
    status: 'pending',
  },
  {
    id: 'compose',
    name: 'Layout Design',
    description: 'Composing optimal preview structure',
    icon: SparklesIcon,
    status: 'pending',
  },
  {
    id: 'validate',
    name: 'Quality Check',
    description: 'Validating clarity and balance',
    icon: DocumentCheckIcon,
    status: 'pending',
  },
  {
    id: 'render',
    name: 'Finalizing',
    description: 'Rendering preview image',
    icon: RocketLaunchIcon,
    status: 'pending',
  },
]

interface GenerationProgressProps {
  isGenerating: boolean
  currentStage?: number
  stages?: GenerationStage[]
  overallProgress?: number
  statusMessage?: string
  estimatedTimeRemaining?: number
}

export default function GenerationProgress({
  isGenerating,
  currentStage = 0,
  stages: customStages,
  overallProgress = 0,
  statusMessage,
  estimatedTimeRemaining,
}: GenerationProgressProps) {
  const [stages, setStages] = useState<GenerationStage[]>(customStages || DEFAULT_STAGES)
  const [pulseStage, setPulseStage] = useState<string | null>(null)
  const [showDetail, setShowDetail] = useState<string | null>(null)

  // Update stage statuses based on currentStage
  useEffect(() => {
    if (!isGenerating) {
      setStages(prev => prev.map(s => ({ ...s, status: 'pending' as const })))
      return
    }

    setStages(prev => prev.map((stage, index) => ({
      ...stage,
      status: index < currentStage 
        ? 'completed' as const
        : index === currentStage 
          ? 'active' as const
          : 'pending' as const
    })))

    // Pulse animation for active stage
    const activeStage = stages[currentStage]
    if (activeStage) {
      setPulseStage(activeStage.id)
    }
  }, [currentStage, isGenerating])

  if (!isGenerating) return null

  const completedCount = stages.filter(s => s.status === 'completed').length
  const progressPercent = Math.max(overallProgress, (completedCount / stages.length) * 100)

  return (
    <div className="w-full max-w-lg mx-auto">
      {/* Main Progress Card */}
      <div className="bg-white rounded-2xl shadow-2xl border border-gray-200/80 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-500 via-amber-500 to-orange-500 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                  <SparklesIcon className="w-6 h-6 text-white animate-pulse" />
                </div>
                {/* Spinning ring */}
                <div className="absolute inset-0 rounded-xl border-2 border-white/30 border-t-white animate-spin" style={{ animationDuration: '2s' }} />
              </div>
              <div>
                <h3 className="text-white font-bold text-lg">AI Working</h3>
                <p className="text-white/80 text-sm">{statusMessage || 'Analyzing your page...'}</p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-white font-bold text-2xl">{Math.round(progressPercent)}%</div>
              {estimatedTimeRemaining && estimatedTimeRemaining > 0 && (
                <div className="text-white/70 text-xs">~{Math.ceil(estimatedTimeRemaining)}s left</div>
              )}
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="mt-4 h-2 bg-white/20 rounded-full overflow-hidden">
            <div 
              className="h-full bg-white rounded-full transition-all duration-500 ease-out relative overflow-hidden"
              style={{ width: `${progressPercent}%` }}
            >
              {/* Shimmer effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent animate-shimmer" />
            </div>
          </div>
        </div>

        {/* Stages List */}
        <div className="p-4 space-y-1">
          {stages.map((stage, index) => {
            const StageIcon = stage.icon
            const isActive = stage.status === 'active'
            const isCompleted = stage.status === 'completed'
            const isPending = stage.status === 'pending'
            
            return (
              <div
                key={stage.id}
                className={`
                  relative flex items-center space-x-3 p-3 rounded-xl transition-all duration-300
                  ${isActive ? 'bg-orange-50 border border-orange-200' : ''}
                  ${isCompleted ? 'opacity-60' : ''}
                  ${isPending ? 'opacity-40' : ''}
                `}
                onMouseEnter={() => setShowDetail(stage.id)}
                onMouseLeave={() => setShowDetail(null)}
              >
                {/* Stage Number / Icon */}
                <div className={`
                  relative w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0
                  transition-all duration-300
                  ${isCompleted ? 'bg-emerald-500' : ''}
                  ${isActive ? 'bg-orange-500' : ''}
                  ${isPending ? 'bg-gray-200' : ''}
                `}>
                  {isCompleted ? (
                    <CheckCircleSolidIcon className="w-6 h-6 text-white" />
                  ) : isActive ? (
                    <>
                      <StageIcon className="w-5 h-5 text-white" />
                      {/* Pulse ring for active */}
                      <div className="absolute inset-0 rounded-full bg-orange-500 animate-ping opacity-30" />
                    </>
                  ) : (
                    <span className="text-gray-500 font-semibold text-sm">{index + 1}</span>
                  )}
                </div>

                {/* Stage Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className={`font-semibold text-sm ${isActive ? 'text-orange-700' : isCompleted ? 'text-gray-600' : 'text-gray-500'}`}>
                      {stage.name}
                    </span>
                    {isActive && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-700">
                        In Progress
                      </span>
                    )}
                    {isCompleted && (
                      <CheckCircleIcon className="w-4 h-4 text-emerald-500" />
                    )}
                  </div>
                  <p className={`text-xs mt-0.5 ${isActive ? 'text-orange-600' : 'text-gray-400'}`}>
                    {stage.description}
                  </p>
                </div>

                {/* Connecting Line */}
                {index < stages.length - 1 && (
                  <div className={`
                    absolute left-7 top-14 w-0.5 h-4 -mt-1
                    ${isCompleted ? 'bg-emerald-300' : 'bg-gray-200'}
                  `} />
                )}
              </div>
            )
          })}
        </div>

        {/* Footer Tips */}
        <div className="px-4 pb-4">
          <div className="bg-gray-50 rounded-xl p-3 border border-gray-100">
            <div className="flex items-start space-x-2">
              <SparklesIcon className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-xs text-gray-600">
                  <span className="font-semibold text-gray-700">AI Insight:</span>
                  {' '}Our multi-stage reasoning framework analyzes your page like a senior designer, identifying what matters most for social sharing.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Custom Animations */}
      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        .animate-shimmer {
          animation: shimmer 1.5s infinite;
        }
      `}</style>
    </div>
  )
}

/**
 * Hook for managing generation progress state
 */
export function useGenerationProgress() {
  const [isGenerating, setIsGenerating] = useState(false)
  const [currentStage, setCurrentStage] = useState(0)
  const [overallProgress, setOverallProgress] = useState(0)
  const [statusMessage, setStatusMessage] = useState('')
  const [estimatedTime, setEstimatedTime] = useState(0)

  const startGeneration = () => {
    setIsGenerating(true)
    setCurrentStage(0)
    setOverallProgress(0)
    setStatusMessage('Initializing...')
    setEstimatedTime(30)
  }

  const advanceStage = (stageName?: string) => {
    setCurrentStage(prev => Math.min(prev + 1, 5))
    if (stageName) {
      setStatusMessage(stageName)
    }
  }

  const updateProgress = (progress: number, message?: string) => {
    setOverallProgress(progress)
    if (message) {
      setStatusMessage(message)
    }
    // Update estimated time based on progress
    const remaining = ((100 - progress) / 100) * 30
    setEstimatedTime(Math.max(0, remaining))
  }

  const completeGeneration = () => {
    setCurrentStage(6)
    setOverallProgress(100)
    setStatusMessage('Complete!')
    setTimeout(() => {
      setIsGenerating(false)
    }, 500)
  }

  const resetGeneration = () => {
    setIsGenerating(false)
    setCurrentStage(0)
    setOverallProgress(0)
    setStatusMessage('')
    setEstimatedTime(0)
  }

  return {
    isGenerating,
    currentStage,
    overallProgress,
    statusMessage,
    estimatedTime,
    startGeneration,
    advanceStage,
    updateProgress,
    completeGeneration,
    resetGeneration,
  }
}

