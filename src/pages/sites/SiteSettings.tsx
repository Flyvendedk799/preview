import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import { fetchSiteSettings, updateSiteSettings, type SiteSettings, type SiteSettingsUpdate } from '../../api/client'

export default function SiteSettings() {
  const { siteId } = useParams<{ siteId: string }>()
  const [settings, setSettings] = useState<SiteSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (siteId) loadSettings()
  }, [siteId])

  async function loadSettings() {
    if (!siteId) return
    try {
      setLoading(true)
      const data = await fetchSiteSettings(parseInt(siteId))
      setSettings(data)
    } catch (err) {
      console.error('Failed to load settings:', err)
    } finally {
      setLoading(false)
    }
  }

  async function handleSave() {
    if (!siteId || !settings) return
    try {
      setSaving(true)
      await updateSiteSettings(parseInt(siteId), settings as SiteSettingsUpdate)
    } catch (err) {
      console.error('Failed to save settings:', err)
    } finally {
      setSaving(false)
    }
  }

  if (loading || !settings) {
    return <Card><div className="text-center py-8">Loading...</div></Card>
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-secondary">Settings</h1>
      </div>

      <Card>
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium mb-2">Site Description</label>
            <textarea
              value={settings.site_description || ''}
              onChange={(e) => setSettings({ ...settings, site_description: e.target.value })}
              rows={4}
              className="w-full px-4 py-2 border rounded-lg"
            />
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

