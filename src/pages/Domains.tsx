import { useState } from 'react'
import { PlusIcon, TrashIcon, CheckCircleIcon, ClipboardIcon, GlobeAltIcon } from '@heroicons/react/24/outline'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import EmptyState from '../components/ui/EmptyState'
import { SkeletonList } from '../components/ui/Skeleton'
import { useDomains } from '../hooks/useDomains'
import { startDomainVerification, checkDomainVerification } from '../api/client'
import type { Domain } from '../api/types'

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

  const handleAddDomain = async () => {
    if (!domainName.trim()) {
      setError('Domain name is required')
      return
    }

    try {
      setIsSubmitting(true)
      setError('')
      await addDomain({
        name: domainName.trim(),
        environment: environment.toLowerCase(),
        status: 'pending',
      })
      setDomainName('')
      setEnvironment('production')
      setIsModalOpen(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add domain')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDeleteDomain = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this domain?')) {
      try {
        await removeDomain(id)
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
    } catch (err) {
      setVerificationError(err instanceof Error ? err.message : 'Failed to start verification')
    }
  }

  const handleCheckVerification = async () => {
    if (!verifyingDomain) return

    try {
      setIsCheckingVerification(true)
      setVerificationError('')
      const updatedDomain = await checkDomainVerification(verifyingDomain.id)
      
      if (updatedDomain.status === 'verified') {
        setSuccessMessage(`Domain ${updatedDomain.name} has been verified successfully!`)
        setIsVerificationModalOpen(false)
        setVerifyingDomain(null)
        setVerificationMethod(null)
        setVerificationData(null)
        await refetch()
        setTimeout(() => setSuccessMessage(''), 5000)
      } else {
        setVerificationError('Verification not yet complete. Please ensure you have completed the steps above and wait 30-60 seconds for DNS propagation if using DNS method.')
      }
    } catch (err) {
      setVerificationError(err instanceof Error ? err.message : 'Failed to check verification')
    } finally {
      setIsCheckingVerification(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setSuccessMessage('Copied to clipboard!')
    setTimeout(() => setSuccessMessage(''), 2000)
  }

  const getStatusBadge = (status: string) => {
    if (status === 'verified') {
      return (
        <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
          <CheckCircleIcon className="w-3 h-3 mr-1" />
          Verified
        </span>
      )
    } else if (status === 'pending' || status === 'active') {
      return (
        <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800 capitalize">
          Pending
        </span>
      )
    } else {
      return (
        <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-600 capitalize">
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
  }

  const getPreviewsCount = (domainName: string) => {
    return Math.floor(Math.random() * 50)
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-secondary mb-2">Your Connected Domains</h1>
        <p className="text-muted">Manage your connected domains and their preview settings.</p>
      </div>
      
      <div className="flex items-center justify-between mb-6">
        <Button onClick={() => setIsModalOpen(true)}>
          <div className="flex items-center space-x-2">
            <PlusIcon className="w-5 h-5" />
            <span>Add Domain</span>
          </div>
        </Button>
      </div>

      {successMessage && (
        <Card className="mb-6 bg-green-50 border-green-200">
          <p className="text-green-800">{successMessage}</p>
        </Card>
      )}

      {/* Embed Script Instructions */}
      <Card className="mb-6">
        <h3 className="text-lg font-semibold text-secondary mb-3">Embed Script</h3>
        <p className="text-gray-600 mb-4">
          Add this script tag to your website's <code className="px-1.5 py-0.5 bg-gray-100 rounded text-sm">&lt;head&gt;</code> to enable automatic URL previews using this platform.
          {domains.filter(d => d.status === 'verified').length > 0 && (
            <span className="block mt-2 text-sm text-gray-500">
              This script will work for your verified domains{domains.filter(d => d.status === 'verified').length === 1 ? '' : 's'}, like {domains.filter(d => d.status === 'verified').slice(0, 2).map(d => d.name).join(', ')}{domains.filter(d => d.status === 'verified').length > 2 ? '...' : ''}.
            </span>
          )}
        </p>
        <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
          <code className="text-sm text-gray-100 font-mono">
            {`<script src="http://localhost:8000/static/snippet.js"></script>`}
          </code>
        </div>
        <p className="text-xs text-gray-500 mt-3">
          Note: Replace <code className="px-1 py-0.5 bg-gray-100 rounded">localhost:8000</code> with your production API URL when deploying.
        </p>
      </Card>

      {apiError && (
        <Card className="mb-6 bg-red-50 border-red-200">
          <p className="text-red-800">Error: {apiError}</p>
        </Card>
      )}

      {loading ? (
        <Card>
          <SkeletonList count={3} />
        </Card>
      ) : domains.length === 0 ? (
        <Card>
          <EmptyState
            icon={<GlobeAltIcon className="w-8 h-8" />}
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
                        <div className="text-sm font-medium text-gray-900">{domain.name}</div>
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
                            <button
                              onClick={() => handleOpenVerificationModal(domain)}
                              className="text-primary hover:text-primary/80 transition-colors text-xs"
                            >
                              Verify
                            </button>
                          )}
                          <button
                            onClick={() => handleDeleteDomain(domain.id)}
                            className="text-red-600 hover:text-red-800 transition-colors inline-flex items-center space-x-1"
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

      {/* Add Domain Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title="Add New Domain"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Domain Name
            </label>
            <input
              type="text"
              placeholder="example.com"
              value={domainName}
              onChange={(e) => {
                setDomainName(e.target.value)
                setError('')
              }}
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all ${
                error ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {error && <p className="text-sm text-red-600 mt-1">{error}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Environment
            </label>
            <select
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
            >
              <option value="production">Production</option>
              <option value="staging">Staging</option>
            </select>
          </div>
          <div className="flex items-center justify-end space-x-3 pt-4">
            <Button variant="secondary" onClick={handleCloseModal} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button onClick={handleAddDomain} disabled={isSubmitting}>
              {isSubmitting ? 'Adding...' : 'Add Domain'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Verification Modal */}
      <Modal
        isOpen={isVerificationModalOpen}
        onClose={handleCloseVerificationModal}
        title={`Verify Domain: ${verifyingDomain?.name || ''}`}
      >
        <div className="space-y-4">
          {!verificationData ? (
            <div className="space-y-3">
              <p className="text-sm text-gray-600 mb-4">Choose a verification method:</p>
              <button
                onClick={() => handleStartVerification('dns')}
                className="w-full text-left p-4 border border-gray-200 rounded-lg hover:border-primary hover:bg-primary/5 transition-all"
              >
                <div className="font-medium text-gray-900 mb-1">DNS TXT Record</div>
                <div className="text-sm text-gray-600">Add a TXT record to your domain's DNS settings</div>
              </button>
              <button
                onClick={() => handleStartVerification('html')}
                className="w-full text-left p-4 border border-gray-200 rounded-lg hover:border-primary hover:bg-primary/5 transition-all"
              >
                <div className="font-medium text-gray-900 mb-1">HTML File Upload</div>
                <div className="text-sm text-gray-600">Upload a verification file to your website's root directory</div>
              </button>
              <button
                onClick={() => handleStartVerification('meta')}
                className="w-full text-left p-4 border border-gray-200 rounded-lg hover:border-primary hover:bg-primary/5 transition-all"
              >
                <div className="font-medium text-gray-900 mb-1">Meta Tag</div>
                <div className="text-sm text-gray-600">Add a meta tag to your homepage HTML</div>
              </button>
            </div>
          ) : (
            <>
              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Verification Token</label>
                  <div className="flex items-center space-x-2">
                    <code className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded text-sm font-mono">
                      {verificationData.token}
                    </code>
                    <button
                      onClick={() => copyToClipboard(verificationData.token)}
                      className="p-2 text-gray-600 hover:text-primary transition-colors"
                      title="Copy token"
                    >
                      <ClipboardIcon className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                {verificationMethod === 'dns' && (
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">TXT Record Value</label>
                    <div className="flex items-center space-x-2">
                      <code className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded text-sm font-mono">
                        {verificationData.instructions.txt_record}
                      </code>
                      <button
                        onClick={() => copyToClipboard(verificationData.instructions.txt_record)}
                        className="p-2 text-gray-600 hover:text-primary transition-colors"
                        title="Copy TXT record"
                      >
                        <ClipboardIcon className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                )}

                {verificationMethod === 'html' && (
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">File Content</label>
                    <div className="flex items-center space-x-2">
                      <code className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded text-sm font-mono">
                        {verificationData.instructions.file_content}
                      </code>
                      <button
                        onClick={() => copyToClipboard(verificationData.instructions.file_content)}
                        className="p-2 text-gray-600 hover:text-primary transition-colors"
                        title="Copy file content"
                      >
                        <ClipboardIcon className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                )}

                {verificationMethod === 'meta' && (
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Meta Tag</label>
                    <div className="flex items-center space-x-2">
                      <code className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded text-sm font-mono">
                        {verificationData.instructions.meta_tag}
                      </code>
                      <button
                        onClick={() => copyToClipboard(verificationData.instructions.meta_tag)}
                        className="p-2 text-gray-600 hover:text-primary transition-colors"
                        title="Copy meta tag"
                      >
                        <ClipboardIcon className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                )}
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800 whitespace-pre-line">
                  {verificationData.instructions.instructions}
                </p>
              </div>

              {verificationError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-sm text-red-800">{verificationError}</p>
                </div>
              )}

              <div className="flex items-center justify-end space-x-3 pt-4">
                <Button variant="secondary" onClick={handleCloseVerificationModal}>
                  Close
                </Button>
                <Button onClick={handleCheckVerification} disabled={isCheckingVerification}>
                  {isCheckingVerification ? 'Checking...' : 'Check Verification'}
                </Button>
              </div>
            </>
          )}
        </div>
      </Modal>
    </div>
  )
}
