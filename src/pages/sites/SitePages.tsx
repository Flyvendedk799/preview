import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { PlusIcon } from '@heroicons/react/24/outline'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import { fetchSitePages, type SitePage } from '../../api/client'

export default function SitePages() {
  const { siteId } = useParams<{ siteId: string }>()
  const navigate = useNavigate()
  const [pages, setPages] = useState<SitePage[]>([])
  const [loading, setLoading] = useState(true)

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

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-secondary">Pages</h1>
        <Button onClick={() => navigate(`/app/sites/${siteId}/pages/new`)}>
          <PlusIcon className="w-5 h-5 mr-2" />
          New Page
        </Button>
      </div>

      <Card>
        {loading ? (
          <div className="text-center py-8">Loading...</div>
        ) : pages.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-600 mb-4">No pages yet</p>
            <Button onClick={() => navigate(`/app/sites/${siteId}/pages/new`)}>
              Create Your First Page
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            {pages.map((page) => (
              <div key={page.id} className="p-3 border-b">
                <h3 className="font-medium">{page.title}</h3>
                <p className="text-sm text-gray-500">{page.status}</p>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

