import { useState, useEffect } from 'react'
import { Sun, Download, Search, ChevronDown, ChevronUp, Check } from 'lucide-react'
import axios from 'axios'
import Plot from 'react-plotly.js'

interface PVModule {
  name: string
  manufacturer: string
  technology: string
  p_stc: number | null
  p_ptc: number | null
  efficiency: number | null
  area: number | null
  cells_in_series: number | null
  v_mp_ref: number | null
  i_mp_ref: number | null
  v_oc_ref: number | null
  i_sc_ref: number | null
}

interface ManualModule {
  p_stc: number
  efficiency: number
  v_mp: number
  i_mp: number
  v_oc: number
  i_sc: number
  alpha_sc: number
  beta_oc: number
  gamma_pdc: number
  area: number
}

export default function SolarForecast() {
  const [capacity, setCapacity] = useState(100)
  const [hours, setHours] = useState(24)
  const [forecast, setForecast] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  // PV Module selection state
  const [modules, setModules] = useState<PVModule[]>([])
  const [selectedModule, setSelectedModule] = useState<PVModule | null>(null)
  const [moduleSearch, setModuleSearch] = useState('')
  const [moduleFilter, setModuleFilter] = useState({ manufacturer: '', technology: '', pmin: '', pmax: '' })
  const [showModuleSelect, setShowModuleSelect] = useState(false)
  const [modulesLoading, setModulesLoading] = useState(false)
  const [manualMode, setManualMode] = useState(false)
  const [manualModule, setManualModule] = useState<ManualModule>({
    p_stc: 550,
    efficiency: 0.21,
    v_mp: 41.5,
    i_mp: 13.25,
    v_oc: 49.5,
    i_sc: 14.1,
    alpha_sc: 0.002146,
    beta_oc: -0.159,
    gamma_pdc: -0.004,
    area: 2.7,
  })

  // Fetch modules on mount
  useEffect(() => {
    fetchModules()
  }, [])

  const fetchModules = async (params?: Record<string, any>) => {
    setModulesLoading(true)
    try {
      const response = await axios.get('http://localhost:8000/api/v1/pv/modules/search', {
        params: { limit: 200, ...params },
      })
      setModules(response.data.modules || [])
    } catch (error) {
      console.error('Failed to load modules:', error)
      setModules([])
    } finally {
      setModulesLoading(false)
    }
  }

  const searchModules = () => {
    const params: Record<string, any> = {}
    if (moduleSearch) params.q = moduleSearch
    if (moduleFilter.manufacturer) params.manufacturer = moduleFilter.manufacturer
    if (moduleFilter.technology) params.technology = moduleFilter.technology
    if (moduleFilter.pmin) params.pmin = parseFloat(moduleFilter.pmin)
    if (moduleFilter.pmax) params.pmax = parseFloat(moduleFilter.pmax)
    fetchModules(params)
  }

  const generateForecast = async () => {
    setLoading(true)
    try {
      // If a module is selected, scale capacity to number of modules
      let numModules = 1
      let moduleCapacity = capacity

      if (selectedModule && selectedModule.p_stc && !manualMode) {
        const moduleW = selectedModule.p_stc
        // If capacity is in kW and module is in W
        if (capacity > moduleW / 1000) {
          // Capacity is total plant capacity, calculate modules
          numModules = Math.round((capacity * 1000) / moduleW)
          moduleCapacity = (numModules * moduleW) / 1000
        } else {
          // Few modules
          numModules = Math.round((capacity * 1000) / moduleW) || 1
          moduleCapacity = (numModules * moduleW) / 1000
        }
      }

      const response = await axios.get('http://localhost:8000/api/v1/forecast/solar', {
        params: {
          capacity: moduleCapacity,
          hours,
        },
      })
      const data = response.data.data
      data.user_capacity_kw = capacity
      data.num_modules = numModules
      data.selected_module = selectedModule
      data.manual_mode = manualMode
      setForecast(data)
    } catch (error) {
      console.error('Forecast failed:', error)
      alert('Failed to generate forecast')
    } finally {
      setLoading(false)
    }
  }

  const selectModule = (mod: PVModule) => {
    setSelectedModule(mod)
    setShowModuleSelect(false)
    // If module selected with known power, suggest capacity = ~100 modules worth (for intuitive defaults)
    if (mod.p_stc && mod.p_stc > 0) {
      const defaultNum = 100
      const suggested = (defaultNum * mod.p_stc) / 1000
      setCapacity(Math.round(suggested))
    }
  }

  const peakPower = () => {
    if (!forecast || !forecast.generation || forecast.generation.length === 0) return 0
    const peakKW = Math.max(...forecast.generation.map((g: number) => Number(g) || 0))
    return peakKW // Backend now sends generation in kW
  }

  const totalGeneration = () => {
    if (!forecast || !forecast.generation) return 0
    const sum = forecast.generation.reduce((a: number, b: number) => a + (Number(b) || 0), 0)
    return sum // Backend now sends generation in kW, sum is kWh
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Solar PV Forecast</h1>
          <p className="text-[#8A7A60] mt-1">
            Generate generation forecasts using pvlib with Bandung weather data
          </p>
        </div>
        <button
          onClick={generateForecast}
          disabled={loading}
          className="flex items-center gap-2 px-6 py-3 bg-[#3A7010] text-white rounded-lg font-medium hover:bg-[#2D6010] disabled:opacity-50"
        >
          <Sun size={20} />
          {loading ? 'Generating...' : 'Generate Forecast'}
        </button>
      </div>

      {/* Configuration */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-[#C8BFA8] p-4">
          <label className="text-sm font-medium">PV Capacity (kW)</label>
          <input
            type="number"
            value={capacity}
            onChange={(e) => setCapacity(Number(e.target.value))}
            className="mt-2 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
          />
          <p className="text-xs text-[#8A7A60] mt-1">Total installed capacity</p>
        </div>

        <div className="bg-white rounded-xl border border-[#C8BFA8] p-4">
          <label className="text-sm font-medium">Forecast Horizon (hours)</label>
          <input
            type="number"
            value={hours}
            onChange={(e) => setHours(Number(e.target.value))}
            min={1}
            max={168}
            className="mt-2 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
          />
        </div>

        <div className="bg-white rounded-xl border border-[#C8BFA8] p-4">
          <label className="text-sm font-medium">System Info</label>
          <p className="mt-2 text-sm text-[#8A7A60]">
            Tilt: auto (latitude-based)<br />
            Azimuth: 0° (North-facing)<br />
            Location: Bandung
          </p>
        </div>
      </div>

      {/* PV Module Selection */}
      <div className="bg-white rounded-xl border border-[#C8BFA8] p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-lg">PV Module Selection</h3>
          <div className="flex gap-2">
            <button
              onClick={() => { setManualMode(false); setShowModuleSelect(!showModuleSelect) }}
              className={`px-3 py-1 rounded-md text-sm ${!manualMode && selectedModule ? 'bg-[#3A7010] text-white' : 'bg-gray-100 text-gray-700'}`}
            >
              {selectedModule ? `Selected: ${selectedModule.name}` : 'Select from Database'}
            </button>
            <button
              onClick={() => { setManualMode(true); setShowModuleSelect(false) }}
              className={`px-3 py-1 rounded-md text-sm ${manualMode ? 'bg-[#3A7010] text-white' : 'bg-gray-100 text-gray-700'}`}
            >
              Manual Entry
            </button>
          </div>
        </div>

        {/* Show selected module info when NOT in manual mode */}
        {!manualMode && selectedModule && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-sm">
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-[#8A7A60] text-xs">Manufacturer</p>
              <p className="font-medium">{selectedModule.manufacturer}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-[#8A7A60] text-xs">Technology</p>
              <p className="font-medium">{selectedModule.technology}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-[#8A7A60] text-xs">STC Power</p>
              <p className="font-medium">{selectedModule.p_stc !== null ? `${selectedModule.p_stc} W` : '—'}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-[#8A7A60] text-xs">Efficiency</p>
              <p className="font-medium">{selectedModule.efficiency !== null ? `${(selectedModule.efficiency * 100).toFixed(2)}%` : '—'}</p>
            </div>
          </div>
        )}

        {/* Module selection panel */}
        {showModuleSelect && !manualMode && (
          <div className="border rounded-lg p-4 bg-gray-50 space-y-3">
            <div className="flex gap-2 flex-wrap">
              <div className="flex-1 min-w-[200px]">
                <input
                  type="text"
                  placeholder="Search modules..."
                  value={moduleSearch}
                  onChange={(e) => setModuleSearch(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && searchModules()}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                />
              </div>
              <button onClick={searchModules} className="px-3 py-2 bg-[#3A7010] text-white rounded-lg text-sm">
                <Search size={14} className="inline mr-1" /> Search
              </button>
              <button onClick={() => { setModuleSearch(''); setModuleFilter({ manufacturer: '', technology: '', pmin: '', pmax: '' }); fetchModules() }} className="px-3 py-2 bg-gray-200 rounded-lg text-sm">
                Reset
              </button>
            </div>

            {/* Filters */}
            <div className="flex gap-2 flex-wrap">
              <select
                value={moduleFilter.manufacturer}
                onChange={(e) => { setModuleFilter({ ...moduleFilter, manufacturer: e.target.value }); }}
                className="px-2 py-1 border rounded text-sm"
              >
                <option value="">All Manufacturers</option>
                <option value="Longi">Longi</option>
                <option value="Jinko">Jinko</option>
                <option value="Trina">Trina</option>
                <option value="Canadian Solar">Canadian Solar</option>
                <option value="First Solar">First Solar</option>
                <option value="SunPower">SunPower</option>
              </select>
              <select
                value={moduleFilter.technology}
                onChange={(e) => { setModuleFilter({ ...moduleFilter, technology: e.target.value }); }}
                className="px-2 py-1 border rounded text-sm"
              >
                <option value="">All Tech</option>
                <option value="Mono-c-Si">Mono Si</option>
                <option value="Multi-c-Si">Multi Si</option>
                <option value="CdTe">CdTe</option>
                <option value="Thin Film">Thin Film</option>
              </select>
              <input
                type="number"
                placeholder="Min W"
                value={moduleFilter.pmin}
                onChange={(e) => setModuleFilter({ ...moduleFilter, pmin: e.target.value })}
                className="w-20 px-2 py-1 border rounded text-sm"
              />
              <input
                type="number"
                placeholder="Max W"
                value={moduleFilter.pmax}
                onChange={(e) => setModuleFilter({ ...moduleFilter, pmax: e.target.value })}
                className="w-20 px-2 py-1 border rounded text-sm"
              />
            </div>

            {/* Module list */}
            <div className="max-h-64 overflow-y-auto border rounded-lg bg-white">
              {modulesLoading ? (
                <p className="p-4 text-sm text-[#8A7A60]">Loading modules...</p>
              ) : modules.length === 0 ? (
                <p className="p-4 text-sm text-[#8A7A60]">No modules found. Try adjusting filters.</p>
              ) : (
                <table className="w-full text-sm">
                  <thead className="bg-gray-100 sticky top-0">
                    <tr>
                      <th className="text-left p-2">Name</th>
                      <th className="text-left p-2">P_STC</th>
                      <th className="text-left p-2">Eff</th>
                      <th className="text-left p-2">Area</th>
                      <th className="p-2"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {modules.map((mod) => (
                      <tr key={mod.name} className="border-b hover:bg-gray-50 cursor-pointer" onClick={() => selectModule(mod)}>
                        <td className="p-2">
                          <div className="font-medium">{mod.name}</div>
                          <div className="text-xs text-[#8A7A60]">{mod.manufacturer} · {mod.technology}</div>
                        </td>
                        <td className="p-2">{mod.p_stc !== null ? `${mod.p_stc} W` : '—'}</td>
                        <td className="p-2">{mod.efficiency !== null ? `${(mod.efficiency * 100).toFixed(1)}%` : '—'}</td>
                        <td className="p-2">{mod.area !== null ? `${mod.area.toFixed(2)} m²` : '—'}</td>
                        <td className="p-2">
                          <button
                            onClick={(e) => { e.stopPropagation(); selectModule(mod) }}
                            className="px-2 py-1 bg-[#3A7010] text-white rounded text-xs"
                          >
                            Select
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* Manual entry panel */}
        {manualMode && (
          <div className="border rounded-lg p-4 bg-gray-50">
            <h4 className="font-medium mb-3">Manual Module Parameters</h4>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <div>
                <label className="text-xs text-[#8A7A60]">P_STC (W)</label>
                <input
                  type="number"
                  value={manualModule.p_stc}
                  onChange={(e) => setManualModule({ ...manualModule, p_stc: Number(e.target.value) })}
                  className="w-full px-2 py-1 border rounded text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-[#8A7A60]">Efficiency</label>
                <input
                  type="number"
                  step="0.01"
                  value={manualModule.efficiency}
                  onChange={(e) => setManualModule({ ...manualModule, efficiency: Number(e.target.value) })}
                  className="w-full px-2 py-1 border rounded text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-[#8A7A60]">V_mp (V)</label>
                <input
                  type="number"
                  value={manualModule.v_mp}
                  onChange={(e) => setManualModule({ ...manualModule, v_mp: Number(e.target.value) })}
                  className="w-full px-2 py-1 border rounded text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-[#8A7A60]">I_mp (A)</label>
                <input
                  type="number"
                  value={manualModule.i_mp}
                  onChange={(e) => setManualModule({ ...manualModule, i_mp: Number(e.target.value) })}
                  className="w-full px-2 py-1 border rounded text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-[#8A7A60]">γ_pdc (%/°C)</label>
                <input
                  type="number"
                  step="0.001"
                  value={manualModule.gamma_pdc}
                  onChange={(e) => setManualModule({ ...manualModule, gamma_pdc: Number(e.target.value) })}
                  className="w-full px-2 py-1 border rounded text-sm"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      {forecast && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl border border-[#C8BFA8] p-4">
              <p className="text-xs text-[#8A7A60] uppercase">Total Generation</p>
              <p className="text-2xl font-semibold mt-1 text-[#3A7A18]">
                {totalGeneration().toFixed(1)} kWh
              </p>
            </div>
            <div className="bg-white rounded-xl border border-[#C8BFA8] p-4">
              <p className="text-xs text-[#8A7A60] uppercase">Peak Power</p>
              <p className="text-2xl font-semibold mt-1">
                {peakPower().toFixed(2)} kW
              </p>
            </div>
            <div className="bg-white rounded-xl border border-[#C8BFA8] p-4">
              <p className="text-xs text-[#8A7A60] uppercase">Avg Capacity Factor</p>
              <p className="text-2xl font-semibold mt-1">
                {(() => {
                  if (!forecast.capacity_factor || forecast.capacity_factor.length === 0) return '0%';
                  const sum = forecast.capacity_factor.reduce((a: number, b: number) => a + (Number(b) || 0), 0);
                  const avg = sum / forecast.capacity_factor.length;
                  return `${(avg * 100).toFixed(1)}%`;
                })()}
              </p>
            </div>
            <div className="bg-white rounded-xl border border-[#C8BFA8] p-4">
              <p className="text-xs text-[#8A7A60] uppercase">Period</p>
              <p className="text-lg font-semibold mt-1">
                {hours}h
              </p>
            </div>
          </div>

          {/* Module info in results */}
          {forecast.selected_module && !forecast.manual_mode && (
            <div className="bg-white rounded-xl border border-[#C8BFA8] p-4">
              <h4 className="font-medium mb-2">PV Module Summary</h4>
              <div className="flex flex-wrap gap-4 text-sm">
                <span><strong>Module:</strong> {forecast.selected_module.name} ({forecast.selected_module.manufacturer})</span>
                <span><strong>Per Module:</strong> {forecast.selected_module.p_stc} W</span>
                <span><strong>Number of modules:</strong> {forecast.num_modules}</span>
                <span><strong>Efficiency:</strong> {(forecast.selected_module.efficiency * 100).toFixed(2)}%</span>
              </div>
            </div>
          )}

          {/* Generation Chart */}
          <div className="bg-white rounded-xl border border-[#C8BFA8] p-6">
            <h3 className="font-semibold mb-4">Solar Generation Forecast</h3>
            <div className="h-72">
              <Plot
                data={[
                  {
                    x: forecast.timestamps.map((t: string) => new Date(t).getHours()),
                    y: forecast.generation.map((g: number) => Number(g) || 0),
                    type: 'bar',
                    marker: { color: '#3A7A18' },
                    name: 'Generation (kW)',
                  },
                  {
                    x: forecast.timestamps.map((t: string) => new Date(t).getHours()),
                    y: forecast.irradiance.map((g: number) => Number(g) || 0),
                    type: 'scatter',
                    mode: 'lines',
                    line: { color: '#A07010', width: 2 },
                    name: 'GHI (W/m²)',
                    yaxis: 'y2',
                  },
                ]}
                layout={{
                  margin: { t: 20, b: 40, l: 50, r: 50 },
                  xaxis: { title: 'Hour of Day', tickmode: 'linear', dtick: 3 },
                  yaxis: { title: 'Generation (kW)' },
                  yaxis2: {
                    title: 'Irradiance (W/m²)',
                    overlaying: 'y',
                    side: 'right',
                  },
                  legend: { orientation: 'h', y: -0.2 },
                }}
                config={{ responsive: true, displayModeBar: false }}
                style={{ width: '100%', height: '100%' }}
              />
            </div>
          </div>

          {/* Temperature Chart */}
          <div className="bg-white rounded-xl border border-[#C8BFA8] p-6">
            <h3 className="font-semibold mb-4">Temperature Profile</h3>
            <div className="h-48">
              <Plot
                data={[{
                  x: forecast.timestamps.map((t: string) => new Date(t).getHours()),
                  y: forecast.temperature.map((g: number) => Number(g) || 0),
                  type: 'scatter',
                  mode: 'lines+markers',
                  line: { color: '#B04030', width: 2 },
                  marker: { size: 6 },
                  name: 'Temperature (°C)',
                }]}
                layout={{
                  margin: { t: 20, b: 40, l: 50, r: 20 },
                  xaxis: { title: 'Hour of Day', tickmode: 'linear', dtick: 3 },
                  yaxis: { title: 'Temperature (°C)' },
                  showlegend: false,
                }}
                config={{ responsive: true, displayModeBar: false }}
                style={{ width: '100%', height: '100%' }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
