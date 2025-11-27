import { Link } from 'react-router-dom'
import { useEffect, useRef, useState, useCallback } from 'react'
import { getApiBaseUrl } from '../api/client'
import {
  CheckIcon,
  ArrowRightIcon,
  LinkIcon,
  BoltIcon,
  ChartBarIcon,
  PuzzlePieceIcon,
  StarIcon,
  CodeBracketIcon,
  PhotoIcon,
  SparklesIcon,
  ArrowUpRightIcon,
  Bars3Icon,
  XMarkIcon,
  ShieldCheckIcon,
  ClockIcon,
  RocketLaunchIcon,
} from '@heroicons/react/24/outline'
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid'

// Animated counter hook for stats
function useCountUp(target: number, duration: number = 2000, startOnView: boolean = true) {
  const [count, setCount] = useState(0)
  const [hasStarted, setHasStarted] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!startOnView) {
      setHasStarted(true)
    }
  }, [startOnView])

  useEffect(() => {
    if (startOnView && ref.current) {
      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting && !hasStarted) {
            setHasStarted(true)
          }
        },
        { threshold: 0.5 }
      )
      observer.observe(ref.current)
      return () => observer.disconnect()
    }
  }, [startOnView, hasStarted])

  useEffect(() => {
    if (!hasStarted) return
    
    let startTime: number
    const animate = (currentTime: number) => {
      if (!startTime) startTime = currentTime
      const progress = Math.min((currentTime - startTime) / duration, 1)
      // Ease out cubic for smooth deceleration
      const easeOut = 1 - Math.pow(1 - progress, 3)
      setCount(Math.floor(easeOut * target))
      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }
    requestAnimationFrame(animate)
  }, [hasStarted, target, duration])

  return { count, ref }
}

