/**
 * PlatformPreviewCard Component
 * 
 * Renders platform-specific social media preview cards with realistic layouts.
 * Each platform (Facebook, X/Twitter, LinkedIn, Slack, Instagram) has its own
 * distinct styling and layout conventions.
 */
import React, { memo, useMemo } from 'react'
import type { DemoPreviewResponseV2 } from '../api/client'

interface PlatformConfig {
  id: string
  name: string
  color: string
  icon: string
  aspectRatio: string
  maxTitleLength: number
  maxDescLength: number
}

interface PlatformPreviewCardProps {
  preview: DemoPreviewResponseV2
  platform: PlatformConfig
  onImageError?: (error: Error) => void
}

const PlatformPreviewCard: React.FC<PlatformPreviewCardProps> = memo(({ 
  preview, 
  platform,
  onImageError 
}) => {
  // Memoize platform-specific data
  const platformData = useMemo(() => {
    const truncate = (text: string, maxLength: number): string => {
      if (!text) return ''
      if (text.length <= maxLength) return text
      return text.substring(0, maxLength - 3) + '...'
    }

    // UNIFIED IMAGE SOURCE: Always use composited_preview_image_url as primary source
    // This ensures consistency with ReconstructedPreview component
    const imageUrl = preview.composited_preview_image_url || preview.screenshot_url || null
    
    return {
      image: imageUrl,
      title: truncate(preview.title || 'Untitled', platform.maxTitleLength),
      description: truncate(preview.description || '', platform.maxDescLength),
      url: preview.url,
    }
  }, [preview, platform])

  // Extract domain from URL
  const domain = useMemo(() => {
    try {
      return new URL(preview.url).hostname.replace('www.', '')
    } catch {
      return 'website.com'
    }
  }, [preview.url])

  // Platform-specific flags
  const isLinkedIn = platform.id === 'linkedin'
  const isTwitter = platform.id === 'twitter'
  const isSlack = platform.id === 'slack'
  const isInstagram = platform.id === 'instagram'
  const isFacebook = platform.id === 'facebook'

  // Handle image load error
  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const target = e.target as HTMLImageElement
    target.style.display = 'none'
    const parent = target.parentElement
    if (parent) {
      parent.style.background = `linear-gradient(135deg, ${preview.blueprint.primary_color}, ${preview.blueprint.secondary_color})`
    }
    if (onImageError) {
      onImageError(new Error(`Failed to load image: ${platformData.image}`))
    }
  }

  // Render platform-specific content
  const renderPlatformContent = () => {
    // Slack - message-style embed
    if (isSlack) {
      return (
        <div className="px-3 py-2.5 bg-white">
          <div className="flex items-start space-x-2">
            <div 
              className="w-4 h-4 rounded mt-0.5 flex-shrink-0" 
              style={{ backgroundColor: preview.blueprint.primary_color }}
              aria-hidden="true"
            />
            <div className="flex-1 min-w-0">
              <div className="text-[11px] text-gray-500 font-medium mb-1">{domain}</div>
              {platformData.title && platformData.title !== "Untitled" && (
                <h4 className="text-[13px] font-semibold text-gray-900 leading-tight line-clamp-2 mb-1">
                  {platformData.title}
                </h4>
              )}
              {platformData.description && platformData.description !== platformData.title && (
                <p className="text-[12px] text-gray-600 leading-snug line-clamp-2">
                  {platformData.description}
                </p>
              )}
              <div className="mt-1.5 text-[11px] text-gray-400 flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                <span>Tap to open site →</span>
              </div>
            </div>
          </div>
        </div>
      )
    }

    // Instagram - image-first, minimal text
    if (isInstagram) {
      return (
        <div className="px-3 py-2 bg-white">
          {platformData.title && platformData.title !== "Untitled" && (
            <h4 className="text-[13px] font-semibold text-gray-900 leading-tight line-clamp-1 mb-1">
              {platformData.title}
            </h4>
          )}
          <div className="text-[11px] text-gray-500 flex items-center gap-1">
            <span>{domain}</span>
            <span aria-hidden="true">·</span>
            <span className="text-gray-400">Tap to open →</span>
          </div>
        </div>
      )
    }

    // X (Twitter) - minimal, clean design
    if (isTwitter) {
      return (
        <div className="px-3 py-2.5 bg-white">
          <div className="text-[11px] text-gray-500 font-medium mb-1.5">{domain}</div>
          {platformData.title && platformData.title !== "Untitled" && (
            <h4 className="text-[15px] font-bold text-gray-900 leading-tight line-clamp-2 mb-1.5">
              {platformData.title}
            </h4>
          )}
          {platformData.description && platformData.description !== platformData.title && (
            <p className="text-[13px] text-gray-700 leading-snug line-clamp-2 mb-1.5">
              {platformData.description}
            </p>
          )}
          <div className="text-[11px] text-gray-400 flex items-center gap-1">
            <span>Tap to open site →</span>
          </div>
        </div>
      )
    }

    // LinkedIn - professional, larger text
    if (isLinkedIn) {
      return (
        <div className="px-3 py-3 bg-white border-t border-gray-100">
          <div className="text-[11px] text-gray-500 font-medium mb-1.5">{domain}</div>
          {platformData.title && platformData.title !== "Untitled" && (
            <h4 className="text-[14px] font-semibold text-gray-900 leading-tight line-clamp-2 mb-1.5">
              {platformData.title}
            </h4>
          )}
          {platformData.description && platformData.description !== platformData.title && (
            <p className="text-[12px] text-gray-700 leading-relaxed line-clamp-2">
              {platformData.description}
            </p>
          )}
        </div>
      )
    }

    // Facebook - default layout
    return (
      <div className="px-3 py-2 bg-gray-50">
        <div className="text-[10px] text-gray-500 uppercase tracking-wide font-medium mb-1">
          {domain}
        </div>
        {platformData.title && platformData.title !== "Untitled" && (
          <h4 className="text-[13px] font-semibold text-gray-900 leading-tight line-clamp-2 mb-0.5">
            {platformData.title}
          </h4>
        )}
        {platformData.description && platformData.description !== platformData.title && (
          <p className="text-[11px] text-gray-600 leading-snug line-clamp-1">
            {platformData.description}
          </p>
        )}
      </div>
    )
  }

  // Determine card styling based on platform
  const cardClassName = useMemo(() => {
    const base = 'mx-3 mb-2 border border-gray-200 rounded-lg overflow-hidden'
    if (isLinkedIn || isTwitter || isInstagram) {
      return `${base} bg-white`
    }
    if (isSlack) {
      return `${base} bg-white border-l-4`
    }
    return `${base} bg-gray-50`
  }, [isLinkedIn, isTwitter, isSlack, isInstagram])

  const cardStyle = useMemo(() => {
    if (isSlack) {
      return { borderLeftColor: preview.blueprint.primary_color }
    }
    return {}
  }, [isSlack, preview.blueprint.primary_color])

  return (
    <div className={cardClassName} style={cardStyle}>
      {/* Preview Image */}
      <div 
        className="bg-gray-200 overflow-hidden relative"
        style={{ aspectRatio: platform.aspectRatio }}
        role="img"
        aria-label={`Preview image for ${platformData.title}`}
      >
        {/* Gradient overlay for text readability */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent pointer-events-none z-10" aria-hidden="true" />
        
        {platformData.image ? (
          <img
            src={platformData.image}
            alt={platformData.title}
            className="w-full h-full object-cover relative z-0"
            onError={handleImageError}
            loading="lazy"
          />
        ) : (
          <div 
            className="w-full h-full relative"
            style={{ 
              background: `linear-gradient(135deg, ${preview.blueprint.primary_color}, ${preview.blueprint.secondary_color})`
            }}
          >
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 mx-auto mb-2 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center">
                  <svg className="w-8 h-8 text-white/70" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <p className="text-xs text-white/80 font-medium">{platformData.title}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Platform-specific content */}
      {renderPlatformContent()}
    </div>
  )
})

PlatformPreviewCard.displayName = 'PlatformPreviewCard'

export default PlatformPreviewCard

