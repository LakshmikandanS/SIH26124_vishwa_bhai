/**
 * FleetTracking — Suradak Screen 2
 * - Shows ONLY real vehicles from live data (no hardcoded bus list)
 * - Fixes overlapping HUD and bare-data issues
 * - Selected bus HUD appears as a proper overlay, not floating over the map
 */

import React, { useState, useEffect } from 'react'
import MapView from '../components/MapView'
import type { Vehicle, DefectMarker } from '../types'
import { ROUTE_17_STOPS, FLEET_DETAILS_MOCK } from '../data/routeData'
import { Search, Gauge, Clock, MapPin, Wifi, WifiOff } from 'lucide-react'

interface FleetTrackingProps {
  vehicles: Vehicle[]
  defects: DefectMarker[]
}

function getBusDisplayId(busId: string): string {
  // bus_1 → BUS-101, bus_2 → BUS-102, etc.
  const match = busId.match(/\d+/)
  if (match) return `BUS-${100 + parseInt(match[0])}`
  return busId.toUpperCase()
}

function getBusColor(busId: string): string {
  const colors = ['#10b981', '#3b82f6', '#a855f7', '#f97316', '#06b6d4', '#f43f5e']
  const match = busId.match(/\d+/)
  const idx = match ? (parseInt(match[0]) - 1) % colors.length : 0
  return colors[idx]
}

function getStatusLabel(v: Vehicle): { text: string; cls: string } {
  if (!v.last_seen) return { text: 'ON ROUTE', cls: 'green' }
  const stale = Date.now() - v.last_seen > 60_000
  if (stale) return { text: 'IDLE', cls: 'amber' }
  return { text: 'ON ROUTE', cls: 'green' }
}

