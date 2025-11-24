import { ReactNode } from 'react'
import Button from './Button'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
  }
  secondaryAction?: {
    label: string
    onClick: () => void
  }
}

export default function EmptyState({
  icon,
  title,
  description,
  action,
  secondaryAction,
}: EmptyStateProps) {
  return (
    <div className="text-center py-12 px-4">
      {icon && (
        <div className="flex justify-center mb-4">
          <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center text-gray-400">
            {icon}
          </div>
        </div>
      )}
      <h3 className="text-lg font-semibold text-secondary mb-2">{title}</h3>
      <p className="text-muted max-w-md mx-auto mb-6">{description}</p>
      {action && (
        <div className="flex items-center justify-center gap-3">
          <Button onClick={action.onClick}>{action.label}</Button>
          {secondaryAction && (
            <Button variant="ghost" onClick={secondaryAction.onClick}>
              {secondaryAction.label}
            </Button>
          )}
        </div>
      )}
    </div>
  )
}

