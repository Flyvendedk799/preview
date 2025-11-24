import { useState, useEffect, useMemo, useCallback } from 'react'
import { PlusIcon, PencilIcon, TrashIcon, PhotoIcon } from '@heroicons/react/24/outline'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import EmptyState from '../components/ui/EmptyState'
import { SkeletonGrid } from '../components/ui/Skeleton'
import { usePreviews } from '../hooks/usePreviews'
import { useDomains } from '../hooks/useDomains'
import { fetchPreviewVariants, updatePreviewVariant } from '../api/client'
import type { PreviewCreate, PreviewUpdate, PreviewVariant } from '../api/types'

const filters = ['All', 'Product', 'Blog', 'Landing Page'] as const
type FilterType = typeof filters[number]

// Map filter display names to backend type values
const filterToTypeMap: Record<string, string | undefined> = {
  'All': undefined,
  'Product': 'product',
  'Blog': 'blog',
  'Landing Page': 'landing',
}

export default function Previews() {
  const [activeFilter, setActiveFilter] = useState<FilterType>('All')
  const filterType = filterToTypeMap[activeFilter]
  const { previews, loading, error, createOrUpdatePreview, updatePreview, deletePreview, generatePreviewAsync } = usePreviews(filterType)
  const { domains } = useDomains()
  
  // Debounce filter changes
  const [debouncedFilter, setDebouncedFilter] = useState<FilterType>(activeFilter)
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedFilter(activeFilter)
    }, 300) // 300ms debounce
    
    return () => clearTimeout(timer)
  }, [activeFilter])
  
  // Variant state
  const [previewVariants, setPreviewVariants] = useState<Record<number, PreviewVariant[]>>({})
  const [activeVariants, setActiveVariants] = useState<Record<number, 'main' | 'a' | 'b' | 'c'>>({})
  const [loadingVariants, setLoadingVariants] = useState<Record<number, boolean>>({})
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingPreview, setEditingPreview] = useState<number | null>(null)
  const [editingVariant, setEditingVariant] = useState<'main' | 'a' | 'b' | 'c' | null>(null)
  const [formData, setFormData] = useState<PreviewCreate>({
    url: '',
    domain: '',
    title: '',
    type: 'product',
    image_url: null,
  })
  const [formError, setFormError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isGeneratingAI, setIsGeneratingAI] = useState(false)
  const [jobStatus, setJobStatus] = useState<'queued' | 'started' | 'finished' | 'failed' | null>(null)
  
  // Load variants for previews
  useEffect(() => {
    const loadVariants = async () => {
      for (const preview of previews) {
        if (!previewVariants[preview.id] && !loadingVariants[preview.id]) {
          setLoadingVariants(prev => ({ ...prev, [preview.id]: true }))
          try {
            const variants = await fetchPreviewVariants(preview.id)
            setPreviewVariants(prev => ({ ...prev, [preview.id]: variants }))
            // Set default active variant to 'main'
            setActiveVariants(prev => ({ ...prev, [preview.id]: 'main' }))
          } catch (err) {
            console.error(`Failed to load variants for preview ${preview.id}:`, err)
          } finally {
            setLoadingVariants(prev => ({ ...prev, [preview.id]: false }))
          }
        }
      }
    }
    loadVariants()
  }, [previews])

  // Generate gradient class from type
  const getImageGradient = (type: string) => {
    const gradients: Record<string, string> = {
      product: 'bg-gradient-to-br from-primary/30 to-accent/30',
      blog: 'bg-gradient-to-br from-purple-300 to-pink-300',
      landing: 'bg-gradient-to-br from-blue-300 to-cyan-300',
    }
    return gradients[type.toLowerCase()] || 'bg-gradient-to-br from-gray-300 to-gray-400'
  }

  const handleOpenCreateModal = () => {
    setEditingPreview(null)
    setFormData({
      url: '',
      domain: domains.length > 0 ? domains[0].name : '',
      title: '',
      type: 'product',
      image_url: null,
    })
    setFormError(null)
    setIsModalOpen(true)
  }

  const handleOpenEditModal = (preview: typeof previews[0], variant: 'main' | 'a' | 'b' | 'c' = 'main') => {
    setEditingPreview(preview.id)
    setEditingVariant(variant)
    
    if (variant === 'main') {
      setFormData({
        url: preview.url,
        domain: preview.domain,
        title: preview.title,
        type: preview.type,
        image_url: preview.image_url || null,
      })
    } else {
      const variantData = previewVariants[preview.id]?.find(v => v.variant_key === variant)
      if (variantData) {
        setFormData({
          url: preview.url,
          domain: preview.domain,
          title: variantData.title,
          type: preview.type,
          image_url: variantData.image_url || preview.highlight_image_url || preview.image_url || null,
        })
      } else {
        setFormData({
          url: preview.url,
          domain: preview.domain,
          title: preview.title,
          type: preview.type,
          image_url: preview.image_url || null,
        })
      }
    }
    setFormError(null)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setEditingPreview(null)
    setEditingVariant(null)
    setFormData({
      url: '',
      domain: '',
      title: '',
      type: 'product',
      image_url: null,
    })
    setFormError(null)
  }
  
  const getDisplayData = (preview: typeof previews[0]) => {
    const activeVariant = activeVariants[preview.id] || 'main'
    
    if (activeVariant === 'main') {
      return {
        title: preview.title,
        description: preview.description,
        image_url: preview.image_url,
      }
    }
    
    const variant = previewVariants[preview.id]?.find(v => v.variant_key === activeVariant)
    if (variant) {
      return {
        title: variant.title,
        description: variant.description,
        image_url: variant.image_url || preview.highlight_image_url || preview.image_url,
      }
    }
    
    return {
      title: preview.title,
      description: preview.description,
      image_url: preview.image_url,
    }
  }

  const handleSubmit = async () => {
    if (!formData.url.trim() || !formData.domain.trim() || !formData.title.trim()) {
      setFormError('URL, Domain, and Title are required')
      return
    }

    try {
      setIsSubmitting(true)
      setFormError(null)

      if (editingPreview !== null) {
        if (editingVariant === 'main') {
          // Update main preview
          const updatePayload: PreviewUpdate = {
            title: formData.title,
            type: formData.type,
            image_url: formData.image_url || null,
          }
          await updatePreview(editingPreview, updatePayload)
        } else {
          // Update variant
          const variantData = previewVariants[editingPreview]?.find(v => v.variant_key === editingVariant)
          if (variantData) {
            await updatePreviewVariant(variantData.id, {
              title: formData.title,
              description: formData.description || null,
              image_url: formData.image_url || null,
            })
            // Refresh variants
            const variants = await fetchPreviewVariants(editingPreview)
            setPreviewVariants(prev => ({ ...prev, [editingPreview]: variants }))
          }
        }
      } else {
        // Create new preview
        await createOrUpdatePreview(formData)
      }

      handleCloseModal()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to save preview')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this preview?')) {
      try {
        await deletePreview(id)
      } catch (err) {
        // Error is handled by hook
      }
    }
  }

  const handleGenerateWithAI = async () => {
    if (!formData.url.trim() || !formData.domain.trim()) {
      setFormError('URL and Domain are required for AI generation')
      return
    }

    try {
      setIsGeneratingAI(true)
      setFormError(null)
      setJobStatus('queued')
      
      // Create job and poll status in parallel with hook's async function
      const { createPreviewJob, getJobStatus } = await import('../api/client')
      const { job_id } = await createPreviewJob({ url: formData.url, domain: formData.domain })
      
      // Poll for status updates (for UI feedback)
      const statusPollInterval = setInterval(async () => {
        try {
          const status = await getJobStatus(job_id)
          setJobStatus(status.status)
        } catch (err) {
          // Ignore polling errors, hook will handle completion
        }
      }, 1500)
      
      // Use hook's async function which handles completion and refresh
      try {
        await generatePreviewAsync(formData.url, formData.domain)
        clearInterval(statusPollInterval)
        setIsGeneratingAI(false)
        setJobStatus(null)
        handleCloseModal()
      } catch (err) {
        clearInterval(statusPollInterval)
        setFormError(err instanceof Error ? err.message : 'Failed to generate preview')
        setIsGeneratingAI(false)
        setJobStatus('failed')
      }
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to start preview generation')
      setIsGeneratingAI(false)
      setJobStatus(null)
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-secondary mb-2">Your URL Previews</h1>
        <p className="text-muted">Browse and manage all your generated URL previews.</p>
      </div>
      
      <div className="flex items-center justify-between mb-6">
        <Button onClick={handleOpenCreateModal}>
          <div className="flex items-center space-x-2">
            <PlusIcon className="w-5 h-5" />
            <span>Create Preview</span>
          </div>
        </Button>
      </div>

      {error && (
        <Card className="mb-6 bg-red-50 border-red-200">
          <p className="text-red-800">Error: {error}</p>
        </Card>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-6">
        {filters.map((filter) => (
          <button
            key={filter}
            onClick={() => setActiveFilter(filter)}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              activeFilter === filter
                ? 'bg-primary text-white shadow-md'
                : 'bg-white text-gray-700 border border-gray-200 hover:border-primary hover:text-primary'
            }`}
          >
            {filter}
          </button>
        ))}
      </div>

      {loading ? (
        <SkeletonGrid count={6} />
      ) : previews.length === 0 ? (
        <Card>
          <EmptyState
            icon={<PhotoIcon className="w-8 h-8" />}
            title="No previews generated yet"
            description="Create your first AI-powered preview to see how your URLs will appear when shared on social media and messaging platforms."
            action={{
              label: 'Generate Your First Preview',
              onClick: handleOpenCreateModal,
            }}
          />
        </Card>
      ) : (
        <>
          {/* Preview Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {previews.map((preview) => {
                const displayData = getDisplayData(preview)
                const variants = previewVariants[preview.id] || []
                const hasVariants = variants.length > 0
                
                return (
                  <Card key={preview.id} className="p-0 overflow-hidden group relative">
                    <div className={`aspect-video ${getImageGradient(preview.type)} flex items-center justify-center transition-transform group-hover:scale-105`}>
                      {displayData.image_url ? (
                        <img 
                          src={displayData.image_url} 
                          alt={displayData.title} 
                          className="w-full h-full object-cover" 
                          loading="lazy"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = preview.image_url || ''
                          }} 
                        />
                      ) : (
                        <div className="w-20 h-20 bg-white/20 backdrop-blur-sm rounded-lg flex items-center justify-center">
                          <span className="text-white text-2xl font-bold">P</span>
                        </div>
                      )}
                    </div>
                    <div className="p-4">
                      {/* Variant Tabs */}
                      {hasVariants && (
                        <div className="flex items-center space-x-1 mb-3 border-b border-gray-200">
                          <button
                            onClick={() => setActiveVariants(prev => ({ ...prev, [preview.id]: 'main' }))}
                            className={`px-2 py-1 text-xs font-medium transition-colors ${
                              (activeVariants[preview.id] || 'main') === 'main'
                                ? 'text-primary border-b-2 border-primary'
                                : 'text-gray-500 hover:text-gray-700'
                            }`}
                          >
                            Main
                          </button>
                          {variants.map((variant) => (
                            <button
                              key={variant.id}
                              onClick={() => setActiveVariants(prev => ({ ...prev, [preview.id]: variant.variant_key as 'a' | 'b' | 'c' }))}
                              className={`px-2 py-1 text-xs font-medium transition-colors ${
                                activeVariants[preview.id] === variant.variant_key
                                  ? 'text-primary border-b-2 border-primary'
                                  : 'text-gray-500 hover:text-gray-700'
                              }`}
                            >
                              {variant.variant_key.toUpperCase()}
                            </button>
                          ))}
                        </div>
                      )}
                      
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold text-gray-900">{displayData.title}</h3>
                        <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-full capitalize">
                          {preview.type}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 mb-2 line-clamp-2">{preview.url}</p>
                      {displayData.description && (
                        <p className="text-xs text-gray-600 mb-2 line-clamp-2">{displayData.description}</p>
                      )}
                      {preview.keywords && (
                        <div className="flex flex-wrap gap-1 mb-2">
                          {preview.keywords.split(',').map((keyword, idx) => (
                            <span
                              key={idx}
                              className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full"
                            >
                              {keyword.trim()}
                            </span>
                          ))}
                        </div>
                      )}
                      {!preview.keywords && (
                        <p className="text-xs text-gray-400 italic mb-2">— no keywords detected —</p>
                      )}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-gray-500">{preview.monthly_clicks.toLocaleString()} clicks</span>
                          {preview.tone && (
                            <span className="text-xs text-gray-400">• {preview.tone}</span>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleOpenEditModal(preview, activeVariants[preview.id] || 'main')}
                            className="text-primary hover:text-primary/80 transition-colors p-1"
                            title="Edit preview"
                          >
                            <PencilIcon className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(preview.id)}
                            className="text-red-600 hover:text-red-800 transition-colors p-1"
                            title="Delete preview"
                          >
                            <TrashIcon className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </Card>
                )
              })}
            </div>
        </>
      )}

      {/* Create/Edit Preview Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={editingPreview !== null 
          ? `Edit Preview${editingVariant && editingVariant !== 'main' ? ` - Variant ${editingVariant.toUpperCase()}` : ''}`
          : 'Create Preview'}
      >
        <div className="space-y-4">
          {formError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-800">{formError}</p>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              URL <span className="text-red-500">*</span>
            </label>
            <input
              type="url"
              placeholder="https://example.com/page"
              value={formData.url}
              onChange={(e) => {
                setFormData({ ...formData, url: e.target.value })
                setFormError(null)
              }}
              disabled={editingPreview !== null}
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all ${
                formError && !formData.url ? 'border-red-300' : 'border-gray-300'
              } ${editingPreview !== null ? 'bg-gray-50 cursor-not-allowed' : ''}`}
            />
            {editingPreview !== null && (
              <p className="text-xs text-gray-500 mt-1">URL cannot be changed after creation</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Domain <span className="text-red-500">*</span>
            </label>
            {domains.length > 0 ? (
              <select
                value={formData.domain}
                onChange={(e) => {
                  setFormData({ ...formData, domain: e.target.value })
                  setFormError(null)
                }}
                disabled={editingPreview !== null}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all ${
                  formError && !formData.domain ? 'border-red-300' : 'border-gray-300'
                } ${editingPreview !== null ? 'bg-gray-50 cursor-not-allowed' : ''}`}
              >
                <option value="">Select a domain</option>
                {domains.map((domain) => (
                  <option key={domain.id} value={domain.name}>
                    {domain.name}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                placeholder="example.com"
                value={formData.domain}
                onChange={(e) => {
                  setFormData({ ...formData, domain: e.target.value })
                  setFormError(null)
                }}
                disabled={editingPreview !== null}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all ${
                  formError && !formData.domain ? 'border-red-300' : 'border-gray-300'
                } ${editingPreview !== null ? 'bg-gray-50 cursor-not-allowed' : ''}`}
              />
            )}
            {domains.length === 0 && (
              <p className="text-xs text-gray-500 mt-1">Add a domain first in the Domains page</p>
            )}
          </div>

          {/* Variant Switcher in Edit Mode */}
          {editingPreview !== null && previewVariants[editingPreview] && previewVariants[editingPreview].length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Edit Variant
              </label>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handleOpenEditModal(previews.find(p => p.id === editingPreview)!, 'main')}
                  className={`px-3 py-2 text-sm rounded-lg transition-colors ${
                    editingVariant === 'main'
                      ? 'bg-primary text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Main
                </button>
                {previewVariants[editingPreview].map((variant) => (
                  <button
                    key={variant.id}
                    onClick={() => handleOpenEditModal(previews.find(p => p.id === editingPreview)!, variant.variant_key as 'a' | 'b' | 'c')}
                    className={`px-3 py-2 text-sm rounded-lg transition-colors ${
                      editingVariant === variant.variant_key
                        ? 'bg-primary text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {variant.variant_key.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              placeholder="Page Title"
              value={formData.title}
              onChange={(e) => {
                setFormData({ ...formData, title: e.target.value })
                setFormError(null)
              }}
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all ${
                formError && !formData.title ? 'border-red-300' : 'border-gray-300'
              }`}
            />
          </div>
          
          {editingPreview !== null && editingVariant !== 'main' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                placeholder="Preview description"
                value={formData.description || ''}
                onChange={(e) => {
                  setFormData({ ...formData, description: e.target.value })
                  setFormError(null)
                }}
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Type <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.type}
              onChange={(e) => {
                setFormData({ ...formData, type: e.target.value })
                setFormError(null)
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
            >
              <option value="product">Product</option>
              <option value="blog">Blog</option>
              <option value="landing">Landing Page</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Image URL (optional)
            </label>
            <input
              type="url"
              placeholder="https://example.com/image.jpg"
              value={formData.image_url || ''}
              onChange={(e) => {
                setFormData({ ...formData, image_url: e.target.value || null })
                setFormError(null)
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
            />
            <p className="text-xs text-gray-500 mt-1">Leave empty for now. AI generation coming soon.</p>
          </div>

          <div className="flex items-center justify-end space-x-3 pt-4">
            <Button variant="secondary" onClick={handleCloseModal} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : editingPreview !== null ? 'Update Preview' : 'Create Preview'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

