import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  PlusIcon,
  GlobeAltIcon,
  PencilSquareIcon,
  TrashIcon,
  EyeIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import EmptyState from '../../components/ui/EmptyState'
import { SkeletonList } from '../../components/ui/Skeleton'
import { fetchSites, deleteSite, publishSite, unpublishSite, type PublishedSite } from '../../api/client'

export default function SitesList() {
  const navigate = useNavigate()
  const [sites, setSites] = useState<PublishedSite[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null)

  useEffect(() => {
    loadSites()
  }, [])

  async function loadSites() {
    try {
      setLoading(true)
      setError('')
      const data = await fetchSites()
      setSites(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sites')
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(siteId: number) {
    try {
      await deleteSite(siteId)
      setSites(sites.filter(s => s.id !== siteId))
      setDeleteConfirm(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete site')
    }
  }

  async function handlePublish(siteId: number) {
    try {
      const updated = await publishSite(siteId)
      setSites(sites.map(s => s.id === siteId ? updated : s))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to publish site')
    }
  }

  async function handleUnpublish(siteId: number) {
    try {
      const updated = await unpublishSite(siteId)
      setSites(sites.map(s => s.id === siteId ? updated : s))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to unpublish site')
    }
  }

  function getStatusBadge(status: string) {
    if (status === 'published') {
      return (
        <span className="inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
          <CheckCircleIcon className="w-3 h-3 mr-1.5" />
          Published
        </span>
      )
    } else if (status === 'draft') {
      return (
        <span className="inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">
          Draft
        </span>
      )
    } else {
      return (
        <span className="inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">
          <XCircleIcon className="w-3 h-3 mr-1.5" />
          Archived
        </span>
      )
    }
  }

  return (
    <div>
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-secondary mb-2">My Sites</h1>
            <p className="text-muted">Manage your hosted blog and news sites</p>
          </div>
          <Button onClick={() => navigate('/app/sites/new')}>
            <div className="flex items-center space-x-2">
              <PlusIcon className="w-5 h-5" />
              <span>Create Site</span>
            </div>
          </Button>
        </div>
      </div>

      {error && (
        <Card className="mb-6 bg-red-50 border-red-200">
          <div className="flex items-start space-x-3">
            <XCircleIcon className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
            <p className="text-red-800">{error}</p>
          </div>
        </Card>
      )}

      {loading ? (
        <Card>
          <SkeletonList count={3} />
        </Card>
      ) : sites.length === 0 ? (
        <Card>
          <EmptyState
            icon={<GlobeAltIcon className="w-12 h-12" />}
            title="No sites yet"
            description="Create your first white-label blog or news site. Connect your domain and choose a template to get started."
            action={{
              label: 'Create Your First Site',
              onClick: () => navigate('/app/sites/new'),
            }}
          />
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sites.map((site) => (
            <Card key={site.id} className="hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-secondary mb-1">{site.name}</h3>
                  <p className="text-sm text-muted mb-2">{site.domain?.name || 'No domain'}</p>
                  {getStatusBadge(site.status)}
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => navigate(`/app/sites/${site.id}`)}
                    className="p-2 text-gray-400 hover:text-primary hover:bg-primary/10 rounded-lg transition-colors"
                    title="View Dashboard"
                  >
                    <EyeIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => navigate(`/app/sites/${site.id}/posts`)}
                    className="p-2 text-gray-400 hover:text-primary hover:bg-primary/10 rounded-lg transition-colors"
                    title="Manage Posts"
                  >
                    <PencilSquareIcon className="w-4 h-4" />
                  </button>
                </div>
                <div className="flex items-center space-x-2">
                  {site.status === 'published' ? (
                    <button
                      onClick={() => handleUnpublish(site.id)}
                      className="px-3 py-1.5 text-xs font-medium text-yellow-700 bg-yellow-50 rounded-lg hover:bg-yellow-100 transition-colors"
                    >
                      Unpublish
                    </button>
                  ) : (
                    <button
                      onClick={() => handlePublish(site.id)}
                      className="px-3 py-1.5 text-xs font-medium text-green-700 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
                    >
                      Publish
                    </button>
                  )}
                  <button
                    onClick={() => setDeleteConfirm(site.id)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="Delete"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-xl p-6 max-w-sm w-full shadow-xl">
            <h3 className="text-lg font-bold text-gray-900 mb-2">Delete Site?</h3>
            <p className="text-gray-500 text-sm mb-6">
              This action cannot be undone. The site and all its content will be permanently deleted.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="flex-1 px-4 py-2 border border-gray-200 rounded-lg font-medium hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteConfirm)}
                className="flex-1 px-4 py-2 bg-red-500 text-white rounded-lg font-medium hover:bg-red-600 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

