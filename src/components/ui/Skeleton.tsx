import { ReactNode } from 'react'

interface SkeletonProps {
  className?: string
  children?: ReactNode
}

export default function Skeleton({ className = '', children }: SkeletonProps) {
  if (children) {
    return <div className={`skeleton ${className}`}>{children}</div>
  }
  return <div className={`skeleton ${className}`} />
}

// Pre-built skeleton components
export function SkeletonCard() {
  return (
    <div className="card">
      <div className="skeleton h-6 w-3/4 mb-4" />
      <div className="skeleton h-4 w-full mb-2" />
      <div className="skeleton h-4 w-5/6" />
    </div>
  )
}

export function SkeletonList({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center space-x-4">
          <div className="skeleton h-12 w-12 rounded-lg flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <div className="skeleton h-4 w-3/4" />
            <div className="skeleton h-3 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  )
}

export function SkeletonGrid({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  )
}

