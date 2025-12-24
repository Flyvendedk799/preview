import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowRightIcon,
  ArrowLeftIcon,
  CheckCircleIcon,
  GlobeAltIcon,
  PaintBrushIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import { fetchDomains, createSite, type Domain, type PublishedSiteCreate } from '../../api/client'

type Step = 'domain' | 'template' | 'branding' | 'settings' | 'complete'

export default function CreateSite() {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState<Step>('domain')
  const [domains, setDomains] = useState<Domain[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  
  // Form data
  const [selectedDomainId, setSelectedDomainId] = useState<number | null>(null)
  const [siteName, setSiteName] = useState('')
  const [templateId, setTemplateId] = useState('default')
  const [primaryColor, setPrimaryColor] = useState('#f97316')
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    loadDomains()
  }, [])

  async function loadDomains() {
    try {
      setLoading(true)
      const data = await fetchDomains()
      // Filter to only verified domains
      const verified = data.filter(d => d.status === 'verified')
      setDomains(verified)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load domains')
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmit() {
    if (!selectedDomainId || !siteName.trim()) {
      setError('Please fill in all required fields')
      return
    }

    try {
      setIsSubmitting(true)
      setError('')
      
      const siteData: PublishedSiteCreate = {
        name: siteName,
        domain_id: selectedDomainId,
        template_id: templateId,
        status: 'draft',
        is_active: true,
      }
      
      const site = await createSite(siteData)
      setCurrentStep('complete')
      
      // Redirect after 2 seconds
      setTimeout(() => {
        navigate(`/app/sites/${site.id}`)
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create site')
    } finally {
      setIsSubmitting(false)
    }
  }

  const steps = [
    { id: 'domain', name: 'Domain', icon: GlobeAltIcon },
    { id: 'template', name: 'Template', icon: PaintBrushIcon },
    { id: 'branding', name: 'Branding', icon: PaintBrushIcon },
    { id: 'settings', name: 'Settings', icon: Cog6ToothIcon },
  ]

  const stepIndex = steps.findIndex(s => s.id === currentStep)

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-secondary mb-2">Create New Site</h1>
        <p className="text-muted">Set up your white-label blog or news site</p>
      </div>

      {/* Step Indicator */}
      <Card className="mb-6">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => {
            const StepIcon = step.icon
            const isActive = index === stepIndex
            const isCompleted = index < stepIndex
            
            return (
              <div key={step.id} className="flex items-center flex-1">
                <div className="flex flex-col items-center flex-1">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                    isCompleted ? 'bg-green-500 text-white' :
                    isActive ? 'bg-primary text-white' :
                    'bg-gray-200 text-gray-600'
                  }`}>
                    {isCompleted ? (
                      <CheckCircleIcon className="w-6 h-6" />
                    ) : (
                      <StepIcon className="w-5 h-5" />
                    )}
                  </div>
                  <span className={`text-xs mt-2 ${isActive ? 'font-medium text-primary' : 'text-gray-500'}`}>
                    {step.name}
                  </span>
                </div>
                {index < steps.length - 1 && (
                  <div className={`h-0.5 flex-1 mx-2 ${isCompleted ? 'bg-green-500' : 'bg-gray-200'}`} />
                )}
              </div>
            )
          })}
        </div>
      </Card>

      {error && (
        <Card className="mb-6 bg-red-50 border-red-200">
          <p className="text-red-800">{error}</p>
        </Card>
      )}

      {/* Step Content */}
      <Card>
        {currentStep === 'domain' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-secondary mb-2">Select Domain</h2>
              <p className="text-muted mb-4">Choose a verified domain for your site</p>
            </div>

            {loading ? (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : domains.length === 0 ? (
              <div className="text-center py-8">
                <GlobeAltIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">No verified domains available</p>
                <Button onClick={() => navigate('/app/domains')}>
                  Add Domain
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {domains.map((domain) => (
                  <button
                    key={domain.id}
                    onClick={() => setSelectedDomainId(domain.id)}
                    className={`w-full text-left p-4 border-2 rounded-lg transition-all ${
                      selectedDomainId === domain.id
                        ? 'border-primary bg-primary/5'
                        : 'border-gray-200 hover:border-primary/50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-secondary">{domain.name}</p>
                        <p className="text-sm text-muted">Verified domain</p>
                      </div>
                      {selectedDomainId === domain.id && (
                        <CheckCircleIcon className="w-5 h-5 text-primary" />
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}

            <div className="flex justify-end pt-4 border-t">
              <Button
                onClick={() => setCurrentStep('template')}
                disabled={!selectedDomainId}
              >
                Next: Choose Template
                <ArrowRightIcon className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        )}

        {currentStep === 'template' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-secondary mb-2">Choose Template</h2>
              <p className="text-muted mb-4">Select a template for your site</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={() => setTemplateId('default')}
                className={`p-6 border-2 rounded-lg text-left transition-all ${
                  templateId === 'default'
                    ? 'border-primary bg-primary/5'
                    : 'border-gray-200 hover:border-primary/50'
                }`}
              >
                <h3 className="font-semibold mb-2">Default Template</h3>
                <p className="text-sm text-muted">Clean and modern blog template</p>
              </button>
            </div>

            <div className="flex justify-between pt-4 border-t">
              <Button variant="secondary" onClick={() => setCurrentStep('domain')}>
                <ArrowLeftIcon className="w-4 h-4 mr-2" />
                Back
              </Button>
              <Button onClick={() => setCurrentStep('branding')}>
                Next: Branding
                <ArrowRightIcon className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        )}

        {currentStep === 'branding' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-secondary mb-2">Site Branding</h2>
              <p className="text-muted mb-4">Configure your site's appearance</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Site Name *
              </label>
              <input
                type="text"
                value={siteName}
                onChange={(e) => setSiteName(e.target.value)}
                placeholder="My Awesome Blog"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Primary Color
              </label>
              <div className="flex items-center space-x-3">
                <input
                  type="color"
                  value={primaryColor}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                  className="w-16 h-10 border border-gray-300 rounded"
                />
                <input
                  type="text"
                  value={primaryColor}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg font-mono"
                />
              </div>
            </div>

            <div className="flex justify-between pt-4 border-t">
              <Button variant="secondary" onClick={() => setCurrentStep('template')}>
                <ArrowLeftIcon className="w-4 h-4 mr-2" />
                Back
              </Button>
              <Button onClick={() => setCurrentStep('settings')}>
                Next: Settings
                <ArrowRightIcon className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        )}

        {currentStep === 'settings' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-secondary mb-2">Final Settings</h2>
              <p className="text-muted mb-4">Review and create your site</p>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Domain:</span>
                <span className="font-medium">{domains.find(d => d.id === selectedDomainId)?.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Site Name:</span>
                <span className="font-medium">{siteName || 'Not set'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Template:</span>
                <span className="font-medium">{templateId}</span>
              </div>
            </div>

            <div className="flex justify-between pt-4 border-t">
              <Button variant="secondary" onClick={() => setCurrentStep('branding')}>
                <ArrowLeftIcon className="w-4 h-4 mr-2" />
                Back
              </Button>
              <Button onClick={handleSubmit} disabled={isSubmitting || !siteName.trim()}>
                {isSubmitting ? 'Creating...' : 'Create Site'}
              </Button>
            </div>
          </div>
        )}

        {currentStep === 'complete' && (
          <div className="text-center py-8">
            <CheckCircleIcon className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-secondary mb-2">Site Created!</h2>
            <p className="text-muted">Redirecting to your site dashboard...</p>
          </div>
        )}
      </Card>
    </div>
  )
}

