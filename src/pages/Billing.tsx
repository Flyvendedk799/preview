import { useState, useEffect } from 'react'
import { CheckCircleIcon, XCircleIcon, ClockIcon, CreditCardIcon } from '@heroicons/react/24/outline'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import EmptyState from '../components/ui/EmptyState'
import { createCheckoutSession, createBillingPortal, getBillingStatus, syncSubscriptionStatus } from '../api/client'
import { useAuth } from '../hooks/useAuth'
import { useOrganization } from '../hooks/useOrganization'

interface BillingStatus {
  subscription_status: string
  subscription_plan?: string | null
  trial_ends_at?: string | null
}

export default function Billing() {
  const { user } = useAuth()
  const { currentOrg } = useOrganization()
  const [billingStatus, setBillingStatus] = useState<BillingStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  useEffect(() => {
    loadBillingStatus()
    
    // Auto-sync subscription status if returning from Stripe checkout
    const urlParams = new URLSearchParams(window.location.search)
    if (urlParams.get('success') === 'true') {
      // Wait a moment for Stripe webhook to process, then sync
      setTimeout(() => {
        handleSyncSubscription()
      }, 2000)
    }
  }, [])

  const loadBillingStatus = async () => {
    try {
      setLoading(true)
      setError(null)
      const status = await getBillingStatus()
      setBillingStatus(status)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load billing status')
    } finally {
      setLoading(false)
    }
  }

  const handleUpgrade = async (priceId: string) => {
    if (!priceId || priceId.trim() === '') {
      setError('Price ID is missing. Please contact support.')
      return
    }
    try {
      setIsProcessing(true)
      setError(null)
      const result = await createCheckoutSession(priceId)
      // Redirect to Stripe Checkout
      window.location.href = result.checkout_url
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create checkout session')
      setIsProcessing(false)
    }
  }

  const handleManageBilling = async () => {
    try {
      setIsProcessing(true)
      setError(null)
      const result = await createBillingPortal()
      // Redirect to Stripe Billing Portal
      window.location.href = result.portal_url
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create billing portal session')
      setIsProcessing(false)
    }
  }

  const handleSyncSubscription = async () => {
    try {
      setIsProcessing(true)
      setError(null)
      const status = await syncSubscriptionStatus()
      setBillingStatus(status)
      // Remove success parameter from URL
      window.history.replaceState({}, '', window.location.pathname)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to sync subscription status')
    } finally {
      setIsProcessing(false)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return (
          <span className="inline-flex items-center px-3 py-1 text-sm font-medium rounded-full bg-green-100 text-green-800">
            <CheckCircleIcon className="w-4 h-4 mr-1" />
            Active
          </span>
        )
      case 'trialing':
        return (
          <span className="inline-flex items-center px-3 py-1 text-sm font-medium rounded-full bg-blue-100 text-blue-800">
            <ClockIcon className="w-4 h-4 mr-1" />
            Trial
          </span>
        )
      case 'past_due':
        return (
          <span className="inline-flex items-center px-3 py-1 text-sm font-medium rounded-full bg-yellow-100 text-yellow-800">
            <ClockIcon className="w-4 h-4 mr-1" />
            Past Due
          </span>
        )
      case 'canceled':
        return (
          <span className="inline-flex items-center px-3 py-1 text-sm font-medium rounded-full bg-gray-100 text-gray-800">
            <XCircleIcon className="w-4 h-4 mr-1" />
            Canceled
          </span>
        )
      default:
        return (
          <span className="inline-flex items-center px-3 py-1 text-sm font-medium rounded-full bg-gray-100 text-gray-800">
            Inactive
          </span>
        )
    }
  }

  const formatTrialEnd = (trialEndsAt: string | null | undefined) => {
    if (!trialEndsAt) return null
    const date = new Date(trialEndsAt)
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
  }

  const getDaysUntilTrialEnd = (trialEndsAt: string | null | undefined) => {
    if (!trialEndsAt) return null
    const endDate = new Date(trialEndsAt)
    const now = new Date()
    const diffTime = endDate.getTime() - now.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays > 0 ? diffDays : 0
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-secondary mb-2">Billing & Subscription</h1>
        <p className="text-muted">
          Manage subscription and billing preferences for {currentOrg?.name || 'your organization'}.
        </p>
      </div>

      {error && (
        <Card className="mb-6 bg-red-50 border-red-200">
          <p className="text-red-800">Error: {error}</p>
        </Card>
      )}

      {loading ? (
        <Card>
          <div className="text-center py-12">
            <p className="text-gray-500">Loading billing information...</p>
          </div>
        </Card>
      ) : (
        <>
          {/* Current Subscription Status */}
          <Card className="mb-6">
            <h2 className="text-xl font-semibold text-secondary mb-4">Current Plan</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Subscription Status</p>
                  <div className="mt-1">
                    {getStatusBadge(billingStatus?.subscription_status || 'inactive')}
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-600">Plan</p>
                  <p className="mt-1 text-lg font-semibold text-gray-900 capitalize">
                    {billingStatus?.subscription_plan || 'Free'}
                  </p>
                </div>
              </div>

              {billingStatus?.trial_ends_at && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <ClockIcon className="w-5 h-5 text-blue-600" />
                    <div>
                      <p className="text-sm font-medium text-blue-900">Trial Period</p>
                      <p className="text-sm text-blue-700">
                        {billingStatus.trial_ends_at
                          ? (() => {
                              const trialEnd = billingStatus.trial_ends_at
                              const daysLeft = getDaysUntilTrialEnd(trialEnd)
                              if (daysLeft === null) return 'No trial period'
                              return daysLeft > 0
                                ? `${daysLeft} days remaining (ends ${formatTrialEnd(trialEnd)})`
                                : `Trial ended on ${formatTrialEnd(trialEnd)}`
                            })()
                          : 'No trial period'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="pt-4 border-t border-gray-200 flex items-center justify-between">
                {billingStatus?.subscription_status === 'active' && (
                  <Button onClick={handleManageBilling} disabled={isProcessing} variant="secondary">
                    {isProcessing ? 'Loading...' : 'Manage Billing'}
                  </Button>
                )}
                <Button onClick={handleSyncSubscription} disabled={isProcessing} variant="secondary" className="ml-auto">
                  {isProcessing ? 'Syncing...' : 'Sync Status'}
                </Button>
              </div>
            </div>
          </Card>

          {/* Upgrade Options */}
          {billingStatus?.subscription_status !== 'active' && (
            <Card>
              <h2 className="text-xl font-semibold text-secondary mb-4">Upgrade Your Plan</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Basic Plan */}
                <div className="border border-gray-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Basic</h3>
                  <p className="text-3xl font-bold text-secondary mb-4">$9<span className="text-lg text-gray-600">/mo</span></p>
                  <ul className="space-y-2 mb-6 text-sm text-gray-600">
                    <li>✓ 100 previews/month</li>
                    <li>✓ Basic support</li>
                    <li>✓ Standard features</li>
                  </ul>
                  <Button
                    onClick={() => handleUpgrade(import.meta.env.VITE_STRIPE_PRICE_TIER_BASIC || '')}
                    disabled={isProcessing || !import.meta.env.VITE_STRIPE_PRICE_TIER_BASIC}
                    className="w-full"
                    variant="secondary"
                  >
                    {isProcessing ? 'Processing...' : !import.meta.env.VITE_STRIPE_PRICE_TIER_BASIC ? 'Price ID not configured' : 'Upgrade to Basic'}
                  </Button>
                </div>

                {/* Pro Plan */}
                <div className="border-2 border-primary rounded-lg p-6 relative">
                  <span className="absolute top-0 right-0 bg-primary text-white text-xs px-3 py-1 rounded-bl-lg rounded-tr-lg">
                    Popular
                  </span>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Pro</h3>
                  <p className="text-3xl font-bold text-secondary mb-4">$29<span className="text-lg text-gray-600">/mo</span></p>
                  <ul className="space-y-2 mb-6 text-sm text-gray-600">
                    <li>✓ 1,000 previews/month</li>
                    <li>✓ Priority support</li>
                    <li>✓ Advanced features</li>
                    <li>✓ API access</li>
                  </ul>
                  <Button
                    onClick={() => handleUpgrade(import.meta.env.VITE_STRIPE_PRICE_TIER_PRO || '')}
                    disabled={isProcessing || !import.meta.env.VITE_STRIPE_PRICE_TIER_PRO}
                    className="w-full"
                  >
                    {isProcessing ? 'Processing...' : !import.meta.env.VITE_STRIPE_PRICE_TIER_PRO ? 'Price ID not configured' : 'Upgrade to Pro'}
                  </Button>
                </div>

                {/* Agency Plan */}
                <div className="border border-gray-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Agency</h3>
                  <p className="text-3xl font-bold text-secondary mb-4">$99<span className="text-lg text-gray-600">/mo</span></p>
                  <ul className="space-y-2 mb-6 text-sm text-gray-600">
                    <li>✓ Unlimited previews</li>
                    <li>✓ Dedicated support</li>
                    <li>✓ White-label options</li>
                    <li>✓ Custom integrations</li>
                  </ul>
                  <Button
                    onClick={() => handleUpgrade(import.meta.env.VITE_STRIPE_PRICE_TIER_AGENCY || '')}
                    disabled={isProcessing || !import.meta.env.VITE_STRIPE_PRICE_TIER_AGENCY}
                    className="w-full"
                    variant="secondary"
                  >
                    {isProcessing ? 'Processing...' : !import.meta.env.VITE_STRIPE_PRICE_TIER_AGENCY ? 'Price ID not configured' : 'Upgrade to Agency'}
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
