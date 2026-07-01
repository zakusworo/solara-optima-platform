import { lazy } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'

// Route-level code splitting: each page is its own chunk, fetched on
// navigation. The Suspense boundary lives in Layout (around <Outlet/>), so
// the sidebar stays mounted while a page chunk loads.
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Marketplace = lazy(() => import('./pages/Marketplace'))
const Optimization = lazy(() => import('./pages/Optimization'))
const SolarForecast = lazy(() => import('./pages/SolarForecast'))
const Generators = lazy(() => import('./pages/Generators'))
const Settings = lazy(() => import('./pages/Settings'))

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="marketplace" element={<Marketplace />} />
        <Route path="optimize" element={<Optimization />} />
        <Route path="solar" element={<SolarForecast />} />
        <Route path="generators" element={<Generators />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App