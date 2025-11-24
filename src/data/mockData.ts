/**
 * Centralized mock data for consistency across pages
 */

export interface Domain {
  id: number
  domain: string
  status: 'Active' | 'Pending'
  previews: number
  clicks: number
  addedDate: string
}

export interface Preview {
  id: number
  title: string
  category: 'Product' | 'Blog' | 'Landing Page'
  image: string
  clicks: number
  url: string
}

export const initialDomains: Domain[] = [
  { id: 1, domain: 'example.com', status: 'Active', previews: 45, clicks: 1234, addedDate: '2024-01-15' },
  { id: 2, domain: 'mysite.io', status: 'Active', previews: 32, clicks: 892, addedDate: '2024-01-10' },
  { id: 3, domain: 'test.dev', status: 'Pending', previews: 0, clicks: 0, addedDate: '2024-01-20' },
  { id: 4, domain: 'demo.app', status: 'Active', previews: 18, clicks: 456, addedDate: '2024-01-05' },
]

export const initialPreviews: Preview[] = [
  { id: 1, title: 'Product Page', category: 'Product', image: 'bg-gradient-to-br from-primary/30 to-accent/30', clicks: 1234, url: 'example.com/product' },
  { id: 2, title: 'Blog Post', category: 'Blog', image: 'bg-gradient-to-br from-purple-300 to-pink-300', clicks: 892, url: 'example.com/blog' },
  { id: 3, title: 'Landing Page', category: 'Landing Page', image: 'bg-gradient-to-br from-blue-300 to-cyan-300', clicks: 654, url: 'example.com/landing' },
  { id: 4, title: 'Product Feature', category: 'Product', image: 'bg-gradient-to-br from-green-300 to-emerald-300', clicks: 456, url: 'example.com/feature' },
  { id: 5, title: 'Article', category: 'Blog', image: 'bg-gradient-to-br from-orange-300 to-red-300', clicks: 321, url: 'example.com/article' },
  { id: 6, title: 'Homepage', category: 'Landing Page', image: 'bg-gradient-to-br from-indigo-300 to-purple-300', clicks: 2100, url: 'example.com' },
]

export const getDashboardStats = (domains: Domain[], previews: Preview[]) => {
  const totalClicks = domains.reduce((sum, d) => sum + d.clicks, 0)
  const newDomains = domains.filter(d => {
    const addedDate = new Date(d.addedDate)
    const now = new Date()
    const daysDiff = (now.getTime() - addedDate.getTime()) / (1000 * 60 * 60 * 24)
    return daysDiff <= 30
  }).length
  const totalPreviews = previews.length
  const brandScore = Math.min(100, Math.floor(85 + Math.random() * 15)) // Mock score between 85-100

  return {
    monthlyClicks: totalClicks,
    newDomains,
    previewsGenerated: totalPreviews,
    brandScore,
  }
}

export const getAnalyticsData = (period: '7d' | '30d') => {
  const days = period === '7d' ? 7 : 30
  const clicksData = Array.from({ length: days }, () => Math.floor(Math.random() * 200) + 50)
  const totalClicks = clicksData.reduce((sum, val) => sum + val, 0)
  const avgCTR = (Math.random() * 5 + 7).toFixed(1) // Between 7-12%
  const impressions = Math.floor(totalClicks * 10)

  return {
    clicksData,
    totalClicks,
    avgCTR: parseFloat(avgCTR),
    impressions,
  }
}

