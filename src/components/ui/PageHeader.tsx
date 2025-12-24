import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRightIcon, HomeIcon } from '@heroicons/react/24/outline'

interface BreadcrumbItem {
  label: string
  href?: string
}

interface PageHeaderProps {
  title: string
  description?: string
  breadcrumbs?: BreadcrumbItem[]
  actions?: ReactNode
  badge?: ReactNode
  className?: string
}

export default function PageHeader({
  title,
  description,
  breadcrumbs,
  actions,
  badge,
  className = '',
}: PageHeaderProps) {
  return (
    <div className={`page-header ${className}`}>
      {/* Breadcrumbs */}
      {breadcrumbs && breadcrumbs.length > 0 && (
        <Breadcrumbs items={breadcrumbs} className="mb-3" />
      )}
      
      {/* Title and Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <h1 className="heading-3">{title}</h1>
          {badge}
        </div>
        
        {actions && (
          <div className="flex items-center gap-3 flex-shrink-0">
            {actions}
          </div>
        )}
      </div>
      
      {/* Description */}
      {description && (
        <p className="text-body mt-2">{description}</p>
      )}
    </div>
  )
}

// Standalone Breadcrumbs component
interface BreadcrumbsProps {
  items: BreadcrumbItem[]
  showHome?: boolean
  className?: string
}

export function Breadcrumbs({ items, showHome = true, className = '' }: BreadcrumbsProps) {
  const allItems = showHome 
    ? [{ label: 'Home', href: '/app' }, ...items]
    : items
  
  return (
    <nav aria-label="Breadcrumb" className={`breadcrumbs ${className}`}>
      {allItems.map((item, index) => {
        const isLast = index === allItems.length - 1
        
        return (
          <div key={index} className="flex items-center">
            {index === 0 && showHome ? (
              <Link 
                to={item.href || '/app'} 
                className="breadcrumb-link flex items-center gap-1"
              >
                <HomeIcon className="w-4 h-4" />
                <span className="sr-only">{item.label}</span>
              </Link>
            ) : (
              <>
                {index > 0 && (
                  <ChevronRightIcon className="w-4 h-4 mx-2 breadcrumb-separator" />
                )}
                {isLast || !item.href ? (
                  <span className={isLast ? 'breadcrumb-current' : ''}>
                    {item.label}
                  </span>
                ) : (
                  <Link to={item.href} className="breadcrumb-link">
                    {item.label}
                  </Link>
                )}
              </>
            )}
          </div>
        )
      })}
    </nav>
  )
}

// Page section header (for sub-sections within a page)
interface SectionHeaderProps {
  title: string
  description?: string
  action?: ReactNode
  className?: string
}

export function SectionHeader({ title, description, action, className = '' }: SectionHeaderProps) {
  return (
    <div className={`flex items-start justify-between mb-4 ${className}`}>
      <div>
        <h2 className="heading-5">{title}</h2>
        {description && (
          <p className="text-sm text-secondary-500 mt-0.5">{description}</p>
        )}
      </div>
      {action && <div className="flex-shrink-0 ml-4">{action}</div>}
    </div>
  )
}

