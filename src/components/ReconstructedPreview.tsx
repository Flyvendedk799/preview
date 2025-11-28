/**
 * ReconstructedPreview Component
 * 
 * Renders a semantically reconstructed preview based on extracted UI elements
 * and an AI-generated layout plan. This creates a purposefully designed preview
 * rather than just displaying a cropped screenshot.
 * 
 * The component:
 * - Uses extracted images, text, and layout instructions
 * - Renders a clean, modern preview card
 * - Adapts to different page types (profile, product, landing, etc.)
 * - Falls back gracefully when data is incomplete
 */

import { DemoPreviewResponse, ExtractedElement, LayoutPlan } from '../api/client'

interface ReconstructedPreviewProps {
  preview: DemoPreviewResponse
  className?: string
}

// Template-specific renderers
const ProfileCardTemplate = ({ preview }: { preview: DemoPreviewResponse }) => {
  const { layout_plan, elements, profile_image_base64, hero_image_base64 } = preview
  
  // Find relevant elements
  const nameElement = elements.find(e => e.type === 'headline' && e.include_in_preview)
  const titleElement = elements.find(e => e.type === 'subheadline' && e.include_in_preview)
  const locationElement = elements.find(e => e.type === 'location' && e.include_in_preview)
  const skillElements = elements.filter(e => e.type === 'skill_tag' && e.include_in_preview).slice(0, 4)
  const ratingElement = elements.find(e => e.type === 'rating' && e.include_in_preview)
  
  const profileImage = profile_image_base64 || hero_image_base64
  
  return (
    <div 
      className="rounded-2xl overflow-hidden shadow-2xl"
      style={{ 
        background: `linear-gradient(135deg, ${layout_plan.primary_color}15, ${layout_plan.secondary_color}10)`,
        borderColor: layout_plan.primary_color + '30'
      }}
    >
      {/* Header with gradient */}
      <div 
        className="h-24 relative"
        style={{ 
          background: `linear-gradient(135deg, ${layout_plan.primary_color}, ${layout_plan.secondary_color})`
        }}
      >
        <div className="absolute inset-0 bg-black/10" />
      </div>
      
      {/* Profile section */}
      <div className="px-6 pb-6 -mt-12 relative">
        {/* Profile image */}
        <div className="flex justify-center mb-4">
          {profileImage ? (
            <img 
              src={`data:image/png;base64,${profileImage}`}
              alt="Profile"
              className="w-24 h-24 rounded-full border-4 border-white shadow-lg object-cover"
            />
          ) : (
            <div 
              className="w-24 h-24 rounded-full border-4 border-white shadow-lg flex items-center justify-center text-3xl font-bold text-white"
              style={{ backgroundColor: layout_plan.primary_color }}
            >
              {(layout_plan.title || 'P')[0].toUpperCase()}
            </div>
          )}
        </div>
        
        {/* Name and title */}
        <div className="text-center mb-4">
          <h3 className="text-xl font-bold text-gray-900 mb-1">
            {nameElement?.text_content || layout_plan.title || 'Profile'}
          </h3>
          {(titleElement?.text_content || layout_plan.subtitle) && (
            <p className="text-gray-600 text-sm">
              {titleElement?.text_content || layout_plan.subtitle}
            </p>
          )}
        </div>
        
        {/* Location */}
        {locationElement?.text_content && (
          <div className="flex items-center justify-center text-gray-500 text-sm mb-4">
            <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            {locationElement.text_content}
          </div>
        )}
        
        {/* Skills/Tags */}
        {skillElements.length > 0 && (
          <div className="flex flex-wrap justify-center gap-2 mb-4">
            {skillElements.map((skill, i) => (
              <span 
                key={i}
                className="px-3 py-1 rounded-full text-xs font-medium"
                style={{ 
                  backgroundColor: layout_plan.primary_color + '15',
                  color: layout_plan.primary_color
                }}
              >
                {skill.text_content || skill.content}
              </span>
            ))}
          </div>
        )}
        
        {/* Rating */}
        {ratingElement?.text_content && (
          <div className="flex items-center justify-center text-amber-500">
            <svg className="w-5 h-5 fill-current" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            <span className="ml-1 text-sm font-semibold text-gray-700">
              {ratingElement.text_content}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

const ProductCardTemplate = ({ preview }: { preview: DemoPreviewResponse }) => {
  const { layout_plan, elements, hero_image_base64, profile_image_base64 } = preview
  
  const productImage = hero_image_base64 || profile_image_base64
  const priceElement = elements.find(e => e.type === 'price' && e.include_in_preview)
  const ctaElement = elements.find(e => e.type === 'cta_button' && e.include_in_preview)
  const featureElements = elements.filter(e => e.type === 'feature_item' && e.include_in_preview).slice(0, 3)
  
  return (
    <div className="rounded-2xl overflow-hidden shadow-2xl bg-white">
      {/* Product image */}
      <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 relative overflow-hidden">
        {productImage ? (
          <img 
            src={`data:image/png;base64,${productImage}`}
            alt="Product"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <svg className="w-16 h-16 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        )}
      </div>
      
      {/* Content */}
      <div className="p-5">
        <h3 className="text-lg font-bold text-gray-900 mb-2 line-clamp-2">
          {layout_plan.title || 'Product'}
        </h3>
        
        {layout_plan.description && (
          <p className="text-gray-600 text-sm mb-3 line-clamp-2">
            {layout_plan.description}
          </p>
        )}
        
        {/* Features */}
        {featureElements.length > 0 && (
          <div className="space-y-1 mb-4">
            {featureElements.map((feature, i) => (
              <div key={i} className="flex items-center text-sm text-gray-600">
                <svg className="w-4 h-4 mr-2 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="line-clamp-1">{feature.text_content || feature.content}</span>
              </div>
            ))}
          </div>
        )}
        
        {/* Price and CTA */}
        <div className="flex items-center justify-between">
          {priceElement?.text_content && (
            <span className="text-xl font-bold" style={{ color: layout_plan.primary_color }}>
              {priceElement.text_content}
            </span>
          )}
          {(ctaElement?.text_content || layout_plan.cta_text) && (
            <button 
              className="px-4 py-2 rounded-lg text-white text-sm font-semibold transition-all hover:opacity-90"
              style={{ backgroundColor: layout_plan.accent_color || layout_plan.primary_color }}
            >
              {ctaElement?.text_content || layout_plan.cta_text}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

const LandingHeroTemplate = ({ preview }: { preview: DemoPreviewResponse }) => {
  const { layout_plan, elements, hero_image_base64, logo_base64 } = preview
  
  const ctaElement = elements.find(e => e.type === 'cta_button' && e.include_in_preview)
  
  return (
    <div 
      className="rounded-2xl overflow-hidden shadow-2xl relative min-h-[280px]"
      style={{ 
        background: hero_image_base64 
          ? undefined 
          : `linear-gradient(135deg, ${layout_plan.primary_color}, ${layout_plan.secondary_color})`
      }}
    >
      {/* Background image */}
      {hero_image_base64 && (
        <div className="absolute inset-0">
          <img 
            src={`data:image/png;base64,${hero_image_base64}`}
            alt="Hero"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/40 to-black/20" />
        </div>
      )}
      
      {/* Content overlay */}
      <div className="relative z-10 p-6 flex flex-col justify-end min-h-[280px]">
        {/* Logo */}
        {logo_base64 && (
          <div className="absolute top-4 left-4">
            <img 
              src={`data:image/png;base64,${logo_base64}`}
              alt="Logo"
              className="h-8 object-contain"
            />
          </div>
        )}
        
        {/* Text content */}
        <div className="mt-auto">
          <h3 className="text-2xl font-bold text-white mb-2 drop-shadow-lg">
            {layout_plan.title || 'Welcome'}
          </h3>
          
          {(layout_plan.subtitle || layout_plan.description) && (
            <p className="text-white/90 text-sm mb-4 line-clamp-2 drop-shadow">
              {layout_plan.subtitle || layout_plan.description}
            </p>
          )}
          
          {(ctaElement?.text_content || layout_plan.cta_text) && (
            <button 
              className="px-5 py-2.5 rounded-lg text-sm font-semibold transition-all hover:scale-105"
              style={{ 
                backgroundColor: layout_plan.accent_color || '#ffffff',
                color: layout_plan.accent_color ? '#ffffff' : layout_plan.primary_color
              }}
            >
              {ctaElement?.text_content || layout_plan.cta_text}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

const ArticleCardTemplate = ({ preview }: { preview: DemoPreviewResponse }) => {
  const { layout_plan, elements, hero_image_base64 } = preview
  
  const bodyTextElement = elements.find(e => e.type === 'body_text' && e.include_in_preview)
  
  return (
    <div className="rounded-2xl overflow-hidden shadow-2xl bg-white">
      {/* Article image */}
      {hero_image_base64 && (
        <div className="aspect-video overflow-hidden">
          <img 
            src={`data:image/png;base64,${hero_image_base64}`}
            alt="Article"
            className="w-full h-full object-cover"
          />
        </div>
      )}
      
      {/* Content */}
      <div className="p-5">
        <div className="flex items-center space-x-2 mb-3">
          <span 
            className="px-2 py-1 rounded text-xs font-semibold uppercase"
            style={{ 
              backgroundColor: layout_plan.primary_color + '15',
              color: layout_plan.primary_color
            }}
          >
            Article
          </span>
        </div>
        
        <h3 className="text-lg font-bold text-gray-900 mb-2 line-clamp-2">
          {layout_plan.title || 'Article'}
        </h3>
        
        {(bodyTextElement?.text_content || layout_plan.description) && (
          <p className="text-gray-600 text-sm line-clamp-3">
            {bodyTextElement?.text_content || layout_plan.description}
          </p>
        )}
      </div>
    </div>
  )
}

const MinimalTemplate = ({ preview }: { preview: DemoPreviewResponse }) => {
  const { layout_plan, hero_image_base64, profile_image_base64, screenshot_url } = preview
  
  const displayImage = hero_image_base64 || profile_image_base64
  
  return (
    <div className="rounded-2xl overflow-hidden shadow-2xl bg-white">
      {/* Image */}
      <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 relative overflow-hidden">
        {displayImage ? (
          <img 
            src={`data:image/png;base64,${displayImage}`}
            alt="Preview"
            className="w-full h-full object-cover"
          />
        ) : screenshot_url ? (
          <img 
            src={screenshot_url}
            alt="Screenshot"
            className="w-full h-full object-cover object-top"
          />
        ) : (
          <div 
            className="w-full h-full flex items-center justify-center"
            style={{ background: `linear-gradient(135deg, ${layout_plan.primary_color}30, ${layout_plan.secondary_color}20)` }}
          >
            <svg className="w-16 h-16 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
            </svg>
          </div>
        )}
      </div>
      
      {/* Content */}
      <div className="p-5">
        <h3 className="text-lg font-bold text-gray-900 mb-2 line-clamp-2">
          {layout_plan.title || 'Page Preview'}
        </h3>
        
        {(layout_plan.subtitle || layout_plan.description) && (
          <p className="text-gray-600 text-sm line-clamp-2">
            {layout_plan.subtitle || layout_plan.description}
          </p>
        )}
      </div>
    </div>
  )
}

// Main component that selects the appropriate template
export default function ReconstructedPreview({ preview, className = '' }: ReconstructedPreviewProps) {
  const { layout_plan } = preview
  
  // Select template based on layout plan
  const renderTemplate = () => {
    switch (layout_plan.template) {
      case 'profile_card':
        return <ProfileCardTemplate preview={preview} />
      case 'product_card':
        return <ProductCardTemplate preview={preview} />
      case 'landing_hero':
        return <LandingHeroTemplate preview={preview} />
      case 'article_card':
        return <ArticleCardTemplate preview={preview} />
      case 'service_card':
        // Service cards are similar to profile cards
        return <ProfileCardTemplate preview={preview} />
      case 'minimal':
      default:
        return <MinimalTemplate preview={preview} />
    }
  }
  
  return (
    <div className={`reconstructed-preview ${className}`}>
      {renderTemplate()}
    </div>
  )
}

// Export individual templates for flexibility
export {
  ProfileCardTemplate,
  ProductCardTemplate,
  LandingHeroTemplate,
  ArticleCardTemplate,
  MinimalTemplate
}

