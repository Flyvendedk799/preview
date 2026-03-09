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
    // Slack unfurl - 5px left border (brand color), site name bold, title as blue link
    if (isSlack) {
      return (
        <div className="px-3 py-2.5 bg-white">
          <div className="flex items-start gap-3">
            <div className="flex-1 min-w-0">
              <div className="text-[13px] text-gray-900 font-bold mb-0.5">
                {preview.brand?.brand_name || domain}
              </div>
              {platformData.title && platformData.title !== "Untitled" && (
                <h4 className="text-[13px] font-normal text-[#1264A3] leading-tight line-clamp-2 mb-1 hover:underline cursor-pointer">
                  {platformData.title}
                </h4>
              )}
              {platformData.description && platformData.description !== platformData.title && (
                <p className="text-[12px] text-gray-500 leading-snug line-clamp-2">
                  {platformData.description}
                </p>
              )}
            </div>
            {/* Thumbnail right-aligned */}
            {platformData.image && (
              <div className="w-[80px] h-[80px] rounded flex-shrink-0 overflow-hidden bg-gray-100">
                <img
                  src={platformData.image}
                  alt=""
                  className="w-full h-full object-cover"
                  onError={handleImageError}
                />
              </div>
            )}
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
          </div>
        </div>
      )
    }

    // X (Twitter) - 16px border-radius, domain overlay bottom-left, title below
    if (isTwitter) {
      return (
        <div className="px-3 py-2 bg-white">
          {platformData.title && platformData.title !== "Untitled" && (
            <h4 className="text-[15px] font-normal text-gray-900 leading-tight line-clamp-2">
              {platformData.title}
            </h4>
          )}
        </div>
      )
    }

    // LinkedIn - title 14px semibold single line, source 12px gray, subtle border
    if (isLinkedIn) {
      return (
        <div className="px-3 py-2.5 bg-white border-t border-gray-200">
          {platformData.title && platformData.title !== "Untitled" && (
            <h4 className="text-[14px] font-semibold text-gray-900 leading-tight line-clamp-1 mb-0.5">
              {platformData.title}
            </h4>
          )}
          <div className="text-[12px] text-gray-500">{domain}</div>
        </div>
      )
    }

    // Facebook - 1px gray border, domain in gray caps, title 16px bold max 2 lines, desc 14px max 1 line
    return (
      <div className="px-3 py-2.5" style={{ backgroundColor: '#F0F2F5' }}>
        <div className="text-[10px] text-gray-500 uppercase tracking-wider font-medium mb-1">
          {domain}
        </div>
        {platformData.title && platformData.title !== "Untitled" && (
          <h4 className="text-[16px] font-bold text-[#1C1E21] leading-tight line-clamp-2 mb-0.5">
            {platformData.title}
          </h4>
        )}
        {platformData.description && platformData.description !== platformData.title && (
          <p className="text-[14px] text-[#606770] leading-snug line-clamp-1">
            {platformData.description}
          </p>
        )}
      </div>
    )
  }

  // Determine card styling based on platform
  const cardClassName = useMemo(() => {
    if (isTwitter) {
      // Twitter: 16px border-radius
      return 'mx-3 mb-2 border border-gray-300 rounded-2xl overflow-hidden bg-white'
    }
    if (isSlack) {
      // Slack: 5px left border with brand color
      return 'mx-3 mb-2 border border-gray-200 rounded overflow-hidden bg-white'
    }
    if (isLinkedIn) {
      // LinkedIn: subtle border
      return 'mx-3 mb-2 border border-gray-300 rounded-lg overflow-hidden bg-white'
    }
    if (isFacebook) {
      // Facebook: 1px gray border, #F0F2F5 background
      return 'mx-3 mb-2 border border-gray-300 rounded-lg overflow-hidden'
    }
    return 'mx-3 mb-2 border border-gray-200 rounded-lg overflow-hidden bg-white'
  }, [isLinkedIn, isTwitter, isSlack, isInstagram, isFacebook])

  const cardStyle = useMemo(() => {
    if (isSlack) {
      return { borderLeftWidth: '5px', borderLeftColor: preview.blueprint.primary_color }
    }
    return {}
  }, [isSlack, preview.blueprint.primary_color])

  // Image section - not shown for Slack (Slack shows thumbnail in content)
  const renderImage = () => {
    if (isSlack) return null

    return (
      <div
        className="bg-gray-200 overflow-hidden relative"
        style={{ aspectRatio: platform.aspectRatio }}
        role="img"
        aria-label={`Preview image for ${platformData.title}`}
      >
        {platformData.image ? (
          <>
            <img
              src={platformData.image}
              alt={platformData.title}
              className="w-full h-full object-cover relative z-0"
              onError={handleImageError}
              loading="lazy"
            />
            {/* Twitter: domain overlay bottom-left with dark scrim */}
            {isTwitter && (
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-2 z-10">
                <span className="text-[13px] text-white/90 font-normal">{domain}</span>
              </div>
            )}
          </>
        ) : (
          <div
            className="w-full h-full relative"
            style={{
              background: `linear-gradient(135deg, ${preview.blueprint.primary_color}, ${preview.blueprint.secondary_color})`,
            }}
          >
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 px-4">
              {preview.brand?.logo_base64 ? (
                <div className="w-20 h-20 rounded-2xl bg-white/15 backdrop-blur-sm flex items-center justify-center p-2 shadow-lg">
                  <img
                    src={`data:image/png;base64,${preview.brand.logo_base64}`}
                    alt={preview.brand.brand_name || ''}
                    className="max-w-full max-h-full object-contain"
                    onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                  />
                </div>
              ) : (
                <div className="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center shadow-lg">
                  <span className="text-2xl font-black text-white">
                    {(preview.brand?.brand_name || platformData.title || 'M').charAt(0).toUpperCase()}
                  </span>
                </div>
              )}
              <p className="text-sm text-white/90 font-semibold text-center line-clamp-2 drop-shadow">
                {preview.brand?.brand_name || platformData.title}
              </p>
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className={cardClassName} style={cardStyle}>
      {renderImage()}
      {renderPlatformContent()}
    </div>
  )
})

PlatformPreviewCard.displayName = 'PlatformPreviewCard'

export default PlatformPreviewCard

