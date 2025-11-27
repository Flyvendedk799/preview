import { useState, useEffect } from 'react'
import { 
  PlusIcon, 
  TrashIcon, 
  CheckCircleIcon, 
  ClipboardIcon, 
  GlobeAltIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
  ArrowRightIcon,
  CheckIcon,
  XMarkIcon,
  SparklesIcon
} from '@heroicons/react/24/outline'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import EmptyState from '../components/ui/EmptyState'
import { SkeletonList } from '../components/ui/Skeleton'
import { useDomains } from '../hooks/useDomains'
import { startDomainVerification, checkDomainVerification, debugDomainVerification } from '../api/client'
import type { Domain } from '../api/types'

type VerificationStep = 'method' | 'instructions' | 'verifying' | 'success'

interface DebugInfo {
  domain: string
  expected_value: string
  found_records: string[]
  is_verified: boolean
  error: string | null
}

export default function Domains() {
  const { domains, loading, error: apiError, addDomain, removeDomain, refetch } = useDomains()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isVerificationModalOpen, setIsVerificationModalOpen] = useState(false)
  const [verifyingDomain, setVerifyingDomain] = useState<Domain | null>(null)
  const [verificationMethod, setVerificationMethod] = useState<'dns' | 'html' | 'meta' | null>(null)
  const [verificationData, setVerificationData] = useState<{
    token: string
    instructions: Record<string, string>
  } | null>(null)
  const [isCheckingVerification, setIsCheckingVerification] = useState(false)
  const [verificationError, setVerificationError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [domainName, setDomainName] = useState('')
  const [environment, setEnvironment] = useState('production')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [verificationStep, setVerificationStep] = useState<VerificationStep>('method')
  const [copiedField, setCopiedField] = useState<string | null>(null)
  const [autoCheckEnabled, setAutoCheckEnabled] = useState(true)
  const [checkAttempts, setCheckAttempts] = useState(0)
  const [debugInfo, setDebugInfo] = useState<DebugInfo | null>(null)
  const [isDebugging, setIsDebugging] = useState(false)
  const [autoCheckStatus, setAutoCheckStatus] = useState<'checking' | 'found' | 'not_found' | null>(null)
  const [lastAutoCheckTime, setLastAutoCheckTime] = useState<Date | null>(null)

  // Auto-check verification every 15 seconds on the instructions step
  useEffect(() => {
    if (autoCheckEnabled && verificationStep === 'instructions' && verifyingDomain && verificationData) {
      const runAutoCheck = async () => {
        if (checkAttempts >= 24) { // Max 24 attempts (6 minutes)
          setAutoCheckEnabled(false)
          return
        }
        
        setAutoCheckStatus('checking')
        try {
          const updatedDomain = await checkDomainVerification(verifyingDomain.id)
          setLastAutoCheckTime(new Date())
          
          if (updatedDomain.status === 'verified') {
            setAutoCheckStatus('found')
            setVerificationStep('success')
            setSuccessMessage(`Domain ${updatedDomain.name} has been verified successfully!`)
            setAutoCheckEnabled(false)
            setTimeout(async () => {
              setIsVerificationModalOpen(false)
              setVerifyingDomain(null)
              setVerificationMethod(null)
              setVerificationData(null)
              setVerificationStep('method')
              await refetch()
            }, 2000)
            setTimeout(() => setSuccessMessage(''), 5000)
          } else {
            setAutoCheckStatus('not_found')
            setCheckAttempts(prev => prev + 1)
          }
        } catch {
          setAutoCheckStatus('not_found')
          setCheckAttempts(prev => prev + 1)
        }
      }
      
      // Run immediately on mount, then every 15 seconds
      const timeoutId = setTimeout(runAutoCheck, 1000) // Initial check after 1 second
      const interval = setInterval(runAutoCheck, 15000)
      
      return () => {
        clearTimeout(timeoutId)
        clearInterval(interval)
      }
    }
  }, [autoCheckEnabled, verificationStep, verifyingDomain?.id, verificationData, checkAttempts])

  const validateDomain = (domain: string): { valid: boolean; error?: string } => {
    const trimmed = domain.trim().toLowerCase()
    
    if (!trimmed) {
      return { valid: false, error: 'Domain name is required' }
    }

    // Remove protocol if present
    const cleaned = trimmed.replace(/^https?:\/\//, '').replace(/\/$/, '')
    
    // Basic domain validation
    const domainRegex = /^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$/i
    if (!domainRegex.test(cleaned)) {
      return { valid: false, error: 'Please enter a valid domain name (e.g., example.com)' }
    }

    // Check for common mistakes
    if (cleaned.includes('www.')) {
      return { valid: false, error: 'Please enter the domain without "www." (e.g., example.com instead of www.example.com)' }
    }

    return { valid: true }
  }

  const handleAddDomain = async () => {
    const validation = validateDomain(domainName)
    if (!validation.valid) {
      setError(validation.error || 'Invalid domain')
      return
    }

    try {
      setIsSubmitting(true)
      setError('')
      const cleanedDomain = domainName.trim().toLowerCase().replace(/^https?:\/\//, '').replace(/\/$/, '')
      await addDomain({
        name: cleanedDomain,
        environment: environment.toLowerCase(),
        status: 'pending',
      })
      setDomainName('')
      setEnvironment('production')
      setIsModalOpen(false)
      setSuccessMessage(`Domain ${cleanedDomain} added successfully! Click "Verify" to complete setup.`)
      setTimeout(() => setSuccessMessage(''), 5000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add domain')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDeleteDomain = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this domain? This action cannot be undone.')) {
      try {
        await removeDomain(id)
        setSuccessMessage('Domain deleted successfully')
        setTimeout(() => setSuccessMessage(''), 3000)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete domain')
      }
    }
  }

  const handleOpenVerificationModal = (domain: Domain) => {
    setVerifyingDomain(domain)
    setVerificationMethod(null)
    setVerificationData(null)
    setVerificationError('')
    setVerificationStep('method')
    setCopiedField(null)
    setAutoCheckEnabled(true)
    setCheckAttempts(0)
    setAutoCheckStatus(null)
    setLastAutoCheckTime(null)
    setDebugInfo(null)
    setIsVerificationModalOpen(true)
  }

  const handleStartVerification = async (method: 'dns' | 'html' | 'meta') => {
    if (!verifyingDomain) return
    
    try {
      setVerificationError('')
      setVerificationData(null)
      const result = await startDomainVerification(verifyingDomain.id, method)
      setVerificationMethod(method)
      setVerificationData({
        token: result.token,
        instructions: result.instructions,
      })
      setVerificationStep('instructions')
    } catch (err) {
      setVerificationError(err instanceof Error ? err.message : 'Failed to start verification')
    }
  }

  const handleCheckVerification = async () => {
    if (!verifyingDomain) return

    try {
      setIsCheckingVerification(true)
      setVerificationStep('verifying')
      setVerificationError('')
      const updatedDomain = await checkDomainVerification(verifyingDomain.id)
      setLastAutoCheckTime(new Date())
      
      if (updatedDomain.status === 'verified') {
        setAutoCheckStatus('found')
        setVerificationStep('success')
        setSuccessMessage(`Domain ${updatedDomain.name} has been verified successfully!`)
        setAutoCheckEnabled(false)
        setTimeout(async () => {
          setIsVerificationModalOpen(false)
          setVerifyingDomain(null)
          setVerificationMethod(null)
          setVerificationData(null)
          setVerificationStep('method')
          await refetch()
        }, 2000)
        setTimeout(() => setSuccessMessage(''), 5000)
      } else {
        setAutoCheckStatus('not_found')
        setVerificationError('Record not found yet. DNS changes can take a few minutes to propagate. Auto-check will keep trying.')
        // Go back to instructions so auto-check can continue
        setTimeout(() => setVerificationStep('instructions'), 1500)
      }
    } catch (err) {
      setAutoCheckStatus('not_found')
      setVerificationError(err instanceof Error ? err.message : 'Failed to check verification')
      setTimeout(() => setVerificationStep('instructions'), 1500)
    } finally {
      setIsCheckingVerification(false)
    }
  }

  const handleDebugVerification = async () => {
    if (!verifyingDomain) return
    
    try {
      setIsDebugging(true)
      setDebugInfo(null)
      const result = await debugDomainVerification(verifyingDomain.id)
      setDebugInfo(result)
    } catch (err) {
      setVerificationError(err instanceof Error ? err.message : 'Failed to debug verification')
    } finally {
      setIsDebugging(false)
    }
  }

  const copyToClipboard = async (text: string, fieldName: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedField(fieldName)
      setTimeout(() => setCopiedField(null), 2000)
    } catch (err) {
      setVerificationError('Failed to copy to clipboard')
    }
  }

  const getStatusBadge = (status: string) => {
    if (status === 'verified') {
      return (
        <span className="inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
          <CheckCircleIcon className="w-3 h-3 mr-1.5" />
          Verified
        </span>
      )
    } else if (status === 'pending' || status === 'active') {
      return (
        <span className="inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">
          <ExclamationTriangleIcon className="w-3 h-3 mr-1.5" />
          Pending Verification
        </span>
      )
    } else {
      return (
        <span className="inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-600">
          Not Verified
        </span>
      )
    }
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setDomainName('')
    setEnvironment('production')
    setError('')
  }

  const handleCloseVerificationModal = () => {
    setIsVerificationModalOpen(false)
    setVerifyingDomain(null)
    setVerificationMethod(null)
    setVerificationData(null)
    setVerificationError('')
    setVerificationStep('method')
    setCopiedField(null)
    setAutoCheckEnabled(false)
    setCheckAttempts(0)
  }

  const getPreviewsCount = (domainName: string) => {
    return Math.floor(Math.random() * 50)
  }

  const verificationMethods = [
    {
      id: 'dns' as const,
      name: 'DNS TXT Record',
      description: 'Recommended for most users',
      icon: '🌐',
      details: 'Add a TXT record to your domain\'s DNS settings. Works for all domain types.',
      pros: ['Most reliable', 'Works for all domains', 'No file uploads needed']
    },
    {
      id: 'html' as const,
      name: 'HTML File Upload',
      description: 'Quick and easy',
      icon: '📄',
      details: 'Upload a verification file to your website\'s root directory.',
      pros: ['Fast verification', 'No DNS access needed', 'Easy to implement']
    },
    {
      id: 'meta' as const,
      name: 'Meta Tag',
      description: 'For static sites',
      icon: '🏷️',
      details: 'Add a meta tag to your homepage HTML <head> section.',
      pros: ['Simple to add', 'No DNS changes', 'Perfect for static sites']
    }
  ]

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-secondary mb-2">Your Connected Domains</h1>
        <p className="text-muted">Manage your connected domains and their preview settings.</p>
      </div>
      
      <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
        <Button onClick={() => setIsModalOpen(true)} className="w-full sm:w-auto">
          <div className="flex items-center justify-center sm:justify-start space-x-2">
            <PlusIcon className="w-5 h-5" />
            <span>Add Domain</span>
          </div>
        </Button>
      </div>

      {successMessage && (
        <Card className="mb-6 bg-green-50 border-green-200">
          <div className="flex items-start space-x-3">
            <CheckCircleIcon className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
            <p className="text-green-800">{successMessage}</p>
          </div>
        </Card>
      )}

      {/* Embed Script Instructions */}
      {domains.filter(d => d.status === 'verified').length > 0 && (
        <Card className="mb-6">
          <div className="flex items-start space-x-3 mb-4">
            <SparklesIcon className="w-6 h-6 text-primary mt-0.5" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-secondary mb-2">Embed Script</h3>
              <p className="text-gray-600 mb-4">
                Add this script tag to your website's <code className="px-1.5 py-0.5 bg-gray-100 rounded text-sm font-mono">&lt;head&gt;</code> to enable automatic URL previews.
              </p>
            </div>
          </div>
          <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
            <code className="text-sm text-gray-100 font-mono">
              {`<script src="http://localhost:8000/static/snippet.js"></script>`}
            </code>
          </div>
          <p className="text-xs text-gray-500 mt-3 flex items-start space-x-1">
            <InformationCircleIcon className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <span>Note: Replace <code className="px-1 py-0.5 bg-gray-100 rounded">localhost:8000</code> with your production API URL when deploying.</span>
          </p>
        </Card>
      )}

      {apiError && (
        <Card className="mb-6 bg-red-50 border-red-200">
          <div className="flex items-start space-x-3">
            <ExclamationTriangleIcon className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
            <p className="text-red-800">Error: {apiError}</p>
          </div>
        </Card>
      )}

      {loading ? (
        <Card>
          <SkeletonList count={3} />
        </Card>
      ) : domains.length === 0 ? (
        <Card>
          <EmptyState
            icon={<GlobeAltIcon className="w-12 h-12" />}
            title="No domains connected yet"
            description="Connect your first domain to start generating beautiful URL previews. Domain verification takes just a few minutes."
            action={{
              label: 'Add Your First Domain',
              onClick: () => setIsModalOpen(true),
            }}
          />
        </Card>
      ) : (
        <Card className="overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Domain
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Previews
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Clicks
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {domains.map((domain) => (
                  <tr key={domain.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <GlobeAltIcon className="w-5 h-5 text-gray-400" />
                        <div className="text-sm font-medium text-gray-900">{domain.name}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(domain.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {getPreviewsCount(domain.name)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {domain.monthly_clicks.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end space-x-2">
                        {domain.status !== 'verified' && (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleOpenVerificationModal(domain)}
                          >
                            <div className="flex items-center space-x-1.5">
                              <CheckCircleIcon className="w-4 h-4" />
                              <span>Verify</span>
                            </div>
                          </Button>
                        )}
                        <button
                          onClick={() => handleDeleteDomain(domain.id)}
                          className="text-red-600 hover:text-red-800 transition-colors inline-flex items-center space-x-1.5 px-2 py-1 rounded hover:bg-red-50"
                          title="Delete domain"
                        >
                          <TrashIcon className="w-4 h-4" />
                          <span>Delete</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Add Domain Modal - Improved */}
      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title="Add New Domain"
      >
        <div className="space-y-5">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start space-x-2">
              <InformationCircleIcon className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-blue-800">
                <p className="font-medium mb-1">Before you start:</p>
                <ul className="list-disc list-inside space-y-1 text-blue-700">
                  <li>Enter your domain without "www" (e.g., example.com)</li>
                  <li>You'll need to verify ownership after adding</li>
                  <li>Verification takes 2-5 minutes</li>
                </ul>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Domain Name <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <input
                type="text"
                placeholder="example.com"
                value={domainName}
                onChange={(e) => {
                  setDomainName(e.target.value)
                  setError('')
                }}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !isSubmitting) {
                    handleAddDomain()
                  }
                }}
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all font-mono ${
                  error ? 'border-red-300 bg-red-50' : 'border-gray-300'
                }`}
                autoFocus
              />
              {domainName && !error && validateDomain(domainName).valid && (
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <CheckCircleIcon className="w-5 h-5 text-green-500" />
                </div>
              )}
            </div>
            {error && (
              <div className="mt-2 flex items-start space-x-2">
                <ExclamationTriangleIcon className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}
            {!error && domainName && (
              <p className="mt-2 text-xs text-gray-500">
                ✓ Valid domain format
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Environment
            </label>
            <select
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
            >
              <option value="production">Production</option>
              <option value="staging">Staging</option>
            </select>
            <p className="mt-1 text-xs text-gray-500">
              Choose the environment where this domain will be used
            </p>
          </div>

          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button variant="secondary" onClick={handleCloseModal} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button 
              onClick={handleAddDomain} 
              disabled={isSubmitting || !domainName.trim() || !validateDomain(domainName).valid}
            >
              {isSubmitting ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Adding...</span>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <span>Add Domain</span>
                  <ArrowRightIcon className="w-4 h-4" />
                </div>
              )}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Verification Modal - Improved */}
      <Modal
        isOpen={isVerificationModalOpen}
        onClose={handleCloseVerificationModal}
        title={`Verify Domain: ${verifyingDomain?.name || ''}`}
      >
        <div className="space-y-6">
          {/* Step Indicator */}
          <div className="flex items-center justify-between mb-6">
            {['method', 'instructions', 'verifying', 'success'].map((step, index) => {
              const stepNames = ['Choose Method', 'Add Record', 'Verifying', 'Complete']
              const currentStepIndex = ['method', 'instructions', 'verifying', 'success'].indexOf(verificationStep)
              const isActive = index === currentStepIndex
              const isCompleted = index < currentStepIndex
              
              return (
                <div key={step} className="flex items-center flex-1">
                  <div className="flex flex-col items-center flex-1">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all ${
                      isCompleted ? 'bg-green-500 text-white' :
                      isActive ? 'bg-primary text-white' :
                      'bg-gray-200 text-gray-600'
                    }`}>
                      {isCompleted ? <CheckIcon className="w-5 h-5" /> : index + 1}
                    </div>
                    <span className={`text-xs mt-2 text-center ${isActive ? 'font-medium text-primary' : 'text-gray-500'}`}>
                      {stepNames[index]}
                    </span>
                  </div>
                  {index < 3 && (
                    <div className={`h-0.5 flex-1 mx-2 ${isCompleted ? 'bg-green-500' : 'bg-gray-200'}`} />
                  )}
                </div>
              )
            })}
          </div>

          {/* Method Selection */}
          {verificationStep === 'method' && (
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start space-x-2">
                  <InformationCircleIcon className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                  <div className="text-sm text-blue-800">
                    <p className="font-medium mb-1">Choose a verification method</p>
                    <p className="text-blue-700">Select the method that works best for your setup. You can change this later if needed.</p>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                {verificationMethods.map((method) => (
                  <button
                    key={method.id}
                    onClick={() => handleStartVerification(method.id)}
                    className="w-full text-left p-4 border-2 border-gray-200 rounded-lg hover:border-primary hover:bg-primary/5 transition-all group"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <span className="text-2xl">{method.icon}</span>
                          <div>
                            <div className="font-semibold text-gray-900 group-hover:text-primary transition-colors">
                              {method.name}
                            </div>
                            <div className="text-xs text-gray-500">{method.description}</div>
                          </div>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{method.details}</p>
                        <ul className="flex flex-wrap gap-2">
                          {method.pros.map((pro, idx) => (
                            <li key={idx} className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                              {pro}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <ArrowRightIcon className="w-5 h-5 text-gray-400 group-hover:text-primary transition-colors ml-4" />
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Instructions */}
          {verificationStep === 'instructions' && verificationData && (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-start space-x-2">
                  <CheckCircleIcon className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <div className="text-sm text-green-800">
                    <p className="font-medium mb-1">Follow these steps to verify your domain</p>
                    <p className="text-green-700">Copy the information below and add it to your domain settings.</p>
                  </div>
                </div>
              </div>

              {verificationMethod === 'dns' && (
                <div className="space-y-4">
                  <div className="bg-gray-50 rounded-lg p-4 space-y-4">
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">
                        Step 1: Add DNS TXT Record
                      </label>
                      <div className="space-y-2">
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Record Type</label>
                          <div className="bg-white border border-gray-300 rounded px-3 py-2 font-mono text-sm">
                            TXT
                          </div>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Name / Host</label>
                          <div className="bg-white border border-gray-300 rounded px-3 py-2 font-mono text-sm">
                            @ or {verifyingDomain?.name}
                          </div>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Value / Content</label>
                          <div className="flex items-center space-x-2">
                            <code className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded text-sm font-mono break-all">
                              {verificationData.instructions.txt_record}
                            </code>
                            <button
                              onClick={() => copyToClipboard(verificationData.instructions.txt_record, 'txt')}
                              className={`p-2 rounded transition-colors ${
                                copiedField === 'txt' 
                                  ? 'bg-green-100 text-green-600' 
                                  : 'text-gray-600 hover:bg-gray-100'
                              }`}
                              title="Copy TXT record"
                            >
                              {copiedField === 'txt' ? (
                                <CheckIcon className="w-5 h-5" />
                              ) : (
                                <ClipboardIcon className="w-5 h-5" />
                              )}
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-start space-x-2">
                      <InformationCircleIcon className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                      <div className="text-sm text-blue-800 space-y-2">
                        <p className="font-medium">How to add a DNS TXT record:</p>
                        <ol className="list-decimal list-inside space-y-1 text-blue-700">
                          <li>Log in to your domain registrar or DNS provider</li>
                          <li>Navigate to DNS management / DNS settings</li>
                          <li>Add a new TXT record with the values above</li>
                          <li>Save the changes (may take 30-60 seconds to propagate)</li>
                          <li>Click "Verify Domain" below</li>
                        </ol>
                        <p className="text-xs text-blue-600 mt-2">
                          💡 Common providers: Cloudflare, GoDaddy, Namecheap, Google Domains
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {verificationMethod === 'html' && (
                <div className="space-y-4">
                  <div className="bg-gray-50 rounded-lg p-4 space-y-4">
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">
                        Step 1: Create Verification File
                      </label>
                      <div className="space-y-2">
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">File Name</label>
                          <div className="bg-white border border-gray-300 rounded px-3 py-2 font-mono text-sm">
                            {verificationData.instructions.file_name || 'verify.html'}
                          </div>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">File Content</label>
                          <div className="flex items-start space-x-2">
                            <code className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded text-sm font-mono whitespace-pre-wrap break-all">
                              {verificationData.instructions.file_content}
                            </code>
                            <button
                              onClick={() => copyToClipboard(verificationData.instructions.file_content, 'html')}
                              className={`p-2 rounded transition-colors ${
                                copiedField === 'html' 
                                  ? 'bg-green-100 text-green-600' 
                                  : 'text-gray-600 hover:bg-gray-100'
                              }`}
                              title="Copy file content"
                            >
                              {copiedField === 'html' ? (
                                <CheckIcon className="w-5 h-5" />
                              ) : (
                                <ClipboardIcon className="w-5 h-5" />
                              )}
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-start space-x-2">
                      <InformationCircleIcon className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                      <div className="text-sm text-blue-800 space-y-2">
                        <p className="font-medium">How to upload the verification file:</p>
                        <ol className="list-decimal list-inside space-y-1 text-blue-700">
                          <li>Create a new file with the name shown above</li>
                          <li>Paste the content into the file</li>
                          <li>Upload it to your website's root directory (where index.html is located)</li>
                          <li>Ensure it's accessible at: <code className="bg-blue-100 px-1 rounded">https://{verifyingDomain?.name}/verify.html</code></li>
                          <li>Click "Verify Domain" below</li>
                        </ol>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {verificationMethod === 'meta' && (
                <div className="space-y-4">
                  <div className="bg-gray-50 rounded-lg p-4 space-y-4">
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">
                        Step 1: Add Meta Tag to Homepage
                      </label>
                      <div className="space-y-2">
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Meta Tag</label>
                          <div className="flex items-start space-x-2">
                            <code className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded text-sm font-mono whitespace-pre-wrap break-all">
                              {verificationData.instructions.meta_tag}
                            </code>
                            <button
                              onClick={() => copyToClipboard(verificationData.instructions.meta_tag, 'meta')}
                              className={`p-2 rounded transition-colors ${
                                copiedField === 'meta' 
                                  ? 'bg-green-100 text-green-600' 
                                  : 'text-gray-600 hover:bg-gray-100'
                              }`}
                              title="Copy meta tag"
                            >
                              {copiedField === 'meta' ? (
                                <CheckIcon className="w-5 h-5" />
                              ) : (
                                <ClipboardIcon className="w-5 h-5" />
                              )}
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-start space-x-2">
                      <InformationCircleIcon className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                      <div className="text-sm text-blue-800 space-y-2">
                        <p className="font-medium">How to add the meta tag:</p>
                        <ol className="list-decimal list-inside space-y-1 text-blue-700">
                          <li>Open your website's homepage HTML file</li>
                          <li>Find the <code className="bg-blue-100 px-1 rounded">&lt;head&gt;</code> section</li>
                          <li>Paste the meta tag above into the <code className="bg-blue-100 px-1 rounded">&lt;head&gt;</code> section</li>
                          <li>Save and publish your changes</li>
                          <li>Click "Verify Domain" below</li>
                        </ol>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {verificationError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-start space-x-2">
                    <ExclamationTriangleIcon className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-red-800">{verificationError}</p>
                  </div>
                </div>
              )}

              {/* Debug Section for DNS */}
              {verificationMethod === 'dns' && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-medium text-gray-700">DNS Debug Tool</h4>
                    <Button 
                      variant="secondary" 
                      size="sm" 
                      onClick={handleDebugVerification}
                      disabled={isDebugging}
                    >
                      {isDebugging ? 'Checking...' : 'Check DNS Records'}
                    </Button>
                  </div>
                  {debugInfo && (
                    <div className="mt-3 space-y-2 text-xs font-mono bg-white p-3 rounded border">
                      <p><span className="text-gray-500">Domain:</span> {debugInfo.domain}</p>
                      <p><span className="text-gray-500">Expected:</span> <span className="text-green-600">{debugInfo.expected_value}</span></p>
                      <div>
                        <span className="text-gray-500">Found TXT Records:</span>
                        {debugInfo.found_records.length > 0 ? (
                          <ul className="mt-1 pl-4">
                            {debugInfo.found_records.map((record, i) => (
                              <li key={i} className={record.includes('preview-verification') ? 'text-green-600' : 'text-gray-700'}>
                                {record}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <span className="ml-2 text-orange-600">None found</span>
                        )}
                      </div>
                      {debugInfo.error && (
                        <p className="text-red-600"><span className="text-gray-500">Error:</span> {debugInfo.error}</p>
                      )}
                      <p className="pt-2 border-t">
                        <span className="text-gray-500">Status:</span>{' '}
                        {debugInfo.is_verified ? (
                          <span className="text-green-600 font-semibold">✓ Token found!</span>
                        ) : (
                          <span className="text-orange-600">Token not found yet</span>
                        )}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Auto-check Status Indicator */}
              {autoCheckEnabled && (
                <div className={`flex items-center justify-between p-3 rounded-lg border ${
                  autoCheckStatus === 'found' 
                    ? 'bg-green-50 border-green-200' 
                    : autoCheckStatus === 'not_found'
                    ? 'bg-orange-50 border-orange-200'
                    : 'bg-blue-50 border-blue-200'
                }`}>
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${
                      autoCheckStatus === 'found'
                        ? 'bg-green-500'
                        : autoCheckStatus === 'not_found'
                        ? 'bg-orange-500'
                        : 'bg-blue-500 animate-pulse'
                    }`} />
                    <div>
                      <p className={`text-sm font-medium ${
                        autoCheckStatus === 'found'
                          ? 'text-green-800'
                          : autoCheckStatus === 'not_found'
                          ? 'text-orange-800'
                          : 'text-blue-800'
                      }`}>
                        {autoCheckStatus === 'checking' && 'Checking DNS records...'}
                        {autoCheckStatus === 'found' && '✓ Verification record found!'}
                        {autoCheckStatus === 'not_found' && 'Record not found yet'}
                        {!autoCheckStatus && 'Auto-check starting...'}
                      </p>
                      <p className="text-xs text-gray-500">
                        {lastAutoCheckTime && `Last checked: ${lastAutoCheckTime.toLocaleTimeString()}`}
                        {!lastAutoCheckTime && 'Checking every 15 seconds'}
                        {autoCheckStatus === 'not_found' && ` • Attempt ${checkAttempts}/24`}
                      </p>
                    </div>
                  </div>
                  {autoCheckStatus === 'not_found' && (
                    <button
                      onClick={() => setAutoCheckEnabled(false)}
                      className="text-xs text-gray-500 hover:text-gray-700"
                    >
                      Stop
                    </button>
                  )}
                </div>
              )}

              <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                <Button variant="secondary" onClick={() => setVerificationStep('method')}>
                  Back
                </Button>
                <div className="flex items-center space-x-3">
                  <Button 
                    onClick={() => {
                      handleCheckVerification()
                    }} 
                    disabled={isCheckingVerification}
                  >
                    {isCheckingVerification ? (
                      <div className="flex items-center space-x-2">
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Verifying...</span>
                      </div>
                    ) : (
                      <div className="flex items-center space-x-2">
                        <span>Verify Domain</span>
                        <ArrowRightIcon className="w-4 h-4" />
                      </div>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Verifying State (manual check in progress) */}
          {verificationStep === 'verifying' && (
            <div className="text-center py-8">
              <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Verifying your domain...</h3>
              <p className="text-sm text-gray-600 mb-4">
                Checking your DNS records now...
              </p>
              {verificationError && (
                <div className="mt-4 bg-orange-50 border border-orange-200 rounded-lg p-4">
                  <p className="text-sm text-orange-800">{verificationError}</p>
                  <p className="text-xs text-gray-500 mt-2">DNS propagation can take a few minutes. The auto-check will keep trying.</p>
                </div>
              )}
              <Button 
                variant="secondary" 
                onClick={() => setVerificationStep('instructions')}
                className="mt-4"
              >
                Back to Instructions
              </Button>
            </div>
          )}

          {/* Success State */}
          {verificationStep === 'success' && (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircleIcon className="w-10 h-10 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Domain Verified Successfully!</h3>
              <p className="text-sm text-gray-600">
                Your domain <span className="font-medium">{verifyingDomain?.name}</span> has been verified and is ready to use.
              </p>
            </div>
          )}
        </div>
      </Modal>
    </div>
  )
}
