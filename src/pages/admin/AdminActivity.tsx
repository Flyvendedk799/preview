import { useState, useEffect, useCallback } from 'react'
import { ClipboardDocumentIcon, CheckIcon, FunnelIcon } from '@heroicons/react/24/outline'
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
  const [filterUserId, setFilterUserId] = useState<number | undefined>(undefined)
  const [filterAction, setFilterAction] = useState<string>('')
  const [filterUrl, setFilterUrl] = useState<string>('')
  const [copiedId, setCopiedId] = useState<number | null>(null)
  const limit = 50

  useEffect(() => { loadUsers() }, [])
  useEffect(() => { loadLogs() }, [page, filterUserId, filterAction, filterUrl])

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
      const data = await fetchAdminActivity(
        page * limit,
        limit,
        filterUserId,
        filterAction || undefined,
        filterUrl || undefined
      )
      setLogs(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load activity logs')
    } finally {
      setLoading(false)
    }
  }

  const copyLogLine = useCallback(async (log: AdminActivityLog) => {
    const user = users.find((u) => u.id === log.user_id)
    const line = JSON.stringify({
      id: log.id,
      action: log.action,
      user: user?.email || log.user_id || 'system',
      ip: log.ip_address,
      time: log.created_at,
      ...log.metadata,
    })
    await navigator.clipboard.writeText(line)
    setCopiedId(log.id)
    setTimeout(() => setCopiedId(null), 1500)
  }, [users])

  const copyAllVisible = useCallback(async () => {
    const lines = logs.map((log) => {
      const user = users.find((u) => u.id === log.user_id)
      return JSON.stringify({
        id: log.id,
        action: log.action,
        user: user?.email || log.user_id || 'system',
        ip: log.ip_address,
        time: log.created_at,
        ...log.metadata,
      })
    })
    await navigator.clipboard.writeText(lines.join('\n'))
    setCopiedId(-1)
    setTimeout(() => setCopiedId(null), 1500)
  }, [logs, users])

  const actionTypes = Array.from(new Set(logs.map((log) => log.action)))

  /** Format metadata into a concise single-line summary for the table */
  const summarizeMetadata = (log: AdminActivityLog): string => {
    const m = log.metadata
    if (!m) return ''

    const parts: string[] = []

    // URL is the most important field
    if (m.url) parts.push(m.url)

    // Outcome / status
    if (m.outcome) parts.push(`outcome=${m.outcome}`)
    if (m.status) parts.push(`status=${m.status}`)

    // Job ID
    if (m.job_id) parts.push(`job=${String(m.job_id).slice(0, 12)}`)

    // Preview result fields
    if (m.title) parts.push(`"${String(m.title).slice(0, 60)}"`)
    if (m.template_type) parts.push(`template=${m.template_type}`)
    if (m.processing_time_ms) parts.push(`${m.processing_time_ms}ms`)
    if (m.confidence !== undefined) parts.push(`conf=${Number(m.confidence).toFixed(2)}`)
    if (m.overall_quality) parts.push(`quality=${m.overall_quality}`)

    // Error
    if (m.error) parts.push(`err="${String(m.error).slice(0, 80)}"`)

    // Warnings
    if (m.warnings && Array.isArray(m.warnings) && m.warnings.length > 0) {
      parts.push(`warnings=[${m.warnings.join(', ')}]`)
    }

    // Image
    if (m.image_url) parts.push(`img=yes`)
    if (m.has_composited_image !== undefined) parts.push(`composited=${m.has_composited_image}`)

    // Generic fallback: show first few keys
    if (parts.length === 0) {
      const keys = Object.keys(m).slice(0, 4)
      for (const k of keys) {
        const v = m[k]
        const vs = typeof v === 'object' ? JSON.stringify(v) : String(v)
        parts.push(`${k}=${vs.slice(0, 40)}`)
      }
    }

    return parts.join(' | ')
  }

  const getActionBadgeColor = (action: string) => {
    if (action.includes('completed')) return 'bg-green-100 text-green-800'
    if (action.includes('failed')) return 'bg-red-100 text-red-800'
    if (action.includes('job_created')) return 'bg-blue-100 text-blue-800'
    if (action.includes('admin')) return 'bg-purple-100 text-purple-800'
    return 'bg-gray-100 text-gray-700'
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-secondary mb-1">Activity</h1>
          <p className="text-gray-500 text-sm">Each row is one event. Click the copy icon to get a single JSON line for debugging.</p>
        </div>
        <Button
          onClick={copyAllVisible}
          variant="secondary"
          className="text-sm flex items-center gap-1.5"
        >
          {copiedId === -1 ? <CheckIcon className="w-4 h-4 text-green-600" /> : <ClipboardDocumentIcon className="w-4 h-4" />}
          {copiedId === -1 ? 'Copied!' : 'Copy all visible'}
        </Button>
      </div>

      {error && (
        <Card className="mb-4 bg-red-50 border-red-200">
          <p className="text-red-800 text-sm">Error: {error}</p>
        </Card>
      )}

      {/* Filters */}
      <Card className="mb-4 p-3">
        <div className="flex items-center gap-2 text-sm">
          <FunnelIcon className="w-4 h-4 text-gray-400 shrink-0" />
          <select
            value={filterUserId || ''}
            onChange={(e) => { setFilterUserId(e.target.value ? parseInt(e.target.value) : undefined); setPage(0) }}
            className="px-2 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-1 focus:ring-primary outline-none"
          >
            <option value="">All Users</option>
            {users.map((user) => (
              <option key={user.id} value={user.id}>{user.email}</option>
            ))}
          </select>
          <select
            value={filterAction}
            onChange={(e) => { setFilterAction(e.target.value); setPage(0) }}
            className="px-2 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-1 focus:ring-primary outline-none"
          >
            <option value="">All Actions</option>
            {actionTypes.map((action) => (
              <option key={action} value={action}>{action}</option>
            ))}
          </select>
          <input
            type="text"
            value={filterUrl}
            onChange={(e) => setFilterUrl(e.target.value)}
            placeholder="Filter by URL..."
            className="flex-1 px-2 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-1 focus:ring-primary outline-none min-w-0"
          />
        </div>
      </Card>

      {loading ? (
        <Card>
          <div className="text-center py-12">
            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
            <p className="text-gray-500 text-sm">Loading...</p>
          </div>
        </Card>
      ) : logs.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <p className="text-gray-500 text-sm">No activity logs found.</p>
          </div>
        </Card>
      ) : (
        <>
          <div className="space-y-1">
            {logs.map((log) => {
              const user = users.find((u) => u.id === log.user_id)
              const isCopied = copiedId === log.id
              return (
                <div
                  key={log.id}
                  className="group flex items-start gap-2 px-3 py-2 bg-white border border-gray-100 rounded-md hover:border-gray-200 hover:bg-gray-50/50 transition-colors font-mono text-xs leading-relaxed"
                >
                  {/* Copy button */}
                  <button
                    onClick={() => copyLogLine(log)}
                    className="shrink-0 mt-0.5 p-0.5 rounded hover:bg-gray-200 transition-colors"
                    title="Copy as JSON line"
                  >
                    {isCopied
                      ? <CheckIcon className="w-3.5 h-3.5 text-green-600" />
                      : <ClipboardDocumentIcon className="w-3.5 h-3.5 text-gray-400 group-hover:text-gray-600" />
                    }
                  </button>

                  {/* Timestamp */}
                  <span className="shrink-0 text-gray-400 tabular-nums">
                    {new Date(log.created_at).toLocaleString('en-US', {
                      month: '2-digit', day: '2-digit',
                      hour: '2-digit', minute: '2-digit', second: '2-digit',
                      hour12: false,
                    })}
                  </span>

                  {/* Action badge */}
                  <span className={`shrink-0 px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide ${getActionBadgeColor(log.action)}`}>
                    {log.action}
                  </span>

                  {/* User */}
                  {(user || log.user_id) && (
                    <span className="shrink-0 text-gray-500">
                      {user ? user.email.split('@')[0] : `#${log.user_id}`}
                    </span>
                  )}

                  {/* Metadata summary - the key debugging info */}
                  <span className="text-gray-700 truncate min-w-0">
                    {summarizeMetadata(log)}
                  </span>
                </div>
              )
            })}
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between mt-4">
            <Button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              variant="secondary"
              className="text-sm"
            >
              Previous
            </Button>
            <span className="text-gray-500 text-sm">Page {page + 1}</span>
            <Button
              onClick={() => setPage(page + 1)}
              disabled={logs.length < limit}
              variant="secondary"
              className="text-sm"
            >
              Next
            </Button>
          </div>
        </>
      )}
    </div>
  )
}
