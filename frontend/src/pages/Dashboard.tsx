import { useQuery } from '@tanstack/react-query'
import { TrendingUp, Sun, Zap, Battery } from 'lucide-react'
import axios from 'axios'
import Plot from 'react-plotly.js'

export default function Dashboard() {
  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const response = await axios.get('http://localhost:8000/')
      return response.data
    },
  })

  const { data: solarResource } = useQuery({
    queryKey: ['solar-resource'],
    queryFn: async () => {
      const response = await axios.get('http://localhost:8000/api/v1/weather/solar-resource')
      return response.data.data
    },
  })

  const stats = [
    {
      name: 'Solar Resource',
      value: solarResource?.annual_irradiation || '—',
      unit: 'kWh/m²/year',
      icon: Sun,
      color: '#3A7A18',
    },
    {
      name: 'Optimal Tilt',
      value: solarResource?.optimal_tilt?.year_round?.toFixed(1) || '—',
      unit: 'degrees',
      icon: TrendingUp,
      color: '#A07010',
    },
    {
      name: 'Capacity Factor',
      value: (solarResource?.capacity_factor_estimate || 0) * 100,
      unit: '%',
      icon: Zap,
      color: '#5A7A30',
    },
    {
      name: 'Azimuth',
      value: solarResource?.optimal_azimuth || 0,
      unit: '° (North)',
      icon: Battery,
      color: '#4A8C20',
    },
  ]

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-semibold">Dashboard</h1>
        <p className="text-[#8A7A60] mt-2">
          Solar-optimized Unit Commitment & Economic Dispatch for Bandung, Indonesia
        </p>
      </div>

      {/* Status Banner */}
      {healthData && (
        <div className="bg-gradient-to-r from-[#3A7010] to-[#5A9E30] rounded-xl p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">{healthData.app}</h2>
              <p className="text-sm opacity-90 mt-1">
                Location: {healthData.location.latitude}°S, {healthData.location.longitude}°E
              </p>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold">{healthData.version}</p>
              <p className="text-sm opacity-90">System Ready</p>
            </div>
          </div>
        </div>
      )}

      {/* Solar Resource Stats */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Solar Resource Assessment</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat) => {
            const Icon = stat.icon
            return (
              <div
                key={stat.name}
                className="bg-white rounded-xl border border-[#C8BFA8] p-5"
              >
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: `${stat.color}20` }}
                  >
                    <Icon size={20} style={{ color: stat.color }} />
                  </div>
                  <div>
                    <p className="text-xs text-[#8A7A60] uppercase tracking-wide">
                      {stat.name}
                    </p>
                    <p className="text-xl font-semibold mt-0.5">
                      {stat.value}{' '}
                      <span className="text-sm text-[#8A7A60] font-normal">
                        {stat.unit}
                      </span>
                    </p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Monthly Solar Irradiance */}
      {solarResource?.monthly_averages && (
        <div className="bg-white rounded-xl border border-[#C8BFA8] p-6">
          <h3 className="font-semibold mb-4">Monthly Solar Irradiance</h3>
          <div className="h-64">
            <Plot
              data={[
                {
                  x: solarResource.monthly_averages.map(m => `Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec`.split(' ')[m.month - 1]),
                  y: solarResource.monthly_averages.map(m => m.ghi),
                  type: 'bar',
                  marker: { color: '#3A7A18' },
                  name: 'GHI (kWh/m²/day)',
                },
                {
                  x: solarResource.monthly_averages.map(m => `Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec`.split(' ')[m.month - 1]),
                  y: solarResource.monthly_averages.map(m => m.temp),
                  type: 'scatter',
                  mode: 'lines+markers',
                  line: { color: '#B04030', width: 2 },
                  marker: { size: 6 },
                  name: 'Temperature (°C)',
                  yaxis: 'y2',
                },
              ]}
              layout={{
                margin: { t: 20, b: 40, l: 50, r: 50 },
                xaxis: { tickangle: -45 },
                yaxis: { title: 'Irradiance (kWh/m²/day)' },
                yaxis2: {
                  title: 'Temperature (°C)',
                  overlaying: 'y',
                  side: 'right',
                },
                legend: { orientation: 'h', y: -0.2 },
                showlegend: true,
              }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <a
          href="/optimize"
          className="bg-white rounded-xl border border-[#C8BFA8] p-6 hover:border-[#3A7010] transition-colors group"
        >
          <h3 className="font-semibold group-hover:text-[#3A7010]">Run Optimization</h3>
          <p className="text-sm text-[#8A7A60] mt-2">
            Optimize generator dispatch with solar and battery integration
          </p>
        </a>
        <a
          href="/solar"
          className="bg-white rounded-xl border border-[#C8BFA8] p-6 hover:border-[#3A7010] transition-colors group"
        >
          <h3 className="font-semibold group-hover:text-[#3A7010]">Solar Forecast</h3>
          <p className="text-sm text-[#8A7A60] mt-2">
            Generate PV generation forecasts using pvlib and weather data
          </p>
        </a>
        <a
          href="/generators"
          className="bg-white rounded-xl border border-[#C8BFA8] p-6 hover:border-[#3A7010] transition-colors group"
        >
          <h3 className="font-semibold group-hover:text-[#3A7010]">Generator Fleet</h3>
          <p className="text-sm text-[#8A7A60] mt-2">
            Configure generators with Indonesian market presets
          </p>
        </a>
      </div>
    </div>
  )
}
