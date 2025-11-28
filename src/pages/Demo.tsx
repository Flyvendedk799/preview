import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRightIcon,
  CheckIcon,
  ExclamationCircleIcon,
  SparklesIcon,
  LinkIcon,
  PhotoIcon,
  ArrowUpRightIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline'
import { subscribeToNewsletter, generateDemoPreview, type DemoPreviewResponse } from '../api/client'

type Step = 'email' | 'url' | 'preview'

export default function Demo() {
  const [step, setStep] = useState<Step>('email')
  const [email, setEmail] = useState('')
  const [url, setUrl] = useState('')
  const [preview, setPreview] = useState<DemoPreviewResponse | null>(null)
  const [scrollY, setScrollY] = useState(0)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  
  const [emailError, setEmailError] = useState<string | null>(null)
  const [urlError, setUrlError] = useState<string | null>(null)
  const [isSubmittingEmail, setIsSubmittingEmail] = useState(false)
  const [isGeneratingPreview, setIsGeneratingPreview] = useState(false)
  const [previewError, setPreviewError] = useState<string | null>(null)

  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.pageYOffset)
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const validateUrl = (url: string): boolean => {
    try {
      const urlObj = new URL(url)
      return urlObj.protocol === 'http:' || urlObj.protocol === 'https:'
    } catch {
      return false
    }
  }

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setEmailError(null)

    if (!email.trim()) {
      setEmailError('Email is required')
      return
    }

    if (!validateEmail(email)) {
      setEmailError('Please enter a valid email address')
      return
    }

    setIsSubmittingEmail(true)
    try {
      await subscribeToNewsletter({
        email: email.trim(),
        source: 'demo',
        consent_given: true,
      })
      setStep('url')
    } catch (error) {
      setEmailError(error instanceof Error ? error.message : 'Failed to subscribe. Please try again.')
    } finally {
      setIsSubmittingEmail(false)
    }
  }

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setUrlError(null)
    setPreviewError(null)

    if (!url.trim()) {
      setUrlError('URL is required')
      return
    }

    // Ensure URL has HTTPS protocol (always use HTTPS)
    let processedUrl = url.trim()
    if (!processedUrl.startsWith('http://') && !processedUrl.startsWith('https://')) {
      processedUrl = `https://${processedUrl}`
    } else if (processedUrl.startsWith('http://')) {
      // Convert HTTP to HTTPS
      processedUrl = processedUrl.replace('http://', 'https://')
    }

    if (!validateUrl(processedUrl)) {
      setUrlError('Please enter a valid URL')
      return
    }

    setIsGeneratingPreview(true)
    try {
      const result = await generateDemoPreview(processedUrl)
      setPreview(result)
      setStep('preview')
    } catch (error) {
      setPreviewError(error instanceof Error ? error.message : 'Failed to generate preview. Please try again.')
    } finally {
      setIsGeneratingPreview(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-orange-50/30">
      {/* Premium Navigation with Enhanced Contrast */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-2xl border-b border-gray-100/80 transition-all duration-300" style={{ boxShadow: scrollY > 10 ? '0 4px 20px rgba(0,0,0,0.06)' : 'none' }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-12">
          <div className="flex items-center justify-between h-16 sm:h-18">
            <Link to="/" className="flex items-center space-x-2 sm:space-x-3 group">
              <div className="relative">
                <div className="w-9 h-9 sm:w-10 sm:h-10 bg-gradient-to-br from-orange-500 via-amber-500 to-yellow-500 rounded-xl flex items-center justify-center shadow-lg shadow-orange-500/25 group-hover:scale-110 group-hover:shadow-orange-500/40 transition-all duration-300">
                  <span className="text-white font-black text-base sm:text-lg">M</span>
                </div>
                <div className="absolute -inset-1 bg-gradient-to-br from-orange-400 to-amber-500 rounded-xl opacity-0 group-hover:opacity-40 blur-lg transition-opacity duration-300" />
              </div>
              <span className="text-lg sm:text-xl font-black text-gray-900 tracking-tight">MetaView</span>
            </Link>
            <div className="hidden lg:flex items-center space-x-10">
              {[
                { href: '/#product', label: 'Product' },
                { href: '/#features', label: 'Features' },
                { href: '/#pricing', label: 'Pricing' },
                { href: '/#docs', label: 'Docs' },
              ].map((item) => (
                <Link 
                  key={item.label}
                  to={item.href} 
                  className="relative py-1 font-semibold text-sm transition-all duration-200 group text-gray-600 hover:text-gray-900"
                >
                  {item.label}
                  <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-orange-500 group-hover:w-full transition-all duration-300" />
                </Link>
              ))}
              <Link 
                to="/blog" 
                className="relative py-1 font-semibold text-sm transition-all duration-200 group text-gray-600 hover:text-gray-900"
              >
                Blog
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-orange-500 group-hover:w-full transition-all duration-300" />
              </Link>
              <Link to="/app" className="text-gray-600 hover:text-gray-900 transition-all duration-200 font-semibold text-sm relative group py-1">
                Login
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-orange-500 group-hover:w-full transition-all duration-300" />
              </Link>
            </div>
            <div className="flex items-center space-x-3">
              <Link
                to="/app"
                className="hidden sm:flex group relative px-5 sm:px-6 py-3 bg-gradient-to-r from-orange-500 via-amber-500 to-orange-500 text-white rounded-xl font-bold text-xs sm:text-sm transition-all duration-300 hover:scale-[1.04] active:scale-[0.98] hover:shadow-xl hover:shadow-orange-500/30 overflow-hidden min-h-[44px] items-center justify-center select-none"
                style={{ boxShadow: scrollY > 10 ? '0 4px 20px rgba(249, 115, 22, 0.3)' : 'none' }}
              >
                <span className="relative z-10 flex items-center">
                  Get Started Free
                  <ArrowUpRightIcon className="w-3.5 h-3.5 sm:w-4 sm:h-4 ml-1.5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform duration-300" />
                </span>
                {/* Shine effect on hover */}
                <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/20 to-transparent" />
              </Link>
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="lg:hidden p-2 text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
                aria-label="Toggle menu"
              >
                {mobileMenuOpen ? (
                  <XMarkIcon className="w-6 h-6" />
                ) : (
                  <Bars3Icon className="w-6 h-6" />
                )}
              </button>
            </div>
          </div>
          
          {/* Mobile Menu */}
          {mobileMenuOpen && (
            <div className="lg:hidden border-t border-gray-100 py-4 bg-white/95 backdrop-blur-xl">
              <div className="flex flex-col space-y-1">
                <Link 
                  to="/#product" 
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-4 py-3 text-gray-700 hover:bg-orange-50 hover:text-orange-600 rounded-xl transition-colors font-semibold text-base min-h-[44px] flex items-center"
                >
                  Product
                </Link>
                <Link 
                  to="/#features" 
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-4 py-3 text-gray-700 hover:bg-orange-50 hover:text-orange-600 rounded-xl transition-colors font-semibold text-base min-h-[44px] flex items-center"
                >
                  Features
                </Link>
                <Link 
                  to="/#pricing" 
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-4 py-3 text-gray-700 hover:bg-orange-50 hover:text-orange-600 rounded-xl transition-colors font-semibold text-base min-h-[44px] flex items-center"
                >
                  Pricing
                </Link>
                <Link 
                  to="/#docs" 
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-4 py-3 text-gray-700 hover:bg-orange-50 hover:text-orange-600 rounded-xl transition-colors font-semibold text-base min-h-[44px] flex items-center"
                >
                  Docs
                </Link>
                <Link 
                  to="/blog" 
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-4 py-3 text-gray-700 hover:bg-orange-50 hover:text-orange-600 rounded-xl transition-colors font-semibold text-base min-h-[44px] flex items-center"
                >
                  Blog
                </Link>
                <Link 
                  to="/app" 
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-4 py-3 text-gray-700 hover:bg-orange-50 hover:text-orange-600 rounded-xl transition-colors font-semibold text-base min-h-[44px] flex items-center"
                >
                  Login
                </Link>
                <Link
                  to="/app"
                  onClick={() => setMobileMenuOpen(false)}
                  className="mx-4 mt-2 px-6 py-3 bg-gradient-to-r from-orange-500 to-amber-500 text-white rounded-xl font-bold text-sm transition-all duration-300 min-h-[44px] flex items-center justify-center shadow-lg shadow-orange-500/25"
                >
                  Get Started Free
                  <ArrowUpRightIcon className="w-4 h-4 ml-2" />
                </Link>
              </div>
            </div>
          )}
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-12 pt-24 sm:pt-28 pb-12 sm:pb-20">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-orange-100 via-amber-100 to-yellow-100 rounded-full border-2 border-orange-300/80 backdrop-blur-sm mb-6">
            <SparklesIcon className="w-4 h-4 text-orange-600" />
            <span className="text-xs font-black text-orange-800 tracking-wide">AI-Powered Preview Demo</span>
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-gray-900 leading-tight mb-4">
            See Your URLs{' '}
            <span className="bg-gradient-to-r from-orange-500 via-amber-500 to-yellow-500 bg-clip-text text-transparent">
              Come to Life
            </span>
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Experience our AI-powered preview generation system. Enter your email to get started, then see how any URL transforms into a beautiful preview card.
          </p>
        </div>

        {/* Step 1: Email Collection */}
        {step === 'email' && (
          <div className="max-w-md mx-auto">
            <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-gradient-to-br from-orange-100 to-amber-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <LinkIcon className="w-8 h-8 text-orange-600" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Get Started</h2>
                <p className="text-gray-600">Enter your email to unlock the demo</p>
              </div>

              <form onSubmit={handleEmailSubmit} className="space-y-4">
                <div>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value)
                      setEmailError(null)
                    }}
                    placeholder="your@email.com"
                    className={`w-full px-4 py-3.5 rounded-xl border-2 transition-all duration-200 focus:outline-none focus:ring-2 ${
                      emailError
                        ? 'border-red-300 focus:border-red-500 focus:ring-red-200'
                        : 'border-gray-200 focus:border-orange-500 focus:ring-orange-200'
                    }`}
                    disabled={isSubmittingEmail}
                  />
                  {emailError && (
                    <div className="mt-2 flex items-center space-x-1 text-sm text-red-600">
                      <ExclamationCircleIcon className="w-4 h-4" />
                      <span>{emailError}</span>
                    </div>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={isSubmittingEmail}
                  className="w-full py-3.5 bg-gradient-to-r from-orange-500 via-amber-500 to-orange-500 text-white rounded-xl font-bold text-base transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] hover:shadow-xl hover:shadow-orange-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  {isSubmittingEmail ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Subscribing...</span>
                    </>
                  ) : (
                    <>
                      <span>Continue to Demo</span>
                      <ArrowRightIcon className="w-5 h-5" />
                    </>
                  )}
                </button>
              </form>

              <p className="mt-4 text-xs text-gray-500 text-center">
                By continuing, you agree to receive updates from MetaView. Unsubscribe anytime.
              </p>
            </div>
          </div>
        )}

        {/* Step 2: URL Input */}
        {step === 'url' && (
          <div className="max-w-md mx-auto">
            <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <LinkIcon className="w-8 h-8 text-blue-600" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Enter a URL</h2>
                <p className="text-gray-600">Try any website URL to see our AI in action</p>
              </div>

              <form onSubmit={handleUrlSubmit} className="space-y-4">
                <div>
                  <input
                    type="text"
                    value={url}
                    onChange={(e) => {
                      setUrl(e.target.value)
                      setUrlError(null)
                    }}
                    placeholder="https://example.com/article"
                    className={`w-full px-4 py-3.5 rounded-xl border-2 transition-all duration-200 focus:outline-none focus:ring-2 ${
                      urlError
                        ? 'border-red-300 focus:border-red-500 focus:ring-red-200'
                        : 'border-gray-200 focus:border-orange-500 focus:ring-orange-200'
                    }`}
                    disabled={isGeneratingPreview}
                  />
                  {urlError && (
                    <div className="mt-2 flex items-center space-x-1 text-sm text-red-600">
                      <ExclamationCircleIcon className="w-4 h-4" />
                      <span>{urlError}</span>
                    </div>
                  )}
                  {previewError && (
                    <div className="mt-2 flex items-center space-x-1 text-sm text-red-600">
                      <ExclamationCircleIcon className="w-4 h-4" />
                      <span>{previewError}</span>
                    </div>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={isGeneratingPreview}
                  className="w-full py-3.5 bg-gradient-to-r from-orange-500 via-amber-500 to-orange-500 text-white rounded-xl font-bold text-base transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] hover:shadow-xl hover:shadow-orange-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  {isGeneratingPreview ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Generating Preview...</span>
                    </>
                  ) : (
                    <>
                      <SparklesIcon className="w-5 h-5" />
                      <span>Generate Preview</span>
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* Step 3: Preview Display */}
        {step === 'preview' && preview && (
          <div className="space-y-8">
            {/* Success Message */}
            <div className="bg-gradient-to-r from-emerald-50 to-teal-50 border-2 border-emerald-200 rounded-xl p-6 text-center">
              <div className="w-12 h-12 bg-emerald-500 rounded-full flex items-center justify-center mx-auto mb-3">
                <CheckIcon className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Preview Generated!</h3>
              <p className="text-gray-600">Here's how your URL will appear when shared</p>
            </div>

            {/* Preview Card */}
            <div className="bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden">
              {preview.image_url && (
                <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 relative overflow-hidden">
                  <img
                    src={preview.image_url}
                    alt={preview.title}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement
                      target.style.display = 'none'
                    }}
                  />
                </div>
              )}
              <div className="p-6">
                <div className="mb-2">
                  <span className="inline-block px-3 py-1 bg-orange-100 text-orange-700 text-xs font-bold rounded-full uppercase">
                    {preview.type}
                  </span>
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">{preview.title}</h3>
                {preview.description && (
                  <p className="text-gray-600 mb-4 leading-relaxed">{preview.description}</p>
                )}
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <LinkIcon className="w-4 h-4" />
                  <span className="truncate">{preview.url}</span>
                </div>
              </div>
            </div>

            {/* Demo Notice */}
            <div className="bg-amber-50 border-2 border-amber-200 rounded-xl p-6">
              <div className="flex items-start space-x-3">
                <PhotoIcon className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-bold text-gray-900 mb-1">This is a Demo Preview</h4>
                  <p className="text-sm text-gray-700 mb-4">{preview.message}</p>
                  <div className="flex flex-col sm:flex-row gap-3">
                    <Link
                      to="/app"
                      className="px-6 py-3 bg-gradient-to-r from-orange-500 via-amber-500 to-orange-500 text-white rounded-xl font-bold text-sm transition-all duration-300 hover:scale-[1.02] hover:shadow-lg hover:shadow-orange-500/30 text-center"
                    >
                      Get Full Access
                    </Link>
                    <button
                      onClick={() => {
                        setStep('url')
                        setUrl('')
                        setPreview(null)
                        setPreviewError(null)
                      }}
                      className="px-6 py-3 bg-white border-2 border-gray-200 text-gray-700 rounded-xl font-bold text-sm transition-all duration-300 hover:scale-[1.02] hover:border-gray-300"
                    >
                      Try Another URL
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* CTA Section */}
            <div className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl p-8 text-center text-white">
              <h3 className="text-2xl font-bold mb-3">Ready to Create Unlimited Previews?</h3>
              <p className="text-gray-300 mb-6 max-w-xl mx-auto">
                Join thousands of teams using MetaView to create high-converting URL previews. Start your free trial today.
              </p>
              <Link
                to="/app"
                className="inline-flex items-center space-x-2 px-8 py-4 bg-gradient-to-r from-orange-500 via-amber-500 to-orange-500 text-white rounded-xl font-bold text-base transition-all duration-300 hover:scale-[1.05] hover:shadow-2xl hover:shadow-orange-500/50"
              >
                <span>Start Free Trial</span>
                <ArrowRightIcon className="w-5 h-5" />
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

