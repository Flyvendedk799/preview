/** API client for backend communication */
import type {
  Domain,
  DomainCreate,
  BrandSettings,
  BrandSettingsUpdate,
  Preview,
  PreviewCreate,
  PreviewUpdate,
  PreviewVariant,
  AnalyticsSummary,
  User,
  Token,
  AnalyticsOverview,
  DomainAnalyticsItem,
  PreviewAnalyticsItem,
  AdminAnalyticsOverview,
  AdminAnalyticsUserItem,
  WorkerHealth,
  ActivityLog,
  AdminActivityLog,
  Organization,
  OrganizationCreate,
  OrganizationUpdate,
  OrganizationMember,
  OrganizationInviteResponse,
  OrganizationJoinRequest,
  OrganizationRole,
  SystemOverview,
  AdminUserSummary,
  AdminUserDetail,
  AdminDomain,
  AdminPreview,
} from './types'

// Re-export types for use in other files
export type {
  Domain,
  DomainCreate,
  BrandSettings,
  BrandSettingsUpdate,
  Preview,
  PreviewCreate,
  PreviewUpdate,
  PreviewVariant,
  AnalyticsSummary,
  User,
  Token,
  AnalyticsOverview,
  DomainAnalyticsItem,
  PreviewAnalyticsItem,
  AdminAnalyticsOverview,
  AdminAnalyticsUserItem,
  WorkerHealth,
  ActivityLog,
  AdminActivityLog,
  Organization,
  OrganizationMember,
  OrganizationInviteResponse,
  OrganizationRole,
  SystemOverview,
  AdminUserSummary,
  AdminUserDetail,
  AdminDomain,
}

/**
 * Get the base URL for API requests.
 * Reads from VITE_API_BASE_URL env var or defaults to localhost:8000
 */
export function getApiBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
}

/**
 * Get auth token from localStorage
 */
export function getAuthToken(): string | null {
  return localStorage.getItem('access_token')
}

/**
 * Set auth token in localStorage
 */
export function setAuthToken(token: string): void {
  localStorage.setItem('access_token', token)
}

/**
 * Remove auth token from localStorage
 */
export function removeAuthToken(): void {
  localStorage.removeItem('access_token')
}

/**
 * Base fetch wrapper with error handling and auth token injection
 */
export async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit,
  requireAuth: boolean = true
): Promise<T> {
  const baseUrl = getApiBaseUrl()
  const url = `${baseUrl}${endpoint}`

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> || {}),
  }

  // Add auth token if available and auth is required
  if (requireAuth) {
    const token = getAuthToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    // Add organization ID header if available
    const selectedOrgId = localStorage.getItem('selected_org_id')
    if (selectedOrgId) {
      headers['X-Organization-ID'] = selectedOrgId
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error')
    throw new Error(`API error: ${response.status} ${response.statusText} - ${errorText}`)
  }

  return response.json()
}

