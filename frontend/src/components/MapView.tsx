/**
 * MapView — RouteSense Electric Midnight-Neon Map
 * Features:
 *   - Deep space-navy basemap with electric cyan/blue glowing road traces
 *   - Neon Pill bus markers (BUS-101, BUS-102) with live pulsing LEDs
 *   - Glowing route trajectory polyline & stop waypoint nodes
 *   - Hazard markers with animated radar pulse rings
 *   - H3 hexagonal density matrix
 *   - Floating glass acrylic legend & filter controls
 */

import { useEffect, useMemo, useRef, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, CircleMarker, useMap } from 'react-leaflet'
import L from 'leaflet'
import { latLngToCell } from 'h3-js'
import H3HexLayer from './H3HexLayer'
import type { Vehicle, DefectMarker } from '../types'
import { getSeverity, getSeverityColor, formatObjectType, formatTime } from '../types'
import { ROUTE_17_WAYPOINTS } from '../data/routeData'

// Custom neon pill bus icon matching RouteSense Screens 1 & 2
function createBusPill(busId: string, isSelected: boolean = false): L.DivIcon {
  // Consistent amber/yellow for all buses — shows clearly on dark map
  const BUS_COLORS = ['#f59e0b', '#06b6d4', '#a855f7', '#10b981', '#f97316', '#3b82f6']
  const match = busId.match(/\d+/)
  const idx = match ? (parseInt(match[0]) - 1) % BUS_COLORS.length : 0
  const color = BUS_COLORS[idx]
  const match2 = busId.match(/\d+/)
  const num = match2 ? 100 + parseInt(match2[0]) : 101
  const displayId = `BUS-${num}`

  return L.divIcon({
    className: 'custom-bus-pill',
    html: `
      <div class="routesense-bus-badge ${isSelected ? 'selected' : ''}" style="--badge-color: ${color};">
        <span class="badge-pulse-dot" style="background: ${color}; box-shadow: 0 0 8px ${color};"></span>
        <span class="badge-text">${displayId}</span>
      </div>
    `,
    iconSize: [88, 28],
    iconAnchor: [44, 14],
    popupAnchor: [0, -18],
  })
}

