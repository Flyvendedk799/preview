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
/**
 * Get the API base URL from environment variables.
 * 
 * IMPORTANT: This should be just the base URL (e.g., https://backend.railway.app)
 * WITHOUT the /api/v1 suffix, as all endpoints already include /api/v1.
 * 
 * Examples:
 * - Development: http://localhost:8000
 * - Production: https://your-backend-service.railway.app
 */
export function getApiBaseUrl(): string {
  const url = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  // Remove trailing slash if present
  return url.replace(/\/$/, '')
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

  // Log API calls in development
  if (import.meta.env.DEV) {
    console.log(`[API] ${options?.method || 'GET'} ${url}`)
  }

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

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      // Try to parse JSON error response
      let errorMessage = `Server error (${response.status})`
      try {
        const errorData = await response.json().catch(() => null)
        if (errorData?.detail) {
          errorMessage = errorData.detail
        } else if (typeof errorData === 'string') {
          errorMessage = errorData
        } else {
          const errorText = await response.text().catch(() => 'Unknown error')
          errorMessage = errorText || `Server error (${response.status})`
        }
      } catch {
        // If JSON parsing fails, try text
        const errorText = await response.text().catch(() => 'Unknown error')
        errorMessage = errorText || `Server error (${response.status})`
      }
      
      console.error(`[API Error] ${url}:`, {
        status: response.status,
        statusText: response.statusText,
        error: errorMessage
      })
      throw new Error(errorMessage)
    }

    return response.json()
  } catch (error) {
    // Handle network errors (connection refused, etc.)
    if (error instanceof TypeError && error.message.includes('fetch')) {
      const errorMessage = `Failed to connect to API at ${url}. Please check that the backend is running and VITE_API_BASE_URL is set correctly.`
      console.error(`[API Connection Error] ${url}:`, errorMessage)
      console.error(`[API Config] Base URL: ${baseUrl}, Endpoint: ${endpoint}`)
      throw new Error(errorMessage)
    }
    throw error
  }
}

// Auth endpoints
export async function login(email: string, password: string): Promise<Token> {
  const baseUrl = getApiBaseUrl()
  const formData = new URLSearchParams()
  formData.append('username', email) // OAuth2PasswordRequestForm uses 'username'
  formData.append('password', password)

  const url = `${baseUrl}/api/v1/auth/login`
  
  // Log API calls in development
  if (import.meta.env.DEV) {
    console.log(`[API] POST ${url}`)
  }

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData,
  })

  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error')
    const errorMessage = `Login failed: ${response.status} ${response.statusText} - ${errorText}`
    console.error(`[API Error] ${url}:`, errorMessage)
    throw new Error(errorMessage)
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

