import { useState, useEffect } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import {
  PlusIcon,
  PencilSquareIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  EyeIcon,
  CheckIcon,
  XMarkIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import {
  fetchSitePosts,
  deleteSitePost,
  updateSitePost,
  fetchSiteCategories,
  type SitePostListItem,
  type SiteCategory,
} from '../../api/client'

type StatusFilter = 'all' | 'published' | 'draft' | 'scheduled'

export default function SitePosts() {
  const { siteId } = useParams<{ siteId: string }>()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const [posts, setPosts] = useState<SitePostListItem[]>([])
  const [categories, setCategories] = useState<SiteCategory[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)

  // Filters
  const [statusFilter, setStatusFilter] = useState<StatusFilter>(
    (searchParams.get('status') as StatusFilter) || 'all'
  )
  const [categoryFilter, setCategoryFilter] = useState<number | null>(
    searchParams.get('category') ? parseInt(searchParams.get('category')!) : null
  )
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [page, setPage] = useState(parseInt(searchParams.get('page') || '1'))

  // Bulk selection
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null)

  useEffect(() => {
    if (siteId) {
      loadCategories()
    }
  }, [siteId])

  useEffect(() => {
    if (siteId) {
      loadPosts()
    }
  }, [siteId, statusFilter, categoryFilter, search, page])

  async function loadCategories() {
    if (!siteId) return
    try {
      const data = await fetchSiteCategories(parseInt(siteId))
      setCategories(data)
    } catch (err) {
      console.error('Failed to load categories:', err)
    }
  }

  async function loadPosts() {
    if (!siteId) return
    try {
      setLoading(true)
      const params: any = { page, per_page: 20 }
      if (statusFilter !== 'all') params.status = statusFilter
      if (categoryFilter) params.category_id = categoryFilter
      if (search) params.search = search

      const data = await fetchSitePosts(parseInt(siteId), params)
      setPosts(data.items)
      setTotal(data.total)
      setTotalPages(data.total_pages)
    } catch (err) {
      console.error('Failed to load posts:', err)
    } finally {
      setLoading(false)
    }
  }

  function updateFilters(updates: Partial<{ status: StatusFilter; category: number | null; search: string; page: number }>) {
    const newParams = new URLSearchParams(searchParams)
    
    if (updates.status !== undefined) {
      if (updates.status === 'all') newParams.delete('status')
      else newParams.set('status', updates.status)
      setStatusFilter(updates.status)
    }
    if (updates.category !== undefined) {
      if (updates.category === null) newParams.delete('category')
      else newParams.set('category', updates.category.toString())
      setCategoryFilter(updates.category)
    }
    if (updates.search !== undefined) {
      if (!updates.search) newParams.delete('search')
      else newParams.set('search', updates.search)
      setSearch(updates.search)
    }
    if (updates.page !== undefined) {
      if (updates.page === 1) newParams.delete('page')
      else newParams.set('page', updates.page.toString())
      setPage(updates.page)
    }
    
    setSearchParams(newParams)
  }

  async function handleDelete(postId: number) {
    if (!siteId) return
    try {
      await deleteSitePost(parseInt(siteId), postId)
      setPosts(posts.filter(p => p.id !== postId))
      setDeleteConfirm(null)
      setSelectedIds(prev => {
        const newSet = new Set(prev)
        newSet.delete(postId)
        return newSet
      })
    } catch (err) {
      console.error('Failed to delete post:', err)
    }
  }

  async function handleBulkDelete() {
    if (!siteId || selectedIds.size === 0) return
    try {
      for (const id of selectedIds) {
        await deleteSitePost(parseInt(siteId), id)
      }
      setPosts(posts.filter(p => !selectedIds.has(p.id)))
      setSelectedIds(new Set())
    } catch (err) {
      console.error('Failed to delete posts:', err)
    }
  }

  async function handleBulkStatusChange(newStatus: 'draft' | 'published') {
    if (!siteId || selectedIds.size === 0) return
    try {
      for (const id of selectedIds) {
        await updateSitePost(parseInt(siteId), id, { status: newStatus })
      }
      loadPosts()
      setSelectedIds(new Set())
    } catch (err) {
      console.error('Failed to update posts:', err)
    }
  }

  function toggleSelect(id: number) {
    setSelectedIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(id)) newSet.delete(id)
      else newSet.add(id)
      return newSet
    })
  }

  function toggleSelectAll() {
    if (selectedIds.size === posts.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(posts.map(p => p.id)))
    }
  }

  function getStatusBadge(status: string) {
    const styles: Record<string, string> = {
      published: 'bg-green-100 text-green-800',
      draft: 'bg-gray-100 text-gray-800',
      scheduled: 'bg-blue-100 text-blue-800',
    }
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[status] || styles.draft}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
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

      {/* Filters */}
      <Card className="mb-6">
        <div className="flex flex-wrap items-center gap-4">
          {/* Status Tabs */}
          <div className="flex rounded-lg border border-gray-200 overflow-hidden">
            {(['all', 'published', 'draft', 'scheduled'] as const).map((status) => (
              <button
                key={status}
                onClick={() => updateFilters({ status, page: 1 })}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  statusFilter === status
                    ? 'bg-primary text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                }`}
              >
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </button>
            ))}
          </div>

          {/* Category Filter */}
          <select
            value={categoryFilter || ''}
            onChange={(e) => updateFilters({ category: e.target.value ? parseInt(e.target.value) : null, page: 1 })}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name}
              </option>
            ))}
          </select>

          {/* Search */}
          <div className="relative flex-1 min-w-[200px]">
            <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => updateFilters({ search: e.target.value, page: 1 })}
              placeholder="Search posts..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>

        {/* Bulk Actions */}
        {selectedIds.size > 0 && (
          <div className="flex items-center gap-4 mt-4 pt-4 border-t">
            <span className="text-sm text-gray-600">
              {selectedIds.size} selected
            </span>
            <button
              onClick={() => handleBulkStatusChange('published')}
              className="px-3 py-1.5 text-sm bg-green-100 text-green-800 rounded-lg hover:bg-green-200"
            >
              Publish
            </button>
            <button
              onClick={() => handleBulkStatusChange('draft')}
              className="px-3 py-1.5 text-sm bg-gray-100 text-gray-800 rounded-lg hover:bg-gray-200"
            >
              Unpublish
            </button>
            <button
              onClick={handleBulkDelete}
              className="px-3 py-1.5 text-sm bg-red-100 text-red-800 rounded-lg hover:bg-red-200"
            >
              Delete
            </button>
          </div>
        )}
      </Card>

      {/* Posts Table */}
      <Card>
        {loading ? (
          <div className="flex items-center justify-center h-48">
            <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : posts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-gray-500">
            <p className="font-medium mb-2">No posts found</p>
            <p className="text-sm mb-4">
              {search || categoryFilter || statusFilter !== 'all'
                ? 'Try adjusting your filters'
                : 'Create your first post to get started'}
            </p>
            <Button onClick={() => navigate(`/app/sites/${siteId}/posts/new`)}>
              Create Post
            </Button>
          </div>
        ) : (
          <>
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="w-12 py-3 px-4 text-left">
                    <input
                      type="checkbox"
                      checked={selectedIds.size === posts.length && posts.length > 0}
                      onChange={toggleSelectAll}
                      className="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary"
                    />
                  </th>
                  <th className="py-3 px-4 text-left text-sm font-medium text-gray-600">Title</th>
                  <th className="py-3 px-4 text-left text-sm font-medium text-gray-600 hidden md:table-cell">Category</th>
                  <th className="py-3 px-4 text-left text-sm font-medium text-gray-600 hidden sm:table-cell">Status</th>
                  <th className="py-3 px-4 text-left text-sm font-medium text-gray-600 hidden lg:table-cell">Views</th>
                  <th className="py-3 px-4 text-left text-sm font-medium text-gray-600 hidden lg:table-cell">Date</th>
                  <th className="py-3 px-4 text-right text-sm font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody>
                {posts.map((post) => {
                  const category = categories.find(c => c.id === post.category_id)
                  return (
                    <tr
                      key={post.id}
                      className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                    >
                      <td className="py-3 px-4">
                        <input
                          type="checkbox"
                          checked={selectedIds.has(post.id)}
                          onChange={() => toggleSelect(post.id)}
                          className="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary"
                        />
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-start gap-3">
                          {post.featured_image && (
                            <img
                              src={post.featured_image}
                              alt=""
                              className="w-12 h-12 object-cover rounded hidden sm:block"
                            />
                          )}
                          <div>
                            <p className="font-medium text-gray-900 line-clamp-1">{post.title}</p>
                            <p className="text-sm text-gray-500 line-clamp-1">/posts/{post.slug}</p>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4 hidden md:table-cell">
                        {category ? (
                          <span
                            className="px-2 py-1 text-xs font-medium rounded-full"
                            style={{
                              backgroundColor: category.color ? `${category.color}20` : '#e5e7eb',
                              color: category.color || '#374151',
                            }}
                          >
                            {category.name}
                          </span>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </td>
                      <td className="py-3 px-4 hidden sm:table-cell">
                        {getStatusBadge(post.status)}
                      </td>
                      <td className="py-3 px-4 text-gray-600 hidden lg:table-cell">
                        {post.views_count?.toLocaleString() || 0}
                      </td>
                      <td className="py-3 px-4 text-gray-600 text-sm hidden lg:table-cell">
                        {formatDate(post.created_at)}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => navigate(`/app/sites/${siteId}/posts/${post.id}`)}
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                            title="Edit"
                          >
                            <PencilSquareIcon className="w-4 h-4 text-gray-600" />
                          </button>
                          <button
                            onClick={() => setDeleteConfirm(post.id)}
                            className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                            title="Delete"
                          >
                            <TrashIcon className="w-4 h-4 text-red-600" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-4 border-t">
                <p className="text-sm text-gray-600">
                  Showing {(page - 1) * 20 + 1} to {Math.min(page * 20, total)} of {total} posts
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => updateFilters({ page: page - 1 })}
                    disabled={page === 1}
                    className="p-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    <ChevronLeftIcon className="w-4 h-4" />
                  </button>
                  <span className="text-sm text-gray-600">
                    Page {page} of {totalPages}
                  </span>
                  <button
                    onClick={() => updateFilters({ page: page + 1 })}
                    disabled={page === totalPages}
                    className="p-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    <ChevronRightIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </Card>

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-xl p-6 max-w-sm w-full shadow-xl">
            <h3 className="text-lg font-bold text-gray-900 mb-2">Delete Post?</h3>
            <p className="text-gray-500 text-sm mb-6">
              This action cannot be undone. The post will be permanently deleted.
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
