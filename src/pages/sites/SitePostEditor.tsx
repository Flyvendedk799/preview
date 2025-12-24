import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import { fetchSitePost, createSitePost, updateSitePost, type SitePost, type SitePostCreate, type SitePostUpdate } from '../../api/client'

export default function SitePostEditor() {
  const { siteId, postId } = useParams<{ siteId: string; postId?: string }>()
  const navigate = useNavigate()
  const [post, setPost] = useState<Partial<SitePost>>({ title: '', content: '', status: 'draft' })
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (postId && siteId) {
      loadPost()
    }
  }, [postId, siteId])

  async function loadPost() {
    if (!postId || !siteId) return
    try {
      setLoading(true)
      const data = await fetchSitePost(parseInt(siteId), parseInt(postId))
      setPost(data)
    } catch (err) {
      console.error('Failed to load post:', err)
    } finally {
      setLoading(false)
    }
  }

  async function handleSave() {
    if (!siteId) return
    try {
      setSaving(true)
      if (postId) {
        await updateSitePost(parseInt(siteId), parseInt(postId), post as SitePostUpdate)
      } else {
        await createSitePost(parseInt(siteId), post as SitePostCreate)
      }
      navigate(`/app/sites/${siteId}/posts`)
    } catch (err) {
      console.error('Failed to save post:', err)
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
          {postId ? 'Edit Post' : 'New Post'}
        </h1>
      </div>

      <Card>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Title</label>
            <input
              type="text"
              value={post.title || ''}
              onChange={(e) => setPost({ ...post, title: e.target.value })}
              className="w-full px-4 py-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Content</label>
            <textarea
              value={post.content || ''}
              onChange={(e) => setPost({ ...post, content: e.target.value })}
              rows={20}
              className="w-full px-4 py-2 border rounded-lg font-mono"
            />
          </div>
          <div className="flex justify-end space-x-3">
            <Button variant="secondary" onClick={() => navigate(`/app/sites/${siteId}/posts`)}>
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

