/**
 * Unified PreviewData model for all platform previews.
 * 
 * This ensures consistency across all platforms - Facebook, X, LinkedIn, etc.
 * Platform components only adapt rendering, never change the underlying data.
 */

export interface PreviewData {
  // Core preview content
  image: string | undefined  // og:image URL
  title: string
  description: string | undefined
  url: string
  
  // Brand metadata
  brand: {
    name: string | undefined
    logo: string | undefined  // Base64 logo
    colors: {
      primary: string
      secondary: string
      accent: string
    }
  }
  
  // Optional metadata
  domain?: string
  favicon?: string
}

/**
 * Platform-specific rendering configuration.
 * These adapt how PreviewData is displayed, but never change the data itself.
 */
export interface PlatformConfig {
  id: string
  name: string
  aspectRatio: string  // CSS aspect-ratio value
  maxTitleLength: number
  maxDescLength: number
  truncationStyle: 'ellipsis' | 'word-break'
  imageStyle: 'cover' | 'contain' | 'fill'
}

/**
 * Convert API response to unified PreviewData model.
 */
export function toPreviewData(apiResponse: any): PreviewData {
  return {
    image: apiResponse.composited_preview_image_url || apiResponse.screenshot_url || undefined,
    title: apiResponse.title || 'Untitled',
    description: apiResponse.description || undefined,
    url: apiResponse.url,
    brand: {
      name: apiResponse.brand?.brand_name || undefined,
      logo: apiResponse.brand?.logo_base64 || undefined,
      colors: {
        primary: apiResponse.blueprint?.primary_color || '#3B82F6',
        secondary: apiResponse.blueprint?.secondary_color || '#1E293B',
        accent: apiResponse.blueprint?.accent_color || '#F59E0B',
      }
    },
    domain: (() => {
      try {
        return new URL(apiResponse.url).hostname.replace('www.', '')
      } catch {
        return undefined
      }
    })(),
  }
}

