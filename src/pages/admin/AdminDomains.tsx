import { useState, useEffect } from 'react'
import { TrashIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import { fetchAdminDomains, deleteAdminDomain, type AdminDomain } from '../../api/client'

export default function AdminDomains() {
  const [domains, setDomains] = useState<AdminDomain[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDomains()
  }, [])

  const loadDomains = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await fetchAdminDomains()
      setDomains(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load domains')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (domainId: number, domainName: string) => {
    if (!window.confirm(`Are you sure you want to delete domain "${domainName}"? This action cannot be undone.`)) {
      return
    }

    try {
      await deleteAdminDomain(domainId)
      await loadDomains()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete domain')
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-secondary mb-2">Admin / Domains</h1>
        <p className="text-muted">View and manage all domains across the system</p>
      </div>

      {error && (
        <Card className="mb-6 bg-red-50 border-red-200">
          <p className="text-red-800">Error: {error}</p>
        </Card>
      )}

      {loading ? (
        <Card>
          <div className="text-center py-12">
            <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-500">Loading domains...</p>
          </div>
        </Card>
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Domain</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">User</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Environment</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Status</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Verified</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Clicks</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Created</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody>
              {domains.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-8 text-gray-500">
                    No domains found
                  </td>
                </tr>
              ) : (
                domains.map((domain) => (
                  <tr key={domain.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 font-medium">{domain.name}</td>
                    <td className="py-3 px-4 text-sm text-gray-600">{domain.user_email}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-full capitalize">
                        {domain.environment}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 text-xs rounded-full capitalize ${
                        domain.status === 'active'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}>
                        {domain.status}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      {domain.verified_at ? (
                        <div className="flex items-center space-x-1">
                          <CheckCircleIcon className="w-4 h-4 text-green-500" />
                          <span className="text-xs text-gray-600">
                            {new Date(domain.verified_at).toLocaleDateString()}
                          </span>
                        </div>
                      ) : (
                        <div className="flex items-center space-x-1">
                          <XCircleIcon className="w-4 h-4 text-gray-400" />
                          <span className="text-xs text-gray-500">Not verified</span>
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4">{domain.monthly_clicks.toLocaleString()}</td>
                    <td className="py-3 px-4 text-sm text-gray-500">
                      {new Date(domain.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => handleDelete(domain.id, domain.name)}
                        className="text-red-600 hover:text-red-800 transition-colors p-1"
                        title="Delete domain"
                      >
                        <TrashIcon className="w-5 h-5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  )
}

