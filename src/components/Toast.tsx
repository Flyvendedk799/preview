import { useEffect } from 'react'
import { CheckCircleIcon, XMarkIcon } from '@heroicons/react/24/outline'

interface ToastProps {
  message: string
  type?: 'success' | 'error'
  onClose: () => void
  duration?: number
}

export default function Toast({ message, type = 'success', onClose, duration = 3000 }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose()
    }, duration)

    return () => clearTimeout(timer)
  }, [duration, onClose])

  return (
    <div className="fixed top-4 right-4 z-50 animate-slide-in-right">
      <div
        className={`flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg border backdrop-blur-sm ${
          type === 'success'
            ? 'bg-green-50 border-green-200 text-green-800'
            : 'bg-red-50 border-red-200 text-red-800'
        }`}
      >
        {type === 'success' && <CheckCircleIcon className="w-5 h-5 flex-shrink-0" />}
        <span className="font-medium text-sm">{message}</span>
        <button
          onClick={onClose}
          className={`ml-2 p-1 rounded-lg hover:bg-opacity-20 transition-colors ${
            type === 'success' ? 'hover:bg-green-600' : 'hover:bg-red-600'
          }`}
          aria-label="Close"
        >
          <XMarkIcon className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

