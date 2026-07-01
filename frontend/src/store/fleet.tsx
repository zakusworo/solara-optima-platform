import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'

/**
 * Shared generator-fleet + system (solar/battery) configuration.
 *
 * The Generators page edits this state (load a preset, add from a template,
 * add/edit/remove custom generators); the Optimization page consumes it so the
 * dispatch run and dashboard reflect what the user actually configured —
 * instead of a hardcoded fleet. Persisted to localStorage so it survives
 * reloads.
 */

export interface FleetGenerator {
  uid: string
  name: string
  fuel_type: string
  min_output: number
  max_output: number
  ramp_up: number
  ramp_down: number
  min_uptime: number
  min_downtime: number
  initial_status: number // 0 | 1
  initial_output: number
  startup_cost: number
  shutdown_cost: number
  no_load_cost: number
  fuel_cost: number
  emissions_rate: number
}

export interface SystemConfig {
  solarCapacityKw: number
  batteryCapacityKwh: number
  batteryPowerKw: number
}

export interface ApiGenerator
  extends Omit<FleetGenerator, 'uid'> {
  generator_id: number
}

interface FleetContextValue {
  generators: FleetGenerator[]
  system: SystemConfig
  loadPreset: (preset: PresetPayload) => void
  addFromTemplate: (tpl: TemplatePayload) => void
  addCustom: (g: { name: string; fuel_type: string; max_output: number }) => void
  updateGenerator: (uid: string, patch: Partial<FleetGenerator>) => void
  removeGenerator: (uid: string) => void
  clearFleet: () => void
  setSystem: (patch: Partial<SystemConfig>) => void
}

interface PresetPayload {
  generators: Array<
    Partial<FleetGenerator> & {
      name: string
      fuel_type: string
      min_output: number
      max_output: number
      ramp_up: number
      ramp_down: number
      min_uptime: number
      min_downtime: number
      startup_cost: number
      no_load_cost: number
      fuel_cost: number
      emissions_rate: number
    }
  >
  solar_capacity: number
  battery_capacity: number
}

interface TemplatePayload {
  name: string
  fuel_type?: string
  min_output?: number
  max_output?: number
  ramp_up?: number
  ramp_down?: number
  min_uptime?: number
  min_downtime?: number
  startup_cost?: number
  shutdown_cost?: number
  no_load_cost?: number
  fuel_cost?: number
  emissions_rate?: number
}

const STORAGE_KEY = 'solara-fleet-v1'

const newUid = (): string =>
  typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID()
    : `g${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`

// Default fleet mirrors the "Industrial Cogeneration" preset so the
// Optimization page works out of the box; loading any preset replaces it.
const DEFAULT_FLEET: FleetGenerator[] = [
  {
    uid: newUid(),
    name: 'Gas Turbine',
    fuel_type: 'Natural Gas',
    min_output: 10,
    max_output: 100,
    ramp_up: 50,
    ramp_down: 50,
    min_uptime: 2,
    min_downtime: 2,
    initial_status: 1,
    initial_output: 10,
    startup_cost: 500000,
    shutdown_cost: 0,
    no_load_cost: 50000,
    fuel_cost: 800,
    emissions_rate: 0.45,
  },
  {
    uid: newUid(),
    name: 'Medium Diesel Generator',
    fuel_type: 'Diesel',
    min_output: 50,
    max_output: 200,
    ramp_up: 50,
    ramp_down: 50,
    min_uptime: 2,
    min_downtime: 2,
    initial_status: 0,
    initial_output: 0,
    startup_cost: 300000,
    shutdown_cost: 0,
    no_load_cost: 75000,
    fuel_cost: 1100,
    emissions_rate: 0.65,
  },
]

const DEFAULT_SYSTEM: SystemConfig = {
  solarCapacityKw: 50,
  batteryCapacityKwh: 100,
  batteryPowerKw: 50,
}

const FleetContext = createContext<FleetContextValue | null>(null)

