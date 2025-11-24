import { useState, useEffect } from 'react'
import { EyeIcon } from '@heroicons/react/24/outline'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import { fetchAdminActivity, fetchAdminUsers, type AdminActivityLog } from '../../api/client'
import type { AdminUserSummary } from '../../api/types'

export default function AdminActivity() {
  const [logs, setLogs] = useState<AdminActivityLog[]>([])
  const [users, setUsers] = useState<AdminUserSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(0)
  const [selectedLog, setSelectedLog] = useState<AdminActivityLog | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const [filterUserId, setFilterUserId] = useState<number | undefined>(undefined)
  const [filterAction, setFilterAction] = useState<string>('')
  const limit = 50

  useEffect(() => {
    loadUsers()
  }, [])

  useEffect(() => {
    loadLogs()
  }, [page, filterUserId, filterAction])

  const loadUsers = async () => {
    try {
      const data = await fetchAdminUsers()
      setUsers(data)
    } catch (err) {
      console.error('Failed to load users:', err)
    }
  }

  const loadLogs = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await fetchAdminActivity(page * limit, limit, filterUserId, filterAction || undefined)
      setLogs(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load activity logs')
    } finally {
      setLoading(false)
    }
  }

  const handleViewDetail = (log: AdminActivityLog) => {
    setSelectedLog(log)
    setIsDetailOpen(true)
  }

  const actionTypes = Array.from(new Set(logs.map((log) => log.action)))

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-secondary mb-2">Admin / Activity</h1>
        <p className="text-gray-600">View all system activity logs</p>
      </div>

      {error && (
        <Card className="mb-6 bg-red-50 border-red-200">
          <p className="text-red-800">Error: {error}</p>
        </Card>
      )}

      {/* Filters */}
      <Card className="mb-6 p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Filter by User</label>
            <select
              value={filterUserId || ''}
              onChange={(e) => setFilterUserId(e.target.value ? parseInt(e.target.value) : undefined)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
            >
              <option value="">All Users</option>
              {users.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.email}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Action</label>
            <select
              value={filterAction}
              onChange={(e) => setFilterAction(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
            >
              <option value="">All Actions</option>
              {actionTypes.map((action) => (
                <option key={action} value={action}>
                  {action}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {loading ? (
        <Card>
          <div className="text-center py-12">
            <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-500">Loading activity logs...</p>
          </div>
        </Card>
      ) : (
        <>
          {logs.length === 0 ? (
            <Card>
              <div className="text-center py-12">
                <p className="text-gray-500">No activity logs found.</p>
              </div>
            </Card>
          ) : (
            <Card className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Action</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">User</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Date</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">IP Address</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => {
                    const user = users.find((u) => u.id === log.user_id)
                    return (
                      <tr key={log.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3 px-4">
                          <span className="font-medium">{log.action}</span>
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600">
                          {user ? user.email : log.user_id ? `User #${log.user_id}` : 'System'}
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-500">
                          {new Date(log.created_at).toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-500">
                          {log.ip_address || '—'}
                        </td>
                        <td className="py-3 px-4">
                          <button
                            onClick={() => handleViewDetail(log)}
                            className="text-primary hover:text-primary/80 transition-colors p-1"
                            title="View details"
                          >
                            <EyeIcon className="w-5 h-5" />
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </Card>
          )}

          {/* Pagination */}
          <div className="flex items-center justify-between mt-6">
            <Button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              variant="secondary"
            >
              Previous
            </Button>
            <span className="text-gray-600">Page {page + 1}</span>
            <Button
              onClick={() => setPage(page + 1)}
              disabled={logs.length < limit}
              variant="secondary"
            >
              Next
            </Button>
          </div>
        </>
      )}

      {/* Detail Drawer */}
      {isDetailOpen && selectedLog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-secondary">Activity Log Details</h2>
              <button
                onClick={() => setIsDetailOpen(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-600">Action</p>
                <p className="font-semibold">{selectedLog.action}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">User ID</p>
                  <p className="font-semibold">{selectedLog.user_id || 'System'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Created At</p>
                  <p className="font-semibold">{new Date(selectedLog.created_at).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">IP Address</p>
                  <p className="font-semibold">{selectedLog.ip_address || '—'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Organization ID</p>
                  <p className="font-semibold">{selectedLog.organization_id || '—'}</p>
                </div>
              </div>
              {selectedLog.user_agent && (
                <div>
                  <p className="text-sm text-gray-600">User Agent</p>
                  <p className="font-semibold text-xs break-all">{selectedLog.user_agent}</p>
                </div>
              )}
              <div>
                <p className="text-sm text-gray-600 mb-2">Metadata</p>
                <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-xs">
                  {JSON.stringify(selectedLog.metadata, null, 2)}
                </pre>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}