export default function Landing() {
  const [isVisible, setIsVisible] = useState(false)
  const [scrollY, setScrollY] = useState(0)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [activeNavItem, setActiveNavItem] = useState('')
  const heroRef = useRef<HTMLDivElement>(null)
  const sectionRefs = useRef<(HTMLDivElement | null)[]>([])
  
  // Animated counters for stats section
  const stat1 = useCountUp(2000, 2000)
  const stat2 = useCountUp(40, 1500)
  const stat3 = useCountUp(10, 1800)
  const stat4 = useCountUp(99, 2200)

  useEffect(() => {
    setIsVisible(true)
    
    // Scroll handler for parallax, scroll position, and active nav tracking
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
      
      // Track active nav section for visual feedback
      const sections = ['product', 'features', 'pricing', 'docs']
      for (const section of sections) {
        const element = document.getElementById(section)
        if (element) {
          const rect = element.getBoundingClientRect()
          if (rect.top <= 100 && rect.bottom >= 100) {
            setActiveNavItem(section)
            break
          }
        }
      }
    }

    // Intersection Observer for staggered fade-in animations
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -80px 0px'
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          // Add staggered animation delay based on element index
          const children = entry.target.querySelectorAll('[data-animate]')
          children.forEach((child, index) => {
            setTimeout(() => {
              child.classList.add('animate-fade-in-up')
            }, index * 80) // 80ms stagger
          })
          entry.target.classList.add('animate-fade-in-up')
          observer.unobserve(entry.target)
        }
      })
    }, observerOptions)

    // Observe all sections
    sectionRefs.current.forEach(ref => {
      if (ref) observer.observe(ref)
    })

    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => {
      window.removeEventListener('scroll', handleScroll)
      observer.disconnect()
    }
  }, [])

  return (
    <div className="min-h-screen bg-white overflow-x-hidden">
      {/* Premium Animated Background with Enhanced Depth */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        {/* Primary gradient orb - warm accent */}
        <div 
          className="absolute -top-20 -left-20 w-[900px] h-[900px] bg-gradient-to-br from-amber-100/40 via-orange-50/30 to-transparent rounded-full blur-3xl"
          style={{
            transform: `translate(${scrollY * 0.08}px, ${scrollY * 0.12}px)`,
            transition: 'transform 0.15s ease-out'
          }}
        />
        {/* Secondary gradient orb - cool accent */}
        <div 
          className="absolute top-1/4 -right-32 w-[700px] h-[700px] bg-gradient-to-br from-blue-100/50 via-indigo-50/30 to-transparent rounded-full blur-3xl"
          style={{
            transform: `translate(${-scrollY * 0.06}px, ${scrollY * 0.1}px)`,
            transition: 'transform 0.15s ease-out'
          }}
        />
        {/* Tertiary gradient orb */}
        <div 
          className="absolute bottom-0 left-1/4 w-[600px] h-[600px] bg-gradient-to-br from-emerald-50/30 via-teal-50/20 to-transparent rounded-full blur-3xl"
          style={{
            transform: `translate(${scrollY * 0.05}px, ${-scrollY * 0.08}px)`,
            transition: 'transform 0.15s ease-out'
          }}
        />
        
        {/* Refined grid pattern */}
        <div 
          className="absolute inset-0 opacity-[0.015]"
          style={{
            backgroundImage: 'radial-gradient(circle at 1px 1px, rgb(0,0,0) 1px, transparent 0)',
            backgroundSize: '48px 48px',
            transform: `translate(${scrollY * 0.03}px, ${scrollY * 0.03}px)`
          }}
        />
      </div>

      {/* Premium Navigation with Enhanced Contrast */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-2xl border-b border-gray-100/80 transition-all duration-300" style={{ boxShadow: scrollY > 10 ? '0 4px 20px rgba(0,0,0,0.06)' : 'none' }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-12">
          <div className="flex items-center justify-between h-16 sm:h-18">
            <div className="flex items-center space-x-2 sm:space-x-3 group cursor-pointer">
              <div className="relative">
                <div className="w-9 h-9 sm:w-10 sm:h-10 bg-gradient-to-br from-orange-500 via-amber-500 to-yellow-500 rounded-xl flex items-center justify-center shadow-lg shadow-orange-500/25 group-hover:scale-110 group-hover:shadow-orange-500/40 transition-all duration-300">
                  <span className="text-white font-black text-base sm:text-lg">M</span>
                </div>
                <div className="absolute -inset-1 bg-gradient-to-br from-orange-400 to-amber-500 rounded-xl opacity-0 group-hover:opacity-40 blur-lg transition-opacity duration-300" />
              </div>
              <span className="text-lg sm:text-xl font-black text-gray-900 tracking-tight">MetaView</span>
            </div>
            <div className="hidden lg:flex items-center space-x-10">
              {[
                { href: '#product', label: 'Product', id: 'product' },
                { href: '#features', label: 'Features', id: 'features' },
                { href: '#pricing', label: 'Pricing', id: 'pricing' },
                { href: '#docs', label: 'Docs', id: 'docs' },
              ].map((item) => (
                <a 
                  key={item.id}
                  href={item.href} 
                  className={`relative py-1 font-semibold text-sm transition-all duration-200 group ${
                    activeNavItem === item.id ? 'text-orange-600' : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {item.label}
                  <span className={`absolute bottom-0 left-0 h-0.5 bg-orange-500 transition-all duration-300 ${
                    activeNavItem === item.id ? 'w-full' : 'w-0 group-hover:w-full'
                  }`} />
                </a>
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
                className="hidden sm:flex group relative px-5 sm:px-6 py-2.5 bg-gradient-to-r from-orange-500 via-amber-500 to-orange-500 text-white rounded-xl font-bold text-xs sm:text-sm transition-all duration-300 hover:scale-[1.04] active:scale-[0.98] hover:shadow-xl hover:shadow-orange-500/30 overflow-hidden min-h-[42px] items-center justify-center select-none"
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
                <a 
                  href="#product" 
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-4 py-3 text-gray-700 hover:bg-orange-50 hover:text-orange-600 rounded-xl transition-colors font-semibold text-base min-h-[44px] flex items-center"
                >
                  Product
                </a>
                <a 
                  href="#features" 
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-4 py-3 text-gray-700 hover:bg-orange-50 hover:text-orange-600 rounded-xl transition-colors font-semibold text-base min-h-[44px] flex items-center"
                >
                  Features
                </a>
                <a 
                  href="#pricing" 
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-4 py-3 text-gray-700 hover:bg-orange-50 hover:text-orange-600 rounded-xl transition-colors font-semibold text-base min-h-[44px] flex items-center"
                >
                  Pricing
                </a>
                <a 
                  href="#docs" 
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-4 py-3 text-gray-700 hover:bg-orange-50 hover:text-orange-600 rounded-xl transition-colors font-semibold text-base min-h-[44px] flex items-center"
                >
                  Docs
                </a>
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

      {/* Hero Section - High-Converting Design */}
      <section className="relative pt-24 sm:pt-28 pb-12 sm:pb-20 px-4 sm:px-6 lg:px-12">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 sm:gap-14 items-center">
            <div className={`space-y-6 transition-all duration-1000 ease-out ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
              <div className="space-y-5">
                {/* Urgency Badge */}
                <div className="inline-flex items-center space-x-2 px-3 py-1.5 bg-gradient-to-r from-orange-50 via-amber-50 to-yellow-50 rounded-full border border-orange-200/60 backdrop-blur-sm w-fit shadow-sm">
                  <div className="flex items-center space-x-1">
                    <RocketLaunchIcon className="w-3.5 h-3.5 text-orange-600" />
                    <span className="text-xs font-bold text-orange-700 tracking-wide">New: AI-Powered Preview Generation</span>
                  </div>
                  <span className="text-xs text-orange-500 font-semibold">→</span>
                </div>
                <h1 className="text-3xl sm:text-4xl lg:text-5xl xl:text-[3.25rem] font-black text-gray-900 leading-[1.1] tracking-[-0.03em]">
                  Turn every shared link into a{' '}
                  <span className="relative inline-block">
                    <span className="bg-gradient-to-r from-orange-500 via-amber-500 to-yellow-500 bg-clip-text text-transparent">high-converting</span>
                    <svg className="absolute -bottom-1 left-0 w-full h-2" viewBox="0 0 200 12" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M0 8C50 4 100 8 150 4C175 2 200 6 200 6" stroke="url(#heroGradient)" strokeWidth="3" strokeLinecap="round" />
                      <defs>
                        <linearGradient id="heroGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                          <stop offset="0%" stopColor="#f97316" stopOpacity="0.5" />
                          <stop offset="100%" stopColor="#eab308" stopOpacity="0.2" />
                        </linearGradient>
                      </defs>
                    </svg>
                  </span>{' '}
                  preview
                </h1>
                <p className="text-base sm:text-lg text-gray-600 leading-relaxed max-w-lg">
                  AI-powered URL previews that automatically generate beautiful, branded cards. 
                  Increase click-through rates by up to <span className="font-bold text-orange-600 bg-orange-50 px-1.5 py-0.5 rounded">40%</span> with zero coding.
                </p>
              </div>
              
              {/* CTA Buttons with Strong Visual Hierarchy & Micro-interactions */}
              <div className="flex flex-col sm:flex-row gap-3">
                <Link 
                  to="/app" 
                  className="group relative px-6 sm:px-7 py-3.5 bg-gradient-to-r from-orange-500 via-amber-500 to-orange-500 text-white rounded-xl font-bold text-sm transition-all duration-300 hover:scale-[1.03] active:scale-[0.98] hover:shadow-xl hover:shadow-orange-500/30 inline-flex items-center justify-center overflow-hidden min-h-[48px] select-none"
                >
                  <span className="relative z-10 flex items-center">
                    Start Free Trial
                    <ArrowRightIcon className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform duration-300" />
                  </span>
                  <div className="absolute inset-0 bg-gradient-to-r from-orange-600 via-amber-600 to-orange-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  {/* Shine sweep effect */}
                  <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/20 to-transparent" />
                </Link>
                <Link 
                  to="/app" 
                  className="group px-6 sm:px-7 py-3.5 bg-white text-gray-800 rounded-xl font-bold text-sm border-2 border-gray-200 hover:border-orange-200 hover:bg-orange-50/50 transition-all duration-300 hover:scale-[1.03] active:scale-[0.98] hover:shadow-lg inline-flex items-center justify-center min-h-[48px] select-none"
                >
                  Watch Demo
                  <span className="ml-2 text-xs bg-gray-100 group-hover:bg-orange-100 px-2 py-0.5 rounded-full text-gray-500 group-hover:text-orange-600 transition-colors duration-200">2 min</span>
                </Link>
              </div>
              
              {/* Trust Signals */}
              <div className="flex flex-wrap items-center gap-3 sm:gap-5 pt-1">
                {[
                  { icon: ClockIcon, text: '14-day free trial', color: 'emerald' },
                  { icon: ShieldCheckIcon, text: 'No credit card', color: 'blue' },
                  { icon: BoltIcon, text: '5 min setup', color: 'purple' },
                ].map((item, i) => (
                  <div key={i} className="flex items-center space-x-2 group">
                    <div className={`w-5 h-5 rounded-md flex items-center justify-center transition-transform duration-300 group-hover:scale-110 ${
                      item.color === 'emerald' ? 'bg-emerald-100' :
                      item.color === 'blue' ? 'bg-blue-100' : 'bg-purple-100'
                    }`}>
                      <item.icon className={`w-3 h-3 ${
                        item.color === 'emerald' ? 'text-emerald-600' :
                        item.color === 'blue' ? 'text-blue-600' : 'text-purple-600'
                      }`} />
                    </div>
                    <span className="text-sm text-gray-600 font-medium">{item.text}</span>
                  </div>
                ))}
              </div>

              {/* Social Proof Mini-Section */}
              <div className="flex items-center gap-4 pt-2 border-t border-gray-100">
                <div className="flex -space-x-2">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className={`w-8 h-8 rounded-full border-2 border-white shadow-sm ${
                      i === 1 ? 'bg-gradient-to-br from-blue-400 to-blue-600' :
                      i === 2 ? 'bg-gradient-to-br from-purple-400 to-purple-600' :
                      i === 3 ? 'bg-gradient-to-br from-green-400 to-green-600' :
                      'bg-gradient-to-br from-orange-400 to-orange-600'
                    }`} />
                  ))}
                </div>
                <div className="flex flex-col">
                  <div className="flex items-center">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <StarIconSolid key={i} className="w-3.5 h-3.5 text-amber-400" />
                    ))}
                    <span className="ml-1.5 text-xs font-bold text-gray-900">4.9</span>
                  </div>
                  <span className="text-xs text-gray-500">Loved by 2,000+ teams</span>
                </div>
              </div>
            </div>
            
            {/* Premium Floating Mockup with Enhanced Design */}
            <div 
              ref={heroRef}
              className={`relative transition-all duration-1000 ease-out ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}
              style={{ transitionDelay: '200ms' }}
            >
              <div className="relative">
                {/* Main Floating Card */}
                <div className="relative group">
                  {/* Enhanced glow effect */}
                  <div className="absolute -inset-4 bg-gradient-to-r from-orange-500/20 via-amber-500/20 to-yellow-500/20 rounded-3xl blur-2xl opacity-50 group-hover:opacity-70 transition-opacity duration-500" />
                  
                  {/* Card */}
                  <div className="relative bg-white rounded-2xl shadow-2xl shadow-gray-900/15 border border-gray-200/80 overflow-hidden transform hover:scale-[1.01] transition-all duration-500">
                    {/* Browser chrome - more realistic */}
                    <div className="h-11 bg-gradient-to-b from-gray-100 to-gray-50 border-b border-gray-200 flex items-center px-4 space-x-2">
                      <div className="w-3 h-3 rounded-full bg-red-400" />
                      <div className="w-3 h-3 rounded-full bg-amber-400" />
                      <div className="w-3 h-3 rounded-full bg-green-400" />
                      <div className="flex-1 mx-4 h-7 bg-white rounded-md border border-gray-200 flex items-center px-3">
                        <svg className="w-3.5 h-3.5 text-gray-400 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.132A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457.39-2.823 1.07-4" />
                        </svg>
                        <span className="text-xs text-gray-500 font-medium">yoursite.com/article</span>
                      </div>
                    </div>
                    
                    {/* Content area with realistic preview */}
                    <div className="aspect-[16/10] bg-gradient-to-br from-orange-50/50 via-white to-amber-50/30 flex items-center justify-center p-8 relative overflow-hidden">
                      {/* Subtle pattern */}
                      <div className="absolute inset-0 opacity-[0.03]" style={{
                        backgroundImage: 'radial-gradient(circle at 1px 1px, rgb(0,0,0) 1px, transparent 0)',
                        backgroundSize: '32px 32px'
                      }} />
                      
                      {/* Preview card mockup - more realistic */}
                      <div className="relative w-full max-w-sm bg-white rounded-xl shadow-xl shadow-gray-900/10 border border-gray-100 overflow-hidden transform hover:scale-[1.02] transition-transform duration-500">
                        {/* Image preview */}
                        <div className="h-32 bg-gradient-to-br from-orange-100 via-amber-50 to-yellow-100 relative overflow-hidden">
                          <div className="absolute inset-0 flex items-center justify-center">
                            <div className="w-12 h-12 rounded-xl bg-white/80 backdrop-blur-sm shadow-lg flex items-center justify-center">
                              <PhotoIcon className="w-6 h-6 text-orange-400" />
                            </div>
                          </div>
                        </div>
                        {/* Content */}
                        <div className="p-5 space-y-3">
                          <div className="h-5 bg-gradient-to-r from-gray-900 via-gray-800 to-gray-700 rounded w-4/5" />
                          <div className="space-y-2">
                            <div className="h-2.5 bg-gray-200 rounded-full w-full" />
                            <div className="h-2.5 bg-gray-200 rounded-full w-3/4" />
                          </div>
                          <div className="flex items-center pt-2">
                            <div className="w-4 h-4 rounded bg-orange-100 mr-2" />
                            <div className="h-2 bg-gray-300 rounded-full w-20" />
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Stats bar */}
                    <div className="px-6 py-4 bg-gradient-to-r from-gray-50 to-white border-t border-gray-100 flex items-center justify-between">
                      <div className="flex items-center space-x-6">
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                          <span className="text-xs font-semibold text-gray-600">Live Preview</span>
                        </div>
                        <div className="text-xs text-gray-400">|</div>
                        <div className="flex items-center space-x-1">
                          <ChartBarIcon className="w-3.5 h-3.5 text-orange-500" />
                          <span className="text-xs font-bold text-gray-700">+42% CTR</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-1">
                        <span className="text-xs text-gray-500">Variant</span>
                        <span className="text-xs font-bold text-orange-600 bg-orange-50 px-2 py-0.5 rounded-full">A</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Floating decorative elements - orange theme */}
                <div className="hidden lg:block absolute -top-6 -right-6 w-24 h-24 bg-gradient-to-br from-orange-200 to-amber-200 rounded-2xl rotate-12 shadow-xl shadow-orange-500/20 animate-float opacity-80" />
                <div className="hidden lg:block absolute -bottom-8 -left-8 w-28 h-28 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-2xl -rotate-12 shadow-xl shadow-blue-500/15 animate-float opacity-70" style={{ animationDelay: '1s' }} />
                <div className="hidden lg:block absolute top-1/3 -right-12 w-16 h-16 bg-gradient-to-br from-emerald-100 to-teal-100 rounded-xl rotate-45 shadow-lg shadow-emerald-500/15 animate-float opacity-60" style={{ animationDelay: '2s' }} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Enhanced Social Proof with Animated Stats */}
      <section className="py-10 sm:py-14 border-y border-gray-100 bg-gradient-to-b from-white to-gray-50/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-12">
          {/* Stats Grid - Animated Key Metrics for Credibility */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 sm:gap-8 mb-10 sm:mb-12">
            <div ref={stat1.ref} className="text-center group cursor-default">
              <div className="text-2xl sm:text-3xl lg:text-4xl font-black text-gray-900 mb-1 group-hover:text-orange-600 transition-colors duration-300 tabular-nums">
                {stat1.count.toLocaleString()}+
              </div>
              <div className="text-xs sm:text-sm text-gray-500 font-medium">Active Teams</div>
            </div>
            <div ref={stat2.ref} className="text-center group cursor-default">
              <div className="text-2xl sm:text-3xl lg:text-4xl font-black text-gray-900 mb-1 group-hover:text-orange-600 transition-colors duration-300 tabular-nums">
                {stat2.count}%
              </div>
              <div className="text-xs sm:text-sm text-gray-500 font-medium">Avg. CTR Increase</div>
            </div>
            <div ref={stat3.ref} className="text-center group cursor-default">
              <div className="text-2xl sm:text-3xl lg:text-4xl font-black text-gray-900 mb-1 group-hover:text-orange-600 transition-colors duration-300 tabular-nums">
                {stat3.count}M+
              </div>
              <div className="text-xs sm:text-sm text-gray-500 font-medium">Previews Generated</div>
            </div>
            <div ref={stat4.ref} className="text-center group cursor-default">
              <div className="text-2xl sm:text-3xl lg:text-4xl font-black text-gray-900 mb-1 group-hover:text-orange-600 transition-colors duration-300 tabular-nums">
                {stat4.count}.9%
              </div>
              <div className="text-xs sm:text-sm text-gray-500 font-medium">Uptime SLA</div>
            </div>
          </div>
          
          {/* Company Logos */}
          <div className="border-t border-gray-100 pt-8">
            <p className="text-center text-xs font-bold text-gray-400 uppercase tracking-[0.2em] mb-6">Trusted by forward-thinking teams</p>
            <div className="flex flex-wrap items-center justify-center gap-8 sm:gap-12 lg:gap-16">
              {[
                { name: 'NordicStore', style: 'font-black tracking-tight' },
                { name: 'CloudWave', style: 'font-bold tracking-wide' },
                { name: 'TechFlow', style: 'font-extrabold italic' },
                { name: 'DataVault', style: 'font-black tracking-tighter' },
                { name: 'StreamLine', style: 'font-bold tracking-wide' },
              ].map((company, i) => (
                <div 
                  key={company.name} 
                  className={`text-xl sm:text-2xl text-gray-300 hover:text-gray-600 transition-all duration-300 hover:scale-105 cursor-default ${company.style}`}
                >
                  {company.name}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* How It Works - Visual Step Process */}
      <section 
        id="product" 
        className="py-14 sm:py-20 px-4 sm:px-6 lg:px-12 bg-white"
        ref={el => sectionRefs.current[0] = el as HTMLDivElement | null}
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10 sm:mb-14 space-y-3">
            <div className="inline-flex items-center space-x-2 px-3 py-1 bg-orange-50 rounded-full border border-orange-100 mb-3">
              <span className="text-xs font-bold text-orange-600">SIMPLE SETUP</span>
            </div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-black text-gray-900 tracking-[-0.02em]">Get started in 4 easy steps</h2>
            <p className="text-base sm:text-lg text-gray-500 max-w-xl mx-auto px-4">
              No technical knowledge required. Up and running in under 5 minutes.
            </p>
          </div>
          
          {/* Steps with connecting line */}
          <div className="relative">
            {/* Connecting line - desktop only */}
            <div className="hidden lg:block absolute top-24 left-[12%] right-[12%] h-0.5 bg-gradient-to-r from-orange-200 via-amber-200 to-emerald-200" />
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
              {[
                {
                  step: '01',
                  title: 'Connect domain',
                  description: 'Add your website and verify with a simple DNS check.',
                  icon: LinkIcon,
                  color: 'orange',
                },
                {
                  step: '02',
                  title: 'Verify ownership',
                  description: 'Complete DNS verification to activate your domain.',
                  icon: ShieldCheckIcon,
                  color: 'blue',
                },
                {
                  step: '03',
                  title: 'AI generates previews',
                  description: 'Our AI creates multi-variant previews (A/B/C) automatically.',
                  icon: SparklesIcon,
                  color: 'purple',
                },
                {
                  step: '04',
                  title: 'Track & optimize',
                  description: 'Add one script tag and monitor performance in real-time.',
                  icon: ChartBarIcon,
                  color: 'emerald',
                },
              ].map((item, index) => (
                <div 
                  key={item.step}
                  data-animate
                  className="group relative bg-white rounded-2xl p-6 sm:p-8 border border-gray-100 hover:border-gray-200 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 opacity-0"
                  style={{ animationDelay: `${index * 120}ms` }}
                >
                  {/* Step number badge */}
                  <div className={`relative z-10 w-12 h-12 rounded-xl flex items-center justify-center mb-5 shadow-lg transition-all duration-300 group-hover:scale-110 group-hover:rotate-6 ${
                    item.color === 'orange' ? 'bg-gradient-to-br from-orange-500 to-amber-500 shadow-orange-500/30' :
                    item.color === 'blue' ? 'bg-gradient-to-br from-blue-500 to-indigo-500 shadow-blue-500/30' :
                    item.color === 'purple' ? 'bg-gradient-to-br from-purple-500 to-violet-500 shadow-purple-500/30' :
                    'bg-gradient-to-br from-emerald-500 to-teal-500 shadow-emerald-500/30'
                  }`}>
                    <item.icon className="w-6 h-6 text-white" />
                  </div>
                  
                  <div className={`text-xs font-black uppercase tracking-wider mb-2 transition-colors duration-300 ${
                    item.color === 'orange' ? 'text-orange-500 group-hover:text-orange-600' :
                    item.color === 'blue' ? 'text-blue-500 group-hover:text-blue-600' :
                    item.color === 'purple' ? 'text-purple-500 group-hover:text-purple-600' :
                    'text-emerald-500 group-hover:text-emerald-600'
                  }`}>Step {item.step}</div>
                  <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-2">{item.title}</h3>
                  <p className="text-gray-500 text-sm leading-relaxed">{item.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Features - Enhanced Visual Hierarchy */}
      <section 
        id="features" 
        className="py-14 sm:py-20 px-4 sm:px-6 lg:px-12 bg-gradient-to-b from-gray-50/80 via-white to-gray-50/50"
        ref={el => sectionRefs.current[1] = el as HTMLDivElement | null}
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10 sm:mb-14 space-y-3">
            <div className="inline-flex items-center space-x-2 px-3 py-1 bg-blue-50 rounded-full border border-blue-100 mb-3">
              <span className="text-xs font-bold text-blue-600">POWERFUL FEATURES</span>
            </div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-black text-gray-900 tracking-[-0.02em]">Everything you need to convert</h2>
            <p className="text-base sm:text-lg text-gray-500 max-w-xl mx-auto px-4">
              Create stunning URL previews that drive engagement and clicks.
            </p>
          </div>
          
          {/* Feature Grid with Visual Interest & Hover Lift */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 sm:gap-6">
            {[
              {
                title: 'AI Semantic Understanding',
                description: 'Deep AI analyzes content to extract meaningful titles, descriptions, and keywords.',
                icon: BoltIcon,
                accent: 'orange',
                badge: 'AI-Powered',
              },
              {
                title: 'Smart Screenshots',
                description: 'Automatic website screenshots with intelligent highlight cropping and focal points.',
                icon: PhotoIcon,
                accent: 'purple',
                badge: null,
              },
              {
                title: 'Multi-Variant A/B/C Testing',
                description: 'Generate three preview variants per URL. Test what resonates best automatically.',
                icon: StarIcon,
                accent: 'amber',
                badge: 'Popular',
              },
              {
                title: 'Real-Time Analytics',
                description: 'Track impressions, clicks, CTR, and performance metrics per domain and preview.',
                icon: ChartBarIcon,
                accent: 'emerald',
                badge: null,
              },
              {
                title: 'Brand Voice Rewriting',
                description: 'Automatically rewrite preview text to match your brand voice and tone.',
                icon: SparklesIcon,
                accent: 'pink',
                badge: null,
              },
              {
                title: 'One-Click Integration',
                description: 'Single script tag works everywhere—WordPress, React, Vue, static sites.',
                icon: PuzzlePieceIcon,
                accent: 'blue',
                badge: 'Easy',
              },
            ].map((feature, index) => (
              <div 
                key={index}
                data-animate
                className="group relative bg-white rounded-xl p-6 border border-gray-100 hover:border-gray-200 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 opacity-0"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                {/* Badge */}
                {feature.badge && (
                  <div className={`absolute -top-2 right-4 text-[10px] font-bold px-2 py-0.5 rounded-full shadow-sm ${
                    feature.badge === 'AI-Powered' ? 'bg-orange-100 text-orange-700' :
                    feature.badge === 'Popular' ? 'bg-amber-100 text-amber-700' :
                    'bg-blue-100 text-blue-700'
                  }`}>
                    {feature.badge}
                  </div>
                )}
                
                <div className={`w-11 h-11 rounded-xl flex items-center justify-center mb-4 transition-all duration-300 group-hover:scale-110 group-hover:rotate-3 ${
                  feature.accent === 'orange' ? 'bg-orange-100 text-orange-600' :
                  feature.accent === 'purple' ? 'bg-purple-100 text-purple-600' :
                  feature.accent === 'amber' ? 'bg-amber-100 text-amber-600' :
                  feature.accent === 'emerald' ? 'bg-emerald-100 text-emerald-600' :
                  feature.accent === 'pink' ? 'bg-pink-100 text-pink-600' :
                  'bg-blue-100 text-blue-600'
                }`}>
                  <feature.icon className="w-5 h-5" />
                </div>
                <h3 className="text-base sm:text-lg font-bold text-gray-900 mb-2 group-hover:text-gray-800 transition-colors">{feature.title}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Social Proof + Features Visual Section */}
      <section 
        className="py-14 sm:py-20 px-4 sm:px-6 lg:px-12 bg-white"
        ref={el => sectionRefs.current[2] = el as HTMLDivElement | null}
      >
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 sm:gap-14 items-center">
            <div className="space-y-6 order-2 lg:order-1">
              <div className="space-y-4">
                <div className="inline-flex items-center space-x-2 px-3 py-1 bg-purple-50 rounded-full border border-purple-100">
                  <span className="text-xs font-bold text-purple-600">CROSS-PLATFORM</span>
                </div>
                <h2 className="text-2xl sm:text-3xl lg:text-4xl font-black text-gray-900 tracking-[-0.02em] leading-tight">
                  Beautiful previews,{' '}
                  <span className="bg-gradient-to-r from-orange-500 via-amber-500 to-yellow-500 bg-clip-text text-transparent">everywhere</span>
                </h2>
                <p className="text-base sm:text-lg text-gray-500 leading-relaxed">
                  Your links look stunning across all platforms—social media, messaging apps, email, and more.
                </p>
              </div>
              <div className="space-y-3">
                {[
                  { text: 'Automatic preview generation for all URLs', highlight: true },
                  { text: 'Multi-platform compatibility (Twitter, LinkedIn, Slack, etc.)', highlight: false },
                  { text: 'Real-time analytics and insights', highlight: false },
                  { text: 'Custom branding and styling', highlight: false },
                ].map((item, i) => (
                  <div key={i} className={`flex items-center space-x-3 p-3 rounded-xl transition-all duration-300 ${item.highlight ? 'bg-orange-50 border border-orange-100' : 'hover:bg-gray-50'}`}>
                    <div className={`w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0 ${item.highlight ? 'bg-orange-500' : 'bg-emerald-100'}`}>
                      <CheckIcon className={`w-3.5 h-3.5 ${item.highlight ? 'text-white' : 'text-emerald-600'}`} />
                    </div>
                    <span className={`text-sm font-medium ${item.highlight ? 'text-orange-700' : 'text-gray-700'}`}>{item.text}</span>
                  </div>
                ))}
              </div>
              
              <Link 
                to="/app" 
                className="inline-flex items-center text-orange-600 hover:text-orange-700 font-bold text-sm group"
              >
                See all features
                <ArrowRightIcon className="w-4 h-4 ml-1.5 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>
            
            {/* Platform Preview Grid with Enhanced Interactions */}
            <div className="relative order-1 lg:order-2">
              <div className="grid grid-cols-2 gap-4">
                {/* Twitter Preview */}
                <div className="group bg-white rounded-xl border border-gray-200 p-4 shadow-lg hover:shadow-xl hover:-translate-y-1 transition-all duration-300 cursor-default">
                  <div className="flex items-center space-x-2 mb-3">
                    <div className="w-6 h-6 bg-gray-900 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                      <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                    </div>
                    <span className="text-xs font-bold text-gray-600">X / Twitter</span>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 space-y-2 overflow-hidden relative">
                    <div className="h-16 bg-gradient-to-br from-orange-100 to-amber-100 rounded-md group-hover:scale-[1.02] transition-transform duration-300" />
                    <div className="h-2.5 bg-gray-300 rounded w-3/4" />
                    <div className="h-2 bg-gray-200 rounded w-full" />
                  </div>
                </div>
                
                {/* LinkedIn Preview */}
                <div className="group bg-white rounded-xl border border-gray-200 p-4 shadow-lg hover:shadow-xl hover:-translate-y-1 transition-all duration-300 cursor-default" style={{ animationDelay: '100ms' }}>
                  <div className="flex items-center space-x-2 mb-3">
                    <div className="w-6 h-6 bg-blue-600 rounded flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                      <svg className="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452z"/></svg>
                    </div>
                    <span className="text-xs font-bold text-gray-600">LinkedIn</span>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 space-y-2 overflow-hidden">
                    <div className="h-16 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-md group-hover:scale-[1.02] transition-transform duration-300" />
                    <div className="h-2.5 bg-gray-300 rounded w-4/5" />
                    <div className="h-2 bg-gray-200 rounded w-full" />
                  </div>
                </div>
                
                {/* Slack Preview */}
                <div className="group bg-white rounded-xl border border-gray-200 p-4 shadow-lg hover:shadow-xl hover:-translate-y-1 transition-all duration-300 cursor-default" style={{ animationDelay: '200ms' }}>
                  <div className="flex items-center space-x-2 mb-3">
                    <div className="w-6 h-6 bg-purple-600 rounded flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                      <span className="text-white text-xs font-bold">#</span>
                    </div>
                    <span className="text-xs font-bold text-gray-600">Slack</span>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 space-y-2 overflow-hidden">
                    <div className="h-16 bg-gradient-to-br from-purple-100 to-violet-100 rounded-md group-hover:scale-[1.02] transition-transform duration-300" />
                    <div className="h-2.5 bg-gray-300 rounded w-2/3" />
                    <div className="h-2 bg-gray-200 rounded w-full" />
                  </div>
                </div>
                
                {/* Email Preview */}
                <div className="group bg-white rounded-xl border border-gray-200 p-4 shadow-lg hover:shadow-xl hover:-translate-y-1 transition-all duration-300 cursor-default" style={{ animationDelay: '300ms' }}>
                  <div className="flex items-center space-x-2 mb-3">
                    <div className="w-6 h-6 bg-emerald-500 rounded flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                      <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                    </div>
                    <span className="text-xs font-bold text-gray-600">Email</span>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 space-y-2 overflow-hidden">
                    <div className="h-16 bg-gradient-to-br from-emerald-100 to-teal-100 rounded-md group-hover:scale-[1.02] transition-transform duration-300" />
                    <div className="h-2.5 bg-gray-300 rounded w-5/6" />
                    <div className="h-2 bg-gray-200 rounded w-full" />
                  </div>
                </div>
              </div>
              
              {/* Floating badge with subtle animation */}
              <div className="absolute -top-4 -right-4 bg-gradient-to-r from-orange-500 to-amber-500 text-white text-xs font-bold px-3 py-1.5 rounded-full shadow-lg animate-pulse hover:scale-110 transition-transform cursor-default">
                +40% CTR
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing - High-Converting Design */}
      <section 
        id="pricing" 
        className="py-14 sm:py-20 px-4 sm:px-6 lg:px-12 bg-gradient-to-b from-white via-orange-50/30 to-white"
        ref={el => sectionRefs.current[3] = el as HTMLDivElement | null}
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10 sm:mb-14 space-y-3">
            <div className="inline-flex items-center space-x-2 px-3 py-1 bg-emerald-50 rounded-full border border-emerald-100 mb-3">
              <span className="text-xs font-bold text-emerald-600">SIMPLE PRICING</span>
            </div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-black text-gray-900 tracking-[-0.02em]">Choose your plan</h2>
            <p className="text-base sm:text-lg text-gray-500 max-w-xl mx-auto px-4">
              Start free for 14 days. No credit card required.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 sm:gap-6 max-w-5xl mx-auto">
            {[
              {
                name: 'Starter',
                price: '$19',
                period: '/mo',
                description: 'Perfect for small websites',
                features: [
                  'Up to 5 domains',
                  'Unlimited previews',
                  'Basic analytics',
                  'Email support',
                ],
                cta: 'Start Free Trial',
                highlighted: false,
              },
              {
                name: 'Growth',
                price: '$49',
                period: '/mo',
                description: 'For growing businesses',
                features: [
                  'Up to 25 domains',
                  'Unlimited previews',
                  'Advanced analytics',
                  'Custom branding',
                  'Priority support',
                ],
                cta: 'Start Free Trial',
                highlighted: true,
                savings: 'Most Popular',
              },
              {
                name: 'Agency',
                price: '$149',
                period: '/mo',
                description: 'For agencies and teams',
                features: [
                  'Unlimited domains',
                  'Unlimited previews',
                  'White-label options',
                  'API access',
                  'Dedicated support',
                  'Team collaboration',
                ],
                cta: 'Contact Sales',
                highlighted: false,
              },
            ].map((plan, index) => (
              <div
                key={plan.name}
                data-animate
                className={`group relative rounded-2xl p-6 sm:p-8 transition-all duration-300 opacity-0 ${
                  plan.highlighted 
                    ? 'bg-gradient-to-br from-orange-500 via-amber-500 to-orange-500 text-white shadow-2xl shadow-orange-500/30 scale-[1.02] md:scale-105 hover:shadow-orange-500/40' 
                    : 'bg-white border border-gray-200 hover:border-gray-300 hover:shadow-xl hover:-translate-y-1'
                }`}
                style={{ animationDelay: `${index * 150}ms` }}
              >
                {/* Popular badge */}
                {plan.highlighted && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white px-4 py-1 text-xs font-bold rounded-full shadow-lg animate-pulse">
                    ⭐ Most Popular
                  </div>
                )}
                
                <div className="mb-6">
                  <h3 className={`text-xl font-bold mb-1 ${plan.highlighted ? 'text-white' : 'text-gray-900'}`}>{plan.name}</h3>
                  <p className={`text-sm mb-4 ${plan.highlighted ? 'text-orange-100' : 'text-gray-500'}`}>{plan.description}</p>
                  <div className="flex items-baseline">
                    <span className={`text-4xl sm:text-5xl font-black tabular-nums ${plan.highlighted ? 'text-white' : 'text-gray-900'}`}>{plan.price}</span>
                    <span className={`ml-1 text-sm ${plan.highlighted ? 'text-orange-100' : 'text-gray-500'}`}>{plan.period}</span>
                  </div>
                </div>
                
                <ul className="space-y-3 mb-6">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-center text-sm group/item">
                      <CheckIcon className={`w-4 h-4 mr-2 flex-shrink-0 transition-transform duration-200 group-hover/item:scale-110 ${plan.highlighted ? 'text-orange-100' : 'text-emerald-500'}`} />
                      <span className={plan.highlighted ? 'text-white' : 'text-gray-700'}>{feature}</span>
                    </li>
                  ))}
                </ul>
                
                <Link
                  to="/app"
                  className={`block w-full text-center py-3 rounded-xl font-bold text-sm transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] select-none ${
                    plan.highlighted
                      ? 'bg-white text-orange-600 hover:bg-gray-50 shadow-lg hover:shadow-xl'
                      : 'bg-gray-900 text-white hover:bg-gray-800'
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
          
          {/* Trust indicators */}
          <div className="flex flex-wrap items-center justify-center gap-6 mt-10 text-sm text-gray-500">
            <div className="flex items-center space-x-2">
              <ShieldCheckIcon className="w-4 h-4 text-emerald-500" />
              <span>Secure payment</span>
            </div>
            <div className="flex items-center space-x-2">
              <ClockIcon className="w-4 h-4 text-blue-500" />
              <span>Cancel anytime</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckIcon className="w-4 h-4 text-purple-500" />
              <span>14-day money back</span>
            </div>
          </div>
        </div>
      </section>

      {/* Premium CTA Section - High Urgency */}
      <section 
        className="py-14 sm:py-20 px-4 sm:px-6 lg:px-12 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white relative overflow-hidden"
        ref={el => sectionRefs.current[4] = el as HTMLDivElement | null}
      >
        {/* Animated background with orange accent */}
        <div className="absolute inset-0">
          <div className="absolute top-0 right-0 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-0 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl" />
          <div className="absolute inset-0 opacity-5" style={{
            backgroundImage: 'radial-gradient(circle at 2px 2px, rgba(255,255,255,0.3) 1px, transparent 0)',
            backgroundSize: '48px 48px'
          }} />
        </div>
        
        <div className="max-w-4xl mx-auto text-center space-y-6 relative z-10">
          {/* Urgency badge */}
          <div className="inline-flex items-center space-x-2 px-4 py-1.5 bg-orange-500/20 rounded-full border border-orange-500/30 backdrop-blur-sm">
            <div className="w-2 h-2 bg-orange-400 rounded-full animate-pulse" />
            <span className="text-xs font-bold text-orange-300">Limited Time: 20% off annual plans</span>
          </div>
          
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-black tracking-[-0.02em] leading-tight px-4">
            Ready to boost your click-through rates?
          </h2>
          <p className="text-base sm:text-lg text-gray-400 max-w-xl mx-auto leading-relaxed px-4">
            Join 2,000+ teams using MetaView to create high-converting URL previews.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4 px-4">
            <Link 
              to="/app" 
              className="group relative px-8 py-4 bg-gradient-to-r from-orange-500 via-amber-500 to-orange-500 text-white rounded-xl font-bold text-base transition-all duration-300 hover:scale-[1.03] hover:shadow-xl hover:shadow-orange-500/30 inline-flex items-center justify-center overflow-hidden"
            >
              <span className="relative z-10 flex items-center">
                Start Free Trial
                <ArrowRightIcon className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform duration-300" />
              </span>
            </Link>
            <Link 
              to="/app" 
              className="px-8 py-4 bg-white/10 text-white rounded-xl font-bold text-base border border-white/20 hover:bg-white/20 hover:border-white/30 transition-all duration-300 inline-flex items-center justify-center backdrop-blur-sm"
            >
              Schedule Demo
            </Link>
          </div>
          
          {/* Trust row */}
          <div className="flex flex-wrap items-center justify-center gap-4 pt-4 text-sm text-gray-400">
            <span className="flex items-center"><CheckIcon className="w-4 h-4 mr-1.5 text-emerald-400" />14-day free trial</span>
            <span className="flex items-center"><CheckIcon className="w-4 h-4 mr-1.5 text-emerald-400" />No credit card</span>
            <span className="flex items-center"><CheckIcon className="w-4 h-4 mr-1.5 text-emerald-400" />Cancel anytime</span>
          </div>
        </div>
      </section>

      {/* Docs Section - Enhanced & Accessible */}
      <section 
        id="docs" 
        className="py-14 sm:py-20 px-4 sm:px-6 lg:px-12 bg-gradient-to-b from-white via-gray-50/30 to-white"
        ref={el => sectionRefs.current[5] = el as HTMLDivElement | null}
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10 sm:mb-12 space-y-3">
            <div className="inline-flex items-center space-x-2 px-3 py-1 bg-orange-50 rounded-full border border-orange-100 mb-3">
              <span className="text-xs font-bold text-orange-600">DOCUMENTATION</span>
            </div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-black text-gray-900 tracking-[-0.02em]">Complete documentation & guides</h2>
            <p className="text-base sm:text-lg text-gray-500 max-w-xl mx-auto px-4">
              Everything you need to integrate MetaView into your workflow. Get started in minutes.
            </p>
          </div>
          
          {/* Prominent CTA Card */}
          <div className="mb-10 sm:mb-12">
            <div className="max-w-3xl mx-auto bg-gradient-to-br from-orange-500 via-amber-500 to-orange-500 rounded-2xl p-8 sm:p-10 text-white shadow-2xl shadow-orange-500/30 relative overflow-hidden">
              <div className="absolute inset-0 opacity-10" style={{
                backgroundImage: 'radial-gradient(circle at 2px 2px, rgba(255,255,255,0.3) 1px, transparent 0)',
                backgroundSize: '32px 32px'
              }} />
              <div className="relative z-10">
                <div className="flex items-center space-x-3 mb-4">
                  <CodeBracketIcon className="w-8 h-8 text-white" />
                  <h3 className="text-2xl sm:text-3xl font-black">Interactive API Documentation</h3>
                </div>
                <p className="text-orange-50 text-base sm:text-lg mb-6 leading-relaxed">
                  Explore our complete API with interactive examples. Test endpoints, view schemas, and integrate faster.
                </p>
                <div className="flex flex-col sm:flex-row gap-3">
                  <a
                    href={`${getApiBaseUrl()}/docs`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group relative px-6 py-3.5 bg-white text-orange-600 rounded-xl font-bold text-sm transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] hover:shadow-xl inline-flex items-center justify-center overflow-hidden"
                  >
                    <span className="relative z-10 flex items-center">
                      Open API Docs
                      <ArrowUpRightIcon className="w-4 h-4 ml-2 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                    </span>
                  </a>
                  <Link
                    to="/app"
                    className="px-6 py-3.5 bg-white/10 text-white rounded-xl font-bold text-sm border-2 border-white/30 hover:bg-white/20 hover:border-white/40 transition-all duration-300 inline-flex items-center justify-center backdrop-blur-sm"
                  >
                    Get Started Free
                  </Link>
                </div>
              </div>
            </div>
          </div>

          {/* Documentation Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5 sm:gap-6 mb-8">
            {[
              {
                title: 'Quick Start Guide',
                description: 'Get up and running in 5 minutes. Connect your first domain and generate previews.',
                link: '/app',
                external: false,
                icon: RocketLaunchIcon,
                color: 'purple',
                badge: 'Start Here',
              },
              {
                title: 'Integration Guide',
                description: 'Step-by-step instructions for WordPress, React, Vue, and static sites.',
                link: '/app',
                external: false,
                icon: PuzzlePieceIcon,
                color: 'orange',
                badge: 'Popular',
              },
              {
                title: 'API Reference',
                description: 'Complete API documentation with authentication, endpoints, and examples.',
                link: `${getApiBaseUrl()}/docs`,
                external: true,
                icon: CodeBracketIcon,
                color: 'blue',
                badge: null,
              },
              {
                title: 'Domain Verification',
                description: 'Learn how to verify domain ownership using DNS, HTML, or meta tags.',
                link: '/app',
                external: false,
                icon: ShieldCheckIcon,
                color: 'emerald',
                badge: null,
              },
              {
                title: 'Brand Customization',
                description: 'Customize preview colors, fonts, and styling to match your brand.',
                link: '/app',
                external: false,
                icon: SparklesIcon,
                color: 'pink',
                badge: null,
              },
              {
                title: 'Analytics & Tracking',
                description: 'Understand your preview performance with detailed analytics and insights.',
                link: '/app',
                external: false,
                icon: ChartBarIcon,
                color: 'indigo',
                badge: null,
              },
            ].map((doc, index) => (
              <div 
                key={index}
                className="group relative bg-white rounded-xl p-6 border-2 border-gray-100 hover:border-gray-200 transition-all duration-300 hover:shadow-xl hover:-translate-y-1"
              >
                {doc.badge && (
                  <div className={`absolute -top-2 right-4 text-[10px] font-bold px-2.5 py-1 rounded-full shadow-sm ${
                    doc.badge === 'Start Here' ? 'bg-purple-100 text-purple-700' :
                    'bg-orange-100 text-orange-700'
                  }`}>
                    {doc.badge}
                  </div>
                )}
                <div className={`w-11 h-11 rounded-xl flex items-center justify-center mb-4 transition-all duration-300 group-hover:scale-110 group-hover:rotate-3 ${
                  doc.color === 'blue' ? 'bg-blue-100 text-blue-600' :
                  doc.color === 'purple' ? 'bg-purple-100 text-purple-600' :
                  doc.color === 'orange' ? 'bg-orange-100 text-orange-600' :
                  doc.color === 'emerald' ? 'bg-emerald-100 text-emerald-600' :
                  doc.color === 'pink' ? 'bg-pink-100 text-pink-600' :
                  'bg-indigo-100 text-indigo-600'
                }`}>
                  <doc.icon className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2 group-hover:text-gray-800 transition-colors">{doc.title}</h3>
                <p className="text-gray-500 text-sm mb-4 leading-relaxed">{doc.description}</p>
                {doc.external ? (
                  <a
                    href={doc.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`inline-flex items-center text-sm font-semibold group-hover:translate-x-1 transition-all duration-300 ${
                      doc.color === 'blue' ? 'text-blue-600 hover:text-blue-700' :
                      doc.color === 'purple' ? 'text-purple-600 hover:text-purple-700' :
                      doc.color === 'orange' ? 'text-orange-600 hover:text-orange-700' :
                      doc.color === 'emerald' ? 'text-emerald-600 hover:text-emerald-700' :
                      doc.color === 'pink' ? 'text-pink-600 hover:text-pink-700' :
                      'text-indigo-600 hover:text-indigo-700'
                    }`}
                  >
                    View Docs
                    <ArrowUpRightIcon className="w-4 h-4 ml-1.5" />
                  </a>
                ) : (
                  <Link
                    to={doc.link}
                    className={`inline-flex items-center text-sm font-semibold group-hover:translate-x-1 transition-all duration-300 ${
                      doc.color === 'blue' ? 'text-blue-600 hover:text-blue-700' :
                      doc.color === 'purple' ? 'text-purple-600 hover:text-purple-700' :
                      doc.color === 'orange' ? 'text-orange-600 hover:text-orange-700' :
                      doc.color === 'emerald' ? 'text-emerald-600 hover:text-emerald-700' :
                      doc.color === 'pink' ? 'text-pink-600 hover:text-pink-700' :
                      'text-indigo-600 hover:text-indigo-700'
                    }`}
                  >
                    Get Started
                    <ArrowRightIcon className="w-4 h-4 ml-1.5" />
                  </Link>
                )}
              </div>
            ))}
          </div>

          {/* Additional Resources */}
          <div className="text-center">
            <p className="text-sm text-gray-500 mb-4">Need more help?</p>
            <div className="flex flex-wrap items-center justify-center gap-4">
              <Link
                to="/blog"
                className="inline-flex items-center text-sm font-semibold text-gray-700 hover:text-orange-600 transition-colors"
              >
                <span>Visit our Blog</span>
                <ArrowRightIcon className="w-4 h-4 ml-1.5" />
              </Link>
              <span className="text-gray-300">•</span>
              <Link
                to="/app"
                className="inline-flex items-center text-sm font-semibold text-gray-700 hover:text-orange-600 transition-colors"
              >
                <span>Contact Support</span>
                <ArrowRightIcon className="w-4 h-4 ml-1.5" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Clean Footer */}
      <footer className="bg-gray-900 text-white py-10 sm:py-14 px-4 sm:px-6 lg:px-12">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8 sm:mb-10">
            <div className="col-span-2 md:col-span-1">
              <div className="flex items-center space-x-2.5 mb-4">
                <div className="w-9 h-9 bg-gradient-to-br from-orange-500 via-amber-500 to-yellow-500 rounded-xl flex items-center justify-center shadow-lg shadow-orange-500/25">
                  <span className="text-white font-black text-sm">M</span>
                </div>
                <span className="text-lg font-black">MetaView</span>
              </div>
              <p className="text-gray-400 text-sm leading-relaxed mb-4">
                Beautiful URL previews that drive engagement and clicks.
              </p>
              {/* Social links */}
              <div className="flex items-center space-x-3">
                <a href="#" className="w-8 h-8 bg-gray-800 hover:bg-gray-700 rounded-lg flex items-center justify-center transition-colors">
                  <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                </a>
                <a href="#" className="w-8 h-8 bg-gray-800 hover:bg-gray-700 rounded-lg flex items-center justify-center transition-colors">
                  <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
                </a>
              </div>
            </div>
            <div>
              <h4 className="font-bold mb-4 text-white text-sm">Product</h4>
              <ul className="space-y-2.5 text-sm text-gray-400">
                <li><a href="#features" className="hover:text-orange-400 transition-colors">Features</a></li>
                <li><a href="#pricing" className="hover:text-orange-400 transition-colors">Pricing</a></li>
                <li><Link to="/app" className="hover:text-orange-400 transition-colors">Dashboard</Link></li>
                <li><a href="#docs" className="hover:text-orange-400 transition-colors">Documentation</a></li>
                <li><Link to="/blog" className="hover:text-orange-400 transition-colors">Blog</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-4 text-white text-sm">Company</h4>
              <ul className="space-y-2.5 text-sm text-gray-400">
                <li><a href="#" className="hover:text-orange-400 transition-colors">About</a></li>
                <li><a href="#" className="hover:text-orange-400 transition-colors">Blog</a></li>
                <li><a href="#" className="hover:text-orange-400 transition-colors">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-4 text-white text-sm">Legal</h4>
              <ul className="space-y-2.5 text-sm text-gray-400">
                <li><a href="#" className="hover:text-orange-400 transition-colors">Privacy</a></li>
                <li><a href="#" className="hover:text-orange-400 transition-colors">Terms</a></li>
                <li><a href="#" className="hover:text-orange-400 transition-colors">Cookies</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-gray-500">
            <span>© 2024 MetaView. All rights reserved.</span>
            <div className="flex items-center space-x-4">
              <span className="flex items-center"><ShieldCheckIcon className="w-4 h-4 mr-1 text-emerald-500" />SOC 2 Compliant</span>
              <span className="flex items-center"><ShieldCheckIcon className="w-4 h-4 mr-1 text-emerald-500" />GDPR Ready</span>
            </div>
          </div>
        </div>
      </footer>

      <style>{`
        /* Floating animation with subtle movement */
        @keyframes float {
          0%, 100% {
            transform: translateY(0px) rotate(0deg);
          }
          50% {
            transform: translateY(-20px) rotate(3deg);
          }
        }
        
        .animate-float {
          animation: float 6s ease-in-out infinite;
        }

        /* Fade in up animation */
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-fade-in-up {
          animation: fadeInUp 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }

        /* Subtle pulse for badges */
        @keyframes subtlePulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.85;
          }
        }

        /* Shine sweep animation for CTAs */
        @keyframes shine {
          from {
            transform: translateX(-100%);
          }
          to {
            transform: translateX(100%);
          }
        }

        /* Smooth scroll behavior */
        html {
          scroll-behavior: smooth;
        }

        /* Better text rendering */
        body {
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
          text-rendering: optimizeLegibility;
        }

        /* Tabular numbers for stats */
        .tabular-nums {
          font-variant-numeric: tabular-nums;
        }

        /* Selection color */
        ::selection {
          background-color: rgba(249, 115, 22, 0.15);
          color: inherit;
        }

        /* Custom scrollbar for webkit */
        ::-webkit-scrollbar {
          width: 10px;
        }
        ::-webkit-scrollbar-track {
          background: #f1f1f1;
        }
        ::-webkit-scrollbar-thumb {
          background: #d1d5db;
          border-radius: 5px;
        }
        ::-webkit-scrollbar-thumb:hover {
          background: #9ca3af;
        }

        /* Focus visible for keyboard navigation */
        *:focus-visible {
          outline: 2px solid rgba(249, 115, 22, 0.5);
          outline-offset: 2px;
        }
      `}</style>
    </div>
  )
}
