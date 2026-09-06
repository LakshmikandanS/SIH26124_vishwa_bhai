/**
 * App.tsx — Root component
 * Orchestrates state, WebSocket, REST, page routing, and layout
 */

import { useState, useCallback, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import CommandCenter from './pages/CommandCenter'
import FleetTracking from './pages/FleetTracking'
import VideoIntelligence from './pages/VideoIntelligence'
import UrbanEvents from './pages/UrbanEvents'
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'
import { useWebSocket } from './hooks/useWebSocket'
import { useRestApi } from './hooks/useRestApi'
import type { Vehicle, DefectMarker, AlertEvent, PageId } from './types'
import './index.css'

function updateVehicle(prev: Vehicle[], updated: Vehicle): Vehicle[] {
  const idx = prev.findIndex(v => v.bus_id === updated.bus_id)
  if (idx >= 0) {
    const next = [...prev]
    next[idx] = { ...updated, last_seen: Date.now() }
    return next
  }
  return [...prev, { ...updated, last_seen: Date.now() }]
}

function updateDefect(prev: DefectMarker[], updated: DefectMarker): DefectMarker[] {
  const idx = prev.findIndex(d => d.defect_id === updated.defect_id)
  if (idx >= 0) {
    const next = [...prev]
    next[idx] = updated
    return next
  }
  return prev
}

function App() {
  const [activePage, setActivePage] = useState<PageId>('command')

  // Seed from REST on load
  const { vehicles: initVehicles, defects: initDefects, health } = useRestApi()
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [defects, setDefects] = useState<DefectMarker[]>([])
  const [alerts, setAlerts] = useState<AlertEvent[]>([])

  // Sync REST seed into state once loaded
  useEffect(() => {
    if (initVehicles.length > 0) setVehicles(initVehicles)
    if (initDefects.length > 0) setDefects(initDefects)
  }, [initVehicles, initDefects])

  const handleVehicleMoved = useCallback((data: Vehicle) => {
    setVehicles(prev => updateVehicle(prev, data))
  }, [])

  const handleDefectNew = useCallback((data: DefectMarker) => {
    setDefects(prev => {
      if (prev.find(d => d.defect_id === data.defect_id)) return prev
      return [...prev, data]
    })
    setAlerts(prev => [{ ...data, received_at: Date.now() }, ...prev].slice(0, 100))
  }, [])

  const handleDefectUpdated = useCallback((data: DefectMarker) => {
    setDefects(prev => updateDefect(prev, data))
  }, [])

  const { isConnected } = useWebSocket({
    onVehicleMoved: handleVehicleMoved,
    onDefectNew: handleDefectNew,
    onDefectUpdated: handleDefectUpdated,
  })

  const handleClearAlerts = useCallback(() => setAlerts([]), [])

  const pageProps = { vehicles, defects, health, isConnected }

  return (
    <div className="app-root">
      <Sidebar
        activePage={activePage}
        onNavigate={setActivePage}
        defectCount={defects.length}
        vehicleCount={vehicles.length}
        isConnected={isConnected}
      />
      <main className="app-main">
        {activePage === 'command' && (
          <CommandCenter {...pageProps} alerts={alerts} onClearAlerts={handleClearAlerts} />
        )}
        {activePage === 'fleet' && (
          <FleetTracking vehicles={vehicles} defects={defects} />
        )}
        {activePage === 'video' && (
          <VideoIntelligence defects={defects} vehicles={vehicles} alerts={alerts} isConnected={isConnected} />
        )}
        {activePage === 'events' && (
          <UrbanEvents defects={defects} vehicles={vehicles} alerts={alerts} isConnected={isConnected} />
        )}
        {activePage === 'analytics' && (
          <Analytics defects={defects} vehicles={vehicles} health={health} isConnected={isConnected} />
        )}
        {activePage === 'settings' && (
          <Settings />
        )}
      </main>
    </div>
  )
}

export default App
