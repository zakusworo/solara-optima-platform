import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Zap, Plus, Trash2, Sun, Battery, Layers } from 'lucide-react'
import { api } from '../utils/api'
import { useFleet } from '../store/fleet'

export default function Generators() {
  const {
    generators,
    system,
    loadPreset,
    addFromTemplate,
    addCustom,
    updateGenerator,
    removeGenerator,
    clearFleet,
    setSystem,
  } = useFleet()

  const { data: templatesData } = useQuery({
    queryKey: ['generator-templates'],
    queryFn: async () => {
      const response = await api.get('/api/v1/generators/templates')
      return response.data
    },
  })

  const { data: presetsData } = useQuery({
    queryKey: ['indonesia-presets'],
    queryFn: async () => {
      const response = await api.get('/api/v1/generators/presets/indonesia')
      return response.data
    },
  })

  // Custom generator form (controlled)
  const [customName, setCustomName] = useState('')
  const [customFuel, setCustomFuel] = useState('Natural Gas')
  const [customMax, setCustomMax] = useState('')

  const handleAddCustom = () => {
    addCustom({
      name: customName,
      fuel_type: customFuel,
      max_output: parseFloat(customMax) || 0,
    })
    setCustomName('')
    setCustomMax('')
  }

  const num = (v: string) => parseFloat(v) || 0

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Generator Fleet</h1>
        <p className="text-[#8A7A60] mt-1">
          Configure generators with Indonesian market presets and custom configurations.
          Your fleet here drives the Optimization page.
        </p>
      </div>

      {/* Current Fleet (shared state consumed by Optimization) */}
      <div className="bg-white rounded-xl border border-[#C8BFA8] p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold flex items-center gap-2">
            <Layers size={18} className="text-[#3A7010]" />
            Current Fleet
            <span className="text-sm font-normal text-[#8A7A60]">
              ({generators.length} generator{generators.length === 1 ? '' : 's'})
            </span>
          </h2>
          <button
            onClick={clearFleet}
            disabled={generators.length === 0}
            className="text-sm px-3 py-1.5 bg-[#F5F0E8] rounded-lg hover:bg-[#E4DDD0] disabled:opacity-50"
          >
            Clear Fleet
          </button>
        </div>

        {generators.length === 0 ? (
          <p className="text-sm text-[#8A7A60] py-6 text-center">
            No generators configured. Load a preset below or add a custom generator.
          </p>
        ) : (
          <div className="space-y-2">
            {generators.map((g) => (
              <div
                key={g.uid}
                className="grid grid-cols-1 md:grid-cols-12 gap-2 items-center bg-[#F5F0E8] rounded-lg p-3"
              >
                <div className="md:col-span-3">
                  <label className="text-[10px] text-[#8A7A60] uppercase tracking-wide">Name</label>
                  <input
                    type="text"
                    value={g.name}
                    onChange={(e) => updateGenerator(g.uid, { name: e.target.value })}
                    className="w-full px-2 py-1 text-sm border border-[#C8BFA8] rounded-md focus:ring-1 focus:ring-[#3A7010] outline-none"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="text-[10px] text-[#8A7A60] uppercase tracking-wide">Fuel</label>
                  <select
                    value={g.fuel_type}
                    onChange={(e) => updateGenerator(g.uid, { fuel_type: e.target.value })}
                    className="w-full px-2 py-1 text-sm border border-[#C8BFA8] rounded-md focus:ring-1 focus:ring-[#3A7010] outline-none"
                  >
                    {['Natural Gas', 'Diesel', 'Coal', 'Biomass', 'Biogas'].map((f) => (
                      <option key={f}>{f}</option>
                    ))}
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="text-[10px] text-[#8A7A60] uppercase tracking-wide">Min kW</label>
                  <input
                    type="number"
                    min={0}
                    value={g.min_output}
                    onChange={(e) => updateGenerator(g.uid, { min_output: num(e.target.value) })}
                    className="w-full px-2 py-1 text-sm border border-[#C8BFA8] rounded-md focus:ring-1 focus:ring-[#3A7010] outline-none text-right font-mono"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="text-[10px] text-[#8A7A60] uppercase tracking-wide">Max kW</label>
                  <input
                    type="number"
                    min={0}
                    value={g.max_output}
                    onChange={(e) => updateGenerator(g.uid, { max_output: num(e.target.value) })}
                    className="w-full px-2 py-1 text-sm border border-[#C8BFA8] rounded-md focus:ring-1 focus:ring-[#3A7010] outline-none text-right font-mono"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="text-[10px] text-[#8A7A60] uppercase tracking-wide">Rp/kWh</label>
                  <input
                    type="number"
                    min={0}
                    value={g.fuel_cost}
                    onChange={(e) => updateGenerator(g.uid, { fuel_cost: num(e.target.value) })}
                    className="w-full px-2 py-1 text-sm border border-[#C8BFA8] rounded-md focus:ring-1 focus:ring-[#3A7010] outline-none text-right font-mono"
                  />
                </div>
                <div className="md:col-span-1 flex md:justify-end">
                  <button
                    onClick={() => removeGenerator(g.uid)}
                    className="p-2 text-[#B04030] hover:bg-[#B04030]/10 rounded-lg"
                    title="Remove generator"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* System config (solar / battery) */}
        <div className="mt-4 pt-4 border-t border-[#C8BFA8] grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center gap-3">
            <Sun size={18} className="text-[#3A7A18]" />
            <div className="flex-1">
              <label className="text-xs text-[#8A7A60]">Solar PV (kW)</label>
              <input
                type="number"
                min={0}
                value={system.solarCapacityKw}
                onChange={(e) => setSystem({ solarCapacityKw: num(e.target.value) })}
                className="w-full px-2 py-1 text-sm border border-[#C8BFA8] rounded-md focus:ring-1 focus:ring-[#3A7010] outline-none text-right font-mono"
              />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Battery size={18} className="text-[#5A7A30]" />
            <div className="flex-1">
              <label className="text-xs text-[#8A7A60]">Battery (kWh)</label>
              <input
                type="number"
                min={0}
                value={system.batteryCapacityKwh}
                onChange={(e) =>
                  setSystem({
                    batteryCapacityKwh: num(e.target.value),
                    batteryPowerKw: Math.round(num(e.target.value) / 2),
                  })
                }
                className="w-full px-2 py-1 text-sm border border-[#C8BFA8] rounded-md focus:ring-1 focus:ring-[#3A7010] outline-none text-right font-mono"
              />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Zap size={18} className="text-[#A07010]" />
            <div className="flex-1">
              <label className="text-xs text-[#8A7A60]">Battery Power (kW)</label>
              <input
                type="number"
                min={0}
                value={system.batteryPowerKw}
                onChange={(e) => setSystem({ batteryPowerKw: num(e.target.value) })}
                className="w-full px-2 py-1 text-sm border border-[#C8BFA8] rounded-md focus:ring-1 focus:ring-[#3A7010] outline-none text-right font-mono"
              />
            </div>
          </div>
        </div>
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

              <div className="mt-4 pt-4 border-t border-[#C8BFA8]">
                <button
                  onClick={() => addFromTemplate(template)}
                  className="w-full px-3 py-2 text-sm bg-[#3A7010] text-white rounded-lg hover:bg-[#2D6010]"
                >
                  Add to Fleet
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
          {presetsData?.data &&
            Object.entries(presetsData.data).map(([key, preset]: [string, any]) => (
              <div key={key} className="bg-white rounded-xl border border-[#C8BFA8] p-5">
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

                <button
                  onClick={() => loadPreset(preset)}
                  className="mt-4 w-full px-4 py-2 bg-[#3A7010] text-white rounded-lg text-sm font-medium hover:bg-[#2D6010]"
                >
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
              value={customName}
              onChange={(e) => setCustomName(e.target.value)}
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Fuel Type</label>
            <select
              value={customFuel}
              onChange={(e) => setCustomFuel(e.target.value)}
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
            >
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
              value={customMax}
              onChange={(e) => setCustomMax(e.target.value)}
              className="mt-1 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
            />
          </div>
        </div>
        <button
          onClick={handleAddCustom}
          className="mt-4 flex items-center gap-2 px-6 py-2 bg-[#3A7010] text-white rounded-lg hover:bg-[#2D6010]"
        >
          <Plus size={18} />
          Add Generator
        </button>
      </div>
    </div>
  )
}