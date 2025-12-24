import { ReactNode, createContext, useContext, useState } from 'react'

interface TabsContextValue {
  activeTab: string
  setActiveTab: (value: string) => void
}

const TabsContext = createContext<TabsContextValue | null>(null)

interface TabsProps {
  children: ReactNode
  defaultValue: string
  value?: string
  onChange?: (value: string) => void
  className?: string
}

export function Tabs({ children, defaultValue, value, onChange, className = '' }: TabsProps) {
  const [internalValue, setInternalValue] = useState(defaultValue)
  
  const activeTab = value ?? internalValue
  const setActiveTab = onChange ?? setInternalValue
  
  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  )
}

interface TabsListProps {
  children: ReactNode
  className?: string
  variant?: 'default' | 'pills' | 'underline'
}

export function TabsList({ children, className = '', variant = 'default' }: TabsListProps) {
  const variantClasses = {
    default: 'flex gap-1 p-1 bg-secondary-100 rounded-lg',
    pills: 'flex gap-2',
    underline: 'flex gap-6 border-b border-secondary-200',
  }
  
  return (
    <div className={`${variantClasses[variant]} ${className}`} role="tablist">
      {children}
    </div>
  )
}

interface TabsTriggerProps {
  children: ReactNode
  value: string
  className?: string
  disabled?: boolean
  icon?: ReactNode
  count?: number
}

export function TabsTrigger({ 
  children, 
  value, 
  className = '', 
  disabled = false,
  icon,
  count,
}: TabsTriggerProps) {
  const context = useContext(TabsContext)
  if (!context) throw new Error('TabsTrigger must be used within Tabs')
  
  const { activeTab, setActiveTab } = context
  const isActive = activeTab === value
  
  return (
    <button
      role="tab"
      aria-selected={isActive}
      disabled={disabled}
      onClick={() => setActiveTab(value)}
      className={`
        relative flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-md
        transition-all duration-200
        disabled:opacity-50 disabled:cursor-not-allowed
        ${isActive 
          ? 'bg-white text-secondary-900 shadow-soft' 
          : 'text-secondary-600 hover:text-secondary-900 hover:bg-white/50'
        }
        ${className}
      `}
    >
      {icon && <span className="flex-shrink-0">{icon}</span>}
      {children}
      {count !== undefined && (
        <span className={`
          ml-1 px-2 py-0.5 text-2xs font-semibold rounded-full
          ${isActive ? 'bg-primary-100 text-primary-700' : 'bg-secondary-200 text-secondary-600'}
        `}>
          {count}
        </span>
      )}
    </button>
  )
}

interface TabsContentProps {
  children: ReactNode
  value: string
  className?: string
}

export function TabsContent({ children, value, className = '' }: TabsContentProps) {
  const context = useContext(TabsContext)
  if (!context) throw new Error('TabsContent must be used within Tabs')
  
  if (context.activeTab !== value) return null
  
  return (
    <div 
      role="tabpanel"
      className={`animate-fade-in ${className}`}
    >
      {children}
    </div>
  )
}

// Simple Tab Button Group (for filter tabs)
interface TabButtonGroupProps {
  options: { value: string; label: string; count?: number }[]
  value: string
  onChange: (value: string) => void
  className?: string
}

export function TabButtonGroup({ options, value, onChange, className = '' }: TabButtonGroupProps) {
  return (
    <div className={`flex rounded-lg border border-secondary-200 overflow-hidden ${className}`}>
      {options.map((option, index) => (
        <button
          key={option.value}
          onClick={() => onChange(option.value)}
          className={`
            flex items-center gap-2 px-4 py-2 text-sm font-medium transition-all
            ${index > 0 ? 'border-l border-secondary-200' : ''}
            ${value === option.value
              ? 'bg-primary-500 text-white'
              : 'bg-white text-secondary-600 hover:bg-secondary-50 hover:text-secondary-900'
            }
          `}
        >
          {option.label}
          {option.count !== undefined && (
            <span className={`
              px-1.5 py-0.5 text-2xs font-semibold rounded-full
              ${value === option.value ? 'bg-white/20 text-white' : 'bg-secondary-100 text-secondary-600'}
            `}>
              {option.count}
            </span>
          )}
        </button>
      ))}
    </div>
  )
}

