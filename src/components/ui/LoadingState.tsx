import { ReactNode } from 'react'

interface LoadingStateProps {
  message?: string
  className?: string
  children?: ReactNode
}

export default function LoadingState({ message = 'Loading...', className = '', children }: LoadingStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center py-12 ${className}`}>
      <div
        className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mb-4"
        aria-hidden
      />
      <p className="text-secondary-500 text-sm">{message}</p>
      {children}
    </div>
  )
}
