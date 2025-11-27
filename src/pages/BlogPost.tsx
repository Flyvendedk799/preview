import { useState, useEffect } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import {
  CalendarIcon,
  ClockIcon,
  EyeIcon,
  TagIcon,
  ArrowLeftIcon,
  ShareIcon,
  BookmarkIcon,
  ChevronRightIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'
import {
  fetchBlogPostBySlug,
  fetchRecentBlogPosts,
  fetchBlogCategories,
  type BlogPost as BlogPostType,
  type BlogPostListItem,
  type BlogCategory,
} from '../api/client'

// Smart content renderer that auto-detects formatting
function renderContent(content: string): JSX.Element {
  // Process inline formatting
  const processInline = (text: string): string => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
      .replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 bg-orange-50 text-orange-600 rounded text-[0.9em] font-mono border border-orange-100">$1</code>')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-orange-600 hover:text-orange-700 underline decoration-orange-300 underline-offset-2 transition-colors font-medium" target="_blank" rel="noopener noreferrer">$1</a>')
  }

  // Helper to detect if a line looks like a heading
  const isLikelyHeading = (text: string): boolean => {
    const trimmed = text.trim()
    // Short text, no period at end, starts with capital
    if (trimmed.length < 80 && !trimmed.endsWith('.') && /^[A-Z]/.test(trimmed)) {
      // Contains = or : which often indicates a key concept
      if (trimmed.includes('=') || (trimmed.includes(':') && trimmed.indexOf(':') < 30)) return true
      // Title case or all caps
      const words = trimmed.split(' ')
      if (words.length <= 8 && words.every(w => /^[A-Z]/.test(w) || w.length <= 3)) return true
    }
    return false
  }

  // Helper to detect key statement / pull quote style text
  const isKeyStatement = (text: string): boolean => {
    const trimmed = text.trim()
    // Short, punchy statement with no period, or ends with specific punctuation
    if (trimmed.length < 60 && trimmed.length > 10) {
      if (!trimmed.endsWith('.') || trimmed.includes('→') || trimmed.includes('—')) return true
      // Starts with "The" and is short - often a key point
      if (trimmed.startsWith('The ') && trimmed.split(' ').length <= 8) return true
    }
    return false
  }

  // Split content into lines, then group into blocks
  const lines = content.split('\n')
  const blocks: { type: string; content: string; lines?: string[] }[] = []
  let i = 0

  while (i < lines.length) {
    const line = lines[i].trim()
    
    // Skip empty lines
    if (!line) {
      i++
      continue
    }

    // Markdown code block
    if (line.startsWith('```')) {
      const lang = line.slice(3)
      const codeLines: string[] = []
      i++
      while (i < lines.length && !lines[i].trim().startsWith('```')) {
        codeLines.push(lines[i])
        i++
      }
      blocks.push({ type: 'code', content: codeLines.join('\n'), lines: [lang] })
      i++
      continue
    }

    // Markdown headings
    if (line.startsWith('# ')) {
      blocks.push({ type: 'h1', content: line.slice(2) })
      i++
      continue
    }
    if (line.startsWith('## ')) {
      blocks.push({ type: 'h2', content: line.slice(3) })
      i++
      continue
    }
    if (line.startsWith('### ')) {
      blocks.push({ type: 'h3', content: line.slice(4) })
      i++
      continue
    }

    // Markdown blockquote
    if (line.startsWith('>')) {
      const quoteLines: string[] = []
      while (i < lines.length && lines[i].trim().startsWith('>')) {
        quoteLines.push(lines[i].trim().replace(/^>\s?/, ''))
        i++
      }
      blocks.push({ type: 'quote', content: quoteLines.join(' ') })
      continue
    }

    // Markdown lists (- or *)
    if (line.startsWith('- ') || line.startsWith('* ')) {
      const listItems: string[] = []
      while (i < lines.length && (lines[i].trim().startsWith('- ') || lines[i].trim().startsWith('* '))) {
        listItems.push(lines[i].trim().slice(2))
        i++
      }
      blocks.push({ type: 'ul', content: '', lines: listItems })
      continue
    }

    // Numbered lists
    if (/^\d+\.\s/.test(line)) {
      const listItems: string[] = []
      while (i < lines.length && /^\d+\.\s/.test(lines[i].trim())) {
        listItems.push(lines[i].trim().replace(/^\d+\.\s/, ''))
        i++
      }
      blocks.push({ type: 'ol', content: '', lines: listItems })
      continue
    }

    // Horizontal rule
    if (line === '---' || line === '***' || line === '___') {
      blocks.push({ type: 'hr', content: '' })
      i++
      continue
    }

    // Auto-detect: Check if this looks like a heading
    if (isLikelyHeading(line)) {
      blocks.push({ type: 'auto-heading', content: line })
      i++
      continue
    }

    // Auto-detect: Key statement / emphasis line
    if (isKeyStatement(line)) {
      blocks.push({ type: 'emphasis', content: line })
      i++
      continue
    }

    // Auto-detect: Multiple short consecutive lines might be a list
    const potentialListItems: string[] = [line]
    let j = i + 1
    while (j < lines.length && lines[j].trim() && lines[j].trim().length < 50 && !lines[j].trim().endsWith('.')) {
      potentialListItems.push(lines[j].trim())
      j++
    }
    if (potentialListItems.length >= 3 && potentialListItems.every(item => item.length < 50)) {
      blocks.push({ type: 'auto-list', content: '', lines: potentialListItems })
      i = j
      continue
    }

    // Regular paragraph - collect consecutive non-empty lines
    const paraLines: string[] = [line]
    i++
    while (i < lines.length && lines[i].trim() && !isLikelyHeading(lines[i].trim()) && 
           !lines[i].trim().startsWith('#') && !lines[i].trim().startsWith('>') &&
           !lines[i].trim().startsWith('- ') && !lines[i].trim().startsWith('* ') &&
           !/^\d+\.\s/.test(lines[i].trim())) {
      paraLines.push(lines[i].trim())
      i++
    }
    blocks.push({ type: 'paragraph', content: paraLines.join(' ') })
  }

  let paragraphCount = 0

  const elements = blocks.map((block, index) => {
    switch (block.type) {
      case 'code':
        return (
          <div key={index} className="my-10 rounded-2xl overflow-hidden shadow-xl border border-gray-200">
            {block.lines?.[0] && (
              <div className="bg-gray-800 px-5 py-3 text-xs font-mono text-gray-400 border-b border-gray-700 flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-red-500/80"></span>
                <span className="w-3 h-3 rounded-full bg-yellow-500/80"></span>
                <span className="w-3 h-3 rounded-full bg-green-500/80"></span>
                <span className="ml-2">{block.lines[0]}</span>
              </div>
            )}
            <pre className="bg-gray-900 p-5 overflow-x-auto">
              <code className="text-sm font-mono text-gray-100 leading-relaxed">{block.content}</code>
            </pre>
          </div>
        )

      case 'h1':
        return (
          <h2 key={index} className="text-3xl sm:text-4xl font-black text-gray-900 mt-16 mb-6 leading-tight tracking-tight">
            {block.content}
          </h2>
        )

      case 'h2':
        return (
          <h2 key={index} className="text-2xl sm:text-3xl font-bold text-gray-900 mt-14 mb-5 leading-tight">
            {block.content}
          </h2>
        )

      case 'h3':
        return (
          <h3 key={index} className="text-xl sm:text-2xl font-bold text-gray-900 mt-12 mb-4 leading-tight">
            {block.content}
          </h3>
        )

      case 'auto-heading':
        return (
          <div key={index} className="mt-14 mb-6">
            <h3 className="text-xl sm:text-2xl font-bold text-gray-900 leading-tight relative inline-block">
              {block.content}
              <span className="absolute -bottom-2 left-0 w-12 h-1 bg-gradient-to-r from-orange-500 to-amber-400 rounded-full"></span>
            </h3>
          </div>
        )

      case 'quote':
        return (
          <blockquote key={index} className="my-10 relative pl-8 py-6 bg-gradient-to-r from-orange-50 to-amber-50 rounded-2xl border-l-4 border-orange-500">
            <svg className="absolute top-4 left-4 w-8 h-8 text-orange-200" fill="currentColor" viewBox="0 0 24 24">
              <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z" />
            </svg>
            <p 
              className="text-xl sm:text-2xl italic text-gray-700 leading-relaxed font-medium pl-8"
              dangerouslySetInnerHTML={{ __html: processInline(block.content) }}
            />
          </blockquote>
        )

      case 'emphasis':
        return (
          <div key={index} className="my-8 py-6 px-8 bg-gradient-to-r from-gray-900 to-gray-800 rounded-2xl shadow-xl">
            <p className="text-xl sm:text-2xl font-semibold text-white leading-relaxed text-center">
              {block.content}
            </p>
          </div>
        )

      case 'ul':
        return (
          <ul key={index} className="my-8 space-y-4 bg-gray-50 rounded-2xl p-6">
            {block.lines?.map((item, i) => (
              <li key={i} className="flex items-start gap-4">
                <span className="flex-shrink-0 w-6 h-6 rounded-lg bg-orange-500 text-white flex items-center justify-center mt-0.5">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </span>
                <span 
                  className="text-lg text-gray-700 leading-relaxed"
                  dangerouslySetInnerHTML={{ __html: processInline(item) }}
                />
              </li>
            ))}
          </ul>
        )

      case 'ol':
        return (
          <ol key={index} className="my-8 space-y-4">
            {block.lines?.map((item, i) => (
              <li key={i} className="flex items-start gap-4 p-4 bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                <span className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-amber-500 text-white font-bold text-sm flex items-center justify-center shadow-lg shadow-orange-500/25">
                  {i + 1}
                </span>
                <span 
                  className="text-lg text-gray-700 leading-relaxed flex-1 pt-1"
                  dangerouslySetInnerHTML={{ __html: processInline(item) }}
                />
              </li>
            ))}
          </ol>
        )

      case 'auto-list':
        return (
          <div key={index} className="my-8 grid gap-3">
            {block.lines?.map((item, i) => (
              <div key={i} className="flex items-center gap-4 p-4 bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md hover:border-orange-200 transition-all group">
                <span className="flex-shrink-0 w-2 h-2 rounded-full bg-orange-500 group-hover:scale-125 transition-transform"></span>
                <span className="text-lg text-gray-700 font-medium">{item}</span>
              </div>
            ))}
          </div>
        )

      case 'hr':
        return (
          <div key={index} className="my-16 flex items-center justify-center gap-4">
            <span className="w-2 h-2 rounded-full bg-orange-300"></span>
            <span className="w-2 h-2 rounded-full bg-orange-400"></span>
            <span className="w-2 h-2 rounded-full bg-orange-500"></span>
            <span className="w-2 h-2 rounded-full bg-orange-400"></span>
            <span className="w-2 h-2 rounded-full bg-orange-300"></span>
          </div>
        )

      case 'paragraph':
      default:
        paragraphCount++
        const isFirstPara = paragraphCount === 1
        
        // First paragraph gets special treatment - larger text, drop cap
        if (isFirstPara) {
          return (
            <p 
              key={index} 
              className="text-xl sm:text-2xl text-gray-800 leading-relaxed mb-8 first-letter:text-6xl first-letter:font-bold first-letter:text-orange-500 first-letter:float-left first-letter:mr-4 first-letter:mt-1 first-letter:leading-none"
              dangerouslySetInnerHTML={{ __html: processInline(block.content) }}
            />
          )
        }
        
        return (
          <p 
            key={index} 
            className="text-lg sm:text-xl text-gray-700 leading-relaxed mb-6"
            dangerouslySetInnerHTML={{ __html: processInline(block.content) }}
          />
        )
    }
  })

  return <div className="article-content space-y-2">{elements}</div>
}

