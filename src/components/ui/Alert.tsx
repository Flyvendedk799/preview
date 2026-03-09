import { ReactNode } from 'react'
import {
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline'

export type AlertVariant = 'error' | 'success' | 'warning' | 'info'

interface AlertProps {
  variant: AlertVariant
  title?: string
  children: ReactNode
  className?: string
  onDismiss?: () => void
}

const variantConfig = {
  error: {
    classes: 'alert-error',
    icon: ExclamationCircleIcon,
    iconClasses: 'text-error-600',
  },
  success: {
    classes: 'alert-success',
    icon: CheckCircleIcon,
    iconClasses: 'text-success-600',
  },
  warning: {
    classes: 'alert-warning',
    icon: ExclamationTriangleIcon,
    iconClasses: 'text-warning-600',
  },
  info: {
    classes: 'alert-info',
    icon: InformationCircleIcon,
    iconClasses: 'text-primary-600',
  },
}

export default function Alert({ variant, title, children, className = '', onDismiss }: AlertProps) {
  const config = variantConfig[variant]
  const Icon = config.icon

  return (
    <div className={`${config.classes} ${className} ${onDismiss ? 'pr-10 relative' : ''}`}>
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 flex-shrink-0 mt-0.5 ${config.iconClasses}`} />
        <div className="flex-1 min-w-0">
          {title && <p className="font-medium mb-1">{title}</p>}
          <div className="text-sm [&>p]:mb-0">{children}</div>
        </div>
      </div>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="absolute top-4 right-4 p-1 rounded hover:bg-black/5 transition-colors"
          aria-label="Dismiss"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  )
}
