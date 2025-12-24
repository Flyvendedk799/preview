import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import { fetchSiteCategories, type SiteCategory } from '../../api/client'

export default function SiteCategories() {
  const { siteId } = useParams<{ siteId: string }>()
  const [categories, setCategories] = useState<SiteCategory[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (siteId) loadCategories()
  }, [siteId])

  async function loadCategories() {
    if (!siteId) return
    try {
      setLoading(true)
      const data = await fetchSiteCategories(parseInt(siteId))
      setCategories(data)
    } catch (err) {
      console.error('Failed to load categories:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-secondary">Categories</h1>
      </div>

      <Card>
        {loading ? (
          <div className="text-center py-8">Loading...</div>
        ) : categories.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-600">No categories yet</p>
          </div>
        ) : (
          <div className="space-y-2">
            {categories.map((cat) => (
              <div key={cat.id} className="p-3 border-b flex items-center justify-between">
                <span className="font-medium">{cat.name}</span>
                <span className="text-sm text-gray-500">{cat.post_count || 0} posts</span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