// Hazard icon with radar wave ring
function createHazardIcon(confidence: number, type: string): L.DivIcon {
  const sev = getSeverity(confidence)
  const color = getSeverityColor(sev)
  const isPothole = type.toLowerCase().includes('pothole')

  return L.divIcon({
    className: 'custom-hazard-node',
    html: `
      <div class="hazard-node-wrapper">
        <div class="hazard-radar-wave" style="border-color: ${color};"></div>
        <div class="hazard-core-pin" style="background: ${color}; box-shadow: 0 0 12px ${color};">
          ${isPothole ? '⚠️' : '▲'}
        </div>
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16],
  })
}

// Smoothly centers map on load
function MapFitter({ vehicles, defects }: { vehicles: Vehicle[]; defects: DefectMarker[] }) {
  const map = useMap()
  const fittedRef = useRef(false)

  useEffect(() => {
    if (fittedRef.current) return
    const validPoints = [
      ...vehicles
        .filter(v => typeof v.latitude === 'number' && Number.isFinite(v.latitude))
        .map(v => [v.latitude, v.longitude] as [number, number]),
      ...defects
        .filter(d => typeof d.latitude === 'number' && Number.isFinite(d.latitude))
        .map(d => [d.latitude, d.longitude] as [number, number]),
    ]
    if (validPoints.length > 0) {
      try {
        map.fitBounds(L.latLngBounds(validPoints), { padding: [60, 60], maxZoom: 15 })
        fittedRef.current = true
      } catch {
        // Safe catch
      }
    }
  }, [map, vehicles.length, defects.length])
  return null
}

interface MapViewProps {
  vehicles: Vehicle[]
  defects: DefectMarker[]
  showHexOverlay?: boolean
  selectedBusId?: string | null
  onSelectBus?: (busId: string | null) => void
  onSelectDefect?: (defect: DefectMarker | null) => void
}

const MAP_CENTER: [number, number] = [28.6250, 77.2180]
const H3_RESOLUTION = 9

export default function MapView({
  vehicles,
  defects,
  showHexOverlay = true,
  selectedBusId = null,
  onSelectBus,
  onSelectDefect,
}: MapViewProps) {
  const [activeFilter, setActiveFilter] = useState('All Routes')

  // Filter valid vehicles and defects
  const validVehicles = useMemo(
    () => vehicles.filter(v => typeof v.latitude === 'number' && Number.isFinite(v.latitude) && Number.isFinite(v.longitude)),
    [vehicles]
  )

  const validDefects = useMemo(
    () => defects.filter(d => typeof d.latitude === 'number' && Number.isFinite(d.latitude) && Number.isFinite(d.longitude)),
    [defects]
  )

  // H3 density overlay mapping
  const densityMap = useMemo(() => {
    const map = new Map<string, number>()
    if (!showHexOverlay) return map
    validDefects.forEach(d => {
      try {
        const cell = latLngToCell(d.latitude, d.longitude, H3_RESOLUTION)
        map.set(cell, (map.get(cell) ?? 0) + 1)
      } catch { /* skip */ }
    })
    return map
  }, [validDefects, showHexOverlay])

  return (
    <div className="routesense-map-container">
      {/* Top Floating Controls */}
      <div className="map-top-bar">
        <div className="map-filter-group">
          {['All Routes', 'All Buses', 'All Events'].map(f => (
            <button
              key={f}
              className={`map-filter-chip ${activeFilter === f ? 'active' : ''}`}
              onClick={() => setActiveFilter(f)}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <MapContainer
        center={MAP_CENTER}
        zoom={14}
        style={{ height: '100%', width: '100%' }}
        id="routesense-map"
        zoomControl={false}
      >
        {/* Esri World Dark Gray Base with high-contrast electric neon filter */}
        <TileLayer
          className="routesense-dark-tiles"
          attribution='&copy; <a href="https://www.esri.com/">Esri</a> &mdash; RouteSense Core'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
          maxZoom={16}
        />

        {/* ── Route 17 Neon Trail Polyline (Outer Glow + Core Line) ── */}
        <Polyline
          positions={ROUTE_17_WAYPOINTS}
          pathOptions={{
            color: '#06b6d4',
            weight: 7,
            opacity: 0.3,
            lineCap: 'round',
          }}
        />
        <Polyline
          positions={ROUTE_17_WAYPOINTS}
          pathOptions={{
            color: '#38bdf8',
            weight: 2.5,
            opacity: 0.9,
            dashArray: '5, 8',
          }}
        />

        {/* Route Waypoint Nodes */}
        {ROUTE_17_WAYPOINTS.filter((_, idx) => idx % 2 === 0).map((pt, i) => (
          <CircleMarker
            key={`wp-${i}`}
            center={pt}
            radius={3.5}
            pathOptions={{
              color: '#38bdf8',
              fillColor: '#0b1329',
              fillOpacity: 1,
              weight: 2,
            }}
          />
        ))}

        {/* H3 Hexagonal Density Overlay */}
        {showHexOverlay && <H3HexLayer densityMap={densityMap} />}

        {/* ── Bus Pill Markers ── */}
        {validVehicles.map(vehicle => {
          const isSelected = selectedBusId === vehicle.bus_id
          return (
            <Marker
              key={vehicle.bus_id}
              position={[vehicle.latitude, vehicle.longitude]}
              icon={createBusPill(vehicle.bus_id, isSelected)}
              eventHandlers={{
                click: () => onSelectBus && onSelectBus(vehicle.bus_id),
              }}
            >
              <Popup className="routesense-popup">
                <div className="popup-glass-card">
                  <div className="popup-header-row">
                    <span className="popup-bus-title">🚌 {vehicle.bus_id.replace('bus_', 'BUS-10').toUpperCase()}</span>
                    <span className="popup-status-pill on-route">ON ROUTE</span>
                  </div>
                  <div className="popup-metrics-grid">
                    <div className="popup-metric">
                      <span className="metric-label">SPEED</span>
                      <span className="metric-value">28 km/h</span>
                    </div>
                    <div className="popup-metric">
                      <span className="metric-label">ETA</span>
                      <span className="metric-value">08 min</span>
                    </div>
                    <div className="popup-metric">
                      <span className="metric-label">LAT / LON</span>
                      <span className="metric-value mono">{vehicle.latitude.toFixed(4)}, {vehicle.longitude.toFixed(4)}</span>
                    </div>
                  </div>
                </div>
              </Popup>
            </Marker>
          )
        })}

        {/* ── Hazard & Pothole Markers ── */}
        {validDefects.map(defect => {
          const sev = getSeverity(defect.confidence)
          const color = getSeverityColor(sev)
          return (
            <Marker
              key={defect.defect_id}
              position={[defect.latitude, defect.longitude]}
              icon={createHazardIcon(defect.confidence, defect.object_type)}
              eventHandlers={{
                click: () => onSelectDefect && onSelectDefect(defect),
              }}
            >
              <Popup className="routesense-popup">
                <div className="popup-glass-card defect">
                  <div className="popup-header-row">
                    <span className="popup-defect-title" style={{ color }}>
                      ⚠️ {formatObjectType(defect.object_type)}
                    </span>
                    <span className="popup-status-pill open">OPEN</span>
                  </div>
                  <div className="popup-metrics-grid">
                    <div className="popup-metric">
                      <span className="metric-label">CONFIDENCE</span>
                      <span className="metric-value" style={{ color }}>{(defect.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div className="popup-metric">
                      <span className="metric-label">SIGHTINGS</span>
                      <span className="metric-value">{defect.sighting_count}x</span>
                    </div>
                    <div className="popup-metric">
                      <span className="metric-label">SEVERITY</span>
                      <span className="metric-value" style={{ color }}>{sev.toUpperCase()}</span>
                    </div>
                  </div>
                </div>
              </Popup>
            </Marker>
          )
        })}

        <MapFitter vehicles={validVehicles} defects={validDefects} />
      </MapContainer>

      {/* Floating Legend */}
      <div className="routesense-glass-legend">
        <div className="legend-row"><span className="legend-dot" style={{ background: '#f59e0b' }}></span>Bus (Active)</div>
        <div className="legend-row"><span className="legend-dot" style={{ background: '#06b6d4' }}></span>Bus (Secondary)</div>
        <div className="legend-row"><span className="legend-dot hazard-red"></span>Pothole / Hazard</div>
        <div className="legend-row"><span className="legend-dot traffic-amber"></span>High Confidence</div>
        {showHexOverlay && (
          <div className="legend-row"><span className="legend-dot hex-cyan"></span>High Traffic Zone</div>
        )}
      </div>
    </div>
  )
}
