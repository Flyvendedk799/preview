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
  ChartBarIcon,
  ShieldCheckIcon,
  ClockIcon,
} from '@heroicons/react/24/outline'
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid'
import { subscribeToNewsletter, generateDemoPreview, type DemoPreviewResponse } from '../api/client'

type Step = 'input' | 'preview'

export default function Demo() {
  const [step, setStep] = useState<Step>('input')
  const [email, setEmail] = useState('')
  const [url, setUrl] = useState('')
  const [preview, setPreview] = useState<DemoPreviewResponse | null>(null)
  const [scrollY, setScrollY] = useState(0)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [emailSubscribed, setEmailSubscribed] = useState(false)
  const [showEmailSuccess, setShowEmailSuccess] = useState(false)
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null)
  const [showEmailPopup, setShowEmailPopup] = useState(false)
  const [pendingUrl, setPendingUrl] = useState<string>('')
  
  const [emailError, setEmailError] = useState<string | null>(null)
  const [urlError, setUrlError] = useState<string | null>(null)
  const [isSubmittingEmail, setIsSubmittingEmail] = useState(false)
  const [isGeneratingPreview, setIsGeneratingPreview] = useState(false)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [consentChecked, setConsentChecked] = useState(false)
  const [generationStatus, setGenerationStatus] = useState<string>('')
  const [generationProgress, setGenerationProgress] = useState<number>(0)

  const heroRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.pageYOffset)
      
      // Parallax effect on hero
      const hero = heroRef.current
      if (hero) {
        const heroRect = hero.getBoundingClientRect()
        const heroTop = heroRect.top + window.pageYOffset
        const scrolled = window.pageYOffset
        const parallaxOffset = (scrolled - heroTop) * 0.3
        hero.style.transform = `translateY(${parallaxOffset}px)`
      }
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

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setUrlError(null)
    setPreviewError(null)

    // Validate URL
    if (!url.trim()) {
      setUrlError('URL is required')
      return
    }

    // Ensure URL has HTTPS protocol (always use HTTPS)
    let processedUrl = url.trim()
    if (!processedUrl.startsWith('http://') && !processedUrl.startsWith('https://')) {
      processedUrl = `https://${processedUrl}`
    } else if (processedUrl.startsWith('http://')) {
      processedUrl = processedUrl.replace('http://', 'https://')
    }

    if (!validateUrl(processedUrl)) {
      setUrlError('Please enter a valid URL')
      return
    }

    // Store the processed URL and show email popup
    setPendingUrl(processedUrl)
    setShowEmailPopup(true)
  }

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setEmailError(null)
    setPreviewError(null)

    // Validate email
    if (!email.trim()) {
      setEmailError('Email is required')
      return
    }

    if (!validateEmail(email)) {
      setEmailError('Please enter a valid email address')
      return
    }

    if (!consentChecked) {
      setEmailError('Please accept the newsletter subscription to continue')
      return
    }

    // Subscribe to newsletter
    setIsSubmittingEmail(true)
    try {
      await subscribeToNewsletter({
        email: email.trim(),
        source: 'demo',
        consent_given: true,
      })
      setEmailSubscribed(true)
      setShowEmailSuccess(true)
    } catch (error) {
      setEmailError(error instanceof Error ? error.message : 'Failed to subscribe. Please try again.')
      setIsSubmittingEmail(false)
      return
    } finally {
      setIsSubmittingEmail(false)
    }

    // Close popup and generate preview with the stored URL
    setShowEmailPopup(false)
    await generatePreviewWithUrl(pendingUrl)
  }

  const generatePreviewWithUrl = async (urlToProcess: string) => {
    setIsGeneratingPreview(true)
    setGenerationStatus('Analyzing page...')
    setGenerationProgress(10)
    
    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setGenerationProgress((prev) => {
          if (prev >= 90) return prev
          return prev + Math.random() * 10
        })
      }, 500)

      const statusMessages = [
        { progress: 20, message: 'Capturing screenshot...' },
        { progress: 40, message: 'Analyzing visual design...' },
        { progress: 60, message: 'Extracting content...' },
        { progress: 80, message: 'Generating preview...' },
      ]

      let statusIndex = 0
      const statusInterval = setInterval(() => {
        if (statusIndex < statusMessages.length) {
          setGenerationStatus(statusMessages[statusIndex].message)
          setGenerationProgress(statusMessages[statusIndex].progress)
          statusIndex++
        }
      }, 3000)

      const result = await generateDemoPreview(urlToProcess)
      
      clearInterval(progressInterval)
      clearInterval(statusInterval)
      
      setGenerationStatus('Finalizing...')
      setGenerationProgress(100)
      
      // Small delay to show completion
      await new Promise(resolve => setTimeout(resolve, 500))
      
      setPreview(result)
      setStep('preview')
      setGenerationStatus('')
      setGenerationProgress(0)
    } catch (error) {
      setPreviewError(error instanceof Error ? error.message : 'Failed to generate preview. Please try again.')
      setShowEmailPopup(false) // Show error on main form
      setGenerationStatus('')
      setGenerationProgress(0)
    } finally {
      setIsGeneratingPreview(false)
    }
  }

  const platforms = [
    { id: 'instagram', name: 'Instagram', color: 'from-purple-500 to-pink-500', icon: '📷' },
    { id: 'facebook', name: 'Facebook', color: 'from-blue-600 to-blue-700', icon: '👤' },
    { id: 'twitter', name: 'X (Twitter)', color: 'from-gray-900 to-black', icon: '🐦' },
    { id: 'linkedin', name: 'LinkedIn', color: 'from-blue-700 to-blue-800', icon: '💼' },
    { id: 'reddit', name: 'Reddit', color: 'from-orange-500 to-red-500', icon: '🤖' },
  ]

  return (
    <div className="min-h-screen bg-white overflow-x-hidden">
      {/* Premium Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div 
          className="absolute -top-20 -left-20 w-[900px] h-[900px] bg-gradient-to-br from-orange-100/40 via-amber-50/30 to-transparent rounded-full blur-3xl"
          style={{
            transform: `translate(${scrollY * 0.08}px, ${scrollY * 0.12}px)`,
            transition: 'transform 0.15s ease-out'
          }}
        />
        <div 
          className="absolute top-1/4 -right-32 w-[700px] h-[700px] bg-gradient-to-br from-blue-100/50 via-indigo-50/30 to-transparent rounded-full blur-3xl"
          style={{
            transform: `translate(${-scrollY * 0.06}px, ${scrollY * 0.1}px)`,
            transition: 'transform 0.15s ease-out'
          }}
        />
        <div 
          className="absolute inset-0 opacity-[0.015]"
          style={{
            backgroundImage: 'radial-gradient(circle at 1px 1px, rgb(0,0,0) 1px, transparent 0)',
            backgroundSize: '48px 48px',
            transform: `translate(${scrollY * 0.03}px, ${scrollY * 0.03}px)`
          }}
        />
      </div>

      {/* Premium Navigation */}
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

      {/* Hero Section */}
      <section className="relative pt-24 sm:pt-28 pb-12 sm:pb-20 px-4 sm:px-6 lg:px-12">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <div className="inline-flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-orange-100 via-amber-100 to-yellow-100 rounded-full border-2 border-orange-300/80 backdrop-blur-sm mb-6 shadow-md animate-pulse">
              <RocketLaunchIcon className="w-4 h-4 text-orange-600" />
              <span className="text-xs font-black text-orange-800 tracking-wide">AI-Powered Preview Demo</span>
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl xl:text-[3.25rem] font-black text-gray-900 leading-[1.1] tracking-[-0.03em] mb-4">
              See Your URLs{' '}
              <span className="relative inline-block">
                <span className="bg-gradient-to-r from-orange-500 via-amber-500 to-yellow-500 bg-clip-text text-transparent">Come to Life</span>
                <svg className="absolute -bottom-1 left-0 w-full h-2" viewBox="0 0 200 12" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M0 8C50 4 100 8 150 4C175 2 200 6 200 6" stroke="url(#heroGradient)" strokeWidth="3" strokeLinecap="round" />
                  <defs>
                    <linearGradient id="heroGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#f97316" stopOpacity="0.5" />
                      <stop offset="100%" stopColor="#eab308" stopOpacity="0.2" />
                    </linearGradient>
                  </defs>
                </svg>
              </span>
            </h1>
            <p className="text-base sm:text-lg text-gray-600 leading-relaxed max-w-2xl mx-auto">
              Experience our AI-powered preview generation. Enter any URL and see how it transforms into beautiful preview cards across all platforms.
            </p>
          </div>

          {/* Input Step */}
          {step === 'input' && (
            <div className="max-w-2xl mx-auto">
              <div className="bg-white rounded-2xl shadow-2xl border border-gray-200/80 overflow-hidden relative">
                <div className="absolute inset-0 bg-gradient-to-br from-orange-50/50 via-amber-50/30 to-yellow-50/50 opacity-50" />
                
                <div className="relative p-8 sm:p-10">
                  {/* Success overlay */}
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

                  <form onSubmit={handleUrlSubmit} className="space-y-6">
                    {/* URL Input - Primary */}
                    <div>
                      <label htmlFor="url" className="block text-sm font-bold text-gray-900 mb-2">
                        Enter a URL to Preview
                      </label>
                      <div className="relative">
                        <div className="absolute left-4 top-1/2 transform -translate-y-1/2">
                          <GlobeAltIcon className={`w-5 h-5 ${url ? 'text-orange-500' : 'text-gray-400'} transition-colors`} />
                        </div>
                        <input
                          id="url"
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
                        <div className="mt-2 flex items-center space-x-2 text-sm text-red-600 bg-red-50 p-3 rounded-lg animate-shake">
                          <ExclamationCircleIcon className="w-5 h-5 flex-shrink-0" />
                          <span>{urlError}</span>
                        </div>
                      )}
                      {previewError && (
                        <div className="mt-2 flex items-center space-x-2 text-sm text-red-600 bg-red-50 p-3 rounded-lg animate-shake">
                          <ExclamationCircleIcon className="w-5 h-5 flex-shrink-0" />
                          <span>{previewError}</span>
                        </div>
                      )}
                    </div>

                    {/* Submit Button */}
                    <button
                      type="submit"
                      disabled={isGeneratingPreview || !url.trim()}
                      className="w-full py-4 bg-gradient-to-r from-orange-500 via-amber-500 to-orange-500 text-white rounded-xl font-bold text-base transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] hover:shadow-2xl hover:shadow-orange-500/40 disabled:opacity-50 disabled:cursor-not-allowed flex flex-col items-center justify-center space-y-2 relative overflow-hidden group"
                    >
                      {isGeneratingPreview ? (
                        <>
                          <div className="w-full space-y-3">
                            <div className="flex items-center justify-center space-x-2">
                              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                              <span className="text-sm font-semibold">{generationStatus || 'Generating Preview...'}</span>
                            </div>
                            {/* Progress Bar */}
                            <div className="w-full bg-white/20 rounded-full h-2 overflow-hidden">
                              <div 
                                className="h-full bg-white rounded-full transition-all duration-500 ease-out"
                                style={{ width: `${generationProgress}%` }}
                              />
                            </div>
                            <div className="text-xs text-white/80 text-center">{Math.round(generationProgress)}%</div>
                          </div>
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

                  {/* Trust Indicators */}
                  <div className="mt-6 flex flex-wrap items-center justify-center gap-4 text-xs text-gray-500">
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

          {/* Email Popup Modal */}
          {showEmailPopup && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
              <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 relative animate-scale-in">
                {/* Close button */}
                <button
                  onClick={() => {
                    setShowEmailPopup(false)
                    setEmail('')
                    setConsentChecked(false)
                    setEmailError(null)
                  }}
                  className="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-600 transition-colors"
                  aria-label="Close"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>

                <div className="text-center mb-6">
                  <div className="w-16 h-16 bg-gradient-to-br from-orange-500 via-amber-500 to-yellow-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-orange-500/30">
                    <EnvelopeIcon className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-black text-gray-900 mb-2">Get Updates</h3>
                  <p className="text-gray-600 text-sm">Stay updated with new features and exclusive tips</p>
                </div>

                <form onSubmit={handleEmailSubmit} className="space-y-4">
                  {/* Email Input */}
                  <div>
                    <label htmlFor="popup-email" className="block text-sm font-semibold text-gray-900 mb-2">
                      Email Address
                    </label>
                    <input
                      id="popup-email"
                      type="email"
                      value={email}
                      onChange={(e) => {
                        setEmail(e.target.value)
                        setEmailError(null)
                      }}
                      placeholder="your@email.com"
                      className={`w-full px-4 py-3 rounded-xl border-2 transition-all duration-200 focus:outline-none focus:ring-2 text-base ${
                        emailError
                          ? 'border-red-300 focus:border-red-500 focus:ring-red-200'
                          : 'border-gray-200 focus:border-orange-500 focus:ring-orange-200'
                      }`}
                      disabled={isSubmittingEmail || isGeneratingPreview}
                      autoFocus
                    />
                  </div>

                  {/* Consent Checkbox */}
                  <div className="flex items-start space-x-3">
                    <input
                      type="checkbox"
                      id="popup-consent"
                      checked={consentChecked}
                      onChange={(e) => {
                        setConsentChecked(e.target.checked)
                        setEmailError(null)
                      }}
                      className="mt-1 w-5 h-5 rounded border-gray-300 text-orange-500 focus:ring-orange-500 focus:ring-2 cursor-pointer"
                      disabled={isSubmittingEmail || isGeneratingPreview}
                      required
                    />
                    <label htmlFor="popup-consent" className="flex-1 text-sm text-gray-700 cursor-pointer">
                      I agree to receive newsletter updates and marketing emails from MetaView
                    </label>
                  </div>

                  {emailError && (
                    <div className="flex items-center space-x-2 text-sm text-red-600 bg-red-50 p-3 rounded-lg animate-shake">
                      <ExclamationCircleIcon className="w-5 h-5 flex-shrink-0" />
                      <span>{emailError}</span>
                    </div>
                  )}

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={isSubmittingEmail || isGeneratingPreview || !email.trim() || !consentChecked}
                    className="w-full py-4 bg-gradient-to-r from-orange-500 via-amber-500 to-orange-500 text-white rounded-xl font-bold text-base transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] hover:shadow-2xl hover:shadow-orange-500/40 disabled:opacity-50 disabled:cursor-not-allowed flex flex-col items-center justify-center space-y-2 relative overflow-hidden group"
                  >
                    {isSubmittingEmail ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Subscribing...</span>
                      </>
                    ) : isGeneratingPreview ? (
                      <>
                        <div className="w-full space-y-3">
                          <div className="flex items-center justify-center space-x-2">
                            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            <span className="text-sm font-semibold">{generationStatus || 'Generating Preview...'}</span>
                          </div>
                          {/* Progress Bar */}
                          <div className="w-full bg-white/20 rounded-full h-2 overflow-hidden">
                            <div 
                              className="h-full bg-white rounded-full transition-all duration-500 ease-out"
                              style={{ width: `${generationProgress}%` }}
                            />
                          </div>
                          <div className="text-xs text-white/80 text-center">{Math.round(generationProgress)}%</div>
                        </div>
                      </>
                    ) : (
                      <>
                        <span className="relative z-10 flex items-center">
                          <CheckIcon className="w-5 h-5 mr-2" />
                          <span>Continue</span>
                        </span>
                        <div className="absolute inset-0 bg-gradient-to-r from-orange-600 via-amber-600 to-orange-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                      </>
                    )}
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* Preview Step */}
          {step === 'preview' && preview && (
            <div className="space-y-12">
              {/* Success Banner with AI Confidence */}
              <div className="bg-gradient-to-r from-emerald-50 via-teal-50 to-emerald-50 border-2 border-emerald-200 rounded-xl p-8 text-center relative overflow-hidden animate-fade-in">
                <div className="absolute inset-0 bg-gradient-to-r from-emerald-400/10 via-teal-400/10 to-emerald-400/10 animate-pulse" />
                <div className="relative z-10">
                  <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg shadow-emerald-500/30 animate-bounce">
                    <CheckIcon className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-black text-gray-900 mb-2">AI Analysis Complete!</h3>
                  <p className="text-gray-600 mb-4">Deep UI/UX intelligence applied to your page</p>
                  
                  {/* AI Confidence Indicator */}
                  <div className="flex items-center justify-center space-x-4">
                    <div className="flex items-center space-x-2 bg-white/80 px-4 py-2 rounded-full">
                      <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                      <span className="text-sm font-semibold text-gray-700">
                        AI Confidence: {Math.round(preview.confidence * 100)}%
                      </span>
                    </div>
                    <div className="bg-white/80 px-4 py-2 rounded-full">
                      <span className="text-sm font-semibold text-gray-700 capitalize">
                        Intent: {preview.design_intent}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Design Intelligence Summary */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Quality Metrics */}
                <div className="bg-gradient-to-br from-violet-50 to-purple-50 rounded-xl p-6 border border-violet-200">
                  <h4 className="font-bold text-violet-900 mb-4 flex items-center">
                    <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    Design Quality
                  </h4>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-600">Visual Hierarchy</span>
                        <span className="font-semibold text-violet-700">{Math.round(preview.quality.hierarchy_score * 100)}%</span>
                      </div>
                      <div className="h-2 bg-violet-200 rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-violet-500 to-purple-500 rounded-full transition-all duration-500" style={{ width: `${preview.quality.hierarchy_score * 100}%` }} />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-600">Message Clarity</span>
                        <span className="font-semibold text-violet-700">{Math.round(preview.quality.clarity_score * 100)}%</span>
                      </div>
                      <div className="h-2 bg-violet-200 rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-violet-500 to-purple-500 rounded-full transition-all duration-500" style={{ width: `${preview.quality.clarity_score * 100}%` }} />
                      </div>
                    </div>
                    <div className="pt-2 border-t border-violet-200">
                      <span className="text-xs text-gray-500">Clutter Assessment: </span>
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                        preview.quality.clutter === 'clean' ? 'bg-green-100 text-green-700' :
                        preview.quality.clutter === 'moderate' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {preview.quality.clutter}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Value Proposition */}
                <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-6 border border-blue-200">
                  <h4 className="font-bold text-blue-900 mb-4 flex items-center">
                    <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    AI Interpretation
                  </h4>
                  <div className="space-y-3">
                    <div>
                      <span className="text-xs text-gray-500 uppercase tracking-wide">Primary Message</span>
                      <p className="text-sm font-medium text-gray-800 mt-1">{preview.primary_message || 'Not detected'}</p>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500 uppercase tracking-wide">Value Proposition</span>
                      <p className="text-sm font-medium text-gray-800 mt-1">{preview.value_proposition || 'Not detected'}</p>
                    </div>
                  </div>
                </div>

                {/* Extracted Content */}
                <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl p-6 border border-amber-200">
                  <h4 className="font-bold text-amber-900 mb-4 flex items-center">
                    <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Key Content
                  </h4>
                  <div className="space-y-2">
                    {preview.content.headline && (
                      <div className="text-sm">
                        <span className="text-gray-500">Headline: </span>
                        <span className="font-medium text-gray-800">{preview.content.headline}</span>
                      </div>
                    )}
                    {preview.content.cta && (
                      <div className="text-sm">
                        <span className="text-gray-500">CTA: </span>
                        <span className="font-semibold text-orange-600">{preview.content.cta}</span>
                      </div>
                    )}
                    {preview.content.features.length > 0 && (
                      <div className="pt-2">
                        <span className="text-xs text-gray-500 uppercase tracking-wide">Key Features</span>
                        <div className="flex flex-wrap gap-1.5 mt-1.5">
                          {preview.content.features.slice(0, 3).map((feature, i) => (
                            <span key={i} className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs rounded-full">
                              {feature}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Main Preview Card with Visual Guidance */}
              <div className="bg-white rounded-2xl shadow-2xl border-2 border-gray-200 overflow-hidden relative group">
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
                    
                    {/* Visual Guidance Overlay - Show emphasis zones */}
                    {preview.visual_guidance.emphasis_zones.length > 0 && (
                      <div className="absolute inset-0 pointer-events-none">
                        {preview.visual_guidance.emphasis_zones.slice(0, 3).map((zone, i) => (
                          <div
                            key={i}
                            className="absolute border-2 border-dashed border-orange-400/50 rounded-lg bg-orange-500/10 transition-all duration-300"
                            style={{
                              left: `${zone.x * 100}%`,
                              top: `${zone.y * 100}%`,
                              width: `${zone.width * 100}%`,
                              height: `${zone.height * 100}%`,
                            }}
                            title={zone.reason}
                          >
                            <span className="absolute -top-5 left-0 text-xs bg-orange-500 text-white px-2 py-0.5 rounded">
                              #{zone.priority}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {/* Style Badge */}
                    <div className="absolute top-4 right-4 bg-black/60 backdrop-blur-sm px-3 py-1.5 rounded-full">
                      <span className="text-xs font-semibold text-white capitalize">
                        Style: {preview.visual_guidance.style}
                      </span>
                    </div>
                  </div>
                )}
                <div className="p-6 relative">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="inline-block px-4 py-1.5 bg-gradient-to-r from-orange-100 to-amber-100 text-orange-700 text-xs font-bold rounded-full uppercase border border-orange-200">
                      {preview.design_intent}
                    </span>
                    <div className="flex items-center space-x-1 text-amber-500">
                      <StarIcon className="w-4 h-4 fill-amber-400" />
                      <span className="text-xs font-semibold">AI Intelligence</span>
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

              {/* Content Variants Section */}
              <div className="bg-gradient-to-br from-gray-50 to-white rounded-2xl p-8 border border-gray-200">
                <div className="text-center mb-8">
                  <h3 className="text-2xl font-black text-gray-900 mb-2">AI Content Variants</h3>
                  <p className="text-gray-600">Different messaging approaches for A/B testing</p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Action-Oriented */}
                  <div className="bg-white rounded-xl p-5 border-2 border-blue-200 hover:border-blue-400 transition-colors">
                    <div className="flex items-center space-x-2 mb-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                        <svg className="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                      </div>
                      <span className="text-sm font-bold text-blue-700">Action-Oriented</span>
                    </div>
                    <h4 className="font-bold text-gray-900 mb-2 text-sm">{preview.variants.action_oriented.title || 'N/A'}</h4>
                    <p className="text-gray-600 text-xs">{preview.variants.action_oriented.description || 'N/A'}</p>
                  </div>

                  {/* Benefit-Focused */}
                  <div className="bg-white rounded-xl p-5 border-2 border-green-200 hover:border-green-400 transition-colors">
                    <div className="flex items-center space-x-2 mb-3">
                      <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                        <svg className="w-4 h-4 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <span className="text-sm font-bold text-green-700">Benefit-Focused</span>
                    </div>
                    <h4 className="font-bold text-gray-900 mb-2 text-sm">{preview.variants.benefit_focused.title || 'N/A'}</h4>
                    <p className="text-gray-600 text-xs">{preview.variants.benefit_focused.description || 'N/A'}</p>
                  </div>

                  {/* Emotional */}
                  <div className="bg-white rounded-xl p-5 border-2 border-purple-200 hover:border-purple-400 transition-colors">
                    <div className="flex items-center space-x-2 mb-3">
                      <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                        <svg className="w-4 h-4 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                        </svg>
                      </div>
                      <span className="text-sm font-bold text-purple-700">Emotional</span>
                    </div>
                    <h4 className="font-bold text-gray-900 mb-2 text-sm">{preview.variants.emotional.title || 'N/A'}</h4>
                    <p className="text-gray-600 text-xs">{preview.variants.emotional.description || 'N/A'}</p>
                  </div>
                </div>
              </div>

              {/* AI Reasoning (Collapsible) */}
              {preview.reasoning && (
                <details className="bg-gray-50 rounded-xl border border-gray-200 overflow-hidden group">
                  <summary className="px-6 py-4 cursor-pointer hover:bg-gray-100 transition-colors flex items-center justify-between">
                    <span className="font-bold text-gray-900 flex items-center">
                      <svg className="w-5 h-5 mr-2 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      AI Reasoning
                    </span>
                    <svg className="w-5 h-5 text-gray-400 transform transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </summary>
                  <div className="px-6 py-4 border-t border-gray-200 bg-white">
                    <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{preview.reasoning}</p>
                  </div>
                </details>
              )}

              {/* Mobile Platform Showcase */}
              <div className="bg-gradient-to-br from-gray-50 to-white rounded-2xl p-8 sm:p-10 border border-gray-200">
                <div className="text-center mb-8">
                  <h3 className="text-2xl sm:text-3xl font-black text-gray-900 mb-2">See It In Action</h3>
                  <p className="text-gray-600">How your preview appears on social media platforms</p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
                  {platforms.map((platform) => (
                    <div
                      key={platform.id}
                      className="flex flex-col items-center group cursor-pointer"
                      onClick={() => setSelectedPlatform(selectedPlatform === platform.id ? null : platform.id)}
                    >
                      {/* Mobile Device Frame */}
                      <div className="relative w-full max-w-[280px] transform transition-all duration-300 group-hover:scale-105">
                        {/* Device Frame */}
                        <div className="relative bg-gray-900 rounded-[2.5rem] p-1.5 shadow-2xl">
                          {/* Notch */}
                          <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-32 h-6 bg-gray-900 rounded-b-2xl z-10"></div>
                          
                          {/* Screen */}
                          <div className="bg-white rounded-[2rem] overflow-hidden">
                            {/* Status Bar */}
                            <div className="h-8 bg-gray-50 flex items-center justify-between px-4 text-xs">
                              <span className="font-semibold">9:41</span>
                              <div className="flex items-center space-x-1">
                                <div className="w-4 h-2 border border-gray-400 rounded-sm">
                                  <div className="w-full h-full bg-gray-400 rounded-sm"></div>
                                </div>
                                <div className="w-5 h-2.5 border border-gray-400 rounded-sm">
                                  <div className="w-3/4 h-full bg-gray-400 rounded-sm"></div>
                                </div>
                              </div>
                            </div>

                            {/* Platform Header */}
                            <div className={`h-12 bg-gradient-to-r ${platform.color} flex items-center justify-between px-4 text-white`}>
                              <div className="flex items-center space-x-2">
                                <div className="w-6 h-6 bg-white/20 rounded flex items-center justify-center text-xs">
                                  {platform.icon}
                                </div>
                                <span className="text-xs font-bold uppercase">{platform.name}</span>
                              </div>
                              <div className="w-1 h-1 bg-white rounded-full"></div>
                            </div>

                            {/* Preview Content */}
                            <div className="p-3 space-y-2 bg-white">
                              {/* Avatar/Profile */}
                              <div className="flex items-center space-x-2">
                                <div className={`w-8 h-8 bg-gradient-to-r ${platform.color} rounded-full flex items-center justify-center text-white text-xs font-bold`}>
                                  {platform.icon}
                                </div>
                                <div className="h-2.5 bg-gray-300 rounded w-20"></div>
                              </div>

                              {/* Preview Image */}
                              {preview.image_url ? (
                                <div className="aspect-video bg-gray-100 rounded-lg overflow-hidden">
                                  <img
                                    src={preview.image_url}
                                    alt={preview.title}
                                    className="w-full h-full object-cover"
                                  />
                                </div>
                              ) : (
                                <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 rounded-lg"></div>
                              )}

                              {/* Preview Text */}
                              <div className="space-y-1.5">
                                <div className="h-3 bg-gray-300 rounded w-full"></div>
                                <div className="h-2.5 bg-gray-200 rounded w-4/5"></div>
                                <div className="h-2 bg-gray-200 rounded w-2/3"></div>
                              </div>

                              {/* Actions Bar */}
                              <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                                <div className="flex items-center space-x-4">
                                  <div className="w-5 h-5 bg-gray-200 rounded"></div>
                                  <div className="w-5 h-5 bg-gray-200 rounded"></div>
                                  <div className="w-5 h-5 bg-gray-200 rounded"></div>
                                </div>
                                <div className="w-5 h-5 bg-gray-200 rounded"></div>
                              </div>
                            </div>

                            {/* Home Indicator */}
                            <div className="h-2 flex items-center justify-center">
                              <div className="w-32 h-1 bg-gray-300 rounded-full"></div>
                            </div>
                          </div>
                        </div>
                      </div>
                      <p className="mt-4 text-sm font-semibold text-gray-700">{platform.name}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Demo Notice & CTAs */}
              <div className="bg-gradient-to-r from-amber-50 via-yellow-50 to-amber-50 border-2 border-amber-200 rounded-xl p-8 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-amber-200/20 rounded-full blur-2xl -mr-16 -mt-16" />
                <div className="relative z-10">
                  <div className="flex items-start space-x-4">
                    <div className="w-12 h-12 bg-amber-500 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg shadow-amber-500/30">
                      <PhotoIcon className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-black text-gray-900 mb-1 text-lg">This is a Demo Preview</h4>
                      <p className="text-sm text-gray-700 mb-6">{preview.message}</p>
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
                            setStep('input')
                            setUrl('')
                            setPreview(null)
                            setPreviewError(null)
                            setSelectedPlatform(null)
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

              {/* Final CTA Section */}
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
      </section>

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

