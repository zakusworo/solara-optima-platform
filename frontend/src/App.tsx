import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Optimization from './pages/Optimization'
import SolarForecast from './pages/SolarForecast'
import Generators from './pages/Generators'
import Settings from './pages/Settings'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="optimize" element={<Optimization />} />
        <Route path="solar" element={<SolarForecast />} />
        <Route path="generators" element={<Generators />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App
