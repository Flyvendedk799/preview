import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  DocumentTextIcon,
  FolderIcon,
  DocumentIcon,
  EyeIcon,
  ArrowTrendingUpIcon,
  PlusIcon,
  PencilSquareIcon,
  Cog6ToothIcon,
  PhotoIcon,
  Bars3Icon,
  PaintBrushIcon,
  GlobeAltIcon,
  ClockIcon,
} from '@heroicons/react/24/outline'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import { SkeletonList } from '../../components/ui/Skeleton'
import {
  fetchSiteById,
  fetchSiteStats,
  fetchSitePosts,
  type PublishedSite,
  type SiteStats,
  type SitePostListItem,
} from '../../api/client'

export default function SiteDashboard() {
  const { siteId } = useParams<{ siteId: string }>()
  const navigate = useNavigate()
  const [site, setSite] = useState<PublishedSite | null>(null)
  const [stats, setStats] = useState<SiteStats | null>(null)
  const [recentPosts, setRecentPosts] = useState<SitePostListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (siteId) {
      loadData()
    }
  }, [siteId])

  async function loadData() {
    if (!siteId) return
    try {
      setLoading(true)
      const [siteData, statsData, postsData] = await Promise.all([
        fetchSiteById(parseInt(siteId)),
        fetchSiteStats(parseInt(siteId)).catch(() => null),
        fetchSitePosts(parseInt(siteId), { per_page: 5 }).catch(() => ({ items: [] })),
      ])
      setSite(siteData)
      setStats(statsData)
      setRecentPosts(postsData.items)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load site')
    } finally {
      setLoading(false)
    }
  }

  function formatDate(dateStr: string) {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    
    if (days === 0) return 'Today'
    if (days === 1) return 'Yesterday'
    if (days < 7) return `${days} days ago`
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  if (loading) {
    return (
      <Card>
        <SkeletonList count={4} />
      </Card>
    )
  }

  if (error || !site) {
    return (
      <Card>
        <div className="text-center py-8">
          <p className="text-red-600">{error || 'Site not found'}</p>
        </div>
      </Card>
    )
  }

  const statCards = [
    {
      name: 'Total Posts',
      value: stats?.total_posts || 0,
      icon: DocumentTextIcon,
      color: 'text-blue-500',
      bgColor: 'bg-blue-50',
      action: () => navigate(`/app/sites/${siteId}/posts`),
    },
    {
      name: 'Published',
      value: stats?.published_posts || 0,
      icon: DocumentIcon,
      color: 'text-green-500',
      bgColor: 'bg-green-50',
      action: () => navigate(`/app/sites/${siteId}/posts?status=published`),
    },
    {
      name: 'Categories',
      value: stats?.categories || 0,
      icon: FolderIcon,
      color: 'text-purple-500',
      bgColor: 'bg-purple-50',
      action: () => navigate(`/app/sites/${siteId}/categories`),
    },
    {
      name: 'Total Views',
      value: stats?.total_views || 0,
      icon: EyeIcon,
      color: 'text-orange-500',
      bgColor: 'bg-orange-50',
    },
  ]

  const quickLinks = [
    { name: 'Posts', icon: DocumentTextIcon, path: 'posts', color: 'text-blue-500' },
    { name: 'Pages', icon: DocumentIcon, path: 'pages', color: 'text-green-500' },
    { name: 'Categories', icon: FolderIcon, path: 'categories', color: 'text-purple-500' },
    { name: 'Media', icon: PhotoIcon, path: 'media', color: 'text-pink-500' },
    { name: 'Menus', icon: Bars3Icon, path: 'menus', color: 'text-indigo-500' },
    { name: 'Branding', icon: PaintBrushIcon, path: 'branding', color: 'text-orange-500' },
    { name: 'Settings', icon: Cog6ToothIcon, path: 'settings', color: 'text-gray-500' },
  ]

  return (
    <div>
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-secondary mb-1">{site.name}</h1>
          <div className="flex items-center gap-3 text-muted">
            <span className="flex items-center gap-1">
              <GlobeAltIcon className="w-4 h-4" />
              {site.domain?.name || 'No domain'}
            </span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
              site.status === 'published' ? 'bg-green-100 text-green-800' :
              site.status === 'draft' ? 'bg-gray-100 text-gray-800' :
              'bg-yellow-100 text-yellow-800'
            }`}>
              {site.status}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {site.status === 'published' && site.domain?.name && (
            <a
              href={`https://${site.domain.name}`}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 border border-gray-300 rounded-lg font-medium hover:bg-gray-50 transition-colors flex items-center gap-2"
            >
              <EyeIcon className="w-4 h-4" />
              View Site
            </a>
          )}
          <Button onClick={() => navigate(`/app/sites/${siteId}/posts/new`)}>
            <PlusIcon className="w-5 h-5 mr-2" />
            New Post
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <Card
              key={stat.name}
              className={`hover:shadow-lg transition-shadow ${stat.action ? 'cursor-pointer' : ''}`}
              onClick={stat.action}
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 mb-1">{stat.name}</p>
                  <p className="text-3xl font-bold text-secondary">
                    {typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value}
                  </p>
                </div>
                <div className={`p-3 rounded-xl ${stat.bgColor}`}>
                  <Icon className={`w-6 h-6 ${stat.color}`} />
                </div>
              </div>
            </Card>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Posts */}
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-secondary">Recent Posts</h3>
            <Link
              to={`/app/sites/${siteId}/posts`}
              className="text-sm text-primary hover:underline"
            >
              View all
            </Link>
          </div>
          {recentPosts.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <DocumentTextIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
              <p className="font-medium mb-2">No posts yet</p>
              <Button
                variant="secondary"
                onClick={() => navigate(`/app/sites/${siteId}/posts/new`)}
              >
                Create Your First Post
              </Button>
            </div>
          ) : (
            <div className="divide-y">
              {recentPosts.map((post) => (
                <div
                  key={post.id}
                  className="py-3 flex items-center justify-between hover:bg-gray-50 -mx-4 px-4 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {post.featured_image ? (
                      <img
                        src={post.featured_image}
                        alt=""
                        className="w-12 h-12 object-cover rounded-lg"
                      />
                    ) : (
                      <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                        <DocumentTextIcon className="w-6 h-6 text-gray-400" />
                      </div>
                    )}
                    <div>
                      <h4 className="font-medium text-gray-900 line-clamp-1">{post.title}</h4>
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <span className={`px-1.5 py-0.5 rounded text-xs ${
                          post.status === 'published' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                        }`}>
                          {post.status}
                        </span>
                        <span className="flex items-center gap-1">
                          <ClockIcon className="w-3 h-3" />
                          {formatDate(post.created_at)}
                        </span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => navigate(`/app/sites/${siteId}/posts/${post.id}`)}
                    className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
                  >
                    <PencilSquareIcon className="w-4 h-4 text-gray-600" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Quick Links & Actions */}
        <div className="space-y-6">
          <Card>
            <h3 className="text-lg font-semibold text-secondary mb-4">Quick Actions</h3>
            <div className="space-y-2">
              <button
                onClick={() => navigate(`/app/sites/${siteId}/posts/new`)}
                className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-primary hover:bg-primary/5 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <PlusIcon className="w-5 h-5 text-primary" />
                  <div>
                    <p className="font-medium text-gray-900">New Post</p>
                    <p className="text-xs text-gray-500">Create a new blog post</p>
                  </div>
                </div>
              </button>
              <button
                onClick={() => navigate(`/app/sites/${siteId}/pages/new`)}
                className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-primary hover:bg-primary/5 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <DocumentIcon className="w-5 h-5 text-green-500" />
                  <div>
                    <p className="font-medium text-gray-900">New Page</p>
                    <p className="text-xs text-gray-500">Add a static page</p>
                  </div>
                </div>
              </button>
              <button
                onClick={() => navigate(`/app/sites/${siteId}/media`)}
                className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-primary hover:bg-primary/5 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <PhotoIcon className="w-5 h-5 text-pink-500" />
                  <div>
                    <p className="font-medium text-gray-900">Upload Media</p>
                    <p className="text-xs text-gray-500">Add images to your library</p>
                  </div>
                </div>
              </button>
            </div>
          </Card>

          <Card>
            <h3 className="text-lg font-semibold text-secondary mb-4">Quick Links</h3>
            <div className="grid grid-cols-3 gap-2">
              {quickLinks.map((link) => {
                const Icon = link.icon
                return (
                  <button
                    key={link.name}
                    onClick={() => navigate(`/app/sites/${siteId}/${link.path}`)}
                    className="flex flex-col items-center gap-1 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <Icon className={`w-5 h-5 ${link.color}`} />
                    <span className="text-xs text-gray-600">{link.name}</span>
                  </button>
                )
              })}
            </div>
          </Card>

          <Card>
            <h3 className="text-lg font-semibold text-secondary mb-4">Site Info</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Template:</span>
                <span className="font-medium">{site.template_id || 'default'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Created:</span>
                <span className="font-medium">
                  {new Date(site.created_at).toLocaleDateString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Last Updated:</span>
                <span className="font-medium">
                  {new Date(site.updated_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
