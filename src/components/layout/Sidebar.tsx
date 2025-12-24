import { Link, useLocation, useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import {
  HomeIcon,
  GlobeAltIcon,
  PaintBrushIcon,
  PhotoIcon,
  ChartBarIcon,
  CreditCardIcon,
  XMarkIcon,
  ShieldCheckIcon,
  UserGroupIcon,
  ServerIcon,
  ClockIcon,
  BuildingOfficeIcon,
  ExclamationTriangleIcon,
  UserCircleIcon,
  DocumentTextIcon,
  EnvelopeIcon,
  NewspaperIcon,
  ChevronDownIcon,
  Cog6ToothIcon,
  Bars3Icon,
  DocumentIcon,
  FolderIcon,
  ArrowLeftIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'
import { useAuth } from '../../hooks/useAuth'
import { CountBadge } from '../ui/Badge'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

interface NavItem {
  name: string
  href: string
  icon: any
  badge?: number
}

interface NavGroup {
  name: string
  items: NavItem[]
  collapsible?: boolean
  defaultExpanded?: boolean
}

const mainNavigation: NavItem[] = [
  { name: 'Dashboard', href: '/app', icon: HomeIcon },
  { name: 'My Sites', href: '/app/sites', icon: NewspaperIcon },
  { name: 'Domains', href: '/app/domains', icon: GlobeAltIcon },
  { name: 'Preview Gallery', href: '/app/previews', icon: PhotoIcon },
]

const settingsNavigation: NavItem[] = [
  { name: 'Brand Settings', href: '/app/brand', icon: PaintBrushIcon },
  { name: 'Analytics', href: '/app/analytics', icon: ChartBarIcon },
  { name: 'Billing', href: '/app/billing', icon: CreditCardIcon },
  { name: 'Activity', href: '/app/activity', icon: ClockIcon },
  { name: 'Organizations', href: '/app/organizations', icon: BuildingOfficeIcon },
  { name: 'Account', href: '/app/account', icon: UserCircleIcon },
]

const adminNavigation: NavItem[] = [
  { name: 'Overview', href: '/app/admin', icon: ShieldCheckIcon },
  { name: 'Users', href: '/app/admin/users', icon: UserGroupIcon },
  { name: 'Domains', href: '/app/admin/domains', icon: GlobeAltIcon },
  { name: 'Previews', href: '/app/admin/previews', icon: PhotoIcon },
  { name: 'Blog', href: '/app/admin/blog', icon: DocumentTextIcon },
  { name: 'Newsletter', href: '/app/admin/newsletter', icon: EnvelopeIcon },
  { name: 'Analytics', href: '/app/admin/analytics', icon: ChartBarIcon },
  { name: 'Activity', href: '/app/admin/activity', icon: ClockIcon },
  { name: 'System', href: '/app/admin/system', icon: ServerIcon },
  { name: 'Errors', href: '/app/admin/errors', icon: ExclamationTriangleIcon },
]

// Site-specific navigation when inside a site
const getSiteNavigation = (siteId: string): NavItem[] => [
  { name: 'Dashboard', href: `/app/sites/${siteId}`, icon: HomeIcon },
  { name: 'Posts', href: `/app/sites/${siteId}/posts`, icon: DocumentTextIcon },
  { name: 'Pages', href: `/app/sites/${siteId}/pages`, icon: DocumentIcon },
  { name: 'Categories', href: `/app/sites/${siteId}/categories`, icon: FolderIcon },
  { name: 'Media', href: `/app/sites/${siteId}/media`, icon: PhotoIcon },
  { name: 'Menus', href: `/app/sites/${siteId}/menus`, icon: Bars3Icon },
  { name: 'Branding', href: `/app/sites/${siteId}/branding`, icon: PaintBrushIcon },
  { name: 'Settings', href: `/app/sites/${siteId}/settings`, icon: Cog6ToothIcon },
]

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const location = useLocation()
  const params = useParams()
  const { user } = useAuth()
  const [settingsExpanded, setSettingsExpanded] = useState(false)
  const [adminExpanded, setAdminExpanded] = useState(false)
  
  // Check if we're in a site context
  const siteId = params.siteId
  const isInSiteContext = Boolean(siteId) && location.pathname.includes('/app/sites/')
  
  // Auto-expand sections based on current path
  useEffect(() => {
    if (settingsNavigation.some(item => location.pathname === item.href)) {
      setSettingsExpanded(true)
    }
    if (adminNavigation.some(item => location.pathname.startsWith(item.href))) {
      setAdminExpanded(true)
    }
  }, [location.pathname])
  
  const isActive = (href: string) => {
    if (href === '/app') return location.pathname === href
    return location.pathname.startsWith(href)
  }
  
  const NavLink = ({ item }: { item: NavItem }) => {
    const active = isActive(item.href)
    const Icon = item.icon
    
    return (
      <Link
        to={item.href}
        onClick={() => window.innerWidth < 1024 && onClose()}
        className={`
          group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium
          transition-all duration-200
          ${active
            ? 'bg-primary-50 text-primary-700 shadow-sm'
            : 'text-secondary-600 hover:bg-secondary-50 hover:text-secondary-900'
          }
        `}
      >
        <Icon className={`w-5 h-5 flex-shrink-0 transition-colors ${
          active ? 'text-primary-600' : 'text-secondary-400 group-hover:text-secondary-600'
        }`} />
        <span className="flex-1">{item.name}</span>
        {item.badge !== undefined && item.badge > 0 && (
          <CountBadge count={item.badge} variant={active ? 'primary' : 'primary'} />
        )}
      </Link>
    )
  }
  
  const CollapsibleSection = ({ 
    title, 
    items, 
    expanded, 
    onToggle,
    variant = 'default'
  }: { 
    title: string
    items: NavItem[]
    expanded: boolean
    onToggle: () => void
    variant?: 'default' | 'admin'
  }) => (
    <div className="mt-6">
      <button
        onClick={onToggle}
        className={`
          w-full flex items-center justify-between px-3 py-2 text-xs font-semibold uppercase tracking-wider
          ${variant === 'admin' ? 'text-error-600' : 'text-secondary-400'}
          hover:text-secondary-600 transition-colors
        `}
      >
        {title}
        <ChevronDownIcon className={`w-4 h-4 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`} />
      </button>
      
      <div className={`
        mt-1 space-y-1 overflow-hidden transition-all duration-200
        ${expanded ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'}
      `}>
        {items.map((item) => (
          <NavLink key={item.name} item={item} />
        ))}
      </div>
    </div>
  )

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-secondary-900/60 backdrop-blur-sm z-40 lg:hidden animate-fade-in"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 z-50 h-full w-72 
          bg-white border-r border-secondary-100 
          transform transition-transform duration-300 ease-out
          flex flex-col
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-5 border-b border-secondary-100 flex-shrink-0">
          <Link to="/app" className="flex items-center gap-3 group">
            <div className="w-9 h-9 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-glow transition-shadow">
              <SparklesIcon className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-secondary-900">MetaView</span>
          </Link>
          <button
            onClick={onClose}
            className="lg:hidden p-2 -mr-2 text-secondary-400 hover:text-secondary-600 hover:bg-secondary-100 rounded-lg transition-colors"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 overflow-y-auto scrollbar-hide">
          {/* Site Context Navigation */}
          {isInSiteContext ? (
            <>
              {/* Back to Sites Link */}
              <Link
                to="/app/sites"
                className="flex items-center gap-2 px-3 py-2 mb-4 text-sm font-medium text-secondary-500 hover:text-secondary-700 transition-colors"
              >
                <ArrowLeftIcon className="w-4 h-4" />
                Back to Sites
              </Link>
              
              <div className="space-y-1">
                {getSiteNavigation(siteId!).map((item) => (
                  <NavLink key={item.name} item={item} />
                ))}
              </div>
            </>
          ) : (
            <>
              {/* Main Navigation */}
              <div className="space-y-1">
                {mainNavigation.map((item) => (
                  <NavLink key={item.name} item={item} />
                ))}
              </div>

              {/* Settings Section */}
              <CollapsibleSection
                title="Settings"
                items={settingsNavigation}
                expanded={settingsExpanded}
                onToggle={() => setSettingsExpanded(!settingsExpanded)}
              />

              {/* Admin Section */}
              {user?.is_admin && (
                <CollapsibleSection
                  title="Admin"
                  items={adminNavigation}
                  expanded={adminExpanded}
                  onToggle={() => setAdminExpanded(!adminExpanded)}
                  variant="admin"
                />
              )}
            </>
          )}
        </nav>

        {/* User Section */}
        <div className="p-4 border-t border-secondary-100 flex-shrink-0">
          <div className="flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-secondary-50 transition-colors cursor-pointer">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary-400 to-accent-400 flex items-center justify-center text-white font-semibold text-sm">
              {user?.email?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-secondary-900 truncate">
                {user?.email || 'User'}
              </p>
              <p className="text-xs text-secondary-500">
                {user?.is_admin ? 'Administrator' : 'Member'}
              </p>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}
