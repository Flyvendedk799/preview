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
} from '@heroicons/react/24/outline'

export default function Landing() {
  const [isVisible, setIsVisible] = useState(false)
  const heroRef = useRef<HTMLDivElement>(null)
  const featuresRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setIsVisible(true)
    
    // Parallax effect on scroll
    const handleScroll = () => {
      const scrolled = window.pageYOffset
      const hero = heroRef.current
      if (hero) {
        hero.style.transform = `translateY(${scrolled * 0.5}px)`
        hero.style.opacity = `${1 - scrolled / 600}`
      }
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <div className="min-h-screen bg-white overflow-x-hidden">
      {/* Animated Background Shapes */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute top-20 -left-40 w-96 h-96 bg-blue-50 rounded-full blur-3xl opacity-40 animate-pulse" style={{ animationDuration: '8s' }} />
        <div className="absolute top-60 right-20 w-80 h-80 bg-blue-100/30 rounded-full blur-3xl opacity-30 animate-pulse" style={{ animationDuration: '10s', animationDelay: '2s' }} />
        <div className="absolute bottom-40 left-1/4 w-72 h-72 bg-blue-50 rounded-full blur-3xl opacity-20 animate-pulse" style={{ animationDuration: '12s', animationDelay: '4s' }} />
      </div>

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/70 backdrop-blur-xl border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="flex items-center justify-between h-20">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
                <span className="text-white font-bold text-xl">P</span>
              </div>
              <span className="text-2xl font-bold text-gray-900 tracking-tight">Previewly</span>
            </div>
            <div className="hidden md:flex items-center space-x-10">
              <a href="#product" className="text-gray-600 hover:text-gray-900 transition-colors font-medium text-sm">Product</a>
              <a href="#features" className="text-gray-600 hover:text-gray-900 transition-colors font-medium text-sm">Features</a>
              <a href="#pricing" className="text-gray-600 hover:text-gray-900 transition-colors font-medium text-sm">Pricing</a>
              <a href="#docs" className="text-gray-600 hover:text-gray-900 transition-colors font-medium text-sm">Docs</a>
              <Link to="/app" className="text-gray-600 hover:text-gray-900 transition-colors font-medium text-sm">Login</Link>
            </div>
            <Link
              to="/app"
              className="px-6 py-2.5 bg-gray-900 text-white rounded-xl font-semibold text-sm hover:bg-gray-800 transition-all hover:scale-105 hover:shadow-lg shadow-gray-900/20"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-40 pb-32 px-6 lg:px-12">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
            <div className={`space-y-8 transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
              <div className="space-y-6">
                <div className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-50 rounded-full border border-blue-100 w-fit">
                  <SparklesIcon className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-semibold text-blue-600">AI-Powered Preview Generation</span>
                </div>
                <h1 className="text-6xl lg:text-7xl font-bold text-gray-900 leading-[1.1] tracking-tight">
                  Turn every shared link into a{' '}
                  <span className="bg-gradient-to-r from-blue-600 to-blue-700 bg-clip-text text-transparent">high-converting</span>{' '}
                  preview
                </h1>
                <p className="text-xl text-gray-600 leading-relaxed max-w-xl">
                  AI-powered URL previews that automatically generate beautiful, branded cards for your website. 
                  Increase click-through rates by up to 40% with zero coding required.
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Link 
                  to="/app" 
                  className="group px-8 py-4 bg-gray-900 text-white rounded-xl font-semibold text-base hover:bg-gray-800 transition-all hover:scale-105 hover:shadow-2xl shadow-gray-900/30 inline-flex items-center justify-center"
                >
                  Start Free Trial
                  <ArrowRightIcon className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                </Link>
                <Link 
                  to="/app" 
                  className="px-8 py-4 bg-white text-gray-900 rounded-xl font-semibold text-base border-2 border-gray-200 hover:border-gray-300 transition-all hover:scale-105 hover:shadow-lg shadow-gray-200/50 inline-flex items-center justify-center"
                >
                  See Examples
                </Link>
              </div>
              
              <div className="flex items-center space-x-6 pt-4">
                <div className="flex items-center space-x-2">
                  <CheckIcon className="w-5 h-5 text-green-600" />
                  <span className="text-sm text-gray-600 font-medium">14-day free trial</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckIcon className="w-5 h-5 text-green-600" />
                  <span className="text-sm text-gray-600 font-medium">No credit card</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckIcon className="w-5 h-5 text-green-600" />
                  <span className="text-sm text-gray-600 font-medium">5 min setup</span>
                </div>
              </div>
            </div>
            
            {/* Floating Mockup */}
            <div 
              ref={heroRef}
              className={`relative transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}
              style={{ transitionDelay: '200ms' }}
            >
              <div className="relative">
                {/* Floating Card Mockup */}
                <div className="relative group">
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500/20 to-blue-600/20 rounded-3xl blur-2xl transform scale-110 group-hover:scale-115 transition-transform duration-500" />
                  <div className="relative bg-white rounded-3xl shadow-2xl shadow-gray-900/10 border border-gray-100 overflow-hidden transform hover:scale-[1.02] transition-all duration-500">
                    <div className="aspect-video bg-gradient-to-br from-blue-50 via-blue-100/50 to-white flex items-center justify-center p-8">
                      <div className="w-full max-w-sm space-y-4">
                        <div className="h-4 bg-gray-200 rounded-full w-3/4 animate-pulse" />
                        <div className="h-4 bg-gray-200 rounded-full w-full animate-pulse" style={{ animationDelay: '0.2s' }} />
                        <div className="h-4 bg-gray-200 rounded-full w-5/6 animate-pulse" style={{ animationDelay: '0.4s' }} />
                      </div>
                    </div>
                    <div className="p-8 space-y-4">
                      <div className="h-6 bg-gray-900 rounded-lg w-2/3" />
                      <div className="space-y-2">
                        <div className="h-3 bg-gray-200 rounded-full w-full" />
                        <div className="h-3 bg-gray-200 rounded-full w-4/5" />
                      </div>
                      <div className="h-3 bg-gray-300 rounded-full w-1/3" />
                    </div>
                  </div>
                </div>

                {/* Floating Elements */}
                <div className="absolute -top-6 -right-6 w-24 h-24 bg-blue-100 rounded-2xl rotate-12 shadow-lg shadow-blue-500/20 animate-float" />
                <div className="absolute -bottom-8 -left-8 w-32 h-32 bg-gray-100 rounded-3xl -rotate-12 shadow-lg shadow-gray-900/10 animate-float" style={{ animationDelay: '1s' }} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Social Proof */}
      <section className="py-16 border-y border-gray-100 bg-gray-50/50">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <p className="text-center text-sm font-semibold text-gray-500 uppercase tracking-wider mb-12">Trusted by innovative teams</p>
          <div className="flex flex-wrap items-center justify-center gap-12 opacity-40 grayscale">
            {['NordicStore', 'CloudWave', 'TechFlow', 'DataVault', 'StreamLine'].map((name, i) => (
              <div 
                key={name} 
                className="text-2xl font-bold text-gray-400 hover:opacity-60 transition-opacity"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                {name}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="product" className="py-32 px-6 lg:px-12 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20 space-y-4">
            <h2 className="text-5xl lg:text-6xl font-bold text-gray-900 tracking-tight">How it works</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
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
              },
              {
                step: '02',
                title: 'Verify the domain',
                description: 'Complete DNS verification to activate your domain and enable preview generation.',
                icon: CheckIcon,
                gradient: 'from-green-500 to-green-600',
              },
              {
                step: '03',
                title: 'Generate AI previews',
                description: 'Our AI analyzes your pages and generates multi-variant previews (A/B/C) with semantic understanding.',
                icon: BoltIcon,
                gradient: 'from-purple-500 to-purple-600',
              },
              {
                step: '04',
                title: 'Install snippet & track',
                description: 'Add our embed code to your site and track performance with real-time analytics.',
                icon: CodeBracketIcon,
                gradient: 'from-orange-500 to-orange-600',
              },
            ].map((item, index) => (
              <div 
                key={item.step} 
                className="group relative bg-white rounded-2xl p-8 border border-gray-100 hover:border-gray-200 transition-all duration-300 hover:scale-105 hover:shadow-xl shadow-gray-900/5"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className={`w-16 h-16 bg-gradient-to-br ${item.gradient} rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-${item.gradient.split('-')[1]}-500/20 group-hover:scale-110 transition-transform duration-300`}>
                  <item.icon className="w-8 h-8 text-white" />
                </div>
                <div className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Step {item.step}</div>
                <h3 className="text-2xl font-bold text-gray-900 mb-4">{item.title}</h3>
                <p className="text-gray-600 leading-relaxed">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-32 px-6 lg:px-12 bg-gray-50/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20 space-y-4">
            <h2 className="text-5xl lg:text-6xl font-bold text-gray-900 tracking-tight">Powerful features</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
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
              },
              {
                title: 'Real Screenshots + Highlight Detection',
                description: 'Automatic website screenshots with smart highlight cropping. Focuses on the most important visual elements of your pages.',
                icon: PhotoIcon,
                gradient: 'from-purple-500 to-purple-600',
              },
              {
                title: 'Multi-Variant Previews (A/B/C)',
                description: 'Generate three preview variants per URL to test what resonates best. A/B test titles, descriptions, and tones automatically.',
                icon: StarIcon,
                gradient: 'from-yellow-500 to-yellow-600',
              },
              {
                title: 'Smart Analytics & Tracking',
                description: 'Track impressions, clicks, CTR, and performance metrics per domain and preview. Real-time insights into what works.',
                icon: ChartBarIcon,
                gradient: 'from-green-500 to-green-600',
              },
              {
                title: 'Brand Tone Rewriting',
                description: 'Automatically rewrite preview text to match your brand voice. Maintain consistent messaging across all shared links.',
                icon: SparklesIcon,
                gradient: 'from-pink-500 to-pink-600',
              },
              {
                title: 'One-Click Integration',
                description: 'Add a single script tag to your site. Works across all platforms—WordPress, React, Vue, static sites, and more.',
                icon: PuzzlePieceIcon,
                gradient: 'from-indigo-500 to-indigo-600',
              },
            ].map((feature, index) => (
              <div 
                key={index} 
                className="group bg-white rounded-2xl p-8 border border-gray-100 hover:border-gray-200 transition-all duration-300 hover:scale-[1.02] hover:shadow-xl shadow-gray-900/5"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <div className={`w-14 h-14 bg-gradient-to-br ${feature.gradient} rounded-xl flex items-center justify-center mb-6 shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                  <feature.icon className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-3">{feature.title}</h3>
                <p className="text-gray-600 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Premium Device Mockup Section */}
      <section className="py-32 px-6 lg:px-12 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div className="space-y-8">
              <div className="space-y-4">
                <h2 className="text-5xl lg:text-6xl font-bold text-gray-900 tracking-tight leading-tight">
                  Beautiful previews,{' '}
                  <span className="bg-gradient-to-r from-blue-600 to-blue-700 bg-clip-text text-transparent">everywhere</span>
                </h2>
                <p className="text-xl text-gray-600 leading-relaxed">
                  Your links look stunning across all platforms—social media, messaging apps, email, and more. 
                  Professional previews that drive engagement.
                </p>
              </div>
              <div className="space-y-4">
                {[
                  'Automatic preview generation for all your URLs',
                  'Multi-platform compatibility',
                  'Real-time analytics and insights',
                  'Custom branding and styling',
                ].map((item, i) => (
                  <div key={i} className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                      <CheckIcon className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-gray-700 font-medium">{item}</span>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Device Mockups */}
            <div className="relative">
              <div className="relative">
                {/* Desktop Mockup */}
                <div className="relative bg-gray-900 rounded-t-2xl p-2 shadow-2xl">
                  <div className="bg-white rounded-lg overflow-hidden">
                    <div className="h-12 bg-gray-100 flex items-center px-4 space-x-2">
                      <div className="w-3 h-3 rounded-full bg-red-500" />
                      <div className="w-3 h-3 rounded-full bg-yellow-500" />
                      <div className="w-3 h-3 rounded-full bg-green-500" />
                    </div>
                    <div className="aspect-video bg-gradient-to-br from-blue-50 to-white p-8 flex items-center justify-center">
                      <div className="w-full max-w-md space-y-3">
                        <div className="h-5 bg-gray-200 rounded-lg w-3/4" />
                        <div className="h-3 bg-gray-200 rounded-lg w-full" />
                        <div className="h-3 bg-gray-200 rounded-lg w-5/6" />
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Mobile Mockup */}
                <div className="absolute -bottom-12 -right-8 w-48 bg-gray-900 rounded-3xl p-2 shadow-2xl transform rotate-6 hover:rotate-0 transition-transform duration-500">
                  <div className="bg-white rounded-2xl overflow-hidden">
                    <div className="h-8 bg-gray-100 flex items-center justify-center">
                      <div className="w-16 h-1 bg-gray-300 rounded-full" />
                    </div>
                    <div className="aspect-[9/16] bg-gradient-to-br from-blue-50 to-white p-4 flex items-center justify-center">
                      <div className="w-full space-y-2">
                        <div className="h-4 bg-gray-200 rounded w-2/3" />
                        <div className="h-2 bg-gray-200 rounded w-full" />
                        <div className="h-2 bg-gray-200 rounded w-4/5" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-32 px-6 lg:px-12 bg-gray-50/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20 space-y-4">
            <h2 className="text-5xl lg:text-6xl font-bold text-gray-900 tracking-tight">Simple, transparent pricing</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
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
              },
            ].map((plan, index) => (
              <div
                key={plan.name}
                className={`relative bg-white rounded-3xl p-10 border-2 transition-all duration-300 hover:scale-105 hover:shadow-2xl ${
                  plan.highlighted 
                    ? 'border-blue-600 shadow-2xl shadow-blue-500/20 scale-105' 
                    : 'border-gray-100 shadow-lg shadow-gray-900/5 hover:border-gray-200'
                }`}
                style={{ animationDelay: `${index * 100}ms` }}
              >
                {plan.highlighted && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-blue-600 to-blue-700 text-white px-4 py-1.5 text-xs font-bold rounded-full shadow-lg">
                    Popular
                  </div>
                )}
                <div className="mb-8">
                  <h3 className="text-3xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                  <p className="text-gray-600 mb-6">{plan.description}</p>
                  <div className="flex items-baseline">
                    <span className="text-5xl font-bold text-gray-900">{plan.price}</span>
                    <span className="text-gray-600 ml-2 text-lg">{plan.period}</span>
                  </div>
                </div>
                <ul className="space-y-4 mb-10">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start">
                      <div className={`w-5 h-5 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ${
                        plan.highlighted ? 'bg-blue-100' : 'bg-gray-100'
                      }`}>
                        <CheckIcon className={`w-3.5 h-3.5 ${plan.highlighted ? 'text-blue-600' : 'text-gray-600'}`} />
                      </div>
                      <span className="text-gray-700 ml-3 font-medium">{feature}</span>
                    </li>
                  ))}
                </ul>
                <Link
                  to="/app"
                  className={`block w-full text-center py-4 rounded-xl font-bold text-base transition-all hover:scale-105 ${
                    plan.highlighted
                      ? 'bg-gray-900 text-white hover:bg-gray-800 shadow-lg shadow-gray-900/20'
                      : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 px-6 lg:px-12 bg-gradient-to-br from-gray-900 to-gray-800 text-white">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <h2 className="text-5xl lg:text-6xl font-bold tracking-tight">
            Ready to transform your link previews?
          </h2>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Join thousands of teams using Previewly to create beautiful, high-converting URL previews.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
            <Link 
              to="/app" 
              className="px-8 py-4 bg-white text-gray-900 rounded-xl font-bold text-base hover:bg-gray-100 transition-all hover:scale-105 hover:shadow-2xl shadow-white/20 inline-flex items-center justify-center"
            >
              Start Free Trial
              <ArrowRightIcon className="w-5 h-5 ml-2" />
            </Link>
            <Link 
              to="/app" 
              className="px-8 py-4 bg-transparent text-white rounded-xl font-bold text-base border-2 border-white/20 hover:border-white/40 transition-all hover:scale-105 inline-flex items-center justify-center"
            >
              View Demo
            </Link>
          </div>
        </div>
      </section>

      {/* Docs Section */}
      <section id="docs" className="py-32 px-6 lg:px-12 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20 space-y-4">
            <h2 className="text-5xl lg:text-6xl font-bold text-gray-900 tracking-tight">Documentation</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Everything you need to integrate Previewly into your workflow.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                title: 'API Reference',
                description: 'Complete API documentation with interactive examples and endpoints.',
                link: 'http://localhost:8000/docs',
                external: true,
              },
              {
                title: 'Getting Started',
                description: 'Quick start guide to connect your first domain and generate previews.',
                link: '/app',
                external: false,
              },
              {
                title: 'Integration Guide',
                description: 'Step-by-step instructions for integrating with your existing infrastructure.',
                link: '#',
                external: false,
              },
            ].map((doc, index) => (
              <div 
                key={index}
                className="group bg-white rounded-2xl p-8 border border-gray-100 hover:border-gray-200 transition-all duration-300 hover:scale-105 hover:shadow-xl shadow-gray-900/5"
              >
                <h3 className="text-2xl font-bold text-gray-900 mb-4">{doc.title}</h3>
                <p className="text-gray-600 mb-6 leading-relaxed">{doc.description}</p>
                {doc.external ? (
                  <a
                    href={doc.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-blue-600 hover:text-blue-700 font-semibold group-hover:translate-x-1 transition-transform"
                  >
                    View API Docs
                    <ArrowRightIcon className="w-5 h-5 ml-2" />
                  </a>
                ) : (
                  <Link
                    to={doc.link}
                    className="inline-flex items-center text-blue-600 hover:text-blue-700 font-semibold group-hover:translate-x-1 transition-transform"
                  >
                    Learn More
                    <ArrowRightIcon className="w-5 h-5 ml-2" />
                  </Link>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-16 px-6 lg:px-12">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-12 mb-12">
            <div>
              <div className="flex items-center space-x-3 mb-6">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl flex items-center justify-center shadow-lg">
                  <span className="text-white font-bold text-xl">P</span>
                </div>
                <span className="text-2xl font-bold">Previewly</span>
              </div>
              <p className="text-gray-400 text-sm leading-relaxed">
                Beautiful URL previews for every website.
              </p>
            </div>
            <div>
              <h4 className="font-bold mb-4 text-gray-300">Product</h4>
              <ul className="space-y-3 text-sm text-gray-400">
                <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#pricing" className="hover:text-white transition-colors">Pricing</a></li>
                <li><Link to="/app" className="hover:text-white transition-colors">Dashboard</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-4 text-gray-300">Company</h4>
              <ul className="space-y-3 text-sm text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">Privacy</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Terms</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-4 text-gray-300">Connect</h4>
              <ul className="space-y-3 text-sm text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">Twitter/X</a></li>
                <li><a href="#" className="hover:text-white transition-colors">LinkedIn</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-center text-sm text-gray-400">
            © 2024 Previewly. All rights reserved.
          </div>
        </div>
      </footer>

      <style>{`
        @keyframes float {
          0%, 100% {
            transform: translateY(0px) rotate(0deg);
          }
          50% {
            transform: translateY(-20px) rotate(5deg);
          }
        }
        
        .animate-float {
          animation: float 6s ease-in-out infinite;
        }
      `}</style>
    </div>
  )
}