export async function debugDomainVerification(domainId: number): Promise<{
  domain: string
  expected_value: string
  found_records: string[]
  is_verified: boolean
  error: string | null
}> {
  return fetchApi(`/api/v1/domains/${domainId}/verification/debug`)
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

export async function changeSubscriptionPlan(priceId: string): Promise<{
  subscription_status: string
  subscription_plan?: string | null
  trial_ends_at?: string | null
}> {
  return fetchApi('/api/v1/billing/change-plan', {
    method: 'POST',
    body: JSON.stringify({ price_id: priceId }),
  })
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

// ============================================================================
// Blog Types
// ============================================================================

export interface BlogCategory {
  id: number
  name: string
  slug: string
  description?: string
  color: string
  icon?: string
  is_active: boolean
  sort_order: number
  meta_title?: string
  meta_description?: string
  created_at: string
  updated_at: string
  post_count?: number
}

export interface BlogPostListItem {
  id: number
  title: string
  slug: string
  excerpt?: string
  featured_image?: string
  author_name?: string
  author_avatar?: string
  category?: BlogCategory
  tags?: string
  status: string
  is_featured: boolean
  is_pinned: boolean
  read_time_minutes?: number
  views_count: number
  published_at?: string
  created_at: string
}

export interface BlogPost extends BlogPostListItem {
  content: string
  featured_image_alt?: string
  og_image?: string
  author_id: number
  author_bio?: string
  category_id?: number
  scheduled_at?: string
  updated_at: string
  meta_title?: string
  meta_description?: string
  meta_keywords?: string
  canonical_url?: string
  no_index: boolean
  schema_type: string
  twitter_title?: string
  twitter_description?: string
  twitter_image?: string
  related_post_ids?: string
}

export interface PaginatedBlogPosts {
  items: BlogPostListItem[]
  total: number
  page: number
  per_page: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export interface BlogPostCreate {
  title: string
  slug?: string
  excerpt?: string
  content: string
  featured_image?: string
  featured_image_alt?: string
  og_image?: string
  author_name?: string
  author_bio?: string
  author_avatar?: string
  category_id?: number
  tags?: string
  status?: 'draft' | 'published' | 'scheduled' | 'archived'
  is_featured?: boolean
  is_pinned?: boolean
  scheduled_at?: string
  meta_title?: string
  meta_description?: string
  meta_keywords?: string
  canonical_url?: string
  no_index?: boolean
  schema_type?: string
  twitter_title?: string
  twitter_description?: string
  twitter_image?: string
  related_post_ids?: string
}

export interface BlogPostUpdate extends Partial<BlogPostCreate> {}

export interface BlogCategoryCreate {
  name: string
  slug?: string
  description?: string
  color?: string
  icon?: string
  is_active?: boolean
  sort_order?: number
  meta_title?: string
  meta_description?: string
}

export interface BlogCategoryUpdate extends Partial<BlogCategoryCreate> {}

// ============================================================================
// Blog Endpoints (Public)
// ============================================================================

export async function fetchBlogPosts(options?: {
  page?: number
  per_page?: number
  category?: string
  tag?: string
  search?: string
  featured?: boolean
}): Promise<PaginatedBlogPosts> {
  const params = new URLSearchParams()
  if (options?.page) params.append('page', options.page.toString())
  if (options?.per_page) params.append('per_page', options.per_page.toString())
  if (options?.category) params.append('category', options.category)
  if (options?.tag) params.append('tag', options.tag)
  if (options?.search) params.append('search', options.search)
  if (options?.featured !== undefined) params.append('featured', options.featured.toString())
  
  const query = params.toString() ? `?${params.toString()}` : ''
  return fetchApi<PaginatedBlogPosts>(`/api/v1/blog/posts${query}`, undefined, false)
}

export async function fetchFeaturedBlogPosts(limit: number = 3): Promise<BlogPostListItem[]> {
  return fetchApi<BlogPostListItem[]>(`/api/v1/blog/posts/featured?limit=${limit}`, undefined, false)
}

export async function fetchRecentBlogPosts(limit: number = 5, excludeId?: number): Promise<BlogPostListItem[]> {
  const params = new URLSearchParams({ limit: limit.toString() })
  if (excludeId) params.append('exclude_id', excludeId.toString())
  return fetchApi<BlogPostListItem[]>(`/api/v1/blog/posts/recent?${params.toString()}`, undefined, false)
}

export async function fetchBlogPostBySlug(slug: string): Promise<BlogPost> {
  return fetchApi<BlogPost>(`/api/v1/blog/posts/${slug}`, undefined, false)
}

export async function fetchBlogCategories(includeEmpty: boolean = false): Promise<BlogCategory[]> {
  return fetchApi<BlogCategory[]>(`/api/v1/blog/categories?include_empty=${includeEmpty}`, undefined, false)
}

export async function fetchBlogCategoryBySlug(slug: string): Promise<BlogCategory> {
  return fetchApi<BlogCategory>(`/api/v1/blog/categories/${slug}`, undefined, false)
}

// ============================================================================
// Blog Endpoints (Admin)
// ============================================================================

export async function adminFetchBlogPosts(options?: {
  page?: number
  per_page?: number
  status?: string
  category_id?: number
  search?: string
}): Promise<PaginatedBlogPosts> {
  const params = new URLSearchParams()
  if (options?.page) params.append('page', options.page.toString())
  if (options?.per_page) params.append('per_page', options.per_page.toString())
  if (options?.status) params.append('status', options.status)
  if (options?.category_id) params.append('category_id', options.category_id.toString())
  if (options?.search) params.append('search', options.search)
  
  const query = params.toString() ? `?${params.toString()}` : ''
  return fetchApi<PaginatedBlogPosts>(`/api/v1/blog/admin/posts${query}`)
}

export async function adminFetchBlogPost(postId: number): Promise<BlogPost> {
  return fetchApi<BlogPost>(`/api/v1/blog/admin/posts/${postId}`)
}

export async function adminCreateBlogPost(data: BlogPostCreate): Promise<BlogPost> {
  return fetchApi<BlogPost>('/api/v1/blog/admin/posts', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function adminUpdateBlogPost(postId: number, data: BlogPostUpdate): Promise<BlogPost> {
  return fetchApi<BlogPost>(`/api/v1/blog/admin/posts/${postId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function adminDeleteBlogPost(postId: number): Promise<void> {
  await fetchApi(`/api/v1/blog/admin/posts/${postId}`, {
    method: 'DELETE',
  })
}

export async function adminPublishBlogPost(postId: number): Promise<BlogPost> {
  return fetchApi<BlogPost>(`/api/v1/blog/admin/posts/${postId}/publish`, {
    method: 'POST',
  })
}

export async function adminUnpublishBlogPost(postId: number): Promise<BlogPost> {
  return fetchApi<BlogPost>(`/api/v1/blog/admin/posts/${postId}/unpublish`, {
    method: 'POST',
  })
}

export async function adminFetchBlogCategories(includeInactive: boolean = true): Promise<BlogCategory[]> {
  return fetchApi<BlogCategory[]>(`/api/v1/blog/admin/categories?include_inactive=${includeInactive}`)
}

export async function adminCreateBlogCategory(data: BlogCategoryCreate): Promise<BlogCategory> {
  return fetchApi<BlogCategory>('/api/v1/blog/admin/categories', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function adminUpdateBlogCategory(categoryId: number, data: BlogCategoryUpdate): Promise<BlogCategory> {
  return fetchApi<BlogCategory>(`/api/v1/blog/admin/categories/${categoryId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function adminDeleteBlogCategory(categoryId: number): Promise<void> {
  await fetchApi(`/api/v1/blog/admin/categories/${categoryId}`, {
    method: 'DELETE',
  })
}

// ============================================================================
// Newsletter Endpoints
// ============================================================================

export interface NewsletterSubscribeRequest {
  email: string
  source?: string
  consent_given?: boolean
}

export interface NewsletterSubscriber {
  id: number
  email: string
  source: string
  subscribed_at: string
  is_active: boolean
  consent_given: boolean
  ip_address?: string | null
  user_agent?: string | null
}

export interface NewsletterSubscriberList {
  items: NewsletterSubscriber[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export async function subscribeToNewsletter(data: NewsletterSubscribeRequest): Promise<NewsletterSubscriber> {
  return fetchApi<NewsletterSubscriber>('/api/v1/newsletter/subscribe', {
    method: 'POST',
    body: JSON.stringify(data),
  }, false) // No auth required
}

export async function fetchNewsletterSubscribers(options?: {
  page?: number
  per_page?: number
  search?: string
  source?: string
}): Promise<NewsletterSubscriberList> {
  const params = new URLSearchParams()
  if (options?.page) params.append('page', options.page.toString())
  if (options?.per_page) params.append('per_page', options.per_page.toString())
  if (options?.search) params.append('search', options.search)
  if (options?.source) params.append('source', options.source)
  
  const query = params.toString() ? `?${params.toString()}` : ''
  return fetchApi<NewsletterSubscriberList>(`/api/v1/newsletter/subscribers${query}`)
}

export async function exportNewsletterSubscribers(format: 'csv' | 'xlsx' = 'csv', source?: string): Promise<Blob> {
  const params = new URLSearchParams()
  params.append('format', format)
  if (source) params.append('source', source)
  
  const baseUrl = getApiBaseUrl()
  const url = `${baseUrl}/api/v1/newsletter/subscribers/export?${params.toString()}`
  const token = getAuthToken()
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  const response = await fetch(url, {
    method: 'GET',
    headers,
  })
  
  if (!response.ok) {
    throw new Error(`Export failed: ${response.statusText}`)
  }
  
  return response.blob()
}

// ============================================================================
// Demo Preview Endpoints - Semantic Reconstruction
// ============================================================================

export interface DemoPreviewRequest {
  url: string
}

export interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
}

export interface ExtractedElement {
  id: string
  type: string  // profile_image, hero_image, headline, subheadline, cta_button, etc.
  content: string
  bounding_box: BoundingBox
  priority: number
  include_in_preview: boolean
  text_content: string | null
  background_color: string | null
  text_color: string | null
  font_weight: string | null
  is_image: boolean
  image_crop_data: string | null  // Base64 of cropped image region
  confidence: number
}

export interface LayoutSection {
  name: string
  element_ids: string[]
  layout_direction: 'horizontal' | 'vertical' | 'grid'
  alignment: 'left' | 'center' | 'right'
  spacing: 'tight' | 'normal' | 'loose'
  emphasis: 'primary' | 'secondary' | 'tertiary'
}

export interface LayoutPlan {
  template: string  // profile_card, product_card, landing_hero, etc.
  page_type: string
  primary_color: string
  secondary_color: string
  accent_color: string
  background_style: string
  font_style: string
  sections: LayoutSection[]
  title: string
  subtitle: string | null
  description: string | null
  cta_text: string | null
  layout_rationale: string
}

export interface DemoPreviewResponse {
  // URL
  url: string
  
  // Layout plan for reconstruction
  layout_plan: LayoutPlan
  
  // Extracted elements
  elements: ExtractedElement[]
  
  // Key images (base64)
  profile_image_base64: string | null
  hero_image_base64: string | null
  logo_base64: string | null
  
  // Screenshot fallback
  screenshot_url: string | null
  
  // Quality metrics
  extraction_confidence: number
  reconstruction_quality: 'excellent' | 'good' | 'fair' | 'fallback'
  processing_time_ms: number
  
  // Demo metadata
  is_demo: boolean
  message: string
}

export async function generateDemoPreview(url: string): Promise<DemoPreviewResponse> {
  return fetchApi<DemoPreviewResponse>('/api/v1/demo/preview', {
    method: 'POST',
    body: JSON.stringify({ url }),
  }, false) // No auth required
}

