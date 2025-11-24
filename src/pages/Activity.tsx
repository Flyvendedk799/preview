import { useState, useEffect } from 'react'
import {
  UserIcon,
  GlobeAltIcon,
  PhotoIcon,
  CreditCardIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ClockIcon as ActivityIcon,
} from '@heroicons/react/24/outline'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import EmptyState from '../components/ui/EmptyState'
import { SkeletonList } from '../components/ui/Skeleton'
import { fetchUserActivity, type ActivityLog } from '../api/client'

const ACTION_ICONS: Record<string, any> = {
  'user.login': UserIcon,
  'user.signup': UserIcon,
  'domain.created': GlobeAltIcon,
  'domain.deleted': GlobeAltIcon,
  'domain.verification.started': ClockIcon,
  'domain.verification.succeeded': CheckCircleIcon,
  'domain.verification.failed': XCircleIcon,
  'preview.created': PhotoIcon,
  'preview.updated': PhotoIcon,
  'preview.edited': PhotoIcon,
  'preview.deleted': PhotoIcon,
  'preview.ai_job.queued': ClockIcon,
  'preview.ai_job.completed': CheckCircleIcon,
  'preview.ai_job.failed': ExclamationTriangleIcon,
  'billing.subscription.created': CreditCardIcon,
  'billing.subscription.updated': CreditCardIcon,
  'billing.subscription.canceled': CreditCardIcon,
}

const ACTION_COLORS: Record<string, string> = {
  'user.login': 'text-blue-500',
  'user.signup': 'text-green-500',
  'domain.created': 'text-purple-500',
  'domain.deleted': 'text-red-500',
  'domain.verification.started': 'text-yellow-500',
  'domain.verification.succeeded': 'text-green-500',
  'domain.verification.failed': 'text-red-500',
  'preview.created': 'text-primary',
  'preview.updated': 'text-primary',
  'preview.edited': 'text-primary',
  'preview.deleted': 'text-red-500',
  'preview.ai_job.queued': 'text-yellow-500',
  'preview.ai_job.completed': 'text-green-500',
  'preview.ai_job.failed': 'text-red-500',
  'billing.subscription.created': 'text-green-500',
  'billing.subscription.updated': 'text-blue-500',
  'billing.subscription.canceled': 'text-red-500',
}

function formatAction(action: string): string {
  return action
    .split('.')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function getActionDescription(action: string, metadata: Record<string, any>): string {
  if (action === 'user.login' || action === 'user.signup') {
    return `User ${action === 'user.login' ? 'logged in' : 'signed up'}`
  }
  if (action === 'domain.created') {
    return `Domain "${metadata.domain_name || 'Unknown'}" created`
  }
  if (action === 'domain.deleted') {
    return `Domain "${metadata.domain_name || 'Unknown'}" deleted`
  }
  if (action.startsWith('domain.verification')) {
    const domain = metadata.domain_name || 'Unknown'
    if (action.includes('succeeded')) return `Domain "${domain}" verified successfully`
    if (action.includes('failed')) return `Domain "${domain}" verification failed`
    return `Domain "${domain}" verification started (${metadata.method || 'unknown method'})`
  }
  if (action === 'preview.created') {
    return `Preview created for "${metadata.url || 'Unknown'}"`
  }
  if (action === 'preview.updated' || action === 'preview.edited') {
    return `Preview updated for "${metadata.url || 'Unknown'}"`
  }
  if (action === 'preview.deleted') {
    return `Preview "${metadata.title || metadata.url || 'Unknown'}" deleted`
  }
  if (action === 'preview.ai_job.queued') {
    return `AI preview generation queued for "${metadata.url || 'Unknown'}"`
  }
  if (action === 'preview.ai_job.completed') {
    return `AI preview generation completed for "${metadata.url || 'Unknown'}"`
  }
  if (action === 'preview.ai_job.failed') {
    return `AI preview generation failed for "${metadata.url || 'Unknown'}"`
  }
  if (action.startsWith('billing.subscription')) {
    const plan = metadata.plan ? ` (${metadata.plan})` : ''
    if (action.includes('created')) return `Subscription created${plan}`
    if (action.includes('updated')) return `Subscription updated${plan}`
    if (action.includes('canceled')) return `Subscription canceled`
  }
  return formatAction(action)
}

export default function Activity() {
  const [logs, setLogs] = useState<ActivityLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(0)
  const limit = 50

  useEffect(() => {
    loadLogs()
  }, [page])

  const loadLogs = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await fetchUserActivity(page * limit, limit)
      setLogs(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load activity logs')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-secondary mb-2">Activity Log</h1>
        <p className="text-gray-600">View your account activity and events</p>
      </div>

      {error && (
        <Card className="mb-6 bg-red-50 border-red-200">
          <p className="text-red-800">Error: {error}</p>
        </Card>
      )}

      {loading ? (
        <Card>
          <SkeletonList count={5} />
        </Card>
      ) : logs.length === 0 ? (
        <Card>
          <EmptyState
            icon={<ActivityIcon className="w-8 h-8" />}
            title="No activity yet"
            description="Your account activity and events will appear here as you use the platform. Start by adding a domain or generating your first preview."
            action={{
              label: 'Go to Dashboard',
              onClick: () => window.location.href = '/app',
            }}
          />
        </Card>
      ) : (
        <>
          <div className="space-y-4">
              {logs.map((log) => {
                const Icon = ACTION_ICONS[log.action] || ClockIcon
                const color = ACTION_COLORS[log.action] || 'text-gray-500'
                return (
                  <Card key={log.id} className="p-4">
                    <div className="flex items-start space-x-4">
                      <div className={`flex-shrink-0 ${color}`}>
                        <Icon className="w-6 h-6" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <h3 className="font-semibold text-gray-900">{formatAction(log.action)}</h3>
                          <span className="text-sm text-gray-500">
                            {new Date(log.created_at).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">{getActionDescription(log.action, log.metadata)}</p>
                        {Object.keys(log.metadata).length > 0 && (
                          <details className="mt-2">
                            <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                              View metadata
                            </summary>
                            <pre className="mt-2 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                              {JSON.stringify(log.metadata, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    </div>
                  </Card>
                )
              })}
            </div>

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
    </div>
  )
}

