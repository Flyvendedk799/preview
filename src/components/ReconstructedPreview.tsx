/**
 * ReconstructedPreview Component
 * 
 * Renders an AI-reconstructed preview using multi-stage reasoning output.
 * Designed for premium SaaS quality with clean, intentional aesthetics.
 * 
 * NOW ENHANCED WITH DESIGN DNA:
 * When design_dna is available, uses the AdaptivePreview component to
 * dynamically style the preview based on the original design's philosophy.
 */

import { useEffect, useRef, useState } from 'react'
import { DemoPreviewResponse } from '../api/client'
import AdaptivePreview from './AdaptivePreview'

interface ReconstructedPreviewProps {
  preview: DemoPreviewResponse
  className?: string
}

// Icon components for context items
const LocationIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
)

const InfoIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)

const StarIcon = ({ filled = false }: { filled?: boolean }) => (
  <svg className={`w-4 h-4 ${filled ? 'text-amber-400 fill-current' : 'text-gray-300'}`} viewBox="0 0 20 20">
    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
  </svg>
)

// Get icon for context type
const getContextIcon = (icon: string) => {
  switch (icon.toLowerCase()) {
    case 'location':
      return <LocationIcon />
    default:
      return <InfoIcon />
  }
}

// Quality badge component
const QualityBadge = ({ quality, score }: { quality: string; score: number }) => {
  const colors: Record<string, string> = {
    excellent: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    good: 'bg-blue-100 text-blue-700 border-blue-200',
    fair: 'bg-amber-100 text-amber-700 border-amber-200',
    poor: 'bg-gray-100 text-gray-600 border-gray-200'
  }
  
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${colors[quality] || colors.good}`}>
      {Math.round(score * 100)}% {quality}
    </span>
  )
}

// =============================================================================
// TEMPLATE COMPONENTS
// =============================================================================

/**
 * Profile Card Template
 * Best for: Personal pages, freelancer profiles, team members
 */
const ProfileTemplate = ({ preview }: { preview: DemoPreviewResponse }) => {
  const { blueprint, primary_image_base64, screenshot_url, composited_preview_image_url, title, subtitle, description, tags, context_items, credibility_items } = preview

  // UNIFIED IMAGE SOURCE: Always use composited_preview_image_url as primary source
  // Priority: Composited Preview Image > AI-extracted image > Screenshot
  const [imageError, setImageError] = useState(false)
  const profileImageUrl = composited_preview_image_url || 
    (primary_image_base64 ? `data:image/png;base64,${primary_image_base64}` : screenshot_url)
  
  const handleImageError = () => {
    setImageError(true)
  }
  
  return (
    <div className="relative overflow-hidden rounded-2xl bg-white shadow-xl">
      {/* Gradient header */}
      <div 
        className="h-28 relative"
        style={{ 
          background: `linear-gradient(135deg, ${blueprint.primary_color}, ${blueprint.secondary_color})` 
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/10" />
        {/* Subtle pattern overlay */}
        <div 
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: `radial-gradient(circle at 25px 25px, white 2%, transparent 0%)`,
            backgroundSize: '50px 50px'
          }}
        />
      </div>
      
      {/* Content section */}
      <div className="relative px-6 pb-6">
        {/* Profile image */}
        <div className="flex justify-center -mt-16 mb-4">
          {profileImageUrl && !imageError ? (
            <img 
              src={profileImageUrl}
              alt={title}
              className="w-28 h-28 rounded-full border-4 border-white shadow-lg object-cover ring-4 ring-white/50"
              onError={handleImageError}
            />
          ) : (
            <div 
              className="w-28 h-28 rounded-full border-4 border-white shadow-lg flex items-center justify-center text-4xl font-bold text-white ring-4 ring-white/50"
              style={{ backgroundColor: blueprint.primary_color }}
            >
              {title.charAt(0).toUpperCase()}
            </div>
          )}
        </div>
        
        {/* Name */}
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-1">
          {title}
        </h2>
        
        {/* Subtitle/role */}
        {subtitle && (
          <p className="text-gray-600 text-center text-sm mb-3">
            {subtitle}
          </p>
        )}
        
        {/* Context items (location, etc.) */}
        {context_items.length > 0 && (
          <div className="flex items-center justify-center gap-4 text-gray-700 text-sm mb-4 font-medium">
            {context_items.map((item, i) => (
              <div key={i} className="flex items-center gap-1">
                {getContextIcon(item.icon)}
                <span className="text-gray-700">{item.text}</span>
              </div>
            ))}
          </div>
        )}
        
        {/* Tags/skills */}
        {tags.length > 0 && (
          <div className="flex flex-wrap justify-center gap-2 mb-4">
            {tags.slice(0, 4).map((tag, i) => (
              <span 
                key={i}
                className="px-3 py-1 rounded-full text-xs font-medium transition-colors hover:opacity-80"
                style={{ 
                  backgroundColor: `${blueprint.primary_color}15`,
                  color: blueprint.primary_color
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        )}
        
        {/* Description */}
        {description && (
          <div className="border-t border-gray-100 pt-4 mt-2">
            <p className="text-gray-700 text-sm leading-relaxed text-center line-clamp-3">
              {description}
            </p>
          </div>
        )}
        
        {/* Credibility items */}
        {credibility_items.length > 0 && (
          <div className="flex items-center justify-center gap-4 mt-4 pt-4 border-t border-gray-100">
            {credibility_items.map((item, i) => (
              <div key={i} className="flex items-center gap-1 text-sm">
                {item.type.includes('rating') && <StarIcon filled />}
                <span className="text-gray-700 font-medium">{item.value}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Product Card Template
 * Best for: E-commerce, SaaS products, services
 */
const ProductTemplate = ({ preview }: { preview: DemoPreviewResponse }) => {
  const { blueprint, primary_image_base64, screenshot_url, composited_preview_image_url, title, subtitle, description, tags, cta_text, credibility_items } = preview

  // UNIFIED IMAGE SOURCE: Always use composited_preview_image_url as primary source
  // Priority: Composited Preview Image > AI-extracted image > Screenshot
  const [imageError, setImageError] = useState(false)
  const productImageUrl = composited_preview_image_url || 
    (primary_image_base64 ? `data:image/png;base64,${primary_image_base64}` : screenshot_url)
  
  const handleImageError = () => {
    setImageError(true)
  }
  
  return (
    <div className="relative overflow-hidden rounded-2xl bg-white shadow-xl">
      {/* Product image */}
      {productImageUrl && !imageError ? (
        <div className="aspect-[16/9] overflow-hidden bg-gray-100">
          <img 
            src={productImageUrl}
            alt={title}
            className="w-full h-full object-cover"
            onError={handleImageError}
          />
        </div>
      ) : (
        <div 
          className="aspect-[16/9] flex items-center justify-center"
          style={{ 
            background: `linear-gradient(135deg, ${blueprint.primary_color}20, ${blueprint.secondary_color}20)` 
          }}
        >
          <span className="text-6xl opacity-30">📦</span>
        </div>
      )}
      
      {/* Content */}
      <div className="p-6">
        {/* Category tags */}
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {tags.slice(0, 2).map((tag, i) => (
              <span 
                key={i}
                className="px-2 py-0.5 rounded text-xs font-medium uppercase tracking-wide"
                style={{ 
                  backgroundColor: `${blueprint.primary_color}15`,
                  color: blueprint.primary_color
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        )}
        
        {/* Title */}
        <h2 className="text-xl font-bold text-gray-900 mb-2 line-clamp-2">
          {title}
        </h2>
        
        {/* Subtitle */}
        {subtitle && (
          <p className="text-gray-600 text-sm mb-3">
            {subtitle}
          </p>
        )}
        
        {/* Description */}
        {description && (
          <p className="text-gray-600 text-sm leading-relaxed mb-4 line-clamp-2">
            {description}
          </p>
        )}
        
        {/* Price/credibility and CTA row */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          {credibility_items.length > 0 ? (
            <div className="flex items-center gap-1">
              {credibility_items[0].type.includes('price') ? (
                <span className="text-xl font-bold" style={{ color: blueprint.primary_color }}>
                  {credibility_items[0].value}
                </span>
              ) : (
                <>
                  <StarIcon filled />
                  <span className="text-sm font-medium text-gray-700">{credibility_items[0].value}</span>
                </>
              )}
            </div>
          ) : (
            <div />
          )}
          
          {cta_text && (
            <button 
              className="px-4 py-2 rounded-lg text-white text-sm font-medium transition-all hover:opacity-90 hover:shadow-md"
              style={{ backgroundColor: blueprint.accent_color || blueprint.primary_color }}
            >
              {cta_text}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

/**
 * Landing/Hero Template
 * Best for: Landing pages, homepages, promotional content
 */
const LandingTemplate = ({ preview }: { preview: DemoPreviewResponse }) => {
  const { blueprint, primary_image_base64, screenshot_url, composited_preview_image_url, title, subtitle, description, cta_text, tags } = preview

  // UNIFIED IMAGE SOURCE: Always use composited_preview_image_url as primary source
  // Priority: Composited Preview Image > Screenshot > AI-extracted image
  const [imageError, setImageError] = useState(false)
  const imageUrl = composited_preview_image_url || screenshot_url || 
    (primary_image_base64 ? `data:image/png;base64,${primary_image_base64}` : null)
  
  const handleImageError = () => {
    setImageError(true)
  }

  // DEBUG: Log image source selection for LandingTemplate (only when image URL changes)
  const imageUrlRef = useRef<string | null>(null)
  useEffect(() => {
    if (imageUrl !== imageUrlRef.current) {
      console.log('[LandingTemplate] Image source selection:', {
        primary_image_base64: primary_image_base64 ? 'present (base64)' : 'null',
        screenshot_url: screenshot_url || 'null',
        selected_imageUrl: imageUrl || 'null',
        using: screenshot_url ? 'screenshot' : primary_image_base64 ? 'primary_base64' : 'none'
      })
      imageUrlRef.current = imageUrl
    }
  }, [imageUrl, primary_image_base64, screenshot_url])
  
  return (
    <div 
      className="relative overflow-hidden rounded-2xl shadow-xl min-h-[300px]"
      style={{ 
        background: imageUrl 
          ? `linear-gradient(135deg, ${blueprint.primary_color}, ${blueprint.secondary_color})` 
          : `linear-gradient(135deg, ${blueprint.primary_color}, ${blueprint.secondary_color})` 
      }}
    >
      {/* Background image with overlay - using composited_preview_image_url */}
      {imageUrl && !imageError && (
        <div className="absolute inset-0">
          <img 
            src={imageUrl}
            alt={title}
            className="w-full h-full object-cover opacity-20"
            onLoad={() => {
              console.log('[LandingTemplate] Background image loaded successfully:', imageUrl)
            }}
            onError={(e) => {
              console.error('[LandingTemplate] Background image failed to load:', imageUrl, e)
              handleImageError()
            }}
          />
          <div className="absolute inset-0 bg-gradient-to-r from-black/60 to-transparent" />
        </div>
      )}
      
      {/* Content */}
      <div className="relative p-8 flex flex-col justify-center min-h-[300px]">
        {/* Tags */}
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {tags.slice(0, 2).map((tag, i) => (
              <span 
                key={i}
                className="px-2 py-0.5 rounded text-xs font-medium uppercase tracking-wide bg-white/20 text-white/90"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
        
        {/* Title */}
        <h2 className="text-3xl font-bold text-white mb-3 max-w-lg">
          {title}
        </h2>
        
        {/* Subtitle */}
        {subtitle && (
          <p className="text-white/90 text-lg mb-2 max-w-md">
            {subtitle}
          </p>
        )}
        
        {/* Description */}
        {description && (
          <p className="text-white/70 text-sm leading-relaxed mb-6 max-w-md line-clamp-2">
            {description}
          </p>
        )}
        
        {/* CTA */}
        {cta_text && (
          <div>
            <button 
              className="px-6 py-3 rounded-lg text-sm font-bold transition-all hover:opacity-90 hover:shadow-lg"
              style={{ 
                backgroundColor: blueprint.accent_color || '#ffffff',
                color: blueprint.primary_color
              }}
            >
              {cta_text}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Article Card Template
 * Best for: Blog posts, news, documentation
 */
const ArticleTemplate = ({ preview }: { preview: DemoPreviewResponse }) => {
  const { blueprint, primary_image_base64, screenshot_url, composited_preview_image_url, title, subtitle, description, tags, credibility_items } = preview

  // UNIFIED IMAGE SOURCE: Always use composited_preview_image_url as primary source
  // Priority: Composited Preview Image > AI-extracted image > Screenshot
  const [imageError, setImageError] = useState(false)
  const articleImageUrl = composited_preview_image_url || 
    (primary_image_base64 ? `data:image/png;base64,${primary_image_base64}` : screenshot_url)
  
  const handleImageError = () => {
    setImageError(true)
  }
  
  return (
    <div className="relative overflow-hidden rounded-2xl bg-white shadow-xl">
      {/* Article image */}
      {articleImageUrl && !imageError && (
        <div className="aspect-[2/1] overflow-hidden bg-gray-100">
          <img 
            src={articleImageUrl}
            alt={title}
            className="w-full h-full object-cover"
            onError={handleImageError}
          />
        </div>
      )}
      
      {/* Content */}
      <div className="p-6">
        {/* Category and meta */}
        <div className="flex items-center gap-3 mb-3">
          {tags.length > 0 && (
            <span 
              className="px-2 py-0.5 rounded text-xs font-medium uppercase tracking-wide"
              style={{ 
                backgroundColor: `${blueprint.primary_color}15`,
                color: blueprint.primary_color
              }}
            >
              {tags[0]}
            </span>
          )}
          {credibility_items.length > 0 && (
            <span className="text-xs text-gray-500">
              {credibility_items[0].value}
            </span>
          )}
        </div>
        
        {/* Title */}
        <h2 className="text-xl font-bold text-gray-900 mb-2 line-clamp-2">
          {title}
        </h2>
        
        {/* Description */}
        {(description || subtitle) && (
          <p className="text-gray-600 text-sm leading-relaxed line-clamp-3">
            {description || subtitle}
          </p>
        )}
      </div>
    </div>
  )
}

/**
 * Service Card Template
 * Best for: Service pages, portfolios, case studies
 */
const ServiceTemplate = ({ preview }: { preview: DemoPreviewResponse }) => {
  const { blueprint, primary_image_base64, screenshot_url, composited_preview_image_url, title, subtitle, description, tags, cta_text, context_items } = preview

  // UNIFIED IMAGE SOURCE: Always use composited_preview_image_url as primary source
  // Priority: Composited Preview Image > AI-extracted image > Screenshot
  const [imageError, setImageError] = useState(false)
  const serviceImageUrl = composited_preview_image_url || 
    (primary_image_base64 ? `data:image/png;base64,${primary_image_base64}` : screenshot_url)
  
  const handleImageError = () => {
    setImageError(true)
  }
  
  return (
    <div className="relative overflow-hidden rounded-2xl bg-white shadow-xl">
      {/* Top accent bar */}
      <div 
        className="h-2"
        style={{ backgroundColor: blueprint.primary_color }}
      />
      
      <div className="p-6">
        {/* Icon or image */}
        <div className="mb-4">
          {serviceImageUrl && !imageError ? (
            <img 
              src={serviceImageUrl}
              alt={title}
              className="w-16 h-16 rounded-xl object-cover shadow-md"
              onError={handleImageError}
            />
          ) : (
            <div 
              className="w-16 h-16 rounded-xl flex items-center justify-center text-2xl shadow-md"
              style={{ 
                backgroundColor: `${blueprint.primary_color}15`,
                color: blueprint.primary_color
              }}
            >
              ✨
            </div>
          )}
        </div>
        
        {/* Title */}
        <h2 className="text-xl font-bold text-gray-900 mb-2">
          {title}
        </h2>
        
        {/* Subtitle */}
        {subtitle && (
          <p className="text-gray-600 text-sm mb-3">
            {subtitle}
          </p>
        )}
        
        {/* Description */}
        {description && (
          <p className="text-gray-600 text-sm leading-relaxed mb-4 line-clamp-3">
            {description}
          </p>
        )}
        
        {/* Tags as features */}
        {tags.length > 0 && (
          <div className="space-y-2 mb-4">
            {tags.slice(0, 3).map((tag, i) => (
              <div key={i} className="flex items-center gap-2 text-sm text-gray-700">
                <svg 
                  className="w-4 h-4 flex-shrink-0" 
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke={blueprint.primary_color}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>{tag}</span>
              </div>
            ))}
          </div>
        )}
        
        {/* Context items */}
        {context_items.length > 0 && (
          <div className="flex items-center gap-4 text-xs text-gray-500 mb-4 pt-4 border-t border-gray-100">
            {context_items.map((item, i) => (
              <div key={i} className="flex items-center gap-1">
                {getContextIcon(item.icon)}
                <span>{item.text}</span>
              </div>
            ))}
          </div>
        )}
        
        {/* CTA */}
        {cta_text && (
          <button 
            className="w-full px-4 py-2.5 rounded-lg text-white text-sm font-medium transition-all hover:opacity-90 hover:shadow-md"
            style={{ backgroundColor: blueprint.primary_color }}
          >
            {cta_text}
          </button>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function ReconstructedPreview({ preview, className = '' }: ReconstructedPreviewProps) {
  const { blueprint, screenshot_url, primary_image_base64 } = preview

  // DEBUG: Log template selection and image data (only once per preview change)
  const previewIdRef = useRef<string | null>(null)
  useEffect(() => {
    const currentId = `${blueprint.template_type}-${screenshot_url || 'no-screenshot'}-${preview.title}`
    if (currentId !== previewIdRef.current) {
      console.log('[ReconstructedPreview] Rendering:', {
        template_type: blueprint.template_type,
        screenshot_url: screenshot_url || 'null',
        primary_image_base64: primary_image_base64 ? 'present (base64)' : 'null',
        title: preview.title,
        note: 'UI card uses raw images, NOT composited_preview_image_url (which is for og:image only)'
      })
      previewIdRef.current = currentId
    }
  }, [blueprint.template_type, screenshot_url, primary_image_base64, preview.title])
  
  // Select template based on type
  // Maps AI page types to visual templates
  // NEW: Uses AdaptivePreview when Design DNA is available for intelligent styling
  const renderTemplate = () => {
    const templateType = (blueprint.template_type || '').toLowerCase()
    
    // NEW: If Design DNA is available and confidence is high, use AdaptivePreview
    // This creates previews that honor the original design's personality
    if (preview.design_dna && preview.design_fidelity_score && preview.design_fidelity_score > 0.5) {
      console.log('[ReconstructedPreview] Using AdaptivePreview with Design DNA:', {
        style: preview.design_dna.style,
        typography: preview.design_dna.typography_personality,
        fidelity: preview.design_fidelity_score
      })
      return <AdaptivePreview preview={preview} />
    }
    
    // Fallback to fixed templates when Design DNA is not available
    
    // Profile template: personal pages, freelancers, team members
    if (templateType === 'profile' || templateType === 'personal') {
      return <ProfileTemplate preview={preview} />
    }
    
    // Product template: e-commerce, products, marketplaces
    if (templateType === 'product' || templateType === 'ecommerce' || templateType === 'marketplace') {
      return <ProductTemplate preview={preview} />
    }
    
    // Article template: blog posts, news, documentation
    if (templateType === 'article' || templateType === 'blog' || templateType === 'news' || templateType === 'documentation') {
      return <ArticleTemplate preview={preview} />
    }
    
    // Service template: agencies, portfolios, services
    if (templateType === 'service' || templateType === 'agency' || templateType === 'portfolio') {
      return <ServiceTemplate preview={preview} />
    }
    
    // Landing template: SaaS, startups, landing pages, homepages, tools, enterprise
    // This is the DEFAULT for business/company pages (most common)
    if (templateType === 'landing' || 
        templateType === 'saas' || 
        templateType === 'startup' || 
        templateType === 'enterprise' || 
        templateType === 'tool' ||
        templateType === 'company') {
      return <LandingTemplate preview={preview} />
    }
    
    // DEFAULT: Use Landing template for unknown types
    // Landing is the most versatile and professional-looking
    // (was incorrectly defaulting to Profile before!)
    return <LandingTemplate preview={preview} />
  }
  
  return (
    <div className={`relative group ${className}`}>
      {/* Glow effect on hover */}
      <div 
        className="absolute -inset-1 rounded-3xl opacity-0 group-hover:opacity-30 blur-xl transition-opacity duration-500"
        style={{ 
          background: `linear-gradient(135deg, ${blueprint.primary_color}, ${blueprint.accent_color || blueprint.secondary_color})` 
        }}
      />
      
      {/* Main content */}
      <div className="relative">
        {renderTemplate()}
      </div>
      
      {/* Quality indicator (subtle) */}
      <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col gap-1 items-end">
        <QualityBadge quality={blueprint.overall_quality} score={blueprint.coherence_score} />
        {/* Design fidelity badge when available */}
        {preview.design_fidelity_score !== undefined && preview.design_fidelity_score > 0 && (
          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${
            preview.design_fidelity_score >= 0.8 ? 'bg-violet-100 text-violet-700 border-violet-200' :
            preview.design_fidelity_score >= 0.6 ? 'bg-indigo-100 text-indigo-700 border-indigo-200' :
            'bg-gray-100 text-gray-600 border-gray-200'
          }`}>
            🧬 {Math.round(preview.design_fidelity_score * 100)}% fidelity
          </span>
        )}
      </div>
    </div>
  )
}
