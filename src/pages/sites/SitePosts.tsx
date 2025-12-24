import { useState, useEffect } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import {
  PlusIcon,
  PencilSquareIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  EyeIcon,
  DocumentTextIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import PageHeader from '../../components/ui/PageHeader'
import { StatusBadge } from '../../components/ui/Badge'
import { TabButtonGroup } from '../../components/ui/Tabs'
import { SkeletonTable } from '../../components/ui/Skeleton'
import { ConfirmDialog } from '../../components/ui/Modal'
import { IllustratedEmptyState } from '../../components/ui/EmptyState'
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
  const [deleteConfirm, setDeleteConfirm] = useState<SitePostListItem | null>(null)
  const [deleteLoading, setDeleteLoading] = useState(false)

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

  async function handleDelete() {
    if (!siteId || !deleteConfirm) return
    try {
      setDeleteLoading(true)
      await deleteSitePost(parseInt(siteId), deleteConfirm.id)
      setPosts(posts.filter(p => p.id !== deleteConfirm.id))
      setDeleteConfirm(null)
      setSelectedIds(prev => {
        const newSet = new Set(prev)
        newSet.delete(deleteConfirm.id)
        return newSet
      })
    } catch (err) {
      console.error('Failed to delete post:', err)
    } finally {
      setDeleteLoading(false)
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

  function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const statusOptions = [
    { value: 'all', label: 'All' },
    { value: 'published', label: 'Published' },
    { value: 'draft', label: 'Draft' },
    { value: 'scheduled', label: 'Scheduled' },
  ]

  return (
    <div>
      <PageHeader
        title="Posts"
        description={`${total} total posts`}
        breadcrumbs={[
          { label: 'Sites', href: '/app/sites' },
          { label: 'Posts' },
        ]}
        actions={
          <Button 
            onClick={() => navigate(`/app/sites/${siteId}/posts/new`)}
            icon={<PlusIcon className="w-5 h-5" />}
          >
            New Post
          </Button>
        }
      />

      {/* Filters */}
      <Card className="mb-6">
        <div className="flex flex-col lg:flex-row lg:items-center gap-4">
          {/* Status Tabs */}
          <TabButtonGroup
            options={statusOptions}
            value={statusFilter}
            onChange={(v) => updateFilters({ status: v as StatusFilter, page: 1 })}
          />

          {/* Category Filter */}
          <div className="flex items-center gap-2">
            <FunnelIcon className="w-4 h-4 text-secondary-400" />
            <select
              value={categoryFilter || ''}
              onChange={(e) => updateFilters({ category: e.target.value ? parseInt(e.target.value) : null, page: 1 })}
              className="select py-2 min-w-[160px]"
            >
              <option value="">All Categories</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>

          {/* Search */}
          <div className="relative flex-1 lg:max-w-xs ml-auto">
            <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-secondary-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => updateFilters({ search: e.target.value, page: 1 })}
              placeholder="Search posts..."
              className="input pl-10"
            />
          </div>
        </div>

        {/* Bulk Actions */}
        {selectedIds.size > 0 && (
          <div className="flex items-center gap-4 mt-4 pt-4 border-t border-secondary-100 animate-fade-in">
            <span className="text-sm font-medium text-secondary-600">
              {selectedIds.size} selected
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleBulkStatusChange('published')}
                className="text-success-600 hover:bg-success-50"
              >
                Publish
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleBulkStatusChange('draft')}
              >
                Unpublish
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleBulkDelete}
                className="text-error-600 hover:bg-error-50"
              >
                Delete
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Posts Table */}
      <Card padding="none">
        {loading ? (
          <div className="p-6">
            <SkeletonTable rows={5} cols={5} />
          </div>
        ) : posts.length === 0 ? (
          <IllustratedEmptyState
            illustration="posts"
            title="No posts found"
            description={
              search || categoryFilter || statusFilter !== 'all'
                ? 'Try adjusting your filters to find what you\'re looking for'
                : 'Create your first post to get started'
            }
            action={{
              label: 'Create Post',
              onClick: () => navigate(`/app/sites/${siteId}/posts/new`),
              icon: <PlusIcon className="w-5 h-5" />,
            }}
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="table">
                <thead className="table-header">
                  <tr>
                    <th className="w-12">
                      <input
                        type="checkbox"
                        checked={selectedIds.size === posts.length && posts.length > 0}
                        onChange={toggleSelectAll}
                        className="w-4 h-4 text-primary-500 border-secondary-300 rounded focus:ring-primary-500"
                      />
                    </th>
                    <th>Title</th>
                    <th className="hidden md:table-cell">Category</th>
                    <th className="hidden sm:table-cell">Status</th>
                    <th className="hidden lg:table-cell">Views</th>
                    <th className="hidden lg:table-cell">Date</th>
                    <th className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {posts.map((post) => {
                    const category = categories.find(c => c.id === post.category_id)
                    return (
                      <tr key={post.id} className="table-row group">
                        <td>
                          <input
                            type="checkbox"
                            checked={selectedIds.has(post.id)}
                            onChange={() => toggleSelect(post.id)}
                            className="w-4 h-4 text-primary-500 border-secondary-300 rounded focus:ring-primary-500"
                          />
                        </td>
                        <td>
                          <div className="flex items-center gap-3">
                            {post.featured_image ? (
                              <img
                                src={post.featured_image}
                                alt=""
                                className="w-12 h-12 object-cover rounded-lg hidden sm:block"
                              />
                            ) : (
                              <div className="w-12 h-12 bg-secondary-100 rounded-lg hidden sm:flex items-center justify-center">
                                <DocumentTextIcon className="w-5 h-5 text-secondary-400" />
                              </div>
                            )}
                            <div className="min-w-0">
                              <p className="font-medium text-secondary-900 truncate group-hover:text-primary-600 transition-colors">
                                {post.title}
                              </p>
                              <p className="text-sm text-secondary-500 truncate">
                                /posts/{post.slug}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td className="hidden md:table-cell">
                          {category ? (
                            <span
                              className="badge"
                              style={{
                                backgroundColor: category.color ? `${category.color}20` : undefined,
                                color: category.color || undefined,
                                borderColor: category.color ? `${category.color}40` : undefined,
                              }}
                            >
                              {category.name}
                            </span>
                          ) : (
                            <span className="text-secondary-400">—</span>
                          )}
                        </td>
                        <td className="hidden sm:table-cell">
                          <StatusBadge status={post.status as any} size="sm" />
                        </td>
                        <td className="hidden lg:table-cell">
                          <span className="text-secondary-600 tabular-nums">
                            {post.views_count?.toLocaleString() || 0}
                          </span>
                        </td>
                        <td className="hidden lg:table-cell">
                          <span className="text-secondary-500 text-sm">
                            {formatDate(post.created_at)}
                          </span>
                        </td>
                        <td>
                          <div className="flex items-center justify-end gap-1">
                            <button
                              onClick={() => navigate(`/app/sites/${siteId}/posts/${post.id}`)}
                              className="p-2 text-secondary-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                              title="Edit"
                            >
                              <PencilSquareIcon className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => setDeleteConfirm(post)}
                              className="p-2 text-secondary-400 hover:text-error-600 hover:bg-error-50 rounded-lg transition-colors"
                              title="Delete"
                            >
                              <TrashIcon className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-6 py-4 border-t border-secondary-100">
                <p className="text-sm text-secondary-500">
                  Showing <span className="font-medium text-secondary-700">{(page - 1) * 20 + 1}</span> to{' '}
                  <span className="font-medium text-secondary-700">{Math.min(page * 20, total)}</span> of{' '}
                  <span className="font-medium text-secondary-700">{total}</span> posts
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => updateFilters({ page: page - 1 })}
                    disabled={page === 1}
                    icon={<ChevronLeftIcon className="w-4 h-4" />}
                  >
                    Previous
                  </Button>
                  <span className="text-sm text-secondary-500 px-2">
                    {page} / {totalPages}
                  </span>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => updateFilters({ page: page + 1 })}
                    disabled={page === totalPages}
                    icon={<ChevronRightIcon className="w-4 h-4" />}
                    iconPosition="right"
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </Card>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={handleDelete}
        title="Delete Post?"
        message={`Are you sure you want to delete "${deleteConfirm?.title}"? This action cannot be undone.`}
        confirmText="Delete"
        variant="danger"
        loading={deleteLoading}
      />
    </div>
  )
}
