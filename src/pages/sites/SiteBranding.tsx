import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import { fetchSiteBranding, updateSiteBranding, type SiteBranding, type SiteBrandingUpdate } from '../../api/client'

export default function SiteBranding() {
  const { siteId } = useParams<{ siteId: string }>()
  const [branding, setBranding] = useState<SiteBranding | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (siteId) loadBranding()
  }, [siteId])

  async function loadBranding() {
    if (!siteId) return
    try {
      setLoading(true)
      const data = await fetchSiteBranding(parseInt(siteId))
      setBranding(data)
    } catch (err) {
      console.error('Failed to load branding:', err)
    } finally {
      setLoading(false)
    }
  }

  async function handleSave() {
    if (!siteId || !branding) return
    try {
      setSaving(true)
      await updateSiteBranding(parseInt(siteId), branding as SiteBrandingUpdate)
    } catch (err) {
      console.error('Failed to save branding:', err)
    } finally {
      setSaving(false)
    }
  }

  if (loading || !branding) {
    return <Card><div className="text-center py-8">Loading...</div></Card>
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-secondary">Branding</h1>
      </div>

      <Card>
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium mb-2">Primary Color</label>
            <div className="flex items-center space-x-3">
              <input
                type="color"
                value={branding.primary_color}
                onChange={(e) => setBranding({ ...branding, primary_color: e.target.value })}
                className="w-16 h-10 border rounded"
              />
              <input
                type="text"
                value={branding.primary_color}
                onChange={(e) => setBranding({ ...branding, primary_color: e.target.value })}
                className="flex-1 px-4 py-2 border rounded-lg font-mono"
              />
            </div>
          </div>
          <div className="flex justify-end">
            <Button onClick={handleSave} disabled={saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}