export default function FleetTracking({ vehicles, defects }: FleetTrackingProps) {
  const [selectedBusId, setSelectedBusId] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [liveTime, setLiveTime] = useState('')

  useEffect(() => {
    const t = setInterval(() => setLiveTime(new Date().toLocaleTimeString('en-US', { hour12: true })), 1000)
    setLiveTime(new Date().toLocaleTimeString('en-US', { hour12: true }))
    return () => clearInterval(t)
  }, [])

  // Auto-select first real bus
  useEffect(() => {
    if (vehicles.length > 0 && !selectedBusId) {
      setSelectedBusId(vehicles[0].bus_id)
    }
  }, [vehicles.length])

  const filteredVehicles = vehicles.filter(v =>
    getBusDisplayId(v.bus_id).toLowerCase().includes(searchQuery.toLowerCase())
  )

  const selectedVehicle = vehicles.find(v => v.bus_id === selectedBusId) ?? vehicles[0] ?? null

  // Bus-specific defects count
  const busDefects = defects.filter(d => d.bus_id === selectedBusId)
  const hudMeta = FLEET_DETAILS_MOCK[selectedBusId ?? ''] ?? FLEET_DETAILS_MOCK['bus_1']

  return (
    <div className="routesense-page fleet-tracking-view">
      {/* Header */}
      <header className="routesense-page-header">
        <div className="header-left">
          <h2 className="header-main-title">Fleet Tracking</h2>
          <p className="header-subtitle">
            {vehicles.length > 0
              ? `${vehicles.length} bus${vehicles.length > 1 ? 'es' : ''} active`
              : 'Waiting for buses to connect...'}
          </p>
        </div>
        <div className="header-right-meta">
          <div className="live-status-chip">
            <span className="live-dot-green"></span>
            <span className="live-text">LIVE</span>
          </div>
          <div className="live-clock-text">{liveTime}</div>
          <div className="header-user-avatar">RK</div>
        </div>
      </header>

      {/* Main Layout: Left Bus List + Right Map (fixed height, no overflow) */}
      <div className="fleet-main-split" style={{ flex: 1, minHeight: 0 }}>
        {/* Left Bus List */}
        <div className="fleet-sidebar-panel">
          <div className="fleet-search-bar">
            <Search size={15} color="#64748b" />
            <input
              type="text"
              placeholder="Search Bus ID..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="fleet-search-input"
            />
          </div>

          <div style={{ padding: '6px 12px', fontSize: 11, color: '#64748b', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
            {vehicles.length} active bus{vehicles.length !== 1 ? 'es' : ''} · {defects.length} defects
          </div>

          <div className="fleet-bus-cards-scroll">
            {filteredVehicles.length === 0 ? (
              <div style={{ padding: 20, textAlign: 'center', color: '#475569', fontSize: 13 }}>
                {vehicles.length === 0
                  ? 'No buses online yet. Start the edge emulator.'
                  : 'No buses match search.'}
              </div>
            ) : filteredVehicles.map(v => {
              const isSelected = selectedBusId === v.bus_id
              const status = getStatusLabel(v)
              const color = getBusColor(v.bus_id)
              const displayId = getBusDisplayId(v.bus_id)
              const myDefects = defects.filter(d => d.bus_id === v.bus_id).length

              return (
                <div
                  key={v.bus_id}
                  className={`fleet-bus-item-card ${isSelected ? 'active' : ''}`}
                  onClick={() => setSelectedBusId(v.bus_id)}
                >
                  <div className="bus-item-header">
                    <div className="bus-item-title-row">
                      <span className="bus-item-badge" style={{ borderColor: color, color }}>
                        🚌 {displayId}
                      </span>
                      <span className={`bus-status-tag ${status.cls}`}>{status.text}</span>
                    </div>
                    <div style={{ display: 'flex', gap: 8, marginTop: 2 }}>
                      <span style={{ fontSize: 10, color: '#64748b', fontFamily: 'monospace' }}>
                        {v.latitude.toFixed(4)}, {v.longitude.toFixed(4)}
                      </span>
                    </div>
                  </div>
                  <div className="bus-item-metrics">
                    <div className="bus-metric-chip">
                      <Gauge size={12} />
                      <span>{v.speed_kmh ?? '—'} km/h</span>
                    </div>
                    {myDefects > 0 && (
                      <div className="bus-metric-chip" style={{ color: '#f59e0b' }}>
                        <span>⚠️ {myDefects} defect{myDefects > 1 ? 's' : ''}</span>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Right Map and Docked HUD Panel */}
        <div className="fleet-map-and-hud">
          <div style={{ flex: 1, minHeight: 0, position: 'relative', borderRadius: 12, overflow: 'hidden', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
            <MapView
              vehicles={vehicles}
              defects={defects}
              showHexOverlay={false}
              selectedBusId={selectedBusId}
              onSelectBus={id => id && setSelectedBusId(id)}
            />
          </div>

          {/* Selected Bus HUD — Cleanly styled acrylic card docked at bottom */}
          {selectedVehicle && (
            <div className="fleet-bottom-hud-card">
              <div className="hud-top-bar">
                <div className="hud-bus-title-row">
                  <span className="hud-bus-name" style={{ color: getBusColor(selectedVehicle.bus_id) }}>
                    🚌 {getBusDisplayId(selectedVehicle.bus_id)}
                  </span>
                  <span className="hud-route-tag">
                    {hudMeta.route}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                  <span style={{ fontSize: 11, fontFamily: 'monospace', color: '#64748b' }}>
                    {selectedVehicle.latitude.toFixed(5)}, {selectedVehicle.longitude.toFixed(5)}
                  </span>
                  <span className="bus-status-tag green">● LIVE</span>
                </div>
              </div>

              <div className="hud-metrics-row">
                <div className="hud-metric-box">
                  <span className="hud-metric-label">Speed</span>
                  <span className="hud-metric-val">{selectedVehicle.speed_kmh ?? hudMeta.speed} km/h</span>
                </div>
                <div className="hud-metric-box">
                  <span className="hud-metric-label">ETA Next Stop</span>
                  <span className="hud-metric-val">{hudMeta.eta} min</span>
                </div>
                <div className="hud-metric-box">
                  <span className="hud-metric-label">Distance</span>
                  <span className="hud-metric-val">{hudMeta.dist}</span>
                </div>
                <div className="hud-metric-box">
                  <span className="hud-metric-label">Next Stop</span>
                  <span className="hud-metric-val">{selectedVehicle.next_stop ?? hudMeta.next}</span>
                </div>
                <div className="hud-metric-box">
                  <span className="hud-metric-label">Defects Detected</span>
                  <span className="hud-metric-val" style={{ color: busDefects.length > 0 ? '#f59e0b' : '#10b981' }}>
                    {busDefects.length}
                  </span>
                </div>
              </div>

              {/* Station Progression Timeline */}
              <div className="station-progress-timeline">
                <div className="station-timeline-line">
                  <div className="station-timeline-line-fill" style={{ width: '40%' }}></div>
                </div>
                {ROUTE_17_STOPS.map(st => (
                  <div key={st.name} className={`timeline-station-node ${st.passed ? 'completed' : ''} ${st.current ? 'current' : ''}`}>
                    <div className="station-node-dot"></div>
                    <div className="station-node-name">{st.name}</div>
                    <div className="station-node-time">{st.time}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
