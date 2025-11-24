/** TypeScript interfaces matching backend Pydantic schemas */

export interface Domain {
  id: number
  name: string
  environment: string
  status: string
  verification_method?: string | null
  verification_token?: string | null
  verified_at?: string | null
  created_at: string // ISO datetime
  monthly_clicks: number
}

export interface DomainCreate {
  name: string
  environment?: string
  status?: string
}

export interface BrandSettings {
  id: number
  primary_color: string
  secondary_color: string
  accent_color: string
  font_family: string
  logo_url?: string | null
}

export interface BrandSettingsUpdate {
  primary_color?: string
  secondary_color?: string
  accent_color?: string
  font_family?: string
  logo_url?: string | null
}

export interface Preview {
  id: number
  url: string
  domain: string
  title: string
  type: string
  image_url: string
  highlight_image_url?: string | null
  description?: string | null
  keywords?: string | null
  tone?: string | null
  ai_reasoning?: string | null
  created_at: string // ISO datetime
  monthly_clicks: number
}

export interface PreviewVariant {
  id: number
  preview_id: number
  variant_key: 'a' | 'b' | 'c'
  title: string
  description?: string | null
  tone?: string | null
  keywords?: string | null
  image_url?: string | null
  created_at: string
}

export interface PreviewCreate {
  url: string
  domain: string
  title: string
  type: string
  image_url?: string | null
  description?: string | null
}

export interface PreviewUpdate {
  title?: string | null
  type?: string | null
  image_url?: string | null
}

export interface TopDomain {
  domain: string
  clicks: number
  ctr: number
}

export interface AnalyticsSummary {
  period: string
  total_clicks: number
  total_previews: number
  total_domains: number
  brand_score: number
  top_domains: TopDomain[]
}

export interface User {
  id: number
  email: string
  is_active: boolean
  is_admin?: boolean
  created_at: string
  stripe_customer_id?: string | null
  stripe_subscription_id?: string | null
  subscription_status: string
  subscription_plan?: string | null
  trial_ends_at?: string | null
}

export interface UserCreate {
  email: string
  password: string
}

export interface Token {
  access_token: string
  token_type: string
}

// Admin types
export interface AdminUserSummary {
  id: number
  email: string
  is_active: boolean
  subscription_status: string
  subscription_plan?: string | null
  created_at: string
  domains_count: number
  previews_count: number
}

export interface AdminUserDetail {
  id: number
  email: string
  is_active: boolean
  is_admin: boolean
  subscription_status: string
  subscription_plan?: string | null
  trial_ends_at?: string | null
  created_at: string
  domains_count: number
  previews_count: number
  total_clicks: number
  stripe_customer_id?: string | null
}

export interface AdminDomain {
  id: number
  name: string
  environment: string
  status: string
  verification_method?: string | null
  verified_at?: string | null
  user_email: string
  user_id: number
  created_at: string
  monthly_clicks: number
}

export interface AdminPreview {
  id: number
  url: string
  domain: string
  title: string
  type: string
  user_email: string
  user_id: number
  created_at: string
  monthly_clicks: number
}

export interface SystemOverview {
  total_users: number
  active_subscribers: number
  total_domains: number
  verified_domains: number
  previews_generated_24h: number
  jobs_running: number
  errors_past_24h: number
  redis_queue_length: number
}

// Activity log types
export interface ActivityLog {
  id: number
  action: string
  metadata: Record<string, any> | null
  created_at: string
}

export interface AdminActivityLog extends ActivityLog {
  user_id?: number | null
  organization_id?: number | null
  ip_address?: string | null
  user_agent?: string | null
}

// Analytics types
export interface TimeseriesPoint {
  date: string
  value: number
}

export interface AnalyticsOverview {
  total_impressions: number
  total_clicks: number
  ctr: number
  impressions_timeseries: TimeseriesPoint[]
  clicks_timeseries: TimeseriesPoint[]
}

export interface DomainAnalyticsItem {
  domain_id: number
  domain_name: string
  impressions_7d: number
  impressions_30d: number
  clicks_7d: number
  clicks_30d: number
  ctr_30d: number
}

export interface PreviewAnalyticsItem {
  preview_id: number
  url: string
  title: string
  domain: string
  impressions_30d: number
  clicks_30d: number
  ctr_30d: number
}

export interface AdminAnalyticsOverview {
  total_users: number
  active_subscribers: number
  total_domains: number
  total_previews: number
  total_impressions_24h: number
  total_clicks_24h: number
  total_impressions_30d: number
  total_clicks_30d: number
}

export interface AdminAnalyticsUserItem {
  user_id: number
  email: string
  impressions_30d: number
  clicks_30d: number
  active_domains: number
  active_previews: number
}

export interface WorkerHealth {
  main_queue_length: number
  dlq_length: number
  recent_failures_count: number
  last_successful_job_at: string | null
  last_failure_at: string | null
}

// Organization types
export type OrganizationRole = 'owner' | 'admin' | 'editor' | 'viewer'

export interface Organization {
  id: number
  name: string
  owner_user_id: number
  created_at: string
  subscription_status: string
  subscription_plan?: string | null
}

export interface OrganizationCreate {
  name: string
}

export interface OrganizationUpdate {
  name?: string
}

export interface OrganizationMember {
  id: number
  organization_id: number
  user_id: number
  role: OrganizationRole
  created_at: string
  user_email?: string | null
}

export interface OrganizationInviteResponse {
  invite_token: string
  invite_url: string
  expires_at: string
}

export interface OrganizationJoinRequest {
  invite_token: string
}