export function FleetProvider({ children }: { children: ReactNode }) {
  const [generators, setGenerators] = useState<FleetGenerator[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed.generators) && parsed.generators.length > 0) {
          return parsed.generators as FleetGenerator[]
        }
      }
    } catch {
      /* ignore corrupt cache */
    }
    return DEFAULT_FLEET
  })

  const [system, setSystemState] = useState<SystemConfig>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        if (parsed.system) return { ...DEFAULT_SYSTEM, ...parsed.system }
      }
    } catch {
      /* ignore */
    }
    return DEFAULT_SYSTEM
  })

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ generators, system }))
    } catch {
      /* storage full / disabled */
    }
  }, [generators, system])

  const loadPreset = (preset: PresetPayload) => {
    const gens: FleetGenerator[] = (preset.generators || []).map((g, i) => ({
      uid: newUid(),
      name: g.name,
      fuel_type: g.fuel_type,
      min_output: g.min_output,
      max_output: g.max_output,
      ramp_up: g.ramp_up,
      ramp_down: g.ramp_down,
      min_uptime: g.min_uptime,
      min_downtime: g.min_downtime,
      // One generator online to meet baseload (avoids a t=0 cold start);
      // presets don't carry initial state, so default it.
      initial_status: g.initial_status ?? (i === 0 ? 1 : 0),
      initial_output: g.initial_output ?? (i === 0 ? g.min_output : 0),
      startup_cost: g.startup_cost,
      shutdown_cost: g.shutdown_cost ?? 0,
      no_load_cost: g.no_load_cost,
      fuel_cost: g.fuel_cost,
      emissions_rate: g.emissions_rate,
    }))
    setGenerators(gens)
    setSystemState({
      solarCapacityKw: preset.solar_capacity ?? 0,
      batteryCapacityKwh: preset.battery_capacity ?? 0,
      batteryPowerKw: Math.round((preset.battery_capacity ?? 0) / 2),
    })
  }

  const addFromTemplate = (tpl: TemplatePayload) => {
    const g: FleetGenerator = {
      uid: newUid(),
      name: tpl.name,
      fuel_type: tpl.fuel_type ?? 'Natural Gas',
      min_output: tpl.min_output ?? 10,
      max_output: tpl.max_output ?? 100,
      ramp_up: tpl.ramp_up ?? 50,
      ramp_down: tpl.ramp_down ?? 50,
      min_uptime: tpl.min_uptime ?? 1,
      min_downtime: tpl.min_downtime ?? 1,
      initial_status: 0,
      initial_output: 0,
      startup_cost: tpl.startup_cost ?? 100000,
      shutdown_cost: tpl.shutdown_cost ?? 0,
      no_load_cost: tpl.no_load_cost ?? 25000,
      fuel_cost: tpl.fuel_cost ?? 1000,
      emissions_rate: tpl.emissions_rate ?? 0.6,
    }
    setGenerators((prev) => [...prev, g])
  }

  const addCustom = ({
    name,
    fuel_type,
    max_output,
  }: {
    name: string
    fuel_type: string
    max_output: number
  }) => {
    if (!name.trim() || !max_output || max_output <= 0) return
    const min = Math.max(1, Math.round(max_output * 0.1))
    const g: FleetGenerator = {
      uid: newUid(),
      name: name.trim(),
      fuel_type,
      min_output: min,
      max_output,
      ramp_up: Math.round(max_output / 2),
      ramp_down: Math.round(max_output / 2),
      min_uptime: 1,
      min_downtime: 1,
      initial_status: 0,
      initial_output: 0,
      startup_cost: 100000,
      shutdown_cost: 0,
      no_load_cost: 25000,
      fuel_cost: 1000,
      emissions_rate: 0.6,
    }
    setGenerators((prev) => [...prev, g])
  }

  const updateGenerator = (uid: string, patch: Partial<FleetGenerator>) =>
    setGenerators((prev) =>
      prev.map((g) => (g.uid === uid ? { ...g, ...patch } : g)),
    )

  const removeGenerator = (uid: string) =>
    setGenerators((prev) => prev.filter((g) => g.uid !== uid))

  const clearFleet = () => setGenerators([])

  const setSystem = (patch: Partial<SystemConfig>) =>
    setSystemState((prev) => ({ ...prev, ...patch }))

  return (
    <FleetContext.Provider
      value={{
        generators,
        system,
        loadPreset,
        addFromTemplate,
        addCustom,
        updateGenerator,
        removeGenerator,
        clearFleet,
        setSystem,
      }}
    >
      {children}
    </FleetContext.Provider>
  )
}

export function useFleet(): FleetContextValue {
  const ctx = useContext(FleetContext)
  if (!ctx) throw new Error('useFleet must be used within a FleetProvider')
  return ctx
}

/** Map the UI fleet to the API's GeneratorData[] (assigns generator_id). */
export function fleetToApiGenerators(fleet: FleetGenerator[]): ApiGenerator[] {
  return fleet.map((g, i) => ({
    generator_id: i + 1,
    name: g.name,
    fuel_type: g.fuel_type,
    min_output: g.min_output,
    max_output: g.max_output,
    ramp_up: g.ramp_up,
    ramp_down: g.ramp_down,
    min_uptime: g.min_uptime,
    min_downtime: g.min_downtime,
    initial_status: g.initial_status,
    initial_output: g.initial_output,
    startup_cost: g.startup_cost,
    shutdown_cost: g.shutdown_cost,
    no_load_cost: g.no_load_cost,
    fuel_cost: g.fuel_cost,
    emissions_rate: g.emissions_rate,
  }))
}