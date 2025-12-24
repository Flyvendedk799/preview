import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import Card from '../../components/ui/Card'
import { fetchSiteMedia, type SiteMedia } from '../../api/client'

export default function SiteMedia() {
  const { siteId } = useParams<{ siteId: string }>()
  const [media, setMedia] = useState<SiteMedia[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (siteId) loadMedia()
  }, [siteId])

  async function loadMedia() {
    if (!siteId) return
    try {
      setLoading(true)
      const data = await fetchSiteMedia(parseInt(siteId))
      setMedia(data)
    } catch (err) {
      console.error('Failed to load media:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-secondary">Media Library</h1>
      </div>

      <Card>
        {loading ? (
          <div className="text-center py-8">Loading...</div>
        ) : media.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-600">No media files yet</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {media.map((item) => (
              <div key={item.id} className="border rounded-lg p-2">
                <div className="aspect-square bg-gray-100 rounded mb-2"></div>
                <p className="text-xs truncate">{item.filename}</p>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

