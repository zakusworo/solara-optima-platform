import { useState } from 'react'
import { Settings as SettingsIcon, Save, Globe, Cpu, Zap } from 'lucide-react'

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

  const handleSave = () => {
    console.log('Saving settings:', settings)
    alert('Settings saved successfully!')
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-[#8A7A60] mt-1">
          Configure location, market parameters, and optimization settings
        </p>
      </div>

      {/* Location Settings */}
      <div className="bg-white rounded-xl border border-[#C8BFA8] p-6">
        <div className="flex items-center gap-3 mb-6">
          <Globe size={20} className="text-[#5A7A30]" />
          <h2 className="font-semibold">Location Settings</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium">Latitude (°S)</label>
            <input
              type="number"
              step="0.0001"
              value={settings.latitude}
              onChange={(e) => setSettings({ ...settings, latitude: Number(e.target.value) })}
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
            />
            <p className="text-xs text-[#8A7A60] mt-1">Negative for Southern Hemisphere</p>
          </div>
          <div>
            <label className="text-sm font-medium">Longitude (°E)</label>
            <input
              type="number"
              step="0.0001"
              value={settings.longitude}
              onChange={(e) => setSettings({ ...settings, longitude: Number(e.target.value) })}
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Altitude (m)</label>
            <input
              type="number"
              value={settings.altitude}
              onChange={(e) => setSettings({ ...settings, altitude: Number(e.target.value) })}
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Timezone</label>
            <select
              value={settings.timezone}
              onChange={(e) => setSettings({ ...settings, timezone: e.target.value })}
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
            >
              <option value="Asia/Jakarta">Asia/Jakarta (WIB)</option>
              <option value="Asia/Makassar">Asia/Makassar (WITA)</option>
              <option value="Asia/Jayapura">Asia/Jayapura (WIT)</option>
            </select>
          </div>
        </div>

        <div className="mt-4 p-4 bg-[#F5F0E8] rounded-lg">
          <p className="text-sm">
            <strong>Note:</strong> For Southern Hemisphere locations, optimal PV azimuth is 0° (North-facing), NOT 180° (South-facing).
          </p>
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
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
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
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
            />
            <p className="text-xs text-[#8A7A60] mt-1">Current: ~15,500 Rp/USD</p>
          </div>
          <div>
            <label className="text-sm font-medium">Carbon Price (Rp/tCO₂)</label>
            <input
              type="number"
              value={settings.carbonPrice}
              onChange={(e) => setSettings({ ...settings, carbonPrice: Number(e.target.value) })}
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
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

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium">MILP Solver</label>
            <select
              value={settings.solverName}
              onChange={(e) => setSettings({ ...settings, solverName: e.target.value })}
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
            >
              <option value="cbc">CBC (COIN-OR)</option>
              <option value="glpk">GLPK</option>
              <option value="gurobi">Gurobi (requires license)</option>
              <option value="cplex">CPLEX (requires license)</option>
            </select>
          </div>
          <div>
            <label className="text-sm font-medium">Time Limit (seconds)</label>
            <input
              type="number"
              value={settings.solverTimeLimit}
              onChange={(e) => setSettings({ ...settings, solverTimeLimit: Number(e.target.value) })}
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
            />
          </div>
        </div>
      </div>

      {/* PV System Defaults */}
      <div className="bg-white rounded-xl border border-[#C8BFA8] p-6">
        <h2 className="font-semibold mb-4">PV System Defaults</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-sm font-medium">Tilt Angle</label>
            <select
              value={settings.pvTilt}
              onChange={(e) => setSettings({ ...settings, pvTilt: e.target.value })}
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
            >
              <option value="auto">Auto (latitude-based)</option>
              <option value="fixed">Fixed angle</option>
            </select>
          </div>
          <div>
            <label className="text-sm font-medium">Azimuth (°)</label>
            <input
              type="number"
              value={settings.pvAzimuth}
              onChange={(e) => setSettings({ ...settings, pvAzimuth: Number(e.target.value) })}
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
            />
            <p className="text-xs text-[#8A7A60] mt-1">0° = North (optimal for SH)</p>
          </div>
          <div>
            <label className="text-sm font-medium">Module Efficiency</label>
            <input
              type="number"
              step="0.01"
              value={settings.pvEfficiency}
              onChange={(e) => setSettings({ ...settings, pvEfficiency: Number(e.target.value) })}
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
            />
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end gap-4">
        <button className="px-6 py-2 border border-[#C8BFA8] rounded-lg hover:bg-[#F5F0E8]">
          Reset to Defaults
        </button>
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
