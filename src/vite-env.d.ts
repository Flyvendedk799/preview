/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_STRIPE_PRICE_TIER_BASIC?: string
  readonly VITE_STRIPE_PRICE_TIER_PRO?: string
  readonly VITE_STRIPE_PRICE_TIER_AGENCY?: string
  readonly VITE_FRONTEND_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

