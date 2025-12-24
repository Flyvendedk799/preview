import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import Card from '../../components/ui/Card'
import { fetchSiteMenus, type SiteMenu } from '../../api/client'

export default function SiteMenus() {
  const { siteId } = useParams<{ siteId: string }>()
  const [menus, setMenus] = useState<SiteMenu[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (siteId) loadMenus()
  }, [siteId])

  async function loadMenus() {
    if (!siteId) return
    try {
      setLoading(true)
      const data = await fetchSiteMenus(parseInt(siteId))
      setMenus(data)
    } catch (err) {
      console.error('Failed to load menus:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-secondary">Menus</h1>
      </div>

      <Card>
        {loading ? (
          <div className="text-center py-8">Loading...</div>
        ) : menus.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-600">No menus yet</p>
          </div>
        ) : (
          <div className="space-y-4">
            {menus.map((menu) => (
              <div key={menu.id} className="p-4 border rounded-lg">
                <h3 className="font-medium mb-2">{menu.name} ({menu.location})</h3>
                <ul className="space-y-1">
                  {menu.items.map((item) => (
                    <li key={item.id} className="text-sm text-gray-600">
                      {item.label} - {item.url}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

