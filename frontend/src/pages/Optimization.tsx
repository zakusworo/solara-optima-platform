import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Play, Download, RefreshCw, TrendingUp, Zap, Sun, Battery } from 'lucide-react'
import axios from 'axios'
import Plot from 'react-plotly.js'

export default function Optimization() {
  const [loadProfile, setLoadProfile] = useState<number[]>([])
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
    setLoadProfile(sample)
  }

  const runOptimization = async () => {
    if (loadProfile.length === 0) {
      alert('Please load a sample or enter load data')
      return
    }

    setIsRunning(true)
    try {
      const response = await axios.post('http://localhost:8000/api/v1/optimize/run-with-solar', {
        load_profile: loadProfile,
        generators: [
          {
            generator_id: 1,
            name: 'Gas Turbine 1',
            fuel_type: 'Natural Gas',
            min_output: 10,
            max_output: 100,
            ramp_up: 50,
            ramp_down: 50,
            min_uptime: 2,
            min_downtime: 2,
            initial_status: 1,
            initial_output: 50,
            startup_cost: 500000,
            shutdown_cost: 0,
            no_load_cost: 50000,
            fuel_cost: 800,
            emissions_rate: 0.45,
          },
          {
            generator_id: 2,
            name: 'Diesel Generator',
            fuel_type: 'Diesel',
            min_output: 5,
            max_output: 50,
            ramp_up: 25,
            ramp_down: 25,
            min_uptime: 1,
            min_downtime: 1,
            initial_status: 0,
            initial_output: 0,
            startup_cost: 100000,
            shutdown_cost: 0,
            no_load_cost: 25000,
            fuel_cost: 1200,
            emissions_rate: 0.7,
          },
        ],
        pv_system_capacity: 100,
        bess_capacity: 50,
        bess_power_rating: 25,
      })

      setResult(response.data.data.result)
    } catch (error) {
      console.error('Optimization failed:', error)
      alert('Optimization failed. Check console for details.')
    } finally {
      setIsRunning(false)
    }
  }

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

          {loadProfile.length > 0 ? (
            <div className="h-48">
              <Plot
                data={[
                  {
                    x: Array.from({ length: loadProfile.length }, (_, i) => i),
                    y: loadProfile,
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: '#A07010', width: 2 },
                    marker: { size: 4 },
                  },
                ]}
                layout={{
                  margin: { t: 20, b: 30, l: 40, r: 20 },
                  xaxis: { title: 'Hour', tickmode: 'linear', dtick: 3 },
                  yaxis: { title: 'Load (kW)', range: [0, Math.max(...loadProfile) * 1.2] },
                  showlegend: false,
                }}
                config={{ responsive: true, displayModeBar: false }}
                style={{ width: '100%', height: '100%' }}
              />
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center bg-[#F5F0E8] rounded-lg border-2 border-dashed border-[#C8BFA8]">
              <p className="text-[#8A7A60]">Click "Load Sample" to load a typical load profile</p>
            </div>
          )}
        </div>

        {/* System Configuration */}
        <div className="bg-white rounded-xl border border-[#C8BFA8] p-6 space-y-4">
          <h2 className="font-semibold mb-4">System Configuration</h2>
          
          <div className="flex items-center gap-3 p-3 bg-[#F5F0E8] rounded-lg">
            <Sun size={20} className="text-[#3A7A18]" />
            <div>
              <p className="font-medium text-sm">Solar PV System</p>
              <p className="text-xs text-[#8A7A60]">100 kW capacity, North-facing (0° azimuth)</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 bg-[#F5F0E8] rounded-lg">
            <Battery size={20} className="text-[#5A7A30]" />
            <div>
              <p className="font-medium text-sm">Battery Storage</p>
              <p className="text-xs text-[#8A7A60]">50 kWh / 25 kW, 90% efficiency</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 bg-[#F5F0E8] rounded-lg">
            <Zap size={20} className="text-[#A07010]" />
            <div>
              <p className="font-medium text-sm">Generator Fleet</p>
              <p className="text-xs text-[#8A7A60]">1× Gas Turbine (100kW), 1× Diesel (50kW)</p>
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
                {result.solar_output ? (result.solar_output.reduce((a, b) => a + b, 0) / 1000).toFixed(1) : 0} kWh
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
              {result.generator_schedules && result.solar_output && (
                <Plot
                  data={[
                    {
                      x: Array.from({ length: 24 }, (_, i) => i),
                      y: result.generator_schedules[0]?.output || [],
                      type: 'bar',
                      name: 'Gas Turbine',
                      marker: { color: '#5A7A30' },
                    },
                    {
                      x: Array.from({ length: 24 }, (_, i) => i),
                      y: result.generator_schedules[1]?.output || [],
                      type: 'bar',
                      name: 'Diesel',
                      marker: { color: '#A07010' },
                    },
                    {
                      x: Array.from({ length: 24 }, (_, i) => i),
                      y: result.solar_output,
                      type: 'bar',
                      name: 'Solar',
                      marker: { color: '#3A7A18' },
                    },
                    {
                      x: Array.from({ length: 24 }, (_, i) => i),
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
