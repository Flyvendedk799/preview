import { useState, useEffect } from 'react'
import { ArrowPathIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import { fetchAdminSystemOverview, fetchAdminWorkerHealth, type SystemOverview, type WorkerHealth } from '../../api/client'

export default function AdminSystem() {
  const [overview, setOverview] = useState<SystemOverview | null>(null)
  const [workerHealth, setWorkerHealth] = useState<WorkerHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [restarting, setRestarting] = useState(false)

  useEffect(() => {
    loadData()
    // Refresh every 10 seconds
    const interval = setInterval(loadData, 10000)
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [overviewData, healthData] = await Promise.all([
        fetchAdminSystemOverview(),
        fetchAdminWorkerHealth(),
      ])
      setOverview(overviewData)
      setWorkerHealth(healthData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load system data')
    } finally {
      setLoading(false)
    }
  }

  const handleRestartWorkers = async () => {
    if (!window.confirm('Are you sure you want to restart workers? This will interrupt any running jobs.')) {
      return
    }

    try {
      setRestarting(true)
      // Worker restart endpoint would be implemented here
      // For now, this is a placeholder - Railway handles worker restarts via service restart
      await new Promise((resolve) => setTimeout(resolve, 2000))
      alert('Worker restart initiated (service restart required)')
      await loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to restart workers')
    } finally {
      setRestarting(false)
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-secondary mb-2">Admin / System</h1>
        <p className="text-muted">Monitor system health and manage workers</p>
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
            <p className="text-gray-500">Loading system status...</p>
          </div>
        </Card>
      ) : (
        <>
          {/* System Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Redis Queue Length</p>
                  <p className="text-2xl font-bold text-secondary">
                    {overview?.redis_queue_length.toLocaleString() || '0'}
                  </p>
                </div>
                <div className={`w-3 h-3 rounded-full ${
                  (overview?.redis_queue_length || 0) > 100 ? 'bg-red-500' : 'bg-green-500'
                }`}></div>
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Jobs Running</p>
                  <p className="text-2xl font-bold text-secondary">
                    {overview?.jobs_running.toLocaleString() || '0'}
                  </p>
                </div>
                <div className={`w-3 h-3 rounded-full ${
                  (overview?.jobs_running || 0) > 0 ? 'bg-yellow-500' : 'bg-gray-300'
                }`}></div>
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Errors (24h)</p>
                  <p className="text-2xl font-bold text-secondary">
                    {overview?.errors_past_24h.toLocaleString() || '0'}
                  </p>
                </div>
                <ExclamationTriangleIcon className={`w-6 h-6 ${
                  (overview?.errors_past_24h || 0) > 0 ? 'text-red-500' : 'text-gray-300'
                }`} />
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Previews (24h)</p>
                  <p className="text-2xl font-bold text-secondary">
                    {overview?.previews_generated_24h.toLocaleString() || '0'}
                  </p>
                </div>
              </div>
            </Card>
          </div>

          {/* Worker Management */}
          <Card className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-secondary">Worker Management</h2>
              <Button
                onClick={handleRestartWorkers}
                disabled={restarting}
                variant="secondary"
              >
                {restarting ? (
                  <span className="flex items-center space-x-2">
                    <ArrowPathIcon className="w-5 h-5 animate-spin" />
                    <span>Restarting...</span>
                  </span>
                ) : (
                  <span className="flex items-center space-x-2">
                    <ArrowPathIcon className="w-5 h-5" />
                    <span>Restart Workers</span>
                  </span>
                )}
              </Button>
            </div>
            <p className="text-sm text-gray-600">
              Worker status monitoring and management. Restart workers if they become unresponsive.
            </p>
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">
                <strong>Note:</strong> Worker restart functionality is currently stubbed. Implement actual worker management endpoint.
              </p>
            </div>
          </Card>

          {/* Error Logs Placeholder */}
          <Card>
            <h2 className="text-xl font-semibold text-secondary mb-4">Recent Errors</h2>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">
                Error logs will be displayed here once error logging is fully implemented in webhooks and jobs.
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Latest {overview?.errors_past_24h || 0} errors in the past 24 hours.
              </p>
            </div>
          </Card>
        </>
      )}
    </div>
  )
}

