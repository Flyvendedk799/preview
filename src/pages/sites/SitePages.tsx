import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  PlusIcon,
  PencilSquareIcon,
  TrashIcon,
  HomeIcon,
} from '@heroicons/react/24/outline'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import { fetchSitePages, deleteSitePage, type SitePage } from '../../api/client'

export default function SitePages() {
  const { siteId } = useParams<{ siteId: string }>()
  const navigate = useNavigate()
  const [pages, setPages] = useState<SitePage[]>([])
  const [loading, setLoading] = useState(true)
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null)

  useEffect(() => {
    if (siteId) loadPages()
  }, [siteId])

  async function loadPages() {
    if (!siteId) return
    try {
      setLoading(true)
      const data = await fetchSitePages(parseInt(siteId))
      setPages(data)
    } catch (err) {
      console.error('Failed to load pages:', err)
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(pageId: number) {
    if (!siteId) return
    try {
      await deleteSitePage(parseInt(siteId), pageId)
      setPages(pages.filter(p => p.id !== pageId))
      setDeleteConfirm(null)
    } catch (err) {
      console.error('Failed to delete page:', err)
    }
  }

  function getStatusBadge(status: string) {
    const styles: Record<string, string> = {
      published: 'bg-green-100 text-green-800',
      draft: 'bg-gray-100 text-gray-800',
    }
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[status] || styles.draft}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-secondary">Pages</h1>
          <p className="text-muted">Static pages for your site (About, Contact, etc.)</p>
        </div>
        <Button onClick={() => navigate(`/app/sites/${siteId}/pages/new`)}>
          <PlusIcon className="w-5 h-5 mr-2" />
          New Page
        </Button>
      </div>

      <Card>
        {loading ? (
          <div className="flex items-center justify-center h-48">
            <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : pages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-gray-500">
            <p className="font-medium mb-2">No pages yet</p>
            <p className="text-sm mb-4">Create static pages like About, Contact, Terms of Service</p>
            <Button onClick={() => navigate(`/app/sites/${siteId}/pages/new`)}>
              Create Page
            </Button>
          </div>
        ) : (
          <div className="divide-y">
            {pages.map((page) => (
              <div
                key={page.id}
                className="flex items-center justify-between py-4 px-2 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  {page.is_homepage && (
                    <HomeIcon className="w-5 h-5 text-primary" title="Homepage" />
                  )}
                  <div>
                    <h3 className="font-medium text-gray-900">{page.title}</h3>
                    <p className="text-sm text-gray-500">/page/{page.slug}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  {getStatusBadge(page.status)}
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => navigate(`/app/sites/${siteId}/pages/${page.id}`)}
                      className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                      title="Edit"
                    >
                      <PencilSquareIcon className="w-4 h-4 text-gray-600" />
                    </button>
                    <button
                      onClick={() => setDeleteConfirm(page.id)}
                      className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete"
                    >
                      <TrashIcon className="w-4 h-4 text-red-600" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-xl p-6 max-w-sm w-full shadow-xl">
            <h3 className="text-lg font-bold text-gray-900 mb-2">Delete Page?</h3>
            <p className="text-gray-500 text-sm mb-6">
              This action cannot be undone. The page will be permanently deleted.
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
