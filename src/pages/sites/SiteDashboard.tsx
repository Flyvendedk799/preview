import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  DocumentTextIcon,
  FolderIcon,
  DocumentIcon,
  EyeIcon,
  ArrowTrendingUpIcon,
} from '@heroicons/react/24/outline'
import Card from '../../components/ui/Card'
import { SkeletonList } from '../../components/ui/Skeleton'
import { fetchSiteById, fetchSiteStats, type PublishedSite, type SiteStats } from '../../api/client'

export default function SiteDashboard() {
  const { siteId } = useParams<{ siteId: string }>()
  const navigate = useNavigate()
  const [site, setSite] = useState<PublishedSite | null>(null)
  const [stats, setStats] = useState<SiteStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (siteId) {
      loadSite()
      loadStats()
    }
  }, [siteId])

  async function loadSite() {
    if (!siteId) return
    try {
      setLoading(true)
      const data = await fetchSiteById(parseInt(siteId))
      setSite(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load site')
    } finally {
      setLoading(false)
    }
  }

  async function loadStats() {
    if (!siteId) return
    try {
      const data = await fetchSiteStats(parseInt(siteId))
      setStats(data)
    } catch (err) {
      console.error('Failed to load stats:', err)
    }
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
      action: () => navigate(`/app/sites/${siteId}/posts`),
    },
    {
      name: 'Published',
      value: stats?.published_posts || 0,
      icon: DocumentIcon,
      color: 'text-green-500',
      action: () => navigate(`/app/sites/${siteId}/posts?status=published`),
    },
    {
      name: 'Categories',
      value: stats?.categories || 0,
      icon: FolderIcon,
      color: 'text-purple-500',
      action: () => navigate(`/app/sites/${siteId}/categories`),
    },
    {
      name: 'Total Views',
      value: stats?.total_views || 0,
      icon: EyeIcon,
      color: 'text-orange-500',
    },
  ]

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-secondary mb-2">{site.name}</h1>
        <p className="text-muted">{site.domain?.name || 'No domain'}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.name} className="hover:shadow-lg transition-shadow cursor-pointer" onClick={stat.action}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600 mb-1">{stat.name}</p>
                  <p className="text-3xl font-bold text-secondary">{stat.value.toLocaleString()}</p>
                </div>
                <div className={`p-3 rounded-lg bg-gray-50 ${stat.color}`}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
            </Card>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h3 className="text-lg font-semibold text-secondary mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <button
              onClick={() => navigate(`/app/sites/${siteId}/posts/new`)}
              className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-primary hover:bg-primary/5 transition-colors"
            >
              <p className="font-medium text-gray-900">Create New Post</p>
              <p className="text-sm text-muted-light">Write a new blog post</p>
            </button>
            <button
              onClick={() => navigate(`/app/sites/${siteId}/pages/new`)}
              className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-primary hover:bg-primary/5 transition-colors"
            >
              <p className="font-medium text-gray-900">Create New Page</p>
              <p className="text-sm text-muted-light">Add a static page</p>
            </button>
            <button
              onClick={() => navigate(`/app/sites/${siteId}/branding`)}
              className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-primary hover:bg-primary/5 transition-colors"
            >
              <p className="font-medium text-gray-900">Customize Branding</p>
              <p className="text-sm text-muted-light">Update colors and logo</p>
            </button>
          </div>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-secondary mb-4">Site Status</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Status:</span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                site.status === 'published' ? 'bg-green-100 text-green-800' :
                site.status === 'draft' ? 'bg-gray-100 text-gray-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {site.status}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Template:</span>
              <span className="font-medium">{site.template_id}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Created:</span>
              <span className="font-medium">{new Date(site.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}

