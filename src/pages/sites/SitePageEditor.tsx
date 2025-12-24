import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeftIcon,
  XMarkIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import RichTextEditor from '../../components/editor/RichTextEditor'
import {
  fetchSitePage,
  createSitePage,
  updateSitePage,
  type SitePage,
  type SitePageCreate,
  type SitePageUpdate,
} from '../../api/client'

export default function SitePageEditor() {
  const { siteId, pageId } = useParams<{ siteId: string; pageId?: string }>()
  const navigate = useNavigate()
  const isNew = !pageId || pageId === 'new'

  // Form state
  const [title, setTitle] = useState('')
  const [slug, setSlug] = useState('')
  const [content, setContent] = useState('')
  const [status, setStatus] = useState<'draft' | 'published'>('draft')
  const [isHomepage, setIsHomepage] = useState(false)

  // SEO fields
  const [metaTitle, setMetaTitle] = useState('')
  const [metaDescription, setMetaDescription] = useState('')

  // UI state
  const [loading, setLoading] = useState(!isNew)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [showSeo, setShowSeo] = useState(false)
  const [autoSlug, setAutoSlug] = useState(true)

  useEffect(() => {
    if (siteId && !isNew) {
      loadPage()
    }
  }, [siteId, pageId])

  useEffect(() => {
    if (autoSlug && title) {
      const generatedSlug = title
        .toLowerCase()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_-]+/g, '-')
        .replace(/^-+|-+$/g, '')
        .slice(0, 250)
      setSlug(generatedSlug)
    }
  }, [title, autoSlug])

  async function loadPage() {
    if (!siteId || !pageId) return
    try {
      setLoading(true)
      const page = await fetchSitePage(parseInt(siteId), parseInt(pageId))
      
      setTitle(page.title)
      setSlug(page.slug)
      setContent(page.content || '')
      setStatus(page.status as 'draft' | 'published')
      setIsHomepage(page.is_homepage || false)
      setMetaTitle(page.meta_title || '')
      setMetaDescription(page.meta_description || '')
      setAutoSlug(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load page')
    } finally {
      setLoading(false)
    }
  }

  async function handleSave(publishStatus?: 'draft' | 'published') {
    if (!siteId || !title.trim()) {
      setError('Title is required')
      return
    }

    try {
      setSaving(true)
      setError('')

      const finalStatus = publishStatus || status

      const pageData: SitePageCreate | SitePageUpdate = {
        title: title.trim(),
        slug: slug.trim() || undefined,
        content,
        status: finalStatus,
        is_homepage: isHomepage,
        meta_title: metaTitle.trim() || undefined,
        meta_description: metaDescription.trim() || undefined,
      }

      if (isNew) {
        await createSitePage(parseInt(siteId), pageData as SitePageCreate)
      } else {
        await updateSitePage(parseInt(siteId), parseInt(pageId!), pageData as SitePageUpdate)
      }

      navigate(`/app/sites/${siteId}/pages`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save page')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <Card>
        <div className="flex items-center justify-center h-64">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      </Card>
    )
  }

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(`/app/sites/${siteId}/pages`)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeftIcon className="w-5 h-5" />
          </button>
          <h1 className="text-2xl font-bold text-secondary">
            {isNew ? 'New Page' : 'Edit Page'}
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="secondary" onClick={() => handleSave('draft')} disabled={saving}>
            {saving ? 'Saving...' : 'Save Draft'}
          </Button>
          <Button onClick={() => handleSave('published')} disabled={saving}>
            {saving ? 'Publishing...' : 'Publish'}
          </Button>
        </div>
      </div>

      {error && (
        <Card className="mb-6 bg-red-50 border-red-200">
          <div className="flex items-center gap-2">
            <XMarkIcon className="w-5 h-5 text-red-600" />
            <p className="text-red-800">{error}</p>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Title */}
          <Card>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Page title..."
              className="w-full text-3xl font-bold border-0 focus:outline-none focus:ring-0 placeholder-gray-300"
            />
          </Card>

          {/* Content Editor */}
          <Card className="p-0 overflow-hidden">
            <RichTextEditor
              content={content}
              onChange={setContent}
              placeholder="Write your page content..."
              minHeight="400px"
            />
          </Card>

          {/* SEO Section */}
          <Card>
            <button
              onClick={() => setShowSeo(!showSeo)}
              className="w-full flex items-center justify-between text-left"
            >
              <span className="font-semibold text-gray-900">SEO Settings</span>
              {showSeo ? (
                <ChevronUpIcon className="w-5 h-5 text-gray-500" />
              ) : (
                <ChevronDownIcon className="w-5 h-5 text-gray-500" />
              )}
            </button>
            
            {showSeo && (
              <div className="mt-4 space-y-4 pt-4 border-t">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Meta Title
                    <span className="text-gray-400 ml-2">({metaTitle.length}/70)</span>
                  </label>
                  <input
                    type="text"
                    value={metaTitle}
                    onChange={(e) => setMetaTitle(e.target.value.slice(0, 70))}
                    placeholder="SEO title (defaults to page title)"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Meta Description
                    <span className="text-gray-400 ml-2">({metaDescription.length}/160)</span>
                  </label>
                  <textarea
                    value={metaDescription}
                    onChange={(e) => setMetaDescription(e.target.value.slice(0, 160))}
                    placeholder="SEO description"
                    rows={2}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                  />
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Status */}
          <Card>
            <h3 className="font-semibold text-gray-900 mb-4">Publish</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value as 'draft' | 'published')}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="draft">Draft</option>
                  <option value="published">Published</option>
                </select>
              </div>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isHomepage}
                  onChange={(e) => setIsHomepage(e.target.checked)}
                  className="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary"
                />
                <span className="text-sm text-gray-700">Set as Homepage</span>
              </label>
            </div>
          </Card>

          {/* URL Slug */}
          <Card>
            <h3 className="font-semibold text-gray-900 mb-4">URL Slug</h3>
            <input
              type="text"
              value={slug}
              onChange={(e) => {
                setSlug(e.target.value)
                setAutoSlug(false)
              }}
              placeholder="page-url-slug"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary font-mono text-sm"
            />
            <p className="text-xs text-gray-500 mt-2">
              /page/{slug || 'page-url-slug'}
            </p>
          </Card>
        </div>
      </div>
    </div>
  )
}
