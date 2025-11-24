import { useState, useEffect } from 'react'
import {
  UsersIcon,
  GlobeAltIcon,
  PhotoIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline'
import Card from '../../components/ui/Card'
import { fetchAdminSystemOverview, type SystemOverview } from '../../api/client'

export default function AdminDashboard() {
  const [overview, setOverview] = useState<SystemOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadOverview()
    // Refresh every 30 seconds
    const interval = setInterval(loadOverview, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadOverview = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await fetchAdminSystemOverview()
      setOverview(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load system overview')
    } finally {
      setLoading(false)
    }
  }

  const stats = [
    {
      name: 'Total Users',
      value: overview?.total_users.toLocaleString() || '0',
      icon: UsersIcon,
      color: 'text-blue-500',
    },
    {
      name: 'Active Subscribers',
      value: overview?.active_subscribers.toLocaleString() || '0',
      icon: UsersIcon,
      color: 'text-green-500',
    },
    {
      name: 'Total Domains',
      value: overview?.total_domains.toLocaleString() || '0',
      icon: GlobeAltIcon,
      color: 'text-purple-500',
    },
    {
      name: 'Verified Domains',
      value: overview?.verified_domains.toLocaleString() || '0',
      icon: GlobeAltIcon,
      color: 'text-accent',
    },
    {
      name: 'Previews (24h)',
      value: overview?.previews_generated_24h.toLocaleString() || '0',
      icon: PhotoIcon,
      color: 'text-primary',
    },
    {
      name: 'Queue Length',
      value: overview?.redis_queue_length.toLocaleString() || '0',
      icon: ChartBarIcon,
      color: 'text-yellow-500',
    },
    {
      name: 'Errors (24h)',
      value: overview?.errors_past_24h.toLocaleString() || '0',
      icon: ExclamationTriangleIcon,
      color: 'text-red-500',
    },
    {
      name: 'Jobs Running',
      value: overview?.jobs_running.toLocaleString() || '0',
      icon: ChartBarIcon,
      color: 'text-indigo-500',
    },
  ]

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-secondary mb-2">Admin / Dashboard</h1>
        <p className="text-gray-600">System-wide overview and metrics</p>
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
            <p className="text-gray-500">Loading system overview...</p>
          </div>
        </Card>
      ) : (
        <>
          {/* System Overview Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            {stats.map((stat) => {
              const Icon = stat.icon
              return (
                <Card key={stat.name} className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">{stat.name}</p>
                      <p className="text-2xl font-bold text-secondary">{stat.value}</p>
                    </div>
                    <Icon className={`w-8 h-8 ${stat.color}`} />
                  </div>
                </Card>
              )
            })}
          </div>

          {/* Charts Placeholder */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-6">
              <h2 className="text-xl font-semibold text-secondary mb-4">Daily Previews Generated</h2>
              <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
                <p className="text-gray-500">Chart placeholder - integrate charting library</p>
              </div>
            </Card>

            <Card className="p-6">
              <h2 className="text-xl font-semibold text-secondary mb-4">New Signups</h2>
              <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
                <p className="text-gray-500">Chart placeholder - integrate charting library</p>
              </div>
            </Card>

            <Card className="p-6">
              <h2 className="text-xl font-semibold text-secondary mb-4">Queue Activity</h2>
              <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
                <p className="text-gray-500">Chart placeholder - integrate charting library</p>
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  )
}

