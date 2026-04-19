import { useState } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { 
  Zap, 
  Sun, 
  Settings as SettingsIcon, 
  BarChart3, 
  Cpu,
  Menu,
  X
} from 'lucide-react'

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

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
                <Sun size={18} className="text-white" />
              </div>
              <div>
                <h1 className="text-sm font-semibold">Solar UC/ED</h1>
                <p className="text-xs text-[#8A7A60] font-mono">Bandung, ID</p>
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
                    flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium
                    transition-colors
                    ${isActive 
                      ? 'bg-[#3A7010] text-white' 
                      : 'text-[#5A4E3A] hover:bg-[#E4DDD0]'
                    }
                  `}
                >
                  <Icon size={18} />
                  {item.name}
                </Link>
              )
            })}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-[#C8BFA8]">
            <div className="text-xs text-[#8A7A60] font-mono">
              <p>v1.0.0</p>
              <p className="mt-1">Politeknik Energi & Pertambangan</p>
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
