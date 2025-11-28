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
  EnvelopeIcon,
  GlobeAltIcon,
  RocketLaunchIcon,
  StarIcon,
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
  const [emailSubscribed, setEmailSubscribed] = useState(false)
  const [showEmailSuccess, setShowEmailSuccess] = useState(false)
  
  const [emailError, setEmailError] = useState<string | null>(null)
  const [urlError, setUrlError] = useState<string | null>(null)
  const [isSubmittingEmail, setIsSubmittingEmail] = useState(false)
  const [isGeneratingPreview, setIsGeneratingPreview] = useState(false)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [consentChecked, setConsentChecked] = useState(false)

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

    // Email is optional, but if provided, validate it
    if (email.trim() && !validateEmail(email)) {
      setEmailError('Please enter a valid email address')
      return
    }

    // If email provided and consent checked, subscribe
    if (email.trim() && consentChecked) {
      setIsSubmittingEmail(true)
      try {
        await subscribeToNewsletter({
          email: email.trim(),
          source: 'demo',
          consent_given: true,
        })
        setEmailSubscribed(true)
        setShowEmailSuccess(true)
        setTimeout(() => setShowEmailSuccess(false), 3000)
      } catch (error) {
        setEmailError(error instanceof Error ? error.message : 'Failed to subscribe. Please try again.')
      } finally {
        setIsSubmittingEmail(false)
      }
    }

    // Always proceed to URL step (email is optional)
    setStep('url')
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

        {/* Step 1: Email Collection (Optional) */}
        {step === 'email' && (
          <div className="max-w-lg mx-auto">
            <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden relative">
              {/* Animated background gradient */}
              <div className="absolute inset-0 bg-gradient-to-br from-orange-50/50 via-amber-50/30 to-yellow-50/50 opacity-50" />
              
              <div className="relative p-8">
                {/* Success animation overlay */}
                {showEmailSuccess && (
                  <div className="absolute inset-0 bg-emerald-500/10 backdrop-blur-sm z-10 flex items-center justify-center animate-fade-in">
                    <div className="bg-white rounded-2xl p-8 shadow-2xl border-2 border-emerald-200 animate-scale-in">
                      <div className="w-16 h-16 bg-emerald-500 rounded-full flex items-center justify-center mx-auto mb-4 animate-bounce">
                        <CheckIcon className="w-8 h-8 text-white" />
                      </div>
                      <h3 className="text-xl font-bold text-gray-900 mb-2 text-center">Subscribed!</h3>
                      <p className="text-gray-600 text-center">You'll receive updates from MetaView</p>
                    </div>
                  </div>
                )}

                <div className="text-center mb-6">
                  <div className="relative inline-block mb-4">
                    <div className="w-20 h-20 bg-gradient-to-br from-orange-500 via-amber-500 to-yellow-500 rounded-2xl flex items-center justify-center mx-auto shadow-lg shadow-orange-500/30 animate-pulse">
                      <RocketLaunchIcon className="w-10 h-10 text-white" />
                    </div>
                    <div className="absolute -top-1 -right-1 w-6 h-6 bg-emerald-500 rounded-full border-4 border-white flex items-center justify-center">
                      <SparklesIcon className="w-3 h-3 text-white" />
                    </div>
                  </div>
                  <h2 className="text-3xl font-black text-gray-900 mb-2">Try It Free</h2>
                  <p className="text-gray-600">See how AI transforms any URL into a beautiful preview</p>
                </div>

                <form onSubmit={handleEmailSubmit} className="space-y-4">
                  {/* Optional email with checkbox */}
                  <div className="bg-gradient-to-r from-gray-50 to-orange-50/30 rounded-xl p-4 border border-gray-200">
                    <div className="flex items-start space-x-3">
                      <input
                        type="checkbox"
                        id="email-consent"
                        checked={consentChecked}
                        onChange={(e) => {
                          setConsentChecked(e.target.checked)
                          setEmailError(null)
                        }}
                        className="mt-1 w-5 h-5 rounded border-gray-300 text-orange-500 focus:ring-orange-500 focus:ring-2 cursor-pointer"
                      />
                      <div className="flex-1">
                        <label htmlFor="email-consent" className="block text-sm font-semibold text-gray-900 mb-2 cursor-pointer">
                          Get updates & exclusive tips (optional)
                        </label>
                        {consentChecked && (
                          <div className="space-y-2 animate-fade-in">
                            <input
                              type="email"
                              value={email}
                              onChange={(e) => {
                                setEmail(e.target.value)
                                setEmailError(null)
                              }}
                              placeholder="your@email.com"
                              className={`w-full px-4 py-3 rounded-xl border-2 transition-all duration-200 focus:outline-none focus:ring-2 ${
                                emailError
                                  ? 'border-red-300 focus:border-red-500 focus:ring-red-200'
                                  : 'border-orange-200 focus:border-orange-500 focus:ring-orange-200 bg-white'
                              }`}
                              disabled={isSubmittingEmail}
                            />
                            {emailError && (
                              <div className="flex items-center space-x-1 text-sm text-red-600 animate-shake">
                                <ExclamationCircleIcon className="w-4 h-4" />
                                <span>{emailError}</span>
                              </div>
                            )}
                            {isSubmittingEmail && (
                              <div className="flex items-center space-x-2 text-sm text-orange-600">
                                <div className="w-4 h-4 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
                                <span>Subscribing...</span>
                              </div>
                            )}
                            {emailSubscribed && !showEmailSuccess && (
                              <div className="flex items-center space-x-2 text-sm text-emerald-600">
                                <CheckIcon className="w-4 h-4" />
                                <span>Subscribed successfully!</span>
                              </div>
                            )}
                          </div>
                        )}
                        {!consentChecked && (
                          <p className="text-xs text-gray-500 mt-1">
                            Stay updated with new features, tips, and exclusive content
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isSubmittingEmail}
                    className="w-full py-4 bg-gradient-to-r from-orange-500 via-amber-500 to-orange-500 text-white rounded-xl font-bold text-base transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] hover:shadow-2xl hover:shadow-orange-500/40 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 relative overflow-hidden group"
                  >
                    <span className="relative z-10 flex items-center">
                      <span>Continue to Demo</span>
                      <ArrowRightIcon className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                    </span>
                    <div className="absolute inset-0 bg-gradient-to-r from-orange-600 via-amber-600 to-orange-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/20 to-transparent" />
                  </button>
                </form>

                {/* Trust indicators */}
                <div className="mt-6 flex items-center justify-center space-x-6 text-xs text-gray-500">
                  <div className="flex items-center space-x-1">
                    <CheckIcon className="w-4 h-4 text-emerald-500" />
                    <span>No credit card</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <CheckIcon className="w-4 h-4 text-emerald-500" />
                    <span>Instant preview</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <CheckIcon className="w-4 h-4 text-emerald-500" />
                    <span>Free to try</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: URL Input */}
        {step === 'url' && (
          <div className="max-w-lg mx-auto">
            {/* Progress indicator */}
            <div className="mb-8">
              <div className="flex items-center justify-center space-x-4 mb-4">
                <div className="flex items-center space-x-2">
                  <div className="w-10 h-10 bg-emerald-500 rounded-full flex items-center justify-center">
                    <CheckIcon className="w-6 h-6 text-white" />
                  </div>
                  <span className="text-sm font-semibold text-gray-700">Step 1</span>
                </div>
                <div className="w-16 h-1 bg-emerald-500 rounded-full" />
                <div className="flex items-center space-x-2">
                  <div className="w-10 h-10 bg-orange-500 rounded-full flex items-center justify-center animate-pulse">
                    <GlobeAltIcon className="w-6 h-6 text-white" />
                  </div>
                  <span className="text-sm font-semibold text-gray-700">Step 2</span>
                </div>
                <div className="w-16 h-1 bg-gray-200 rounded-full" />
                <div className="flex items-center space-x-2">
                  <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                    <PhotoIcon className="w-6 h-6 text-gray-400" />
                  </div>
                  <span className="text-sm font-semibold text-gray-400">Step 3</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden relative">
              {/* Animated background */}
              <div className="absolute inset-0 bg-gradient-to-br from-blue-50/50 via-indigo-50/30 to-purple-50/50 opacity-50" />
              
              <div className="relative p-8">
                <div className="text-center mb-6">
                  <div className="relative inline-block mb-4">
                    <div className="w-20 h-20 bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-500 rounded-2xl flex items-center justify-center mx-auto shadow-lg shadow-blue-500/30 animate-pulse">
                      <GlobeAltIcon className="w-10 h-10 text-white" />
                    </div>
                    <div className="absolute -top-1 -right-1 w-6 h-6 bg-orange-500 rounded-full border-4 border-white flex items-center justify-center animate-bounce">
                      <SparklesIcon className="w-3 h-3 text-white" />
                    </div>
                  </div>
                  <h2 className="text-3xl font-black text-gray-900 mb-2">Enter a URL</h2>
                  <p className="text-gray-600">Try any website URL to see our AI in action</p>
                </div>

                <form onSubmit={handleUrlSubmit} className="space-y-4">
                  <div className="relative">
                    <div className="absolute left-4 top-1/2 transform -translate-y-1/2">
                      <LinkIcon className={`w-5 h-5 ${url ? 'text-orange-500' : 'text-gray-400'} transition-colors`} />
                    </div>
                    <input
                      type="text"
                      value={url}
                      onChange={(e) => {
                        setUrl(e.target.value)
                        setUrlError(null)
                        setPreviewError(null)
                      }}
                      placeholder="https://example.com/article"
                      className={`w-full pl-12 pr-4 py-4 rounded-xl border-2 transition-all duration-200 focus:outline-none focus:ring-2 text-lg ${
                        urlError || previewError
                          ? 'border-red-300 focus:border-red-500 focus:ring-red-200'
                          : url
                          ? 'border-orange-300 focus:border-orange-500 focus:ring-orange-200'
                          : 'border-gray-200 focus:border-orange-500 focus:ring-orange-200'
                      }`}
                      disabled={isGeneratingPreview}
                    />
                    {url && !urlError && !previewError && (
                      <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
                        <div className="w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center animate-scale-in">
                          <CheckIcon className="w-4 h-4 text-white" />
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {urlError && (
                    <div className="flex items-center space-x-2 text-sm text-red-600 bg-red-50 p-3 rounded-lg animate-shake">
                      <ExclamationCircleIcon className="w-5 h-5 flex-shrink-0" />
                      <span>{urlError}</span>
                    </div>
                  )}
                  {previewError && (
                    <div className="flex items-center space-x-2 text-sm text-red-600 bg-red-50 p-3 rounded-lg animate-shake">
                      <ExclamationCircleIcon className="w-5 h-5 flex-shrink-0" />
                      <span>{previewError}</span>
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={isGeneratingPreview || !url.trim()}
                    className="w-full py-4 bg-gradient-to-r from-orange-500 via-amber-500 to-orange-500 text-white rounded-xl font-bold text-base transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] hover:shadow-2xl hover:shadow-orange-500/40 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 relative overflow-hidden group"
                  >
                    {isGeneratingPreview ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Generating Preview...</span>
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer" />
                      </>
                    ) : (
                      <>
                        <span className="relative z-10 flex items-center">
                          <SparklesIcon className="w-5 h-5 mr-2" />
                          <span>Generate Preview</span>
                        </span>
                        <div className="absolute inset-0 bg-gradient-to-r from-orange-600 via-amber-600 to-orange-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                        <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/20 to-transparent" />
                      </>
                    )}
                  </button>
                </form>

                {/* Example URLs */}
                <div className="mt-6">
                  <p className="text-xs text-gray-500 mb-2 text-center">Try these examples:</p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {['https://github.com', 'https://news.ycombinator.com', 'https://producthunt.com'].map((exampleUrl) => (
                      <button
                        key={exampleUrl}
                        onClick={() => {
                          setUrl(exampleUrl)
                          setUrlError(null)
                        }}
                        className="px-3 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
                      >
                        {exampleUrl.replace('https://', '')}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Preview Display */}
        {step === 'preview' && preview && (
          <div className="space-y-8">
            {/* Progress indicator - all complete */}
            <div className="mb-8">
              <div className="flex items-center justify-center space-x-4 mb-4">
                <div className="flex items-center space-x-2">
                  <div className="w-10 h-10 bg-emerald-500 rounded-full flex items-center justify-center">
                    <CheckIcon className="w-6 h-6 text-white" />
                  </div>
                  <span className="text-sm font-semibold text-gray-700">Step 1</span>
                </div>
                <div className="w-16 h-1 bg-emerald-500 rounded-full" />
                <div className="flex items-center space-x-2">
                  <div className="w-10 h-10 bg-emerald-500 rounded-full flex items-center justify-center">
                    <CheckIcon className="w-6 h-6 text-white" />
                  </div>
                  <span className="text-sm font-semibold text-gray-700">Step 2</span>
                </div>
                <div className="w-16 h-1 bg-emerald-500 rounded-full" />
                <div className="flex items-center space-x-2">
                  <div className="w-10 h-10 bg-emerald-500 rounded-full flex items-center justify-center animate-pulse">
                    <PhotoIcon className="w-6 h-6 text-white" />
                  </div>
                  <span className="text-sm font-semibold text-gray-700">Step 3</span>
                </div>
              </div>
            </div>

            {/* Success Message with animation */}
            <div className="bg-gradient-to-r from-emerald-50 via-teal-50 to-emerald-50 border-2 border-emerald-200 rounded-xl p-8 text-center relative overflow-hidden animate-fade-in">
              <div className="absolute inset-0 bg-gradient-to-r from-emerald-400/10 via-teal-400/10 to-emerald-400/10 animate-pulse" />
              <div className="relative z-10">
                <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg shadow-emerald-500/30 animate-bounce">
                  <CheckIcon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-black text-gray-900 mb-2">Preview Generated!</h3>
                <p className="text-gray-600">Here's how your URL will appear when shared</p>
              </div>
            </div>

            {/* Preview Card with enhanced styling */}
            <div className="bg-white rounded-2xl shadow-2xl border-2 border-gray-200 overflow-hidden transform hover:scale-[1.01] transition-all duration-300 relative group">
              {/* Glow effect */}
              <div className="absolute -inset-1 bg-gradient-to-r from-orange-500 via-amber-500 to-yellow-500 rounded-2xl opacity-0 group-hover:opacity-20 blur-xl transition-opacity duration-300" />
              
              {preview.image_url && (
                <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 relative overflow-hidden">
                  <img
                    src={preview.image_url}
                    alt={preview.title}
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement
                      target.style.display = 'none'
                    }}
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent" />
                </div>
              )}
              <div className="p-6 relative">
                <div className="mb-3 flex items-center justify-between">
                  <span className="inline-block px-4 py-1.5 bg-gradient-to-r from-orange-100 to-amber-100 text-orange-700 text-xs font-bold rounded-full uppercase border border-orange-200">
                    {preview.type}
                  </span>
                  <div className="flex items-center space-x-1 text-amber-500">
                    <StarIcon className="w-4 h-4 fill-amber-400" />
                    <span className="text-xs font-semibold">AI Generated</span>
                  </div>
                </div>
                <h3 className="text-2xl font-black text-gray-900 mb-3 leading-tight">{preview.title}</h3>
                {preview.description && (
                  <p className="text-gray-600 mb-4 leading-relaxed">{preview.description}</p>
                )}
                <div className="flex items-center space-x-2 text-sm text-gray-500 bg-gray-50 rounded-lg p-2">
                  <LinkIcon className="w-4 h-4 text-orange-500" />
                  <span className="truncate font-medium">{preview.url}</span>
                </div>
              </div>
            </div>

            {/* Demo Notice with enhanced styling */}
            <div className="bg-gradient-to-r from-amber-50 via-yellow-50 to-amber-50 border-2 border-amber-200 rounded-xl p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-amber-200/20 rounded-full blur-2xl -mr-16 -mt-16" />
              <div className="relative z-10">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-amber-500 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg shadow-amber-500/30">
                    <PhotoIcon className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-black text-gray-900 mb-1 text-lg">This is a Demo Preview</h4>
                    <p className="text-sm text-gray-700 mb-4">{preview.message}</p>
                    <div className="flex flex-col sm:flex-row gap-3">
                      <Link
                        to="/app"
                        className="group px-6 py-3 bg-gradient-to-r from-orange-500 via-amber-500 to-orange-500 text-white rounded-xl font-bold text-sm transition-all duration-300 hover:scale-[1.02] hover:shadow-xl hover:shadow-orange-500/30 text-center relative overflow-hidden"
                      >
                        <span className="relative z-10 flex items-center justify-center">
                          Get Full Access
                          <ArrowRightIcon className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                        </span>
                        <div className="absolute inset-0 bg-gradient-to-r from-orange-600 via-amber-600 to-orange-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                      </Link>
                      <button
                        onClick={() => {
                          setStep('url')
                          setUrl('')
                          setPreview(null)
                          setPreviewError(null)
                        }}
                        className="px-6 py-3 bg-white border-2 border-gray-200 text-gray-700 rounded-xl font-bold text-sm transition-all duration-300 hover:scale-[1.02] hover:border-orange-300 hover:bg-orange-50"
                      >
                        Try Another URL
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* CTA Section with enhanced styling */}
            <div className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl p-10 text-center text-white relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-orange-500/10 via-amber-500/10 to-yellow-500/10 animate-pulse" />
              <div className="relative z-10">
                <div className="inline-flex items-center space-x-2 px-4 py-2 bg-orange-500/20 rounded-full border border-orange-400/30 mb-4">
                  <SparklesIcon className="w-4 h-4 text-orange-300" />
                  <span className="text-sm font-bold text-orange-200">Limited Time Offer</span>
                </div>
                <h3 className="text-3xl font-black mb-3">Ready to Create Unlimited Previews?</h3>
                <p className="text-gray-300 mb-8 max-w-xl mx-auto text-lg">
                  Join thousands of teams using MetaView to create high-converting URL previews. Start your free trial today.
                </p>
                <div className="flex flex-wrap items-center justify-center gap-4 mb-6">
                  <div className="flex items-center space-x-2 text-sm text-gray-400">
                    <CheckIcon className="w-5 h-5 text-emerald-400" />
                    <span>14-day free trial</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-gray-400">
                    <CheckIcon className="w-5 h-5 text-emerald-400" />
                    <span>No credit card required</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-gray-400">
                    <CheckIcon className="w-5 h-5 text-emerald-400" />
                    <span>Cancel anytime</span>
                  </div>
                </div>
                <Link
                  to="/app"
                  className="group inline-flex items-center space-x-2 px-10 py-5 bg-gradient-to-r from-orange-500 via-amber-500 to-orange-500 text-white rounded-xl font-black text-lg transition-all duration-300 hover:scale-[1.05] hover:shadow-2xl hover:shadow-orange-500/50 relative overflow-hidden"
                >
                  <span className="relative z-10 flex items-center">
                    Start Free Trial
                    <ArrowRightIcon className="w-6 h-6 ml-2 group-hover:translate-x-1 transition-transform" />
                  </span>
                  <div className="absolute inset-0 bg-gradient-to-r from-orange-600 via-amber-600 to-orange-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/20 to-transparent" />
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Custom animations */}
      <style>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes scale-in {
          from {
            opacity: 0;
            transform: scale(0.9);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }
        
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
          20%, 40%, 60%, 80% { transform: translateX(5px); }
        }
        
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        
        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }
        
        .animate-scale-in {
          animation: scale-in 0.3s ease-out;
        }
        
        .animate-shake {
          animation: shake 0.5s ease-in-out;
        }
        
        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
      `}</style>
    </div>
  )
}

