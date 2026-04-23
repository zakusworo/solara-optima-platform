import { useState, useEffect } from 'react'
import { Settings as SettingsIcon, Save, Globe, Cpu, Zap, MapPin, Search } from 'lucide-react'
import axios from 'axios'
import LocationMap from '../components/LocationMap'

interface GeoResult {
  name: string
  latitude: number
  longitude: number
}

export default function Settings() {
  const [settings, setSettings] = useState({
    latitude: -6.9147,
    longitude: 107.6098,
    altitude: 768,
    timezone: 'Asia/Jakarta',
    currency: 'IDR',
    usdIdrRate: 15500,
    carbonPrice: 50000,
    solverName: 'cbc',
    solverTimeLimit: 300,
    pvTilt: 'auto',
    pvAzimuth: 0,
    pvEfficiency: 0.20,
    bessEfficiency: 0.90,
  })

  const [locationName, setLocationName] = useState('Bandung, Indonesia')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<GeoResult[]>([])
  const [searching, setSearching] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    axios.get('http://localhost:8000/api/v1/location/current')
      .then(r => {
        if (r.data.success) {
          const d = r.data.data
          setSettings(s => ({
            ...s,
            latitude: d.latitude,
            longitude: d.longitude,
            altitude: d.altitude,
            timezone: d.timezone,
          }))
          setLocationName(d.name)
        }
      })
      .catch((e: any) => console.error('Load location failed:', e))
  }, [])

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    setSearching(true)
    try {
      const resp = await axios.get('http://localhost:8000/api/v1/location/search', {
        params: { q: searchQuery, limit: 5 },
      })
      if (resp.data.success) {
        setSearchResults(resp.data.data)
      } else {
        setSearchResults([])
      }
    } catch (e: any) {
      console.error('Search failed:', e)
      setSearchResults([])
    } finally {
      setSearching(false)
    }
  }

  const selectLocation = (result: GeoResult) => {
    setSettings(s => ({ ...s, latitude: result.latitude, longitude: result.longitude }))
    setLocationName(result.name)
    setSearchResults([])
    setSearchQuery('')
  }

  const handleMapClick = (lat: number, lon: number) => {
    setSettings(s => ({ ...s, latitude: lat, longitude: lon }))
    setLocationName(`${lat.toFixed(4)}, ${lon.toFixed(4)}`)
  }

  const handleSave = async () => {
    try {
      await axios.post('http://localhost:8000/api/v1/location/update', {
        latitude: settings.latitude,
        longitude: settings.longitude,
        altitude: settings.altitude,
        timezone: settings.timezone,
        name: locationName,
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (e: any) {
      alert('Save failed: ' + (e.response?.data?.detail || e.message))
    }
  }

  const hemisphere = settings.latitude < 0 ? 'southern' : 'northern'
  const azimuthHint = settings.latitude < 0 ? '0 = North (optimal for Southern Hemisphere)' : '180 = South (optimal for Northern Hemisphere)'

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-12">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-[#8A7A60] mt-1">
          Configure location, market parameters, and optimization settings
        </p>
      </div>

      {/* Location + Map */}
      <div className="bg-white rounded-xl border border-[#C8BFA8] p-6">
        <div className="flex items-center gap-3 mb-6">
          <Globe size={20} className="text-[#5A7A30]" />
          <h2 className="font-semibold">Location Settings</h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Map */}
          <div className="lg:col-span-2 h-[400px]">
            <LocationMap
              latitude={settings.latitude}
              longitude={settings.longitude}
              onLocationChange={handleMapClick}
            />
            <p className="text-xs text-[#8A7A60] mt-2">
              Click on the map or drag the marker to change location.
            </p>
          </div>

          {/* Location Controls */}
          <div className="space-y-4">
            {/* Search */}
            <div className="relative">
              <label className="text-sm font-medium">Search Place</label>
              <div className="flex gap-2 mt-1">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="e.g. Jakarta, Surabaya..."
                  className="flex-1 px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010] text-sm"
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                />
                <button
                  onClick={handleSearch}
                  disabled={searching}
                  className="px-3 py-2 bg-[#3A7010] text-white rounded-lg hover:bg-[#2D6010] disabled:opacity-50"
                >
                  <Search size={16} />
                </button>
              </div>
              {searching && <p className="text-xs text-[#8A7A60] mt-1">Searching...</p>}
              {searchResults.length > 0 && (
                <div className="mt-2 border border-[#C8BFA8] rounded-lg overflow-hidden max-h-48 overflow-y-auto">
                  {searchResults.map((r, i) => (
                    <button
                      key={i}
                      onClick={() => selectLocation(r)}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-[#F5F0E8] border-b border-[#C8BFA8] last:border-b-0 flex items-start gap-2"
                    >
                      <MapPin size={14} className="text-[#3A7010] mt-0.5 shrink-0" />
                      <span className="truncate">{r.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div>
              <label className="text-sm font-medium">Location Name</label>
              <input
                type="text"
                value={locationName}
                onChange={(e) => setLocationName(e.target.value)}
                className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010] text-sm"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-sm font-medium">Latitude</label>
                <input
                  type="number"
                  step="0.0001"
                  value={settings.latitude}
                  onChange={(e) => setSettings({ ...settings, latitude: Number(e.target.value) })}
                  className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010] text-sm font-mono"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Longitude</label>
                <input
                  type="number"
                  step="0.0001"
                  value={settings.longitude}
                  onChange={(e) => setSettings({ ...settings, longitude: Number(e.target.value) })}
                  className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010] text-sm font-mono"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-sm font-medium">Altitude (m)</label>
                <input
                  type="number"
                  value={settings.altitude}
                  onChange={(e) => setSettings({ ...settings, altitude: Number(e.target.value) })}
                  className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010] text-sm font-mono"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Timezone</label>
                <select
                  value={settings.timezone}
                  onChange={(e) => setSettings({ ...settings, timezone: e.target.value })}
                  className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010] text-sm"
                >
                  <option value="Asia/Jakarta">Asia/Jakarta</option>
                  <option value="Asia/Makassar">Asia/Makassar</option>
                  <option value="Asia/Jayapura">Asia/Jayapura</option>
                  <option value="Asia/Singapore">Asia/Singapore</option>
                  <option value="Australia/Perth">Australia/Perth</option>
                  <option value="Australia/Sydney">Australia/Sydney</option>
                  <option value="UTC">UTC</option>
                </select>
              </div>
            </div>

            <div className="p-3 bg-[#F5F0E8] rounded-lg text-sm">
              <p>
                <strong>Hemisphere:</strong> {hemisphere}
              </p>
              <p>
                <strong>Optimal PV Azimuth:</strong> {settings.latitude < 0 ? '0 (North-facing)' : '180 (South-facing)'}
              </p>
              <p>
                <strong>Optimal PV Tilt:</strong> {(Math.abs(settings.latitude) * 0.76 + 3.1).toFixed(1)} degrees
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Market Settings */}
      <div className="bg-white rounded-xl border border-[#C8BFA8] p-6">
        <div className="flex items-center gap-3 mb-6">
          <Zap size={20} className="text-[#A07010]" />
          <h2 className="font-semibold">Market Parameters</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-sm font-medium">Currency</label>
            <select
              value={settings.currency}
              onChange={(e) => setSettings({ ...settings, currency: e.target.value })}
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010] text-sm"
            >
              <option value="IDR">IDR (Indonesian Rupiah)</option>
              <option value="USD">USD (US Dollar)</option>
              <option value="EUR">EUR (Euro)</option>
            </select>
          </div>
          <div>
            <label className="text-sm font-medium">USD/IDR Rate</label>
            <input
              type="number"
              value={settings.usdIdrRate}
              onChange={(e) => setSettings({ ...settings, usdIdrRate: Number(e.target.value) })}
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010] text-sm"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Carbon Price (Rp/tCO₂)</label>
            <input
              type="number"
              value={settings.carbonPrice}
              onChange={(e) => setSettings({ ...settings, carbonPrice: Number(e.target.value) })}
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010] text-sm"
            />
          </div>
        </div>
      </div>

      {/* Optimization Settings */}
      <div className="bg-white rounded-xl border border-[#C8BFA8] p-6">
        <div className="flex items-center gap-3 mb-6">
          <Cpu size={20} className="text-[#5A7A30]" />
          <h2 className="font-semibold">Optimization Settings</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-sm font-medium">MILP Solver</label>
            <select
              value={settings.solverName}
              onChange={(e) => setSettings({ ...settings, solverName: e.target.value })}
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010] text-sm"
            >
              <option value="cbc">CBC (Free)</option>
              <option value="glpk">GLPK</option>
            </select>
          </div>
          <div>
            <label className="text-sm font-medium">Time Limit (s)</label>
            <input
              type="number"
              value={settings.solverTimeLimit}
              onChange={(e) => setSettings({ ...settings, solverTimeLimit: Number(e.target.value) })}
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010] text-sm"
            />
          </div>
        </div>
      </div>

      {/* PV System */}
      <div className="bg-white rounded-xl border border-[#C8BFA8] p-6">
        <h2 className="font-semibold mb-4">PV System Defaults</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-sm font-medium">Azimuth (°)</label>
            <input
              type="number"
              value={settings.pvAzimuth}
              onChange={(e) => setSettings({ ...settings, pvAzimuth: Number(e.target.value) })}
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010] text-sm"
            />
            <p className="text-xs text-[#8A7A60] mt-1">{azimuthHint}</p>
          </div>
          <div>
            <label className="text-sm font-medium">Module Efficiency</label>
            <input
              type="number"
              step="0.01"
              value={settings.pvEfficiency}
              onChange={(e) => setSettings({ ...settings, pvEfficiency: Number(e.target.value) })}
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010] text-sm"
            />
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end gap-4">
        <div className="flex items-center gap-2">
          {saved && <span className="text-sm text-[#3A7010]">Saved successfully!</span>}
        </div>
        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-6 py-2 bg-[#3A7010] text-white rounded-lg hover:bg-[#2D6010]"
        >
          <Save size={18} />
          Save Settings
        </button>
      </div>
    </div>
  )
}
