import { Link } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'
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
} from '@heroicons/react/24/outline'

export default function Landing() {
  const [isVisible, setIsVisible] = useState(false)
  const [scrollY, setScrollY] = useState(0)
  const heroRef = useRef<HTMLDivElement>(null)
  const sectionRefs = useRef<(HTMLDivElement | null)[]>([])

  useEffect(() => {
    setIsVisible(true)
    
    // Scroll handler for parallax and scroll position
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

    // Intersection Observer for fade-in animations
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -100px 0px'
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
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
      {/* Sophisticated Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        {/* Large gradient orbs */}
        <div 
          className="absolute top-0 -left-1/4 w-[800px] h-[800px] bg-gradient-to-br from-blue-50 via-blue-100/50 to-transparent rounded-full blur-3xl opacity-30"
          style={{
            transform: `translate(${scrollY * 0.1}px, ${scrollY * 0.15}px)`,
            transition: 'transform 0.1s ease-out'
          }}
        />
        <div 
          className="absolute top-1/3 right-0 w-[600px] h-[600px] bg-gradient-to-br from-purple-50/50 via-blue-50/30 to-transparent rounded-full blur-3xl opacity-20"
          style={{
            transform: `translate(${-scrollY * 0.08}px, ${scrollY * 0.12}px)`,
            transition: 'transform 0.1s ease-out'
          }}
        />
        <div 
          className="absolute bottom-0 left-1/3 w-[700px] h-[700px] bg-gradient-to-br from-gray-50/40 via-blue-50/20 to-transparent rounded-full blur-3xl opacity-25"
          style={{
            transform: `translate(${scrollY * 0.06}px, ${-scrollY * 0.1}px)`,
            transition: 'transform 0.1s ease-out'
          }}
        />
        
        {/* Subtle grid pattern */}
        <div 
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: 'linear-gradient(rgba(0,0,0,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,0.1) 1px, transparent 1px)',
            backgroundSize: '60px 60px',
            transform: `translate(${scrollY * 0.05}px, ${scrollY * 0.05}px)`
          }}
        />
      </div>

      {/* Premium Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-2xl border-b border-gray-100/50 transition-all duration-300" style={{ boxShadow: scrollY > 10 ? '0 1px 3px rgba(0,0,0,0.05)' : 'none' }}>
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="flex items-center justify-between h-20">
            <div className="flex items-center space-x-3 group cursor-pointer">
              <div className="relative">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-600 via-blue-700 to-blue-800 rounded-2xl flex items-center justify-center shadow-xl shadow-blue-500/30 group-hover:scale-110 transition-transform duration-300">
                  <span className="text-white font-bold text-xl">P</span>
                </div>
                <div className="absolute inset-0 bg-gradient-to-br from-blue-400 to-blue-600 rounded-2xl opacity-0 group-hover:opacity-100 blur-xl transition-opacity duration-300" />
              </div>
              <span className="text-2xl font-bold text-gray-900 tracking-tight">MetaView</span>
            </div>
            <div className="hidden lg:flex items-center space-x-12">
              <a href="#product" className="text-gray-600 hover:text-gray-900 transition-all duration-200 font-medium text-sm relative group">
                Product
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-gray-900 group-hover:w-full transition-all duration-300" />
              </a>
              <a href="#features" className="text-gray-600 hover:text-gray-900 transition-all duration-200 font-medium text-sm relative group">
                Features
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-gray-900 group-hover:w-full transition-all duration-300" />
              </a>
              <a href="#pricing" className="text-gray-600 hover:text-gray-900 transition-all duration-200 font-medium text-sm relative group">
                Pricing
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-gray-900 group-hover:w-full transition-all duration-300" />
              </a>
              <a href="#docs" className="text-gray-600 hover:text-gray-900 transition-all duration-200 font-medium text-sm relative group">
                Docs
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-gray-900 group-hover:w-full transition-all duration-300" />
              </a>
              <Link to="/app" className="text-gray-600 hover:text-gray-900 transition-all duration-200 font-medium text-sm relative group">
                Login
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-gray-900 group-hover:w-full transition-all duration-300" />
              </Link>
            </div>
            <Link
              to="/app"
              className="group relative px-7 py-3 bg-gray-900 text-white rounded-2xl font-semibold text-sm hover:bg-gray-800 transition-all duration-300 hover:scale-105 hover:shadow-2xl shadow-gray-900/20 overflow-hidden"
            >
              <span className="relative z-10 flex items-center">
                Get Started
                <ArrowUpRightIcon className="w-4 h-4 ml-2 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform duration-300" />
              </span>
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-blue-700 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section - Premium */}
      <section className="relative pt-32 pb-24 px-6 lg:px-12">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div className={`space-y-8 transition-all duration-1000 ease-out ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
              <div className="space-y-6">
                <div className="inline-flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-50 to-blue-100/50 rounded-full border border-blue-200/50 backdrop-blur-sm w-fit shadow-sm shadow-blue-500/10">
                  <div className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-pulse" />
                  <span className="text-xs font-bold text-blue-700 tracking-wide">AI-Powered Preview Generation</span>
                </div>
                <h1 className="text-5xl lg:text-6xl font-extrabold text-gray-900 leading-[1.1] tracking-[-0.02em]">
                  Turn every shared link into a{' '}
                  <span className="relative inline-block">
                    <span className="bg-gradient-to-r from-blue-600 via-blue-700 to-blue-800 bg-clip-text text-transparent">high-converting</span>
                    <svg className="absolute -bottom-1 left-0 w-full h-2" viewBox="0 0 200 12" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M0 8C50 4 100 8 150 4C175 2 200 6 200 6" stroke="url(#gradient)" strokeWidth="2" strokeLinecap="round" />
                      <defs>
                        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                          <stop offset="0%" stopColor="#2563eb" stopOpacity="0.3" />
                          <stop offset="100%" stopColor="#1d4ed8" stopOpacity="0.1" />
                        </linearGradient>
                      </defs>
                    </svg>
                  </span>{' '}
                  preview
                </h1>
                <p className="text-lg lg:text-xl text-gray-600 leading-relaxed max-w-xl font-light">
                  AI-powered URL previews that automatically generate beautiful, branded cards for your website. 
                  Increase click-through rates by up to <span className="font-semibold text-gray-900">40%</span> with zero coding required.
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Link 
                  to="/app" 
                  className="group relative px-8 py-4 bg-gray-900 text-white rounded-xl font-bold text-sm hover:bg-gray-800 transition-all duration-300 hover:scale-105 hover:shadow-2xl shadow-gray-900/40 inline-flex items-center justify-center overflow-hidden"
                >
                  <span className="relative z-10 flex items-center">
                    Start Free Trial
                    <ArrowRightIcon className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform duration-300" />
                  </span>
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-blue-700 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                </Link>
                <Link 
                  to="/app" 
                  className="px-8 py-4 bg-white text-gray-900 rounded-xl font-bold text-sm border-2 border-gray-200 hover:border-gray-300 transition-all duration-300 hover:scale-105 hover:shadow-xl shadow-gray-200/50 inline-flex items-center justify-center backdrop-blur-sm"
                >
                  See Examples
                </Link>
              </div>
              
              <div className="flex flex-wrap items-center gap-6 pt-2">
                {[
                  { icon: CheckIcon, text: '14-day free trial' },
                  { icon: CheckIcon, text: 'No credit card' },
                  { icon: CheckIcon, text: '5 min setup' },
                ].map((item, i) => (
                  <div key={i} className="flex items-center space-x-2.5 group">
                    <div className="w-6 h-6 bg-green-100 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                      <item.icon className="w-4 h-4 text-green-600" />
                    </div>
                    <span className="text-sm text-gray-600 font-medium">{item.text}</span>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Premium Floating Mockup */}
            <div 
              ref={heroRef}
              className={`relative transition-all duration-1000 ease-out ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}
              style={{ transitionDelay: '200ms' }}
            >
              <div className="relative">
                {/* Main Floating Card */}
                <div className="relative group">
                  {/* Glow effect */}
                  <div className="absolute -inset-4 bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-blue-500/20 rounded-3xl blur-2xl opacity-60 group-hover:opacity-80 transition-opacity duration-500 animate-pulse" style={{ animationDuration: '4s' }} />
                  
                  {/* Card */}
                  <div className="relative bg-white rounded-3xl shadow-2xl shadow-gray-900/10 border border-gray-100/50 overflow-hidden transform hover:scale-[1.02] transition-all duration-500 backdrop-blur-sm">
                    {/* Browser chrome */}
                    <div className="h-14 bg-gradient-to-b from-gray-50 to-gray-100/50 border-b border-gray-200/50 flex items-center px-4 space-x-2">
                      <div className="w-3 h-3 rounded-full bg-red-400 shadow-sm" />
                      <div className="w-3 h-3 rounded-full bg-yellow-400 shadow-sm" />
                      <div className="w-3 h-3 rounded-full bg-green-400 shadow-sm" />
                      <div className="flex-1 mx-4 h-8 bg-white rounded-lg border border-gray-200/50 shadow-sm flex items-center px-3">
                        <div className="w-4 h-4 bg-gray-300 rounded mr-2" />
                        <div className="flex-1 h-2 bg-gray-200 rounded" />
                      </div>
                    </div>
                    
                    {/* Content area */}
                    <div className="aspect-video bg-gradient-to-br from-blue-50 via-white to-purple-50/30 flex items-center justify-center p-12 relative overflow-hidden">
                      {/* Animated background pattern */}
                      <div className="absolute inset-0 opacity-5" style={{
                        backgroundImage: 'radial-gradient(circle at 2px 2px, rgb(0,0,0) 1px, transparent 0)',
                        backgroundSize: '40px 40px',
                        transform: `translate(${scrollY * 0.1}px, ${scrollY * 0.1}px)`
                      }} />
                      
                      {/* Preview card mockup */}
                      <div className="relative w-full max-w-md bg-white rounded-2xl shadow-xl border border-gray-100 p-8 transform hover:scale-105 transition-transform duration-500">
                        <div className="space-y-4">
                          <div className="h-6 bg-gradient-to-r from-gray-900 to-gray-700 rounded-lg w-3/4" />
                          <div className="space-y-2">
                            <div className="h-3 bg-gray-200 rounded-full w-full" />
                            <div className="h-3 bg-gray-200 rounded-full w-5/6" />
                            <div className="h-3 bg-gray-200 rounded-full w-4/5" />
                          </div>
                          <div className="h-20 bg-gradient-to-br from-blue-100 to-purple-100 rounded-xl" />
                          <div className="h-3 bg-gray-300 rounded-full w-1/3" />
                        </div>
                      </div>
                    </div>
                    
                    {/* Footer */}
                    <div className="p-8 bg-white border-t border-gray-100/50">
                      <div className="space-y-3">
                        <div className="h-5 bg-gray-900 rounded-lg w-2/3" />
                        <div className="space-y-2">
                          <div className="h-2.5 bg-gray-200 rounded-full w-full" />
                          <div className="h-2.5 bg-gray-200 rounded-full w-4/5" />
                        </div>
                        <div className="h-2.5 bg-gray-300 rounded-full w-1/3" />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Floating decorative elements */}
                <div className="absolute -top-8 -right-8 w-28 h-28 bg-gradient-to-br from-blue-100 to-blue-200 rounded-3xl rotate-12 shadow-2xl shadow-blue-500/20 animate-float opacity-80" />
                <div className="absolute -bottom-12 -left-12 w-36 h-36 bg-gradient-to-br from-gray-100 to-gray-200 rounded-3xl -rotate-12 shadow-2xl shadow-gray-900/10 animate-float opacity-70" style={{ animationDelay: '1s' }} />
                <div className="absolute top-1/2 -right-16 w-20 h-20 bg-gradient-to-br from-purple-100 to-purple-200 rounded-2xl rotate-45 shadow-xl shadow-purple-500/20 animate-float opacity-60" style={{ animationDelay: '2s' }} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Social Proof - Refined */}
      <section className="py-12 border-y border-gray-100/50 bg-white/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <p className="text-center text-xs font-bold text-gray-400 uppercase tracking-[0.2em] mb-8">Trusted by innovative teams</p>
          <div className="flex flex-wrap items-center justify-center gap-16 opacity-30 grayscale hover:grayscale-0 transition-all duration-500">
            {['NordicStore', 'CloudWave', 'TechFlow', 'DataVault', 'StreamLine'].map((name, i) => (
              <div 
                key={name} 
                className="text-3xl font-bold text-gray-400 hover:text-gray-600 transition-all duration-300 hover:scale-110"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                {name}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works - Premium */}
      <section 
        id="product" 
        className="py-24 px-6 lg:px-12 bg-white"
        ref={el => sectionRefs.current[0] = el as HTMLDivElement | null}
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16 space-y-3">
            <h2 className="text-4xl lg:text-5xl font-extrabold text-gray-900 tracking-[-0.02em]">How it works</h2>
            <p className="text-lg lg:text-xl text-gray-600 max-w-2xl mx-auto font-light">
              Get started in minutes. No technical knowledge required.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              {
                step: '01',
                title: 'Connect your domain',
                description: 'Add your website domain and verify ownership with a simple DNS check. Takes less than 5 minutes.',
                icon: LinkIcon,
                gradient: 'from-blue-500 to-blue-600',
                bgGradient: 'from-blue-50 to-blue-100/50',
              },
              {
                step: '02',
                title: 'Verify the domain',
                description: 'Complete DNS verification to activate your domain and enable preview generation.',
                icon: CheckIcon,
                gradient: 'from-green-500 to-green-600',
                bgGradient: 'from-green-50 to-green-100/50',
              },
              {
                step: '03',
                title: 'Generate AI previews',
                description: 'Our AI analyzes your pages and generates multi-variant previews (A/B/C) with semantic understanding.',
                icon: BoltIcon,
                gradient: 'from-purple-500 to-purple-600',
                bgGradient: 'from-purple-50 to-purple-100/50',
              },
              {
                step: '04',
                title: 'Install snippet & track',
                description: 'Add our embed code to your site and track performance with real-time analytics.',
                icon: CodeBracketIcon,
                gradient: 'from-orange-500 to-orange-600',
                bgGradient: 'from-orange-50 to-orange-100/50',
              },
            ].map((item, index) => (
              <div 
                key={item.step} 
                className="group relative bg-white rounded-3xl p-10 border border-gray-100/50 hover:border-gray-200 transition-all duration-500 hover:scale-105 hover:shadow-2xl shadow-gray-900/5 backdrop-blur-sm"
              >
                {/* Background gradient on hover */}
                <div className={`absolute inset-0 bg-gradient-to-br ${item.bgGradient} rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 -z-10`} />
                
                <div className={`w-20 h-20 bg-gradient-to-br ${item.gradient} rounded-3xl flex items-center justify-center mb-8 shadow-xl shadow-${item.gradient.split('-')[1]}-500/30 group-hover:scale-110 group-hover:rotate-3 transition-all duration-500`}>
                  <item.icon className="w-10 h-10 text-white" />
                </div>
                <div className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">Step {item.step}</div>
                <h3 className="text-2xl font-bold text-gray-900 mb-5 leading-tight">{item.title}</h3>
                <p className="text-gray-600 leading-relaxed text-lg">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features - Premium */}
      <section 
        id="features" 
        className="py-24 px-6 lg:px-12 bg-gradient-to-b from-white via-gray-50/30 to-white"
        ref={el => sectionRefs.current[1] = el as HTMLDivElement | null}
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16 space-y-3">
            <h2 className="text-4xl lg:text-5xl font-extrabold text-gray-900 tracking-[-0.02em]">Powerful features</h2>
            <p className="text-lg lg:text-xl text-gray-600 max-w-2xl mx-auto font-light">
              Everything you need to create stunning URL previews that drive engagement.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                title: 'AI-Powered Semantic Understanding',
                description: 'Deep AI intelligence analyzes your content to extract meaningful titles, descriptions, and keywords. Understands context, tone, and intent.',
                icon: BoltIcon,
                gradient: 'from-blue-500 to-blue-600',
                bgGradient: 'from-blue-50 to-blue-100/30',
              },
              {
                title: 'Real Screenshots + Highlight Detection',
                description: 'Automatic website screenshots with smart highlight cropping. Focuses on the most important visual elements of your pages.',
                icon: PhotoIcon,
                gradient: 'from-purple-500 to-purple-600',
                bgGradient: 'from-purple-50 to-purple-100/30',
              },
              {
                title: 'Multi-Variant Previews (A/B/C)',
                description: 'Generate three preview variants per URL to test what resonates best. A/B test titles, descriptions, and tones automatically.',
                icon: StarIcon,
                gradient: 'from-yellow-500 to-yellow-600',
                bgGradient: 'from-yellow-50 to-yellow-100/30',
              },
              {
                title: 'Smart Analytics & Tracking',
                description: 'Track impressions, clicks, CTR, and performance metrics per domain and preview. Real-time insights into what works.',
                icon: ChartBarIcon,
                gradient: 'from-green-500 to-green-600',
                bgGradient: 'from-green-50 to-green-100/30',
              },
              {
                title: 'Brand Tone Rewriting',
                description: 'Automatically rewrite preview text to match your brand voice. Maintain consistent messaging across all shared links.',
                icon: SparklesIcon,
                gradient: 'from-pink-500 to-pink-600',
                bgGradient: 'from-pink-50 to-pink-100/30',
              },
              {
                title: 'One-Click Integration',
                description: 'Add a single script tag to your site. Works across all platforms—WordPress, React, Vue, static sites, and more.',
                icon: PuzzlePieceIcon,
                gradient: 'from-indigo-500 to-indigo-600',
                bgGradient: 'from-indigo-50 to-indigo-100/30',
              },
            ].map((feature, index) => (
              <div 
                key={index} 
                className="group relative bg-white rounded-3xl p-10 border border-gray-100/50 hover:border-gray-200 transition-all duration-500 hover:scale-[1.02] hover:shadow-2xl shadow-gray-900/5 backdrop-blur-sm"
              >
                {/* Hover background */}
                <div className={`absolute inset-0 bg-gradient-to-br ${feature.bgGradient} rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 -z-10`} />
                
                <div className={`w-16 h-16 bg-gradient-to-br ${feature.gradient} rounded-2xl flex items-center justify-center mb-8 shadow-lg group-hover:scale-110 group-hover:rotate-3 transition-all duration-500`}>
                  <feature.icon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-4 leading-tight">{feature.title}</h3>
                <p className="text-gray-600 leading-relaxed text-lg">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Premium Device Mockup Section */}
      <section 
        className="py-24 px-6 lg:px-12 bg-white"
        ref={el => sectionRefs.current[2] = el as HTMLDivElement | null}
      >
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <div className="space-y-4">
                <h2 className="text-4xl lg:text-5xl font-extrabold text-gray-900 tracking-[-0.02em] leading-tight">
                  Beautiful previews,{' '}
                  <span className="bg-gradient-to-r from-blue-600 via-blue-700 to-blue-800 bg-clip-text text-transparent">everywhere</span>
                </h2>
                <p className="text-lg lg:text-xl text-gray-600 leading-relaxed font-light">
                  Your links look stunning across all platforms—social media, messaging apps, email, and more. 
                  Professional previews that drive engagement.
                </p>
              </div>
              <div className="space-y-5">
                {[
                  'Automatic preview generation for all your URLs',
                  'Multi-platform compatibility',
                  'Real-time analytics and insights',
                  'Custom branding and styling',
                ].map((item, i) => (
                  <div key={i} className="flex items-start space-x-4 group">
                    <div className="w-7 h-7 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5 shadow-lg shadow-blue-500/30 group-hover:scale-110 transition-transform duration-300">
                      <CheckIcon className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-gray-700 font-semibold text-lg pt-1">{item}</span>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Premium Device Mockups */}
            <div className="relative">
              <div className="relative">
                {/* Desktop Mockup */}
                <div className="relative bg-gray-900 rounded-t-3xl p-3 shadow-2xl transform hover:scale-105 transition-transform duration-500">
                  <div className="bg-white rounded-2xl overflow-hidden border border-gray-200">
                    {/* Browser chrome */}
                    <div className="h-14 bg-gradient-to-b from-gray-50 to-gray-100 flex items-center px-5 space-x-2 border-b border-gray-200">
                      <div className="w-3 h-3 rounded-full bg-red-400 shadow-sm" />
                      <div className="w-3 h-3 rounded-full bg-yellow-400 shadow-sm" />
                      <div className="w-3 h-3 rounded-full bg-green-400 shadow-sm" />
                      <div className="flex-1 mx-4 h-9 bg-white rounded-lg border border-gray-200 shadow-sm flex items-center px-4">
                        <div className="w-4 h-4 bg-gray-300 rounded mr-3" />
                        <div className="flex-1 h-2 bg-gray-200 rounded" />
                      </div>
                    </div>
                    {/* Content */}
                    <div className="aspect-video bg-gradient-to-br from-blue-50 via-white to-purple-50/30 p-10 flex items-center justify-center">
                      <div className="w-full max-w-lg bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
                        <div className="space-y-4">
                          <div className="h-6 bg-gradient-to-r from-gray-900 to-gray-700 rounded-lg w-3/4" />
                          <div className="space-y-2.5">
                            <div className="h-3 bg-gray-200 rounded-full w-full" />
                            <div className="h-3 bg-gray-200 rounded-full w-5/6" />
                          </div>
                          <div className="h-32 bg-gradient-to-br from-blue-100 via-purple-100 to-pink-100 rounded-xl" />
                          <div className="h-3 bg-gray-300 rounded-full w-1/3" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Mobile Mockup */}
                <div className="absolute -bottom-16 -right-12 w-56 bg-gray-900 rounded-[2.5rem] p-2.5 shadow-2xl transform rotate-6 hover:rotate-0 transition-all duration-500">
                  <div className="bg-white rounded-[2rem] overflow-hidden">
                    <div className="h-10 bg-gradient-to-b from-gray-50 to-gray-100 flex items-center justify-center border-b border-gray-200">
                      <div className="w-20 h-1.5 bg-gray-300 rounded-full" />
                    </div>
                    <div className="aspect-[9/16] bg-gradient-to-br from-blue-50 via-white to-purple-50/30 p-5 flex items-center justify-center">
                      <div className="w-full space-y-3">
                        <div className="h-5 bg-gray-900 rounded-lg w-2/3" />
                        <div className="h-2 bg-gray-200 rounded-full w-full" />
                        <div className="h-2 bg-gray-200 rounded-full w-4/5" />
                        <div className="h-24 bg-gradient-to-br from-blue-100 to-purple-100 rounded-xl" />
                        <div className="h-2 bg-gray-300 rounded-full w-1/3" />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Tablet Mockup */}
                <div className="absolute top-1/2 -left-16 w-64 bg-gray-900 rounded-3xl p-2 shadow-2xl transform -rotate-12 hover:rotate-0 transition-all duration-500">
                  <div className="bg-white rounded-2xl overflow-hidden">
                    <div className="h-8 bg-gradient-to-b from-gray-50 to-gray-100 flex items-center justify-center border-b border-gray-200">
                      <div className="w-16 h-1 bg-gray-300 rounded-full" />
                    </div>
                    <div className="aspect-[4/3] bg-gradient-to-br from-blue-50 to-purple-50/30 p-6 flex items-center justify-center">
                      <div className="w-full space-y-3">
                        <div className="h-4 bg-gray-900 rounded-lg w-3/4" />
                        <div className="h-2 bg-gray-200 rounded-full w-full" />
                        <div className="h-16 bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing - Premium */}
      <section 
        id="pricing" 
        className="py-24 px-6 lg:px-12 bg-gradient-to-b from-white via-gray-50/30 to-white"
        ref={el => sectionRefs.current[3] = el as HTMLDivElement | null}
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16 space-y-3">
            <h2 className="text-4xl lg:text-5xl font-extrabold text-gray-900 tracking-[-0.02em]">Simple, transparent pricing</h2>
            <p className="text-lg lg:text-xl text-gray-600 max-w-2xl mx-auto font-light">
              Choose the plan that fits your needs. All plans include a 14-day free trial.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {[
              {
                name: 'Starter',
                price: '$19',
                period: '/month',
                description: 'Perfect for small websites',
                features: [
                  'Up to 5 domains',
                  'Unlimited previews',
                  'Basic analytics',
                  'Email support',
                ],
                cta: 'Start Free Trial',
                highlighted: false,
                gradient: 'from-gray-100 to-gray-50',
                borderColor: 'border-gray-200',
              },
              {
                name: 'Growth',
                price: '$49',
                period: '/month',
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
                gradient: 'from-blue-600 to-blue-700',
                borderColor: 'border-blue-600',
              },
              {
                name: 'Agency',
                price: '$149',
                period: '/month',
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
                gradient: 'from-gray-100 to-gray-50',
                borderColor: 'border-gray-200',
              },
            ].map((plan, index) => (
              <div
                key={plan.name}
                className={`group relative bg-white rounded-3xl p-12 border-2 transition-all duration-500 hover:scale-105 hover:shadow-2xl ${
                  plan.highlighted 
                    ? `${plan.borderColor} shadow-2xl shadow-blue-500/20 scale-105` 
                    : `${plan.borderColor} shadow-xl shadow-gray-900/5 hover:border-gray-300`
                }`}
              >
                {plan.highlighted && (
                  <div className="absolute -top-5 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-blue-600 to-blue-700 text-white px-5 py-2 text-xs font-bold rounded-full shadow-xl">
                    Popular
                  </div>
                )}
                <div className="mb-10">
                  <h3 className="text-3xl font-bold text-gray-900 mb-3">{plan.name}</h3>
                  <p className="text-gray-600 mb-8 text-lg">{plan.description}</p>
                  <div className="flex items-baseline">
                    <span className="text-6xl font-extrabold text-gray-900">{plan.price}</span>
                    <span className="text-gray-600 ml-3 text-xl">{plan.period}</span>
                  </div>
                </div>
                <ul className="space-y-5 mb-12">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start">
                      <div className={`w-6 h-6 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5 ${
                        plan.highlighted ? 'bg-blue-100' : 'bg-gray-100'
                      } group-hover:scale-110 transition-transform duration-300`}>
                        <CheckIcon className={`w-4 h-4 ${plan.highlighted ? 'text-blue-600' : 'text-gray-600'}`} />
                      </div>
                      <span className="text-gray-700 ml-4 font-semibold text-lg">{feature}</span>
                    </li>
                  ))}
                </ul>
                <Link
                  to="/app"
                  className={`block w-full text-center py-5 rounded-2xl font-bold text-base transition-all duration-300 hover:scale-105 ${
                    plan.highlighted
                      ? 'bg-gray-900 text-white hover:bg-gray-800 shadow-xl shadow-gray-900/30'
                      : 'bg-gray-100 text-gray-900 hover:bg-gray-200 shadow-lg'
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Premium CTA Section */}
      <section 
        className="py-24 px-6 lg:px-12 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white relative overflow-hidden"
        ref={el => sectionRefs.current[4] = el as HTMLDivElement | null}
      >
        {/* Animated background */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-full h-full" style={{
            backgroundImage: 'radial-gradient(circle at 2px 2px, rgba(255,255,255,0.15) 1px, transparent 0)',
            backgroundSize: '60px 60px',
            transform: `translate(${scrollY * 0.05}px, ${scrollY * 0.05}px)`
          }} />
        </div>
        
        <div className="max-w-5xl mx-auto text-center space-y-6 relative z-10">
          <h2 className="text-4xl lg:text-5xl font-extrabold tracking-[-0.02em] leading-tight">
            Ready to transform your link previews?
          </h2>
          <p className="text-lg lg:text-xl text-gray-300 max-w-2xl mx-auto font-light leading-relaxed">
            Join thousands of teams using MetaView to create beautiful, high-converting URL previews.
          </p>
          <div className="flex flex-col sm:flex-row gap-5 justify-center pt-6">
            <Link 
              to="/app" 
              className="group relative px-12 py-6 bg-white text-gray-900 rounded-2xl font-bold text-lg hover:bg-gray-100 transition-all duration-300 hover:scale-105 hover:shadow-2xl shadow-white/20 inline-flex items-center justify-center overflow-hidden"
            >
              <span className="relative z-10 flex items-center">
                Start Free Trial
                <ArrowRightIcon className="w-6 h-6 ml-3 group-hover:translate-x-1 transition-transform duration-300" />
              </span>
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-blue-700 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </Link>
            <Link 
              to="/app" 
              className="px-12 py-6 bg-transparent text-white rounded-2xl font-bold text-lg border-2 border-white/20 hover:border-white/40 transition-all duration-300 hover:scale-105 inline-flex items-center justify-center backdrop-blur-sm"
            >
              View Demo
            </Link>
          </div>
        </div>
      </section>

      {/* Docs Section - Premium */}
      <section 
        id="docs" 
        className="py-24 px-6 lg:px-12 bg-white"
        ref={el => sectionRefs.current[5] = el as HTMLDivElement | null}
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16 space-y-3">
            <h2 className="text-4xl lg:text-5xl font-extrabold text-gray-900 tracking-[-0.02em]">Documentation</h2>
            <p className="text-lg lg:text-xl text-gray-600 max-w-2xl mx-auto font-light">
              Everything you need to integrate MetaView into your workflow.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                title: 'API Reference',
                description: 'Complete API documentation with interactive examples and endpoints.',
                link: 'http://localhost:8000/docs',
                external: true,
                gradient: 'from-blue-500 to-blue-600',
              },
              {
                title: 'Getting Started',
                description: 'Quick start guide to connect your first domain and generate previews.',
                link: '/app',
                external: false,
                gradient: 'from-purple-500 to-purple-600',
              },
              {
                title: 'Integration Guide',
                description: 'Step-by-step instructions for integrating with your existing infrastructure.',
                link: '#',
                external: false,
                gradient: 'from-orange-500 to-orange-600',
              },
            ].map((doc, index) => (
              <div 
                key={index}
                className="group relative bg-white rounded-3xl p-10 border border-gray-100/50 hover:border-gray-200 transition-all duration-500 hover:scale-105 hover:shadow-2xl shadow-gray-900/5 backdrop-blur-sm"
              >
                <div className={`w-16 h-16 bg-gradient-to-br ${doc.gradient} rounded-2xl flex items-center justify-center mb-8 shadow-lg group-hover:scale-110 group-hover:rotate-3 transition-all duration-500`}>
                  <CodeBracketIcon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-5">{doc.title}</h3>
                <p className="text-gray-600 mb-8 leading-relaxed text-lg">{doc.description}</p>
                {doc.external ? (
                  <a
                    href={doc.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-blue-600 hover:text-blue-700 font-bold text-lg group-hover:translate-x-2 transition-all duration-300"
                  >
                    View API Docs
                    <ArrowUpRightIcon className="w-5 h-5 ml-2" />
                  </a>
                ) : (
                  <Link
                    to={doc.link}
                    className="inline-flex items-center text-blue-600 hover:text-blue-700 font-bold text-lg group-hover:translate-x-2 transition-all duration-300"
                  >
                    Learn More
                    <ArrowUpRightIcon className="w-5 h-5 ml-2" />
                  </Link>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Premium Footer */}
      <footer className="bg-gray-900 text-white py-16 px-6 lg:px-12">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-12 mb-12">
            <div>
              <div className="flex items-center space-x-3 mb-6">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-600 via-blue-700 to-blue-800 rounded-2xl flex items-center justify-center shadow-xl">
                  <span className="text-white font-bold text-xl">P</span>
                </div>
                <span className="text-2xl font-bold">MetaView</span>
              </div>
              <p className="text-gray-400 text-sm leading-relaxed">
                Beautiful URL previews for every website.
              </p>
            </div>
            <div>
              <h4 className="font-bold mb-6 text-gray-300 text-sm uppercase tracking-wider">Product</h4>
              <ul className="space-y-4 text-sm text-gray-400">
                <li><a href="#features" className="hover:text-white transition-colors duration-200">Features</a></li>
                <li><a href="#pricing" className="hover:text-white transition-colors duration-200">Pricing</a></li>
                <li><Link to="/app" className="hover:text-white transition-colors duration-200">Dashboard</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-6 text-gray-300 text-sm uppercase tracking-wider">Company</h4>
              <ul className="space-y-4 text-sm text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors duration-200">Privacy</a></li>
                <li><a href="#" className="hover:text-white transition-colors duration-200">Terms</a></li>
                <li><a href="#" className="hover:text-white transition-colors duration-200">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-6 text-gray-300 text-sm uppercase tracking-wider">Connect</h4>
              <ul className="space-y-4 text-sm text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors duration-200">Twitter/X</a></li>
                <li><a href="#" className="hover:text-white transition-colors duration-200">LinkedIn</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-center text-sm text-gray-500">
            © 2024 MetaView. All rights reserved.
          </div>
        </div>
      </footer>

      <style>{`
        @keyframes float {
          0%, 100% {
            transform: translateY(0px) rotate(0deg);
          }
          50% {
            transform: translateY(-30px) rotate(5deg);
          }
        }
        
        .animate-float {
          animation: float 8s ease-in-out infinite;
        }

        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(40px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-fade-in-up {
          animation: fadeInUp 0.8s ease-out forwards;
        }

        /* Smooth scroll behavior */
        html {
          scroll-behavior: smooth;
        }
      `}</style>
    </div>
  )
}
