import {
  ArrowTrendingUpIcon,
  GlobeAltIcon,
  PhotoIcon,
  StarIcon,
  SparklesIcon,
  XMarkIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline'
import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import EmptyState from '../components/ui/EmptyState'
import { useDomains } from '../hooks/useDomains'
import { usePreviews } from '../hooks/usePreviews'
import { useAnalyticsSummary } from '../hooks/useAnalyticsSummary'

export default function Dashboard() {
  const navigate = useNavigate()
  const { domains, loading: domainsLoading } = useDomains()
  const { previews, loading: previewsLoading } = usePreviews()
  const { summary, loading: analyticsLoading } = useAnalyticsSummary('30d')
  const [onboardingDismissed, setOnboardingDismissed] = useState(false)
  
  // Check if onboarding should be shown
  useEffect(() => {
    const dismissed = localStorage.getItem('onboarding_dismissed') === 'true'
    setOnboardingDismissed(dismissed)
  }, [])
  
  const shouldShowOnboarding = !onboardingDismissed && 
    !domainsLoading && 
    !previewsLoading && 
    domains.length === 0 && 
    previews.length === 0
  
  const handleDismissOnboarding = () => {
    localStorage.setItem('onboarding_dismissed', 'true')
    setOnboardingDismissed(true)
  }
  
  const verifiedDomains = domains.filter(d => d.status === 'verified')
  const hasVerifiedDomain = verifiedDomains.length > 0

  // Calculate new domains count (domains created in last 30 days)
  const newDomainsCount = useMemo(() => {
    if (!domains.length) return 0
    const thirtyDaysAgo = new Date()
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)
    return domains.filter((d) => {
      const createdDate = new Date(d.created_at)
      return createdDate >= thirtyDaysAgo
    }).length
  }, [domains])

  const statsConfig = [
    {
      name: 'Monthly Clicks',
      value: summary?.total_clicks.toLocaleString() || '0',
      description: '+12.5% from last month',
      icon: ArrowTrendingUpIcon,
      color: 'text-primary',
    },
    {
      name: 'New Domains',
      value: newDomainsCount.toString(),
      description: 'Added this month',
      icon: GlobeAltIcon,
      color: 'text-accent',
    },
    {
      name: 'Previews Generated',
      value: summary?.total_previews.toLocaleString() || '0',
      description: 'Across all domains',
      icon: PhotoIcon,
      color: 'text-purple-500',
    },
    {
      name: 'Brand Score',
      value: summary?.brand_score.toString() || '0',
      description: 'Excellent consistency',
      icon: StarIcon,
      color: 'text-yellow-500',
    },
  ]

  const isLoading = domainsLoading || analyticsLoading || previewsLoading
  
  const onboardingSteps = [
    {
      id: 1,
      title: 'Add your first domain',
      description: 'Connect your website domain to start generating previews',
      completed: domains.length > 0,
      action: () => navigate('/app/domains'),
    },
    {
      id: 2,
      title: 'Verify the domain',
      description: 'Complete DNS verification to activate your domain',
      completed: hasVerifiedDomain,
      action: () => navigate('/app/domains'),
    },
    {
      id: 3,
      title: 'Generate your first AI preview',
      description: 'Create beautiful preview cards for your URLs',
      completed: previews.length > 0,
      action: () => navigate('/app/previews'),
    },
    {
      id: 4,
      title: 'Install the snippet on your site',
      description: 'Add our embed code to enable automatic previews',
      completed: false, // This would require checking if snippet is installed
      action: () => navigate('/app/previews'),
    },
  ]
  
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-secondary mb-2">Dashboard</h1>
        <p className="text-muted">
          {domains.length === 0 && previews.length === 0
            ? "Welcome! Let's get you started with your first preview."
            : "Welcome back! Here's what's happening with your previews."}
        </p>
      </div>

      {/* Onboarding Panel */}
      {shouldShowOnboarding && (
        <Card className="mb-8 bg-gradient-to-r from-primary/5 to-accent/5 border-primary/20">
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                <SparklesIcon className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-secondary">Getting Started</h2>
                <p className="text-sm text-muted">Follow these steps to set up your preview system</p>
              </div>
            </div>
            <button
              onClick={handleDismissOnboarding}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Dismiss onboarding"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>
          
          <div className="space-y-4">
            {onboardingSteps.map((step, index) => (
              <div
                key={step.id}
                className={`flex items-start space-x-4 p-4 rounded-lg border transition-colors ${
                  step.completed
                    ? 'bg-green-50 border-green-200'
                    : 'bg-white border-gray-200 hover:border-primary/50'
                }`}
              >
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  step.completed ? 'bg-green-500' : 'bg-gray-200'
                }`}>
                  {step.completed ? (
                    <CheckCircleIcon className="w-5 h-5 text-white" />
                  ) : (
                    <span className="text-sm font-semibold text-gray-600">{step.id}</span>
                  )}
                </div>
                <div className="flex-1">
                  <h3 className={`font-medium mb-1 ${
                    step.completed ? 'text-green-900' : 'text-secondary'
                  }`}>
                    {step.title}
                  </h3>
                  <p className="text-sm text-muted mb-3">{step.description}</p>
                  {!step.completed && (
                    <Button size="sm" onClick={step.action}>
                      {step.id === 1 ? 'Add Domain' : step.id === 2 ? 'Verify Domain' : step.id === 3 ? 'Generate Preview' : 'View Instructions'}
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {isLoading ? (
        <Card>
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-4"></div>
            <p className="text-muted">Loading dashboard data...</p>
          </div>
        </Card>
      ) : domains.length === 0 && previews.length === 0 && onboardingDismissed ? (
        <Card>
          <EmptyState
            icon={<SparklesIcon className="w-8 h-8" />}
            title="Get started with your first preview"
            description="Connect a domain and generate your first AI-powered preview to see how your links will appear when shared."
            action={{
              label: 'Add Your First Domain',
              onClick: () => navigate('/app/domains'),
            }}
          />
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {statsConfig.map((stat) => (
              <Card key={stat.name} className="hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-600 mb-1">{stat.name}</p>
                    <p className="text-3xl font-bold text-secondary mb-2">{stat.value}</p>
                    <p className="text-xs text-gray-500">{stat.description}</p>
                  </div>
                  <div className={`p-3 rounded-lg bg-gray-50 ${stat.color}`}>
                    <stat.icon className="w-6 h-6" />
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h3 className="text-lg font-semibold text-secondary mb-4">Recent Activity</h3>
          {previews.length === 0 ? (
            <EmptyState
              icon={<PhotoIcon className="w-6 h-6" />}
              title="No activity yet"
              description="Once you generate previews, your recent activity will appear here."
              action={{
                label: 'Generate Your First Preview',
                onClick: () => navigate('/app/previews'),
              }}
            />
          ) : (
            <div className="space-y-4">
              {previews.slice(0, 3).map((preview) => (
                <div key={preview.id} className="flex items-center space-x-4 pb-4 border-b border-gray-100 last:border-0">
                  <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                    <PhotoIcon className="w-5 h-5 text-primary" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{preview.title || 'Preview generated'}</p>
                    <p className="text-xs text-muted-light">
                      {new Date(preview.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-secondary mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <button 
              onClick={() => navigate('/app/domains')}
              className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-primary hover:bg-primary/5 transition-colors"
            >
              <p className="font-medium text-gray-900">Add New Domain</p>
              <p className="text-sm text-muted-light">Connect a new website</p>
            </button>
            <button 
              onClick={() => navigate('/app/brand')}
              className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-primary hover:bg-primary/5 transition-colors"
            >
              <p className="font-medium text-gray-900">Customize Brand</p>
              <p className="text-sm text-muted-light">Update your preview style</p>
            </button>
            <button 
              onClick={() => navigate('/app/previews')}
              className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-primary hover:bg-primary/5 transition-colors"
            >
              <p className="font-medium text-gray-900">Generate Preview</p>
              <p className="text-sm text-muted-light">Create a new AI preview</p>
            </button>
          </div>
        </Card>
      </div>
    </div>
  )
}

