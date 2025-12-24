import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import { fetchSitePage, createSitePage, updateSitePage, type SitePage, type SitePageCreate, type SitePageUpdate } from '../../api/client'

export default function SitePageEditor() {
  const { siteId, pageId } = useParams<{ siteId: string; pageId?: string }>()
  const navigate = useNavigate()
  const [page, setPage] = useState<Partial<SitePage>>({ title: '', content: '', status: 'draft' })
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (pageId && siteId) {
      loadPage()
    }
  }, [pageId, siteId])

  async function loadPage() {
    if (!pageId || !siteId) return
    try {
      setLoading(true)
      const data = await fetchSitePage(parseInt(siteId), parseInt(pageId))
      setPage(data)
    } catch (err) {
      console.error('Failed to load page:', err)
    } finally {
      setLoading(false)
    }
  }

  async function handleSave() {
    if (!siteId) return
    try {
      setSaving(true)
      if (pageId) {
        await updateSitePage(parseInt(siteId), parseInt(pageId), page as SitePageUpdate)
      } else {
        await createSitePage(parseInt(siteId), page as SitePageCreate)
      }
      navigate(`/app/sites/${siteId}/pages`)
    } catch (err) {
      console.error('Failed to save page:', err)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <Card><div className="text-center py-8">Loading...</div></Card>
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-secondary">
          {pageId ? 'Edit Page' : 'New Page'}
        </h1>
      </div>

      <Card>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Title</label>
            <input
              type="text"
              value={page.title || ''}
              onChange={(e) => setPage({ ...page, title: e.target.value })}
              className="w-full px-4 py-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Content</label>
            <textarea
              value={page.content || ''}
              onChange={(e) => setPage({ ...page, content: e.target.value })}
              rows={20}
              className="w-full px-4 py-2 border rounded-lg font-mono"
            />
          </div>
          <div className="flex justify-end space-x-3">
            <Button variant="secondary" onClick={() => navigate(`/app/sites/${siteId}/pages`)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? 'Saving...' : 'Save'}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}

