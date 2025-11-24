import { Link } from 'react-router-dom'
import {
  CheckIcon,
  ArrowRightIcon,
  LinkIcon,
  BoltIcon,
  ShareIcon,
  ChartBarIcon,
  PuzzlePieceIcon,
  StarIcon,
  CodeBracketIcon,
  PhotoIcon,
} from '@heroicons/react/24/outline'
import Card from '../components/ui/Card'

export default function Landing() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">P</span>
              </div>
              <span className="text-xl font-semibold text-secondary">Previewly</span>
            </div>
            <div className="hidden md:flex items-center space-x-8">
              <a href="#product" className="text-gray-600 hover:text-gray-900 transition-colors">Product</a>
              <a href="#features" className="text-gray-600 hover:text-gray-900 transition-colors">Features</a>
              <a href="#pricing" className="text-gray-600 hover:text-gray-900 transition-colors">Pricing</a>
              <a href="#docs" className="text-gray-600 hover:text-gray-900 transition-colors">Docs</a>
              <Link to="/app" className="text-gray-600 hover:text-gray-900 transition-colors">Login</Link>
            </div>
            <Link
              to="/app"
              className="btn-primary"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-5xl lg:text-6xl font-bold text-secondary mb-6 leading-tight">
                Turn every shared link into a{' '}
                <span className="text-primary">high-converting preview</span>
              </h1>
              <p className="text-xl text-muted mb-8 leading-relaxed">
                AI-powered URL previews that automatically generate beautiful, branded cards for your website. 
                Increase click-through rates by up to 40% with zero coding required.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link to="/app" className="btn-primary text-center inline-flex items-center justify-center">
                  Start Free Trial
                  <ArrowRightIcon className="w-5 h-5 ml-2" />
                </Link>
                <Link to="/app" className="btn-secondary text-center">
                  See Examples
                </Link>
              </div>
              <p className="text-sm text-muted-light mt-6">
                ✓ 14-day free trial • ✓ No credit card required • ✓ Setup in 5 minutes
              </p>
            </div>
            <div className="flex justify-center lg:justify-end">
              <div className="w-full max-w-md">
                <div className="card p-0 overflow-hidden">
                  <div className="aspect-video bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
                    <div className="w-24 h-24 bg-primary rounded-lg flex items-center justify-center shadow-lg">
                      <span className="text-white font-bold text-4xl">P</span>
                    </div>
                  </div>
                  <div className="p-6">
                    <h3 className="font-semibold text-gray-900 text-lg mb-2">Your Website Title</h3>
                    <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                      This is how your URL previews will appear on social media, messaging apps, and anywhere links are shared.
                    </p>
                    <p className="text-xs text-gray-500">example.com</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Social Proof */}
      <section className="py-12 border-y border-gray-200 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-muted-light mb-8">Trusted by innovative teams</p>
          <div className="flex flex-wrap items-center justify-center gap-8 opacity-60">
            {['NordicStore', 'CloudWave', 'TechFlow', 'DataVault', 'StreamLine'].map((name) => (
              <div key={name} className="text-xl font-semibold text-gray-400">
                {name}
              </div>
            ))}
          </div>
          {/* Testimonials placeholder */}
          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {[
              { quote: "Previewly increased our link click-through rate by 35%. The AI-generated previews are spot-on.", author: "Sarah Chen", role: "Marketing Director" },
              { quote: "Setup took 5 minutes. The multi-variant previews help us A/B test what works best.", author: "Michael Rodriguez", role: "Product Manager" },
              { quote: "Beautiful previews that match our brand perfectly. Our social shares look professional now.", author: "Emma Thompson", role: "Content Lead" },
            ].map((testimonial, i) => (
              <Card key={i} className="text-center">
                <p className="text-gray-700 mb-4 italic">"{testimonial.quote}"</p>
                <p className="font-semibold text-secondary">{testimonial.author}</p>
                <p className="text-sm text-muted-light">{testimonial.role}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="product" className="py-24 px-4 sm:px-6 lg:px-8 bg-background">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-secondary mb-4">How it works</h2>
            <p className="text-xl text-muted max-w-2xl mx-auto">
              Get started in minutes. No technical knowledge required.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {[
              {
                step: '1',
                title: 'Connect your domain',
                description: 'Add your website domain and verify ownership with a simple DNS check. Takes less than 5 minutes.',
                icon: LinkIcon,
              },
              {
                step: '2',
                title: 'Verify the domain',
                description: 'Complete DNS verification to activate your domain and enable preview generation.',
                icon: CheckIcon,
              },
              {
                step: '3',
                title: 'Generate AI previews',
                description: 'Our AI analyzes your pages and generates multi-variant previews (A/B/C) with semantic understanding.',
                icon: BoltIcon,
              },
              {
                step: '4',
                title: 'Install snippet & track',
                description: 'Add our embed code to your site and track performance with real-time analytics.',
                icon: CodeBracketIcon,
              },
            ].map((item) => (
              <div key={item.step} className="card text-center">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
                  <item.icon className="w-8 h-8 text-primary" />
                </div>
                <div className="text-sm font-semibold text-primary mb-2">Step {item.step}</div>
                <h3 className="text-xl font-semibold text-secondary mb-3">{item.title}</h3>
                <p className="text-muted">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-secondary mb-4">Powerful features</h2>
            <p className="text-xl text-muted max-w-2xl mx-auto">
              Everything you need to create stunning URL previews that drive engagement.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
            {[
              {
                title: 'AI-Powered Semantic Understanding',
                description: 'Deep AI intelligence analyzes your content to extract meaningful titles, descriptions, and keywords. Understands context, tone, and intent.',
                icon: BoltIcon,
              },
              {
                title: 'Real Screenshots + Highlight Detection',
                description: 'Automatic website screenshots with smart highlight cropping. Focuses on the most important visual elements of your pages.',
                icon: PhotoIcon,
              },
              {
                title: 'Multi-Variant Previews (A/B/C)',
                description: 'Generate three preview variants per URL to test what resonates best. A/B test titles, descriptions, and tones automatically.',
                icon: StarIcon,
              },
              {
                title: 'Smart Analytics & Tracking',
                description: 'Track impressions, clicks, CTR, and performance metrics per domain and preview. Real-time insights into what works.',
                icon: ChartBarIcon,
              },
              {
                title: 'Brand Tone Rewriting',
                description: 'Automatically rewrite preview text to match your brand voice. Maintain consistent messaging across all shared links.',
                icon: StarIcon,
              },
              {
                title: 'One-Click Integration',
                description: 'Add a single script tag to your site. Works across all platforms—WordPress, React, Vue, static sites, and more.',
                icon: PuzzlePieceIcon,
              },
            ].map((feature, index) => (
              <div key={index} className="card">
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-lg font-semibold text-secondary mb-2">{feature.title}</h3>
                <p className="text-muted">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-24 px-4 sm:px-6 lg:px-8 bg-background">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-secondary mb-4">Simple, transparent pricing</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Choose the plan that fits your needs. All plans include a 14-day free trial.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
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
              },
            ].map((plan) => (
              <div
                key={plan.name}
                className={`card relative ${plan.highlighted ? 'ring-2 ring-primary shadow-lg' : ''}`}
              >
                {plan.highlighted && (
                  <div className="absolute top-0 right-0 bg-primary text-white px-3 py-1 text-xs font-semibold rounded-bl-lg rounded-tr-lg">
                    Popular
                  </div>
                )}
                <div className="mb-6">
                  <h3 className="text-2xl font-bold text-secondary mb-2">{plan.name}</h3>
                  <p className="text-gray-600 mb-4">{plan.description}</p>
                  <div className="flex items-baseline">
                    <span className="text-4xl font-bold text-secondary">{plan.price}</span>
                    <span className="text-gray-600 ml-2">{plan.period}</span>
                  </div>
                </div>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <CheckIcon className="w-5 h-5 text-primary mr-2 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>
                <Link
                  to="/app"
                  className={`block w-full text-center py-3 rounded-lg font-medium transition-all ${
                    plan.highlighted
                      ? 'bg-primary text-white hover:bg-primary/90'
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

      {/* Docs Section */}
      <section id="docs" className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-secondary mb-4">Documentation</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Everything you need to integrate Previewly into your workflow.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <h3 className="text-xl font-semibold text-secondary mb-3">API Reference</h3>
              <p className="text-gray-600 mb-4">
                Complete API documentation with interactive examples and endpoints.
              </p>
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:text-primary/80 font-medium inline-flex items-center"
              >
                View API Docs
                <ArrowRightIcon className="w-4 h-4 ml-2" />
              </a>
            </Card>
            <Card>
              <h3 className="text-xl font-semibold text-secondary mb-3">Getting Started</h3>
              <p className="text-gray-600 mb-4">
                Quick start guide to connect your first domain and generate previews.
              </p>
              <Link
                to="/app"
                className="text-primary hover:text-primary/80 font-medium inline-flex items-center"
              >
                Start Now
                <ArrowRightIcon className="w-4 h-4 ml-2" />
              </Link>
            </Card>
            <Card>
              <h3 className="text-xl font-semibold text-secondary mb-3">Integration Guide</h3>
              <p className="text-gray-600 mb-4">
                Step-by-step instructions for integrating with your existing infrastructure.
              </p>
              <a
                href="#"
                className="text-primary hover:text-primary/80 font-medium inline-flex items-center"
              >
                Learn More
                <ArrowRightIcon className="w-4 h-4 ml-2" />
              </a>
            </Card>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-secondary text-white py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">P</span>
                </div>
                <span className="text-xl font-semibold">Previewly</span>
              </div>
              <p className="text-gray-400 text-sm">
                Beautiful URL previews for every website.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#pricing" className="hover:text-white transition-colors">Pricing</a></li>
                <li><Link to="/app" className="hover:text-white transition-colors">Dashboard</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">Privacy</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Terms</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Connect</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">Twitter/X</a></li>
                <li><a href="#" className="hover:text-white transition-colors">LinkedIn</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-700 pt-8 text-center text-sm text-gray-400">
            © 2024 Previewly. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}

