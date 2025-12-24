import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { PlusIcon, PencilSquareIcon, TrashIcon } from '@heroicons/react/24/outline'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import { fetchSitePosts, deleteSitePost, type SitePostListItem } from '../../api/client'

export default function SitePosts() {
  const { siteId } = useParams<{ siteId: string }>()
  const navigate = useNavigate()
  const [posts, setPosts] = useState<SitePostListItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (siteId) loadPosts()
  }, [siteId])

  async function loadPosts() {
    if (!siteId) return
    try {
      setLoading(true)
      const data = await fetchSitePosts(parseInt(siteId), { per_page: 50 })
      setPosts(data.items)
    } catch (err) {
      console.error('Failed to load posts:', err)
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(postId: number) {
    if (!siteId) return
    try {
      await deleteSitePost(parseInt(siteId), postId)
      setPosts(posts.filter(p => p.id !== postId))
    } catch (err) {
      console.error('Failed to delete post:', err)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-secondary">Posts</h1>
        <Button onClick={() => navigate(`/app/sites/${siteId}/posts/new`)}>
          <PlusIcon className="w-5 h-5 mr-2" />
          New Post
        </Button>
      </div>

      <Card>
        {loading ? (
          <div className="text-center py-8">Loading...</div>
        ) : posts.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-600 mb-4">No posts yet</p>
            <Button onClick={() => navigate(`/app/sites/${siteId}/posts/new`)}>
              Create Your First Post
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {posts.map((post) => (
              <div key={post.id} className="flex items-center justify-between p-4 border-b">
                <div>
                  <h3 className="font-medium">{post.title}</h3>
                  <p className="text-sm text-gray-500">{post.status}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => navigate(`/app/sites/${siteId}/posts/${post.id}`)}
                    className="p-2 hover:bg-gray-100 rounded"
                  >
                    <PencilSquareIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(post.id)}
                    className="p-2 hover:bg-red-50 rounded text-red-600"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

