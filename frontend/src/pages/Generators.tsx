import { useQuery } from '@tanstack/react-query'
import { Zap, Plus, Edit, Trash2 } from 'lucide-react'
import axios from 'axios'

export default function Generators() {
  const { data: templatesData } = useQuery({
    queryKey: ['generator-templates'],
    queryFn: async () => {
      const response = await axios.get('http://localhost:8000/api/v1/generators/templates')
      return response.data
    },
  })

  const { data: presetsData } = useQuery({
    queryKey: ['indonesia-presets'],
    queryFn: async () => {
      const response = await axios.get('http://localhost:8000/api/v1/generators/presets/indonesia')
      return response.data
    },
  })

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Generator Fleet</h1>
        <p className="text-[#8A7A60] mt-1">
          Configure generators with Indonesian market presets and custom configurations
        </p>
      </div>

      {/* Generator Templates */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Generator Templates</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templatesData?.data?.map((template: any) => (
            <div
              key={template.id}
              className="bg-white rounded-xl border border-[#C8BFA8] p-5 hover:border-[#3A7010] transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-[#F5F0E8] flex items-center justify-center">
                    <Zap size={20} className="text-[#A07010]" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{template.name}</h3>
                    <p className="text-xs text-[#8A7A60]">{template.fuel_type}</p>
                  </div>
                </div>
              </div>

              <div className="mt-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-[#8A7A60]">Output</span>
                  <span className="font-mono">{template.min_output}-{template.max_output} kW</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#8A7A60]">Ramp Rate</span>
                  <span className="font-mono">{template.ramp_up} kW/h</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#8A7A60]">Fuel Cost</span>
                  <span className="font-mono">Rp {template.fuel_cost}/kWh</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#8A7A60]">Emissions</span>
                  <span className="font-mono">{template.emissions_rate} kg/kWh</span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-[#C8BFA8] flex gap-2">
                <button className="flex-1 px-3 py-2 text-sm bg-[#F5F0E8] rounded-lg hover:bg-[#E4DDD0]">
                  Use Template
                </button>
                <button className="px-3 py-2 text-sm bg-[#F5F0E8] rounded-lg hover:bg-[#E4DDD0]">
                  <Edit size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Indonesia Presets */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Indonesian Market Presets</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {presetsData?.data && Object.entries(presetsData.data).map(([key, preset]: [string, any]) => (
            <div
              key={key}
              className="bg-white rounded-xl border border-[#C8BFA8] p-5"
            >
              <h3 className="font-semibold">{preset.name}</h3>
              <p className="text-sm text-[#8A7A60] mt-1">{preset.description}</p>

              <div className="mt-4 flex flex-wrap gap-2">
                <span className="px-3 py-1 bg-[#F5F0E8] rounded-full text-xs font-mono">
                  {preset.generators.length} Generators
                </span>
                <span className="px-3 py-1 bg-[#F5F0E8] rounded-full text-xs font-mono text-[#3A7A18]">
                  {preset.solar_capacity}kW Solar
                </span>
                <span className="px-3 py-1 bg-[#F5F0E8] rounded-full text-xs font-mono text-[#5A7A30]">
                  {preset.battery_capacity}kWh Battery
                </span>
              </div>

              <button className="mt-4 w-full px-4 py-2 bg-[#3A7010] text-white rounded-lg text-sm font-medium hover:bg-[#2D6010]">
                Load Preset
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Custom Generator */}
      <div className="bg-white rounded-xl border border-[#C8BFA8] p-6">
        <h2 className="font-semibold mb-4">Add Custom Generator</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-sm font-medium">Generator Name</label>
            <input
              type="text"
              placeholder="e.g., Gas Turbine 2"
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Fuel Type</label>
            <select className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]">
              <option>Natural Gas</option>
              <option>Diesel</option>
              <option>Coal</option>
              <option>Biomass</option>
              <option>Biogas</option>
            </select>
          </div>
          <div>
            <label className="text-sm font-medium">Max Output (kW)</label>
            <input
              type="number"
              placeholder="100"
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
            />
          </div>
        </div>
        <button className="mt-4 flex items-center gap-2 px-6 py-2 bg-[#F5F0E8] rounded-lg hover:bg-[#E4DDD0]">
          <Plus size={18} />
          Add Generator
        </button>
      </div>
    </div>
  )
}
