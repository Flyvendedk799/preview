import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeftIcon,
  CheckIcon,
  CloudArrowUpIcon,
  DocumentTextIcon,
  EyeIcon,
  PhotoIcon,
  SparklesIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  GlobeAltIcon,
  MagnifyingGlassIcon,
  HashtagIcon,
  LinkIcon,
  UserIcon,
  CalendarIcon,
  PencilIcon,
} from '@heroicons/react/24/outline'
import {
  adminFetchBlogPost,
  adminCreateBlogPost,
  adminUpdateBlogPost,
  adminFetchBlogCategories,
  adminPublishBlogPost,
  type BlogPost,
  type BlogPostCreate,
  type BlogCategory,
} from '../../api/client'

// Generate URL-friendly slug
function generateSlug(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .substring(0, 250)
}

// Calculate reading time from content
function calculateReadTime(content: string): number {
  const words = content.trim().split(/\s+/).length
  return Math.max(1, Math.round(words / 225))
}

// Generate excerpt from content
function generateExcerpt(content: string, maxLength: number = 160): string {
  const cleanContent = content
    .replace(/[#*_\[\]()]/g, '')
    .replace(/\n+/g, ' ')
    .trim()
  
  if (cleanContent.length <= maxLength) return cleanContent
  return cleanContent.substring(0, maxLength - 3).replace(/\s+\S*$/, '') + '...'
}

export default function AdminBlogEditor() {
  const { postId } = useParams<{ postId: string }>()
  const navigate = useNavigate()
  const isEditing = postId && postId !== 'new'
  
  const [loading, setLoading] = useState(isEditing)
  const [saving, setSaving] = useState(false)
  const [categories, setCategories] = useState<BlogCategory[]>([])
  const [activeTab, setActiveTab] = useState<'write' | 'preview'>('write')
  const [expandedSections, setExpandedSections] = useState({
    seo: true,
    social: false,
    advanced: false,
  })
  
  // Form state
  const [formData, setFormData] = useState<BlogPostCreate>({
    title: '',
    slug: '',
    excerpt: '',
    content: '',
    featured_image: '',
    featured_image_alt: '',
    og_image: '',
    author_name: '',
    author_bio: '',
    author_avatar: '',
    category_id: undefined,
    tags: '',
    status: 'draft',
    is_featured: false,
    is_pinned: false,
    meta_title: '',
    meta_description: '',
    meta_keywords: '',
    canonical_url: '',
    no_index: false,
    schema_type: 'Article',
    twitter_title: '',
    twitter_description: '',
    twitter_image: '',
  })
  
  const [autoSlug, setAutoSlug] = useState(true)
  const [lastSaved, setLastSaved] = useState<Date | null>(null)

  useEffect(() => {
    loadCategories()
    if (isEditing) {
      loadPost(parseInt(postId))
    }
  }, [postId])

  // Auto-generate slug from title
  useEffect(() => {
    if (autoSlug && formData.title && !isEditing) {
      setFormData(prev => ({ ...prev, slug: generateSlug(prev.title) }))
    }
  }, [formData.title, autoSlug, isEditing])

  async function loadPost(id: number) {
    setLoading(true)
    try {
      const post = await adminFetchBlogPost(id)
      setFormData({
        title: post.title,
        slug: post.slug,
        excerpt: post.excerpt || '',
        content: post.content,
        featured_image: post.featured_image || '',
        featured_image_alt: post.featured_image_alt || '',
        og_image: post.og_image || '',
        author_name: post.author_name || '',
        author_bio: post.author_bio || '',
        author_avatar: post.author_avatar || '',
        category_id: post.category_id || undefined,
        tags: post.tags || '',
        status: post.status as any,
        is_featured: post.is_featured,
        is_pinned: post.is_pinned,
        meta_title: post.meta_title || '',
        meta_description: post.meta_description || '',
        meta_keywords: post.meta_keywords || '',
        canonical_url: post.canonical_url || '',
        no_index: post.no_index,
        schema_type: post.schema_type,
        twitter_title: post.twitter_title || '',
        twitter_description: post.twitter_description || '',
        twitter_image: post.twitter_image || '',
      })
      setAutoSlug(false)
    } catch (error) {
      console.error('Failed to load post:', error)
      navigate('/app/admin/blog')
    } finally {
      setLoading(false)
    }
  }

  async function loadCategories() {
    try {
      const data = await adminFetchBlogCategories()
      setCategories(data)
    } catch (error) {
      console.error('Failed to load categories:', error)
    }
  }

  async function handleSave(publish: boolean = false) {
    setSaving(true)
    try {
      const dataToSave = {
        ...formData,
        status: publish ? 'published' : formData.status,
      }
      
      if (isEditing) {
        await adminUpdateBlogPost(parseInt(postId), dataToSave)
      } else {
        const created = await adminCreateBlogPost(dataToSave as BlogPostCreate)
        navigate(`/app/admin/blog/${created.id}`, { replace: true })
      }
      
      setLastSaved(new Date())
      
      if (publish) {
        // Navigate back to list after publishing
        navigate('/app/admin/blog')
      }
    } catch (error) {
      console.error('Failed to save post:', error)
      alert('Failed to save post. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  async function handlePublish() {
    if (isEditing) {
      setSaving(true)
      try {
        await adminUpdateBlogPost(parseInt(postId), formData)
        await adminPublishBlogPost(parseInt(postId))
        navigate('/app/admin/blog')
      } catch (error) {
        console.error('Failed to publish:', error)
        alert('Failed to publish. Please try again.')
      } finally {
        setSaving(false)
      }
    } else {
      await handleSave(true)
    }
  }

  function updateFormData(field: keyof BlogPostCreate, value: any) {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  function toggleSection(section: keyof typeof expandedSections) {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }))
  }

  // Auto-generate meta description from excerpt or content
  function autoGenerateMetaDescription() {
    const text = formData.excerpt || generateExcerpt(formData.content)
    setFormData(prev => ({ ...prev, meta_description: text.substring(0, 160) }))
  }

  const readTime = calculateReadTime(formData.content)
  const effectiveMetaTitle = formData.meta_title || formData.title
  const effectiveMetaDesc = formData.meta_description || formData.excerpt || generateExcerpt(formData.content)

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin w-8 h-8 border-4 border-orange-500 border-t-transparent rounded-full" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 -m-8 p-8">
      {/* Top Bar */}
      <div className="bg-white border-b border-gray-200 -mx-8 -mt-8 px-8 py-4 mb-6 sticky top-0 z-30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/app/admin/blog')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeftIcon className="w-5 h-5 text-gray-600" />
            </button>
            <div>
              <h1 className="text-lg font-bold text-gray-900">
                {isEditing ? 'Edit Post' : 'New Post'}
              </h1>
              {lastSaved && (
                <p className="text-xs text-gray-500">
                  Last saved {lastSaved.toLocaleTimeString()}
                </p>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded-lg">
              <span className={`w-2 h-2 rounded-full ${
                formData.status === 'published' ? 'bg-green-500' :
                formData.status === 'scheduled' ? 'bg-blue-500' :
                'bg-gray-400'
              }`} />
              <span className="text-sm font-medium text-gray-700 capitalize">{formData.status}</span>
            </div>
            <button
              onClick={() => handleSave()}
              disabled={saving}
              className="px-4 py-2 border border-gray-200 rounded-lg font-medium hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Draft'}
            </button>
            <button
              onClick={handlePublish}
              disabled={saving || !formData.title || !formData.content}
              className="px-4 py-2 bg-orange-500 text-white rounded-lg font-medium hover:bg-orange-600 transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              <CloudArrowUpIcon className="w-5 h-5" />
              {formData.status === 'published' ? 'Update' : 'Publish'}
            </button>
          </div>
        </div>
      </div>

      <div className="flex gap-6">
        {/* Main Editor */}
        <div className="flex-1 space-y-6">
          {/* Title */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <input
              type="text"
              value={formData.title}
              onChange={(e) => updateFormData('title', e.target.value)}
              placeholder="Post title..."
              className="w-full text-3xl font-bold text-gray-900 placeholder-gray-400 border-none outline-none"
            />
            <div className="flex items-center gap-2 mt-4">
              <span className="text-sm text-gray-500">/blog/</span>
              <input
                type="text"
                value={formData.slug}
                onChange={(e) => {
                  setAutoSlug(false)
                  updateFormData('slug', e.target.value)
                }}
                placeholder="post-slug"
                className="flex-1 text-sm text-gray-600 border-none outline-none bg-gray-50 px-2 py-1 rounded"
              />
            </div>
          </div>

          {/* Tabs */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="flex border-b border-gray-200">
              <button
                onClick={() => setActiveTab('write')}
                className={`flex-1 py-3 text-sm font-medium transition-colors ${
                  activeTab === 'write'
                    ? 'text-orange-600 border-b-2 border-orange-500 bg-orange-50/50'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <PencilIcon className="w-4 h-4 inline mr-2" />
                Write
              </button>
              <button
                onClick={() => setActiveTab('preview')}
                className={`flex-1 py-3 text-sm font-medium transition-colors ${
                  activeTab === 'preview'
                    ? 'text-orange-600 border-b-2 border-orange-500 bg-orange-50/50'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <EyeIcon className="w-4 h-4 inline mr-2" />
                Preview
              </button>
            </div>
            
            <div className="p-6">
              {activeTab === 'write' ? (
                <div className="space-y-4">
                  {/* Excerpt */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Excerpt</label>
                    <textarea
                      value={formData.excerpt}
                      onChange={(e) => updateFormData('excerpt', e.target.value)}
                      placeholder="Brief summary of the post (shown in listings)..."
                      rows={2}
                      className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 resize-none"
                    />
                    <div className="flex justify-between mt-1">
                      <span className="text-xs text-gray-400">Recommended: 150-200 characters</span>
                      <span className={`text-xs ${(formData.excerpt?.length || 0) > 200 ? 'text-red-500' : 'text-gray-400'}`}>
                        {formData.excerpt?.length || 0}/200
                      </span>
                    </div>
                  </div>
                  
                  {/* Content */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Content (Markdown)</label>
                    <textarea
                      value={formData.content}
                      onChange={(e) => updateFormData('content', e.target.value)}
                      placeholder="Write your post content here... Supports Markdown formatting.

## Heading 2
### Heading 3

**Bold text** and *italic text*

- Bullet point
1. Numbered list

> Blockquote

`inline code`

[Link text](https://example.com)"
                      rows={20}
                      className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 font-mono text-sm resize-y min-h-[400px]"
                    />
                    <div className="flex justify-between mt-1">
                      <span className="text-xs text-gray-400">
                        {formData.content.split(/\s+/).filter(Boolean).length} words • ~{readTime} min read
                      </span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="prose prose-lg max-w-none">
                  {formData.content ? (
                    <div className="space-y-4">
                      {formData.content.split('\n').map((line, i) => {
                        const trimmed = line.trim()
                        if (trimmed.startsWith('## ')) {
                          return <h2 key={i} className="text-2xl font-bold mt-6 mb-3">{trimmed.slice(3)}</h2>
                        }
                        if (trimmed.startsWith('### ')) {
                          return <h3 key={i} className="text-xl font-bold mt-4 mb-2">{trimmed.slice(4)}</h3>
                        }
                        if (trimmed.startsWith('> ')) {
                          return <blockquote key={i} className="border-l-4 border-orange-500 pl-4 italic text-gray-600">{trimmed.slice(2)}</blockquote>
                        }
                        if (trimmed.startsWith('- ')) {
                          return <li key={i} className="ml-4">{trimmed.slice(2)}</li>
                        }
                        if (trimmed) {
                          return <p key={i} className="text-gray-700">{trimmed}</p>
                        }
                        return null
                      })}
                    </div>
                  ) : (
                    <p className="text-gray-400 italic">Start writing to see preview...</p>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="w-96 space-y-6">
          {/* Featured Image */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <PhotoIcon className="w-5 h-5 text-gray-400" />
              Featured Image
            </h3>
            {formData.featured_image ? (
              <div className="space-y-3">
                <img
                  src={formData.featured_image}
                  alt={formData.featured_image_alt || 'Preview'}
                  className="w-full h-40 object-cover rounded-lg"
                />
                <button
                  onClick={() => updateFormData('featured_image', '')}
                  className="text-sm text-red-500 hover:text-red-600"
                >
                  Remove image
                </button>
              </div>
            ) : (
              <div className="border-2 border-dashed border-gray-200 rounded-lg p-6 text-center">
                <PhotoIcon className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-500">Enter image URL below</p>
              </div>
            )}
            <input
              type="text"
              value={formData.featured_image}
              onChange={(e) => updateFormData('featured_image', e.target.value)}
              placeholder="https://example.com/image.jpg"
              className="w-full mt-3 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/20"
            />
            <input
              type="text"
              value={formData.featured_image_alt}
              onChange={(e) => updateFormData('featured_image_alt', e.target.value)}
              placeholder="Image alt text (for accessibility)"
              className="w-full mt-2 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/20"
            />
          </div>

          {/* Category & Tags */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <HashtagIcon className="w-5 h-5 text-gray-400" />
              Organization
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-600 mb-1">Category</label>
                <select
                  value={formData.category_id || ''}
                  onChange={(e) => updateFormData('category_id', e.target.value ? parseInt(e.target.value) : undefined)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/20 text-sm"
                >
                  <option value="">No category</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Tags</label>
                <input
                  type="text"
                  value={formData.tags}
                  onChange={(e) => updateFormData('tags', e.target.value)}
                  placeholder="seo, marketing, tips"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/20 text-sm"
                />
                <p className="text-xs text-gray-400 mt-1">Comma-separated</p>
              </div>
            </div>
          </div>

          {/* Author */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <UserIcon className="w-5 h-5 text-gray-400" />
              Author
            </h3>
            <div className="space-y-3">
              <input
                type="text"
                value={formData.author_name}
                onChange={(e) => updateFormData('author_name', e.target.value)}
                placeholder="Author name"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/20 text-sm"
              />
              <input
                type="text"
                value={formData.author_avatar}
                onChange={(e) => updateFormData('author_avatar', e.target.value)}
                placeholder="Avatar URL"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/20 text-sm"
              />
              <textarea
                value={formData.author_bio}
                onChange={(e) => updateFormData('author_bio', e.target.value)}
                placeholder="Brief author bio..."
                rows={2}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/20 text-sm resize-none"
              />
            </div>
          </div>

          {/* Visibility */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Visibility</h3>
            <div className="space-y-3">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_featured}
                  onChange={(e) => updateFormData('is_featured', e.target.checked)}
                  className="w-4 h-4 text-orange-500 border-gray-300 rounded focus:ring-orange-500"
                />
                <span className="text-sm text-gray-700">Featured post</span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_pinned}
                  onChange={(e) => updateFormData('is_pinned', e.target.checked)}
                  className="w-4 h-4 text-orange-500 border-gray-300 rounded focus:ring-orange-500"
                />
                <span className="text-sm text-gray-700">Pin to top</span>
              </label>
            </div>
          </div>

          {/* SEO Section */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <button
              onClick={() => toggleSection('seo')}
              className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
            >
              <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                <MagnifyingGlassIcon className="w-5 h-5 text-gray-400" />
                SEO Settings
              </h3>
              {expandedSections.seo ? (
                <ChevronUpIcon className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDownIcon className="w-5 h-5 text-gray-400" />
              )}
            </button>
            {expandedSections.seo && (
              <div className="px-6 pb-6 space-y-4 border-t border-gray-100 pt-4">
                {/* Google Preview */}
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500 mb-2">Google Preview</p>
                  <div className="text-blue-600 text-lg hover:underline cursor-pointer truncate">
                    {effectiveMetaTitle || 'Post Title'}
                  </div>
                  <div className="text-green-700 text-sm truncate">
                    mymetaview.com/blog/{formData.slug || 'post-slug'}
                  </div>
                  <div className="text-gray-600 text-sm line-clamp-2">
                    {effectiveMetaDesc || 'Add a meta description to improve SEO...'}
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    Meta Title
                    <span className={`ml-2 ${(formData.meta_title?.length || 0) > 60 ? 'text-red-500' : 'text-gray-400'}`}>
                      ({formData.meta_title?.length || 0}/60)
                    </span>
                  </label>
                  <input
                    type="text"
                    value={formData.meta_title}
                    onChange={(e) => updateFormData('meta_title', e.target.value)}
                    placeholder={formData.title || 'SEO title (defaults to post title)'}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/20 text-sm"
                  />
                </div>
                
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-sm text-gray-600">
                      Meta Description
                      <span className={`ml-2 ${(formData.meta_description?.length || 0) > 160 ? 'text-red-500' : 'text-gray-400'}`}>
                        ({formData.meta_description?.length || 0}/160)
                      </span>
                    </label>
                    <button
                      onClick={autoGenerateMetaDescription}
                      className="text-xs text-orange-500 hover:text-orange-600"
                    >
                      Auto-generate
                    </button>
                  </div>
                  <textarea
                    value={formData.meta_description}
                    onChange={(e) => updateFormData('meta_description', e.target.value)}
                    placeholder="Brief description for search results..."
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/20 text-sm resize-none"
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Keywords</label>
                  <input
                    type="text"
                    value={formData.meta_keywords}
                    onChange={(e) => updateFormData('meta_keywords', e.target.value)}
                    placeholder="keyword1, keyword2, keyword3"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/20 text-sm"
                  />
                </div>

                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.no_index}
                    onChange={(e) => updateFormData('no_index', e.target.checked)}
                    className="w-4 h-4 text-orange-500 border-gray-300 rounded focus:ring-orange-500"
                  />
                  <span className="text-sm text-gray-700">No index (hide from search engines)</span>
                </label>
              </div>
            )}
          </div>

          {/* Social Media Section */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <button
              onClick={() => toggleSection('social')}
              className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
            >
              <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                <GlobeAltIcon className="w-5 h-5 text-gray-400" />
                Social Media
              </h3>
              {expandedSections.social ? (
                <ChevronUpIcon className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDownIcon className="w-5 h-5 text-gray-400" />
              )}
            </button>
            {expandedSections.social && (
              <div className="px-6 pb-6 space-y-4 border-t border-gray-100 pt-4">
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Open Graph Image</label>
                  <input
                    type="text"
                    value={formData.og_image}
                    onChange={(e) => updateFormData('og_image', e.target.value)}
                    placeholder="https://... (1200x630 recommended)"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/20 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Twitter Title</label>
                  <input
                    type="text"
                    value={formData.twitter_title}
                    onChange={(e) => updateFormData('twitter_title', e.target.value)}
                    placeholder="Custom title for Twitter"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/20 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Twitter Description</label>
                  <input
                    type="text"
                    value={formData.twitter_description}
                    onChange={(e) => updateFormData('twitter_description', e.target.value)}
                    placeholder="Custom description for Twitter"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/20 text-sm"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Advanced Section */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <button
              onClick={() => toggleSection('advanced')}
              className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
            >
              <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                <LinkIcon className="w-5 h-5 text-gray-400" />
                Advanced
              </h3>
              {expandedSections.advanced ? (
                <ChevronUpIcon className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDownIcon className="w-5 h-5 text-gray-400" />
              )}
            </button>
            {expandedSections.advanced && (
              <div className="px-6 pb-6 space-y-4 border-t border-gray-100 pt-4">
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Canonical URL</label>
                  <input
                    type="text"
                    value={formData.canonical_url}
                    onChange={(e) => updateFormData('canonical_url', e.target.value)}
                    placeholder="https://example.com/original-post"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/20 text-sm"
                  />
                  <p className="text-xs text-gray-400 mt-1">Use if this content was originally published elsewhere</p>
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Schema Type</label>
                  <select
                    value={formData.schema_type}
                    onChange={(e) => updateFormData('schema_type', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/20 text-sm"
                  >
                    <option value="Article">Article</option>
                    <option value="BlogPosting">Blog Posting</option>
                    <option value="NewsArticle">News Article</option>
                    <option value="TechArticle">Tech Article</option>
                  </select>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

