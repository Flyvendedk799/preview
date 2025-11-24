import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Bars3Icon, ArrowRightOnRectangleIcon, ChevronDownIcon, BuildingOfficeIcon, PlusIcon } from '@heroicons/react/24/outline'
import { useAuth } from '../../hooks/useAuth'
import { useOrganization } from '../../hooks/useOrganization'
import Button from '../ui/Button'

interface HeaderProps {
  onMenuClick: () => void
}

const pageTitles: Record<string, string> = {
  '/app': 'Dashboard',
  '/app/domains': 'Domains',
  '/app/brand': 'Brand Settings',
  '/app/previews': 'Preview Gallery',
  '/app/analytics': 'Analytics',
  '/app/billing': 'Billing',
}

export default function Header({ onMenuClick }: HeaderProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const { currentOrg, organizations, setCurrentOrg, loading: orgLoading } = useOrganization()
  const [showMenu, setShowMenu] = useState(false)
  const [showOrgMenu, setShowOrgMenu] = useState(false)
  const pageTitle = pageTitles[location.pathname] || 'Dashboard'

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-gray-200">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-4">
            <button
              onClick={onMenuClick}
              className="lg:hidden text-gray-500 hover:text-gray-700 p-2 rounded-lg hover:bg-gray-50"
            >
              <Bars3Icon className="w-6 h-6" />
            </button>
            <h1 className="text-2xl font-semibold text-secondary">{pageTitle}</h1>
          </div>
          <div className="flex items-center space-x-4">
            {/* Organization Switcher */}
            {currentOrg && !orgLoading && (
              <div className="relative hidden sm:block">
                <button
                  onClick={() => setShowOrgMenu(!showOrgMenu)}
                  className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors border border-gray-200"
                >
                  <BuildingOfficeIcon className="w-5 h-5 text-gray-600" />
                  <span className="text-sm font-medium text-gray-700 max-w-[150px] truncate">
                    {currentOrg.name}
                  </span>
                  <ChevronDownIcon className="w-4 h-4 text-gray-500" />
                </button>
                {showOrgMenu && (
                  <>
                    <div
                      className="fixed inset-0 z-40"
                      onClick={() => setShowOrgMenu(false)}
                    />
                    <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
                      <div className="px-4 py-2 border-b border-gray-200">
                        <p className="text-xs font-semibold text-gray-500 uppercase">Organizations</p>
                      </div>
                      <div className="max-h-64 overflow-y-auto">
                        {organizations.map((org) => (
                          <button
                            key={org.id}
                            onClick={() => {
                              setCurrentOrg(org)
                              setShowOrgMenu(false)
                              // Reload page to refresh org context
                              window.location.reload()
                            }}
                            className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 flex items-center justify-between ${
                              currentOrg.id === org.id ? 'bg-primary/5 text-primary font-medium' : 'text-gray-700'
                            }`}
                          >
                            <span>{org.name}</span>
                            {currentOrg.id === org.id && (
                              <span className="text-xs text-primary">Current</span>
                            )}
                          </button>
                        ))}
                      </div>
                      <div className="border-t border-gray-200 px-4 py-2">
                        <button
                          onClick={() => {
                            setShowOrgMenu(false)
                            navigate('/app/organizations')
                          }}
                          className="w-full text-left px-3 py-2 text-sm text-primary hover:bg-primary/5 rounded-lg flex items-center space-x-2"
                        >
                          <PlusIcon className="w-4 h-4" />
                          <span>Create Organization</span>
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}
            <div className="relative">
              <button
                onClick={() => setShowMenu(!showMenu)}
                className="hidden sm:flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                  <span className="text-primary font-medium text-sm">
                    {user?.email.charAt(0).toUpperCase()}
                  </span>
                </div>
                <span className="text-sm font-medium text-gray-700">{user?.email}</span>
              </button>
              {showMenu && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setShowMenu(false)}
                  />
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
                    <div className="px-4 py-2 border-b border-gray-200">
                      <p className="text-sm font-medium text-gray-900">{user?.email}</p>
                    </div>
                    <button
                      onClick={() => {
                        logout()
                        setShowMenu(false)
                      }}
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center space-x-2"
                    >
                      <ArrowRightOnRectangleIcon className="w-4 h-4" />
                      <span>Logout</span>
                    </button>
                  </div>
                </>
              )}
            </div>
            <Button
              variant="secondary"
              onClick={logout}
              className="sm:hidden"
            >
              <ArrowRightOnRectangleIcon className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  )
}