// Auth endpoints
export async function login(email: string, password: string): Promise<Token> {
  const baseUrl = getApiBaseUrl()
  const formData = new URLSearchParams()
  formData.append('username', email) // OAuth2PasswordRequestForm uses 'username'
  formData.append('password', password)

  const response = await fetch(`${baseUrl}/api/v1/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData,
  })

  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error')
    throw new Error(`Login failed: ${response.status} ${response.statusText} - ${errorText}`)
  }

  return response.json()
}

export async function signup(email: string, password: string): Promise<User> {
  return fetchApi<User>(
    '/api/v1/auth/signup',
    {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    },
    false // Don't require auth for signup
  )
}

export async function fetchCurrentUser(): Promise<User> {
  return fetchApi<User>('/api/v1/auth/me')
}

// Domain endpoints
export async function fetchDomains(): Promise<Domain[]> {
  return fetchApi<Domain[]>('/api/v1/domains')
}

export async function createDomain(payload: DomainCreate): Promise<Domain> {
  return fetchApi<Domain>('/api/v1/domains', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function fetchDomainById(id: number): Promise<Domain> {
  return fetchApi<Domain>(`/api/v1/domains/${id}`)
}

export async function deleteDomain(id: number): Promise<void> {
  await fetchApi<{ success: boolean }>(`/api/v1/domains/${id}`, {
    method: 'DELETE',
  })
}

// Brand settings endpoints
export async function fetchBrandSettings(): Promise<BrandSettings> {
  return fetchApi<BrandSettings>('/api/v1/brand')
}

export async function updateBrandSettings(
  payload: BrandSettingsUpdate
): Promise<BrandSettings> {
  return fetchApi<BrandSettings>('/api/v1/brand', {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

// Preview endpoints
export async function fetchPreviews(type?: string): Promise<Preview[]> {
  const queryParam = type ? `?type=${encodeURIComponent(type)}` : ''
  return fetchApi<Preview[]>(`/api/v1/previews${queryParam}`)
}

export async function createOrUpdatePreview(
  payload: PreviewCreate
): Promise<Preview> {
  return fetchApi<Preview>('/api/v1/previews', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updatePreview(
  previewId: number,
  payload: PreviewUpdate
): Promise<Preview> {
  return fetchApi<Preview>(`/api/v1/previews/${previewId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export async function deletePreview(previewId: number): Promise<void> {
  await fetchApi<{ success: boolean }>(`/api/v1/previews/${previewId}`, {
    method: 'DELETE',
  })
}

export async function generatePreviewWithAI(payload: { url: string; domain: string }): Promise<Preview> {
  return fetchApi<Preview>('/api/v1/previews/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

// Job queue endpoints
export interface JobStatus {
  status: 'queued' | 'started' | 'finished' | 'failed'
  result: Preview | null
  error: string | null
}

export async function createPreviewJob(payload: { url: string; domain: string }): Promise<{ job_id: string }> {
  return fetchApi<{ job_id: string }>('/api/v1/jobs/preview', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  return fetchApi<JobStatus>(`/api/v1/jobs/${jobId}/status`)
}

// Analytics endpoints
export async function fetchAnalyticsSummary(
  period: '7d' | '30d' = '7d'
): Promise<AnalyticsSummary> {
  return fetchApi<AnalyticsSummary>(`/api/v1/analytics/summary?period=${period}`)
}

// Domain Verification
export async function startDomainVerification(domainId: number, method: 'dns' | 'html' | 'meta'): Promise<{
  domain_id: number
  method: string
  token: string
  instructions: Record<string, string>
}> {
  return fetchApi(`/api/v1/domains/${domainId}/verification/start`, {
    method: 'POST',
    body: JSON.stringify({ method }),
  })
}

export async function checkDomainVerification(domainId: number): Promise<Domain> {
  return fetchApi<Domain>(`/api/v1/domains/${domainId}/verification/check`)
}

// Billing endpoints
export async function createCheckoutSession(priceId: string): Promise<{ checkout_url: string }> {
  return fetchApi<{ checkout_url: string }>('/api/v1/billing/checkout', {
    method: 'POST',
    body: JSON.stringify({ price_id: priceId }),
  })
}

export async function createBillingPortal(): Promise<{ portal_url: string }> {
  return fetchApi<{ portal_url: string }>('/api/v1/billing/portal', {
    method: 'POST',
  })
}

export async function getBillingStatus(): Promise<{
  subscription_status: string
  subscription_plan?: string | null
  trial_ends_at?: string | null
}> {
  return fetchApi('/api/v1/billing/status')
}

// Admin endpoints

export async function fetchAdminUsers(): Promise<AdminUserSummary[]> {
  return fetchApi<AdminUserSummary[]>('/api/v1/admin/users')
}

export async function fetchAdminUserById(userId: number): Promise<AdminUserDetail> {
  return fetchApi<AdminUserDetail>(`/api/v1/admin/users/${userId}`)
}

export async function toggleUserActive(userId: number): Promise<{
  id: number
  email: string
  is_active: boolean
  message: string
}> {
  return fetchApi(`/api/v1/admin/users/${userId}/toggle-active`, {
    method: 'POST',
  })
}

export async function fetchAdminDomains(): Promise<AdminDomain[]> {
  return fetchApi<AdminDomain[]>('/api/v1/admin/domains')
}

export async function deleteAdminDomain(domainId: number): Promise<{ message: string }> {
  return fetchApi(`/api/v1/admin/domains/${domainId}`, {
    method: 'DELETE',
  })
}

export async function fetchAdminPreviews(skip = 0, limit = 50): Promise<AdminPreview[]> {
  return fetchApi<AdminPreview[]>(`/api/v1/admin/previews?skip=${skip}&limit=${limit}`)
}

export async function deleteAdminPreview(previewId: number): Promise<{ message: string }> {
  return fetchApi(`/api/v1/admin/previews/${previewId}`, {
    method: 'DELETE',
  })
}

export async function fetchAdminPreviewVariants(previewId: number): Promise<PreviewVariant[]> {
  return fetchApi<PreviewVariant[]>(`/api/v1/admin/previews/${previewId}/variants`)
}

export async function deleteAdminPreviewVariant(variantId: number): Promise<{ message: string }> {
  return fetchApi(`/api/v1/admin/preview-variants/${variantId}`, {
    method: 'DELETE',
  })
}

export async function fetchAdminSystemOverview(): Promise<SystemOverview> {
  return fetchApi<SystemOverview>('/api/v1/admin/system/overview')
}

export async function fetchAdminWorkerHealth(): Promise<WorkerHealth> {
  return fetchApi<WorkerHealth>('/api/v1/admin/system/worker-health')
}

export async function exportUserData(): Promise<any> {
  return fetchApi('/api/v1/account/export')
}

export async function deleteUserAccount(): Promise<{ success: boolean; message: string }> {
  return fetchApi('/api/v1/account', {
    method: 'DELETE',
  })
}

export async function deleteOrganization(orgId: number): Promise<{ success: boolean; message: string }> {
  return fetchApi(`/api/v1/account/organizations/${orgId}`, {
    method: 'DELETE',
  })
}

// Activity endpoints

export async function fetchUserActivity(skip = 0, limit = 50): Promise<ActivityLog[]> {
  return fetchApi<ActivityLog[]>(`/api/v1/activity?skip=${skip}&limit=${limit}`)
}

export async function fetchAdminActivity(
  skip = 0,
  limit = 50,
  userId?: number,
  action?: string
): Promise<AdminActivityLog[]> {
  const params = new URLSearchParams({
    skip: skip.toString(),
    limit: limit.toString(),
  })
  if (userId !== undefined) params.append('user_id', userId.toString())
  if (action) params.append('action', action)
  return fetchApi<AdminActivityLog[]>(`/api/v1/activity/admin?${params.toString()}`)
}

// Analytics endpoints
export async function fetchAnalyticsOverview(): Promise<AnalyticsOverview> {
  return fetchApi<AnalyticsOverview>('/api/v1/analytics/overview')
}

export async function fetchDomainAnalytics(): Promise<DomainAnalyticsItem[]> {
  return fetchApi<DomainAnalyticsItem[]>('/api/v1/analytics/domains')
}

export async function fetchPreviewAnalytics(limit = 20): Promise<PreviewAnalyticsItem[]> {
  return fetchApi<PreviewAnalyticsItem[]>(`/api/v1/analytics/previews?limit=${limit}`)
}

export async function fetchAdminAnalyticsOverview(): Promise<AdminAnalyticsOverview> {
  return fetchApi<AdminAnalyticsOverview>('/api/v1/admin/analytics/overview')
}

export async function fetchAdminAnalyticsUsers(limit = 20): Promise<AdminAnalyticsUserItem[]> {
  return fetchApi<AdminAnalyticsUserItem[]>(`/api/v1/admin/analytics/users?limit=${limit}`)
}

// Organization endpoints

export async function fetchOrganizations(): Promise<Organization[]> {
  return fetchApi<Organization[]>('/api/v1/organizations')
}

export async function createOrganization(data: OrganizationCreate): Promise<Organization> {
  return fetchApi<Organization>('/api/v1/organizations', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getOrganization(orgId: number): Promise<Organization> {
  return fetchApi<Organization>(`/api/v1/organizations/${orgId}`)
}

export async function updateOrganization(orgId: number, data: OrganizationUpdate): Promise<Organization> {
  return fetchApi<Organization>(`/api/v1/organizations/${orgId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function fetchOrganizationMembers(orgId: number): Promise<OrganizationMember[]> {
  return fetchApi<OrganizationMember[]>(`/api/v1/organizations/${orgId}/members`)
}

export async function updateMemberRole(
  orgId: number,
  memberId: number,
  role: string
): Promise<OrganizationMember> {
  return fetchApi<OrganizationMember>(`/api/v1/organizations/${orgId}/members/${memberId}/role?new_role=${role}`, {
    method: 'PUT',
  })
}

export async function removeMember(orgId: number, memberId: number): Promise<{ success: boolean }> {
  return fetchApi<{ success: boolean }>(`/api/v1/organizations/${orgId}/members/${memberId}`, {
    method: 'DELETE',
  })
}

export async function createInviteLink(
  orgId: number,
  role: string = 'viewer',
  expiresInDays: number = 7
): Promise<OrganizationInviteResponse> {
  return fetchApi<OrganizationInviteResponse>(`/api/v1/organizations/${orgId}/invite`, {
    method: 'POST',
    body: JSON.stringify({ role, expires_in_days: expiresInDays }),
  })
}

export async function joinOrganization(data: OrganizationJoinRequest): Promise<Organization> {
  return fetchApi<Organization>('/api/v1/organizations/join', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

// Preview Variant endpoints
export async function fetchPreviewVariants(previewId: number): Promise<PreviewVariant[]> {
  return fetchApi<PreviewVariant[]>(`/api/v1/preview-variants/preview/${previewId}`)
}

export async function getPreviewVariant(variantId: number): Promise<PreviewVariant> {
  return fetchApi<PreviewVariant>(`/api/v1/preview-variants/${variantId}`)
}

export async function updatePreviewVariant(
  variantId: number,
  data: { title?: string; description?: string; tone?: string; keywords?: string; image_url?: string }
): Promise<PreviewVariant> {
  return fetchApi<PreviewVariant>(`/api/v1/preview-variants/${variantId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deletePreviewVariant(variantId: number): Promise<void> {
  await fetchApi(`/api/v1/preview-variants/${variantId}`, {
    method: 'DELETE',
  })
}

