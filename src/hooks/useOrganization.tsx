import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { fetchOrganizations, getOrganization, type Organization } from '../api/client'
import { useAuth } from './useAuth'

interface OrganizationContextType {
  currentOrg: Organization | null
  organizations: Organization[]
  loading: boolean
  error: string | null
  setCurrentOrg: (org: Organization | null) => void
  refreshOrganizations: () => Promise<void>
}

const OrganizationContext = createContext<OrganizationContextType | undefined>(undefined)

export function OrganizationProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [currentOrg, setCurrentOrgState] = useState<Organization | null>(null)
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadOrganizations = async () => {
    if (!user) {
      setOrganizations([])
      setCurrentOrgState(null)
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)
      const orgs = await fetchOrganizations()
      setOrganizations(orgs)

      // Get selected org from localStorage or use first org
      const savedOrgId = localStorage.getItem('selected_org_id')
      if (savedOrgId) {
        const savedOrg = orgs.find((o) => o.id === parseInt(savedOrgId))
        if (savedOrg) {
          setCurrentOrgState(savedOrg)
        } else if (orgs.length > 0) {
          setCurrentOrgState(orgs[0])
          localStorage.setItem('selected_org_id', orgs[0].id.toString())
        }
      } else if (orgs.length > 0) {
        setCurrentOrgState(orgs[0])
        localStorage.setItem('selected_org_id', orgs[0].id.toString())
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load organizations')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadOrganizations()
  }, [user])

  const setCurrentOrg = (org: Organization | null) => {
    setCurrentOrgState(org)
    if (org) {
      localStorage.setItem('selected_org_id', org.id.toString())
    } else {
      localStorage.removeItem('selected_org_id')
    }
  }

  const refreshOrganizations = async () => {
    await loadOrganizations()
  }

  return (
    <OrganizationContext.Provider
      value={{
        currentOrg,
        organizations,
        loading,
        error,
        setCurrentOrg,
        refreshOrganizations,
      }}
    >
      {children}
    </OrganizationContext.Provider>
  )
}

export function useOrganization() {
  const context = useContext(OrganizationContext)
  if (context === undefined) {
    throw new Error('useOrganization must be used within an OrganizationProvider')
  }
  return context
}

