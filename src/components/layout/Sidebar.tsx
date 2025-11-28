import { Link, useLocation } from 'react-router-dom'
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
} from '@heroicons/react/24/outline'
import { useAuth } from '../../hooks/useAuth'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

const navigation = [
  { name: 'Dashboard', href: '/app', icon: HomeIcon },
  { name: 'Domains', href: '/app/domains', icon: GlobeAltIcon },
  { name: 'Brand Settings', href: '/app/brand', icon: PaintBrushIcon },
  { name: 'Preview Gallery', href: '/app/previews', icon: PhotoIcon },
  { name: 'Analytics', href: '/app/analytics', icon: ChartBarIcon },
  { name: 'Billing', href: '/app/billing', icon: CreditCardIcon },
  { name: 'Activity', href: '/app/activity', icon: ClockIcon },
  { name: 'Organizations', href: '/app/organizations', icon: BuildingOfficeIcon },
  { name: 'Account', href: '/app/account', icon: UserCircleIcon },
]

const adminNavigation = [
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

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const location = useLocation()
  const { user } = useAuth()

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-gray-900/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-50 h-full w-64 bg-white border-r border-gray-200 transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">P</span>
              </div>
              <span className="text-xl font-semibold text-secondary">MetaView</span>
            </div>
            <button
              onClick={onClose}
              className="lg:hidden text-gray-500 hover:text-gray-700"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => {
                    if (window.innerWidth < 1024) {
                      onClose()
                    }
                  }}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                    isActive
                      ? 'bg-primary/10 text-primary font-medium'
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <item.icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </Link>
              )
            })}

            {/* Admin Section */}
            {user?.is_admin && (
              <>
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <p className="px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                    Admin
                  </p>
                  {adminNavigation.map((item) => {
                    const isActive = location.pathname === item.href
                    return (
                      <Link
                        key={item.name}
                        to={item.href}
                        onClick={() => {
                          if (window.innerWidth < 1024) {
                            onClose()
                          }
                        }}
                        className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                          isActive
                            ? 'bg-red-50 text-red-700 font-medium'
                            : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                        }`}
                      >
                        <item.icon className="w-5 h-5" />
                        <span>{item.name}</span>
                      </Link>
                    )
                  })}
                </div>
              </>
            )}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-gray-200">
            <div className="px-4 py-2 text-sm text-gray-500">
              © 2024 MetaView
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}

