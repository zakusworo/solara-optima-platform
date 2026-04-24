import { useState, useEffect } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { 
  Zap, 
  Sun, 
  Settings as SettingsIcon, 
  BarChart3, 
  Cpu,
  Menu,
  X,
  MapPin,
  Loader2
} from 'lucide-react'

interface GeoLocation {
  city: string
  country: string
  label: string
}

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const [userLocation, setUserLocation] = useState<GeoLocation | null>(null)
  const [locLoading, setLocLoading] = useState(true)

  useEffect(() => {
    detectLocation()
  }, [])

  async function detectLocation() {
    setLocLoading(true)
    
    // Try browser geolocation first
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const lat = pos.coords.latitude
          const lon = pos.coords.longitude
          try {
            // Reverse geocode with OpenStreetMap Nominatim (free, no API key)
            const resp = await fetch(
              `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=18&addressdetails=1`,
              { headers: { 'User-Agent': 'SolaraOptima/1.0' } }
            )
            const data = await resp.json()
            const addr = data.address
            const city = addr?.city || addr?.town || addr?.village || addr?.county || 'Local'
            const country = addr?.country_code?.toUpperCase() || addr?.country || 'ID'
            setUserLocation({ city, country, label: `${city}, ${country}` })
          } catch (err) {
            // Fallback to raw coordinates or backend default
            setUserLocation({
              city: lat.toFixed(1),
              country: lon.toFixed(1),
              label: `${lat.toFixed(2)}, ${lon.toFixed(2)}`
            })
          } finally {
            setLocLoading(false)
          }
        },
        async () => {
          // Geolocation denied → fallback to backend config
          await fetchBackendLocation()
        },
        { timeout: 8000, maximumAge: 600000 }
      )
    } else {
      // No browser geolocation → fallback
      await fetchBackendLocation()
    }
  }

  async function fetchBackendLocation() {
    try {
      const resp = await fetch('http://localhost:8000/api/v1/location/current')
      const data = await resp.json()
      setUserLocation({
        city: data?.city || 'Bandung',
        country: data?.country || 'ID',
        label: `${data?.city || 'Bandung'}, ${data?.country_code?.toUpperCase() || data?.country || 'ID'}`
      })
    } catch {
      // Ultimate fallback
      setUserLocation({ city: 'Bandung', country: 'ID', label: 'Bandung, ID' })
    } finally {
      setLocLoading(false)
    }
  }

  const navigation = [
    { name: 'Dashboard', href: '/', icon: BarChart3 },
    { name: 'Optimization', href: '/optimize', icon: Cpu },
    { name: 'Solar Forecast', href: '/solar', icon: Sun },
    { name: 'Generators', href: '/generators', icon: Zap },
    { name: 'Settings', href: '/settings', icon: SettingsIcon },
  ]

  return (
    <div className="min-h-screen bg-[#F5F0E8]">
      {/* Mobile sidebar button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-[#EDE8DC] border border-[#C8BFA8]"
      >
        {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Sidebar */}
      <aside className={`
        fixed top-0 left-0 z-40 h-screen w-64 
        bg-[#EDE8DC] border-r border-[#C8BFA8]
        transform transition-transform duration-200
        lg:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="h-full flex flex-col">
          {/* Logo */}
          <div className="h-14 flex items-center px-6 border-b border-[#C8BFA8]">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#3A7010] to-[#5A9E30] flex items-center justify-center">
                <Sun size={24} className="text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold">Solara Optima</h1>
                <div className="flex items-center gap-1 text-base text-[#8A7A60] font-mono">
                  {locLoading ? (
                    <>
                      <Loader2 size={14} className="animate-spin" />
                      <span className="text-sm">Locating...</span>
                    </>
                  ) : (
                    <>
                      <MapPin size={14} />
                      <span>{userLocation?.label || 'Bandung, ID'}</span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.href
              
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`
                    flex items-center gap-3 px-4 py-3 rounded-lg text-lg font-medium
                    transition-colors
                    ${isActive 
                      ? 'bg-[#3A7010] text-white' 
                      : 'text-[#5A4E3A] hover:bg-[#E4DDD0]'
                    }
                  `}
                >
                  <Icon size={24} />
                  {item.name}
                </Link>
              )
            })}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-[#C8BFA8]">
            <div className="text-xs text-[#8A7A60] font-mono">
              <p>v1.0.0</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="lg:ml-64 min-h-screen">
        <div className="p-6 lg:p-8">
          <Outlet />
        </div>
      </main>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  )
}
