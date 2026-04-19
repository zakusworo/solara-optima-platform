import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Sun, Download, Calculator } from 'lucide-react'
import axios from 'axios'
import Plot from 'react-plotly.js'

export default function SolarForecast() {
  const [capacity, setCapacity] = useState(100)
  const [hours, setHours] = useState(24)
  const [forecast, setForecast] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const generateForecast = async () => {
    setLoading(true)
    try {
      const response = await axios.get('http://localhost:8000/api/v1/forecast/solar', {
        params: { capacity, hours },
      })
      setForecast(response.data.data)
    } catch (error) {
      console.error('Forecast failed:', error)
      alert('Failed to generate forecast')
    } finally {
      setLoading(false)
    }
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

      {/* Results */}
      {forecast && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl border border-[#C8BFA8] p-4">
              <p className="text-xs text-[#8A7A60] uppercase">Total Generation</p>
              <p className="text-2xl font-semibold mt-1 text-[#3A7A18]">
                {forecast.total_generation.toFixed(1)} kWh
              </p>
            </div>
            <div className="bg-white rounded-xl border border-[#C8BFA8] p-4">
              <p className="text-xs text-[#8A7A60] uppercase">Peak Power</p>
              <p className="text-2xl font-semibold mt-1">
                {(forecast.generation[Math.max(...forecast.generation)] / 1000).toFixed(2)} kW
              </p>
            </div>
            <div className="bg-white rounded-xl border border-[#C8BFA8] p-4">
              <p className="text-xs text-[#8A7A60] uppercase">Avg Capacity Factor</p>
              <p className="text-2xl font-semibold mt-1">
                {(forecast.capacity_factor.reduce((a, b) => a + b, 0) / forecast.capacity_factor.length * 100).toFixed(1)}%
              </p>
            </div>
            <div className="bg-white rounded-xl border border-[#C8BFA8] p-4">
              <p className="text-xs text-[#8A7A60] uppercase">Period</p>
              <p className="text-lg font-semibold mt-1">
                {hours}h
              </p>
            </div>
          </div>

          {/* Generation Chart */}
          <div className="bg-white rounded-xl border border-[#C8BFA8] p-6">
            <h3 className="font-semibold mb-4">Solar Generation Forecast</h3>
            <div className="h-72">
              <Plot
                data={[
                  {
                    x: forecast.timestamps.map((t: string) => new Date(t).getHours()),
                    y: forecast.generation,
                    type: 'bar',
                    marker: { color: '#3A7A18' },
                    name: 'Generation (kW)',
                  },
                  {
                    x: forecast.timestamps.map((t: string) => new Date(t).getHours()),
                    y: forecast.irradiance,
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
                  y: forecast.temperature,
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
