import { useState } from 'react'
import { Play, RefreshCw, Zap, Sun, Battery, Edit3, Layers } from 'lucide-react'
import LazyPlot from '../components/LazyPlot'
import { api } from '../utils/api'
import { useFleet, fleetToApiGenerators } from '../store/fleet'

// Distinct bar colors cycled across fleet generators so the dispatch stack
// stays legible regardless of fleet size.
const GEN_COLORS = [
  '#5A7A30', '#A07010', '#3A7A18', '#B04030',
  '#6A5A8A', '#3A8A8A', '#C8842A', '#2C5A8A',
]

export default function Optimization() {
  // Initialize with 24 zeros so inputs are always present
  const [loadProfile, setLoadProfile] = useState<number[]>(Array(24).fill(0))
  const [isRunning, setIsRunning] = useState(false)
  const [result, setResult] = useState<any>(null)

  // Sample load profile (24 hours)
  const loadSample = () => {
    const sample = [
      80, 75, 70, 65, 60, 65,
      85, 100, 120, 130, 125, 120,
      115, 110, 115, 125, 140, 160,
      170, 165, 150, 130, 110, 95,
    ]
    setLoadProfile([...sample])
  }

  const updateLoad = (hour: number, value: string) => {
    const num = parseFloat(value) || 0
    const updated = [...loadProfile]
    updated[hour] = num
    setLoadProfile(updated)
  }

  const { generators, system } = useFleet()

  const runOptimization = async () => {
    const hasData = loadProfile.some(v => v > 0)
    if (!hasData) {
      alert('Please load a sample or enter load data')
      return
    }
    if (generators.length === 0) {
      alert('No generators in fleet. Add generators on the Generators page first.')
      return
    }

    setIsRunning(true)
    try {
      const response = await api.post('/api/v1/optimize/run-with-solar', {
        load_profile: loadProfile,
        generators: fleetToApiGenerators(generators),
        // Omit pv_system_capacity when 0 so the backend skips solar generation.
        pv_system_capacity: system.solarCapacityKw || undefined,
        bess_capacity: system.batteryCapacityKwh,
        bess_power_rating: system.batteryPowerKw,
      })

      setResult(response.data.data.result)
    } catch (error) {
      console.error('Optimization failed:', error)
      alert('Optimization failed. Check console for details.')
    } finally {
      setIsRunning(false)
    }
  }

  // Determine if chart should show empty placeholder
  const hasSample = loadProfile.some(v => v > 0)

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Unit Commitment & Economic Dispatch</h1>
          <p className="text-[#8A7A60] mt-1">Optimize generator dispatch with solar and battery storage</p>
        </div>
        <button
          onClick={runOptimization}
          disabled={isRunning}
          className="flex items-center gap-2 px-6 py-3 bg-[#3A7010] text-white rounded-lg font-medium hover:bg-[#2D6010] disabled:opacity-50"
        >
          {isRunning ? <RefreshCw className="animate-spin" size={20} /> : <Play size={20} />}
          {isRunning ? 'Running...' : 'Run Optimization'}
        </button>
      </div>

      {/* Input Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Load Profile */}
        <div className="bg-white rounded-xl border border-[#C8BFA8] p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold flex items-center gap-2">
              <Zap size={18} className="text-[#A07010]" />
              Load Profile
            </h2>
            <button
              onClick={loadSample}
              className="text-sm px-3 py-1.5 bg-[#EDE8DC] rounded-md hover:bg-[#E4DDD0]"
            >
              Load Sample
            </button>
          </div>

          {/* Chart */}
          {hasSample ? (
            <div className="h-48">
              <LazyPlot
                data={[
                  {
                    x: Array.from({ length: 24 }, (_, i) => i),
                    y: loadProfile,
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: '#A07010', width: 2 },
                    marker: { size: 6, symbol: 'diamond' },
                  },
                ]}
                layout={{
                  margin: { t: 20, b: 30, l: 40, r: 20 },
                  xaxis: { title: 'Hour', tickmode: 'linear', dtick: 3, range: [0, 23] },
                  yaxis: {
                    title: 'Load (kW)',
                    range: [0, Math.max(...loadProfile) * 1.2 > 0 ? Math.max(...loadProfile) * 1.2 : 200],
                  },
                  showlegend: false,
                }}
                config={{ responsive: true, displayModeBar: false }}
                style={{ width: '100%', height: '100%' }}
              />
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center bg-[#F5F0E8] rounded-lg border-2 border-dashed border-[#C8BFA8]">
              <p className="text-[#8A7A60]">Click "Load Sample" or enter values below to build a load profile</p>
            </div>
          )}

          {/* Hourly Load Editor */}
          <div className="mt-6 border-t border-[#C8BFA8] pt-4">
            <div className="flex items-center gap-2 mb-3">
              <Edit3 size={16} className="text-[#8A7A60]" />
              <span className="text-sm font-medium text-[#5A4E3A]">Hourly Load Editor (kW)</span>
            </div>
            <div className="grid grid-cols-6 gap-2">
              {loadProfile.map((value, hour) => (
                <div key={hour} className="flex flex-col">
                  <label className="text-[10px] text-[#8A7A60] font-mono mb-0.5">
                    {hour.toString().padStart(2, '0')}:00
                  </label>
                  <input
                    type="number"
                    min={0}
                    step={1}
                    value={value === 0 && !hasSample ? '' : value}
                    onChange={(e) => updateLoad(hour, e.target.value)}
                    className="w-full px-2 py-1.5 text-sm border border-[#C8BFA8] rounded-md focus:ring-1 focus:ring-[#3A7010] focus:border-[#3A7010] outline-none text-right font-mono"
                    placeholder="0"
                  />
                </div>
              ))}
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-[#8A7A60]">
              <span>
                Total daily load: {' '}
                <span className="font-mono font-medium text-[#5A4E3A]">{loadProfile.reduce((a, b) => a + b, 0).toFixed(0)}</span>{' '}
                kWh
              </span>
              <span>
                Peak: {' '}
                <span className="font-mono font-medium text-[#5A4E3A]">{Math.max(...loadProfile).toFixed(0)}</span>{' '}
                kW · Avg: {' '}
                <span className="font-mono font-medium text-[#5A4E3A]">{(loadProfile.reduce((a, b) => a + b, 0) / 24).toFixed(1)}</span>{' '}
                kW
              </span>
            </div>
          </div>
        </div>

        {/* System Configuration */}
        <div className="bg-white rounded-xl border border-[#C8BFA8] p-6 space-y-4">
          <h2 className="font-semibold mb-4">System Configuration</h2>
          
          <div className="flex items-center gap-3 p-3 bg-[#F5F0E8] rounded-lg">
            <Sun size={20} className="text-[#3A7A18]" />
            <div>
              <p className="font-medium text-sm">Solar PV System</p>
              <p className="text-xs text-[#8A7A60]">
                {system.solarCapacityKw} kW capacity
                {system.solarCapacityKw > 0 ? ' (auto clear-sky forecast)' : ' (disabled)'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 bg-[#F5F0E8] rounded-lg">
            <Battery size={20} className="text-[#5A7A30]" />
            <div>
              <p className="font-medium text-sm">Battery Storage</p>
              <p className="text-xs text-[#8A7A60]">
                {system.batteryCapacityKwh} kWh / {system.batteryPowerKw} kW, 90% efficiency
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 p-3 bg-[#F5F0E8] rounded-lg">
            <Layers size={20} className="text-[#A07010] mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-sm">Generator Fleet ({generators.length})</p>
              {generators.length === 0 ? (
                <p className="text-xs text-[#B04030]">
                  No generators — configure on the Generators page.
                </p>
              ) : (
                <ul className="text-xs text-[#8A7A60] mt-1 space-y-0.5">
                  {generators.map((g) => (
                    <li key={g.uid} className="flex justify-between">
                      <span>
                        {g.name} <span className="opacity-70">({g.fuel_type})</span>
                      </span>
                      <span className="font-mono">{g.min_output}–{g.max_output} kW</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div className="pt-4 border-t border-[#C8BFA8]">
            <div className="flex items-center justify-between text-sm">
              <span className="text-[#8A7A60]">Location</span>
              <span className="font-mono">Bandung (-6.9147°S, 107.6098°E)</span>
            </div>
            <div className="flex items-center justify-between text-sm mt-2">
              <span className="text-[#8A7A60]">Solver</span>
              <span className="font-mono">CBC MILP</span>
            </div>
          </div>
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl border border-[#C8BFA8] p-4">
              <p className="text-xs text-[#8A7A60] uppercase tracking-wide">Total Cost</p>
              <p className="text-2xl font-semibold mt-1">Rp {(result.total_cost / 1000000).toFixed(2)}M</p>
            </div>
            <div className="bg-white rounded-xl border border-[#C8BFA8] p-4">
              <p className="text-xs text-[#8A7A60] uppercase tracking-wide">Solar Generation</p>
              <p className="text-2xl font-semibold mt-1 text-[#3A7A18]">
                {result.solar_output ? (result.solar_output.reduce((a: number, b: number) => a + b, 0) / 1000).toFixed(1) : 0} kWh
              </p>
            </div>
            <div className="bg-white rounded-xl border border-[#C8BFA8] p-4">
              <p className="text-xs text-[#8A7A60] uppercase tracking-wide">Solve Time</p>
              <p className="text-2xl font-semibold mt-1">{result.solve_time.toFixed(2)}s</p>
            </div>
            <div className="bg-white rounded-xl border border-[#C8BFA8] p-4">
              <p className="text-xs text-[#8A7A60] uppercase tracking-wide">Status</p>
              <p className="text-lg font-semibold mt-1 text-[#3A7A18]">{result.status}</p>
            </div>
          </div>

          {/* Generation Stack Chart */}
          <div className="bg-white rounded-xl border border-[#C8BFA8] p-6">
            <h3 className="font-semibold mb-4">Generation Stack</h3>
            <div className="h-64">
              {result.generator_schedules && (
                <LazyPlot
                  data={[
                    // One bar series per fleet generator, matched by generator_id.
                    ...generators.map((g, i) => {
                      const sched =
                        result.generator_schedules.find(
                          (s: any) => s.generator_id === i + 1,
                        ) || result.generator_schedules[i]
                      return {
                        x: Array.from({ length: 24 }, (_, h) => h),
                        y: sched?.output || [],
                        type: 'bar',
                        name: g.name,
                        marker: { color: GEN_COLORS[i % GEN_COLORS.length] },
                      }
                    }),
                    ...(result.solar_output
                      ? [{
                          x: Array.from({ length: 24 }, (_, h) => h),
                          y: result.solar_output,
                          type: 'bar',
                          name: 'Solar',
                          marker: { color: '#3A7A18' },
                        }]
                      : []),
                    {
                      x: Array.from({ length: 24 }, (_, h) => h),
                      y: loadProfile,
                      type: 'scatter',
                      name: 'Load',
                      line: { color: '#2C2418', width: 2, dash: 'dash' },
                    },
                  ]}
                  layout={{
                    margin: { t: 20, b: 40, l: 50, r: 20 },
                    barmode: 'stack',
                    xaxis: { title: 'Hour', tickmode: 'linear', dtick: 3 },
                    yaxis: { title: 'Power (kW)' },
                    legend: { orientation: 'h', y: -0.2 },
                  }}
                  config={{ responsive: true, displayModeBar: false }}
                  style={{ width: '100%', height: '100%' }}
                />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