export default function BlogPost() {
  const { slug } = useParams<{ slug: string }>()
  const navigate = useNavigate()
  const [post, setPost] = useState<BlogPostType | null>(null)
  const [relatedPosts, setRelatedPosts] = useState<BlogPostListItem[]>([])
  const [categories, setCategories] = useState<BlogCategory[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (slug) {
      loadPost(slug)
      loadCategories()
    }
  }, [slug])

  async function loadPost(slug: string) {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchBlogPostBySlug(slug)
      setPost(data)
      
      // Load related posts
      const recent = await fetchRecentBlogPosts(4, data.id)
      setRelatedPosts(recent)
    } catch (err: any) {
      console.error('Failed to load post:', err)
      setError('Post not found')
    } finally {
      setLoading(false)
    }
  }

  async function loadCategories() {
    try {
      const data = await fetchBlogCategories()
      setCategories(data)
    } catch (err) {
      console.error('Failed to load categories:', err)
    }
  }

  function formatDate(dateString?: string) {
    if (!dateString) return ''
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  }

  function sharePost() {
    if (navigator.share && post) {
      navigator.share({
        title: post.title,
        text: post.excerpt || post.meta_description || '',
        url: window.location.href,
      })
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(window.location.href)
      alert('Link copied to clipboard!')
    }
  }

  function getTags(): string[] {
    if (!post?.tags) return []
    return post.tags.split(',').map(t => t.trim()).filter(Boolean)
  }

  // Generate JSON-LD structured data for SEO
  function getStructuredData() {
    if (!post) return null
    
    return {
      '@context': 'https://schema.org',
      '@type': post.schema_type || 'Article',
      headline: post.meta_title || post.title,
      description: post.meta_description || post.excerpt,
      image: post.og_image || post.featured_image,
      datePublished: post.published_at,
      dateModified: post.updated_at,
      author: {
        '@type': 'Person',
        name: post.author_name || 'MetaView Team',
      },
      publisher: {
        '@type': 'Organization',
        name: 'MetaView',
        logo: {
          '@type': 'ImageObject',
          url: `${window.location.origin}/logo.png`,
        },
      },
      mainEntityOfPage: {
        '@type': 'WebPage',
        '@id': window.location.href,
      },
    }
  }

  // Update document meta tags for SEO
  useEffect(() => {
    if (!post) return
    
    // Set title
    document.title = `${post.meta_title || post.title} | MetaView Blog`
    
    // Helper to update or create meta tag
    const setMetaTag = (name: string, content: string, property?: boolean) => {
      const attr = property ? 'property' : 'name'
      let meta = document.querySelector(`meta[${attr}="${name}"]`) as HTMLMetaElement
      if (!meta) {
        meta = document.createElement('meta')
        meta.setAttribute(attr, name)
        document.head.appendChild(meta)
      }
      meta.setAttribute('content', content)
    }
    
    // Standard meta
    if (post.meta_description || post.excerpt) {
      setMetaTag('description', post.meta_description || post.excerpt || '')
    }
    if (post.meta_keywords) {
      setMetaTag('keywords', post.meta_keywords)
    }
    if (post.no_index) {
      setMetaTag('robots', 'noindex, nofollow')
    }
    
    // Open Graph
    setMetaTag('og:type', 'article', true)
    setMetaTag('og:title', post.meta_title || post.title, true)
    setMetaTag('og:description', post.meta_description || post.excerpt || '', true)
    setMetaTag('og:url', window.location.href, true)
    if (post.og_image || post.featured_image) {
      setMetaTag('og:image', post.og_image || post.featured_image || '', true)
    }
    if (post.published_at) {
      setMetaTag('article:published_time', post.published_at, true)
    }
    setMetaTag('article:modified_time', post.updated_at, true)
    
    // Twitter Card
    setMetaTag('twitter:card', 'summary_large_image')
    setMetaTag('twitter:title', post.twitter_title || post.meta_title || post.title)
    setMetaTag('twitter:description', post.twitter_description || post.meta_description || post.excerpt || '')
    if (post.twitter_image || post.og_image || post.featured_image) {
      setMetaTag('twitter:image', post.twitter_image || post.og_image || post.featured_image || '')
    }
    
    // Canonical URL
    let canonical = document.querySelector('link[rel="canonical"]') as HTMLLinkElement
    if (!canonical) {
      canonical = document.createElement('link')
      canonical.setAttribute('rel', 'canonical')
      document.head.appendChild(canonical)
    }
    canonical.setAttribute('href', post.canonical_url || window.location.href)
    
    // Structured Data (JSON-LD)
    let script = document.querySelector('script[type="application/ld+json"]#blog-post-schema') as HTMLScriptElement
    if (!script) {
      script = document.createElement('script')
      script.setAttribute('type', 'application/ld+json')
      script.id = 'blog-post-schema'
      document.head.appendChild(script)
    }
    script.textContent = JSON.stringify(getStructuredData())
    
    // Cleanup on unmount
    return () => {
      document.title = 'MetaView'
    }
  }, [post])

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="animate-pulse space-y-8 max-w-3xl w-full px-4">
          <div className="h-8 bg-gray-200 rounded w-3/4" />
          <div className="h-64 bg-gray-200 rounded-xl" />
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded w-full" />
            <div className="h-4 bg-gray-200 rounded w-5/6" />
            <div className="h-4 bg-gray-200 rounded w-4/5" />
          </div>
        </div>
      </div>
    )
  }

  if (error || !post) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">404</h1>
          <p className="text-gray-500 mb-8">Post not found</p>
          <Link
            to="/blog"
            className="text-orange-600 font-semibold hover:text-orange-700"
          >
            ← Back to Blog
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white">
        {/* Navigation */}
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-2xl border-b border-gray-100/80">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-12">
            <div className="flex items-center justify-between h-16">
              <Link to="/" className="flex items-center space-x-2.5 group">
                <div className="w-9 h-9 bg-gradient-to-br from-orange-500 via-amber-500 to-yellow-500 rounded-xl flex items-center justify-center shadow-lg shadow-orange-500/25 group-hover:scale-110 transition-transform">
                  <span className="text-white font-black text-base">M</span>
                </div>
                <span className="text-lg font-black text-gray-900">MetaView</span>
              </Link>
              <div className="hidden md:flex items-center space-x-8">
                <Link to="/" className="text-gray-600 hover:text-gray-900 font-semibold text-sm">Home</Link>
                <Link to="/blog" className="text-orange-600 font-semibold text-sm">Blog</Link>
                <Link to="/#pricing" className="text-gray-600 hover:text-gray-900 font-semibold text-sm">Pricing</Link>
              </div>
              <Link
                to="/app"
                className="px-5 py-2.5 bg-gradient-to-r from-orange-500 to-amber-500 text-white rounded-xl font-bold text-sm hover:shadow-lg transition-all"
              >
                Get Started
              </Link>
            </div>
          </div>
        </nav>

        {/* Breadcrumb */}
        <div className="pt-20 bg-gray-50 border-b border-gray-100">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4">
            <nav className="flex items-center space-x-2 text-sm">
              <Link to="/" className="text-gray-500 hover:text-gray-700">Home</Link>
              <ChevronRightIcon className="w-4 h-4 text-gray-400" />
              <Link to="/blog" className="text-gray-500 hover:text-gray-700">Blog</Link>
              {post.category && (
                <>
                  <ChevronRightIcon className="w-4 h-4 text-gray-400" />
                  <Link
                    to={`/blog?category=${post.category.slug}`}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    {post.category.name}
                  </Link>
                </>
              )}
              <ChevronRightIcon className="w-4 h-4 text-gray-400" />
              <span className="text-gray-900 font-medium truncate max-w-[200px]">{post.title}</span>
            </nav>
          </div>
        </div>

        {/* Article Header */}
        <header className="py-12 px-4 sm:px-6">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center gap-3 mb-6 flex-wrap">
              {post.category && (
                <Link
                  to={`/blog?category=${post.category.slug}`}
                  className="px-3 py-1 rounded-full text-sm font-semibold text-white hover:opacity-90 transition-opacity"
                  style={{ backgroundColor: post.category.color }}
                >
                  {post.category.name}
                </Link>
              )}
              {post.read_time_minutes && (
                <span className="flex items-center gap-1.5 text-sm text-gray-500">
                  <ClockIcon className="w-4 h-4" />
                  {post.read_time_minutes} min read
                </span>
              )}
              <span className="flex items-center gap-1.5 text-sm text-gray-500">
                <EyeIcon className="w-4 h-4" />
                {post.views_count.toLocaleString()} views
              </span>
            </div>
            
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-gray-900 leading-tight mb-6">
              {post.title}
            </h1>
            
            {post.excerpt && (
              <p className="text-xl text-gray-600 leading-relaxed mb-8">
                {post.excerpt}
              </p>
            )}
            
            <div className="flex items-center justify-between flex-wrap gap-4 pb-8 border-b border-gray-100">
              <div className="flex items-center gap-4">
                {post.author_avatar ? (
                  <img
                    src={post.author_avatar}
                    alt={post.author_name || 'Author'}
                    className="w-12 h-12 rounded-full object-cover ring-2 ring-white shadow-lg"
                  />
                ) : (
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-orange-400 to-amber-400 ring-2 ring-white shadow-lg" />
                )}
                <div>
                  <div className="font-semibold text-gray-900">
                    {post.author_name || 'MetaView Team'}
                  </div>
                  <div className="text-sm text-gray-500 flex items-center gap-2">
                    <CalendarIcon className="w-4 h-4" />
                    {formatDate(post.published_at)}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <button
                  onClick={sharePost}
                  className="p-2.5 rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors"
                  aria-label="Share"
                >
                  <ShareIcon className="w-5 h-5" />
                </button>
                <button
                  className="p-2.5 rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors"
                  aria-label="Bookmark"
                >
                  <BookmarkIcon className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Featured Image */}
        {post.featured_image && (
          <div className="px-4 sm:px-6 mb-12">
            <div className="max-w-5xl mx-auto">
              <img
                src={post.featured_image}
                alt={post.featured_image_alt || post.title}
                className="w-full h-auto rounded-2xl shadow-xl"
              />
            </div>
          </div>
        )}

        {/* Article Content */}
        <article className="px-4 sm:px-6 pb-16">
          <div className="max-w-3xl mx-auto">
            <div className="article-body">
              {renderContent(post.content)}
            </div>
            
            {/* Tags */}
            {getTags().length > 0 && (
              <div className="mt-12 pt-8 border-t border-gray-100">
                <div className="flex items-center gap-2 flex-wrap">
                  <TagIcon className="w-5 h-5 text-gray-400" />
                  {getTags().map((tag) => (
                    <Link
                      key={tag}
                      to={`/blog?tag=${encodeURIComponent(tag)}`}
                      className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm font-medium hover:bg-gray-200 transition-colors"
                    >
                      {tag}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* Author Bio */}
            {post.author_bio && (
              <div className="mt-12 p-6 bg-gray-50 rounded-2xl">
                <div className="flex items-start gap-4">
                  {post.author_avatar ? (
                    <img
                      src={post.author_avatar}
                      alt={post.author_name || 'Author'}
                      className="w-16 h-16 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-16 h-16 rounded-full bg-gradient-to-br from-orange-400 to-amber-400" />
                  )}
                  <div>
                    <div className="font-bold text-gray-900 mb-1">
                      About {post.author_name || 'the Author'}
                    </div>
                    <p className="text-gray-600">{post.author_bio}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </article>

        {/* Related Posts */}
        {relatedPosts.length > 0 && (
          <section className="py-16 px-4 sm:px-6 bg-gray-50">
            <div className="max-w-7xl mx-auto">
              <h2 className="text-2xl font-bold text-gray-900 mb-8">Continue Reading</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {relatedPosts.map((relatedPost) => (
                  <Link
                    key={relatedPost.id}
                    to={`/blog/${relatedPost.slug}`}
                    className="group bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-lg hover:-translate-y-1 transition-all"
                  >
                    {relatedPost.featured_image ? (
                      <div className="h-32 overflow-hidden">
                        <img
                          src={relatedPost.featured_image}
                          alt={relatedPost.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                      </div>
                    ) : (
                      <div className="h-32 bg-gradient-to-br from-orange-100 to-amber-100 flex items-center justify-center">
                        <SparklesIcon className="w-8 h-8 text-orange-300" />
                      </div>
                    )}
                    <div className="p-4">
                      <h3 className="font-semibold text-gray-900 group-hover:text-orange-600 transition-colors line-clamp-2 mb-2">
                        {relatedPost.title}
                      </h3>
                      <span className="text-xs text-gray-500">
                        {formatDate(relatedPost.published_at)}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* CTA Section */}
        <section className="py-16 px-4 sm:px-6 bg-gradient-to-br from-orange-500 via-amber-500 to-orange-500">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-3xl font-bold text-white mb-4">Ready to boost your CTR?</h2>
            <p className="text-orange-100 mb-8">
              Start creating beautiful, high-converting URL previews today with MetaView.
            </p>
            <Link
              to="/app"
              className="inline-flex items-center gap-2 px-8 py-4 bg-white text-orange-600 rounded-xl font-bold hover:bg-orange-50 transition-colors"
            >
              Start Free Trial
              <ChevronRightIcon className="w-5 h-5" />
            </Link>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-gray-900 text-white py-12 px-4 sm:px-6">
          <div className="max-w-7xl mx-auto">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
              <Link to="/" className="flex items-center space-x-2.5">
                <div className="w-9 h-9 bg-gradient-to-br from-orange-500 via-amber-500 to-yellow-500 rounded-xl flex items-center justify-center">
                  <span className="text-white font-black text-sm">M</span>
                </div>
                <span className="text-lg font-black">MetaView</span>
              </Link>
              <div className="flex items-center gap-6 text-sm text-gray-400">
                <Link to="/" className="hover:text-white transition-colors">Home</Link>
                <Link to="/blog" className="hover:text-white transition-colors">Blog</Link>
                <Link to="/#pricing" className="hover:text-white transition-colors">Pricing</Link>
              </div>
              <span className="text-sm text-gray-500">© 2024 MetaView. All rights reserved.</span>
            </div>
          </div>
        </footer>
      </div>
  )
}

