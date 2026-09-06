/**
 * UrbanEvents — Suradak Screen 4
 * Fixes:
 *  - Collapsible left defect panel (toggle show/hide)
 *  - Bus oscillation fixed by not rendering vehicles in this map (defects only)
 *  - Live time in header
 *  - Scrollable events list
 */

import React, { useState, useEffect } from 'react'
import MapView from '../components/MapView'
import type { DefectMarker, Vehicle, AlertEvent } from '../types'
import { getIncidentPhoto } from '../data/mockPhotos'
import { formatObjectType, getSeverityColor, getSeverity, timeAgo } from '../types'
import { ChevronLeft, ChevronRight, X } from 'lucide-react'

interface UrbanEventsProps {
  defects: DefectMarker[]
  vehicles: Vehicle[]
  alerts?: AlertEvent[]
  isConnected?: boolean
}

const TYPE_FILTERS = ['All Types', 'pothole', 'road_hazard', 'accident', 'waterlogging']

const SEV_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high:     '#f97316',
  medium:   '#f59e0b',
  low:      '#10b981',
}

export default function UrbanEvents({ defects, vehicles, isConnected = true }: UrbanEventsProps) {
  const [typeFilter, setTypeFilter] = useState('All Types')
  const [selectedDefect, setSelectedDefect] = useState<DefectMarker | null>(null)
  const [panelOpen, setPanelOpen] = useState(true)
  const [liveTime, setLiveTime] = useState('')

  useEffect(() => {
    const t = setInterval(() => setLiveTime(new Date().toLocaleTimeString('en-US', { hour12: true })), 1000)
    setLiveTime(new Date().toLocaleTimeString('en-US', { hour12: true }))
    return () => clearInterval(t)
  }, [])

  // Auto-select first defect
  useEffect(() => {
    if (!selectedDefect && defects.length > 0) {
      setSelectedDefect(defects[0])
    }
  }, [defects.length])

  const filtered = defects.filter(d => {
    if (typeFilter === 'All Types') return true
    return d.object_type.toLowerCase().includes(typeFilter.toLowerCase())
  })

  const activeDefect = selectedDefect || filtered[0] || null

  return (
    <div className="routesense-page urban-events-view">
      {/* Header */}
      <header className="routesense-page-header">
        <div className="header-left">
          <h2 className="header-main-title">Urban Events</h2>
          <p className="header-subtitle">AI-detected road incidents · {defects.length} total</p>
        </div>
        <div className="header-right-meta">
          <div className="live-status-chip">
            <span className={isConnected ? 'live-dot-green' : 'live-dot-red'}></span>
            <span className="live-text">{isConnected ? 'LIVE' : 'OFFLINE'}</span>
          </div>
          <div className="live-clock-text">{liveTime}</div>
          <div className="header-user-avatar">RK</div>
        </div>
      </header>

      {/* Filter Row */}
      <div className="events-filter-bar">
        <div className="filter-pill-cluster">
          {TYPE_FILTERS.map(f => (
            <button
              key={f}
              className={`event-filter-chip ${typeFilter === f ? 'active' : ''}`}
              onClick={() => setTypeFilter(f)}
            >
              {f === 'All Types' ? f : formatObjectType(f)}
            </button>
          ))}
        </div>
        <div className="events-total-badge">{filtered.length} Detected</div>

        {/* Panel Toggle Button */}
        <button
          onClick={() => setPanelOpen(p => !p)}
          style={{
            display: 'flex', alignItems: 'center', gap: 4,
            background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.3)',
            borderRadius: 6, padding: '4px 10px', cursor: 'pointer',
            fontSize: 11, color: '#93c5fd', marginLeft: 'auto',
          }}
        >
          {panelOpen ? <ChevronLeft size={13} /> : <ChevronRight size={13} />}
          {panelOpen ? 'Hide Panel' : 'Show Events'}
        </button>
      </div>

      {/* Main Split: Collapsible Left + Right Map */}
      <div className="events-split-layout" style={{ flex: 1, minHeight: 0 }}>
        {/* Left Collapsible Panel */}
        {panelOpen && (
          <div className="events-list-column" style={{ overflowY: 'auto', maxHeight: '100%', position: 'relative' }}>
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '8px 12px', borderBottom: '1px solid rgba(255,255,255,0.06)',
              background: 'rgba(13,21,38,0.85)', backdropFilter: 'blur(8px)',
              position: 'sticky', top: 0, zIndex: 5,
            }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                Events List ({filtered.length})
              </span>
              <button
                onClick={() => setPanelOpen(false)}
                style={{
                  background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                  color: '#94a3b8', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', padding: '2px 6px', borderRadius: 4,
                  fontSize: 11, gap: 4,
                }}
                title="Close panel"
              >
                <X size={13} />
                <span>Close</span>
              </button>
            </div>
            {filtered.length === 0 ? (
              <div style={{ padding: 20, textAlign: 'center', color: '#475569', fontSize: 13 }}>
                No events yet. Start edge emulator.
              </div>
            ) : filtered.map(d => {
              const isSelected = activeDefect?.defect_id === d.defect_id
              const photoUrl = getIncidentPhoto(d.object_type)
              const sev = getSeverity(d.confidence)
              const color = SEV_COLORS[sev]
              const busLabel = d.bus_id ? d.bus_id.replace('bus_', 'BUS-10') : 'Unknown'
              const ago = d.last_seen_ms ? timeAgo(d.last_seen_ms) : '—'

              return (
                <div
                  key={d.defect_id}
                  className={`event-thumbnail-card ${isSelected ? 'active' : ''}`}
                  onClick={() => setSelectedDefect(d)}
                >
                  <div className="event-card-thumb-wrapper">
                    <img src={photoUrl} alt={d.object_type} className="event-photo-img" />
                    <span style={{
                      position: 'absolute', top: 4, right: 4,
                      background: `${color}cc`, color: '#fff', fontSize: 9, fontWeight: 700,
                      padding: '2px 5px', borderRadius: 4,
                    }}>{sev.toUpperCase()}</span>
                  </div>
                  <div className="event-card-body">
                    <div className="event-title-row">
                      <span className="event-card-title" style={{ color }}>{formatObjectType(d.object_type)}</span>
                      <span className="event-status-pill open">OPEN</span>
                    </div>
                    <div style={{ fontSize: 10, color: '#64748b', marginTop: 2 }}>
                      {busLabel} · {ago}
                    </div>
                    <div style={{ fontSize: 10, fontFamily: 'monospace', color: '#475569', marginTop: 2 }}>
                      {d.latitude.toFixed(4)}, {d.longitude.toFixed(4)}
                    </div>
                    <div style={{ fontSize: 10, color: '#64748b', marginTop: 2 }}>
                      Conf: <strong style={{ color }}>{(d.confidence * 100).toFixed(0)}%</strong>
                      {' '}· Seen <strong style={{ color: '#f8fafc' }}>{d.sighting_count}×</strong>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Right Map — does NOT render vehicles to stop oscillation */}
        <div className="events-map-wrapper" style={{ position: 'relative', flex: 1, minWidth: 0 }}>
          <MapView
            vehicles={[]}
            defects={filtered}
            showHexOverlay={false}
            onSelectDefect={def => setSelectedDefect(def)}
          />

          {/* Floating Detail Card over the map */}
          {activeDefect && (
            <div className="floating-event-detail-card">
              <div className="detail-card-header">
                <div className="detail-title-col">
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <h4 style={{ margin: 0 }}>{formatObjectType(activeDefect.object_type)}</h4>
                    <button
                      onClick={() => setSelectedDefect(null)}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b', padding: 2 }}
                    >
                      <X size={14} />
                    </button>
                  </div>
                  <span className="detail-sub-meta">
                    {activeDefect.bus_id?.replace('bus_', 'BUS-10') ?? '—'} · {activeDefect.last_seen_ms ? timeAgo(activeDefect.last_seen_ms) : ''}
                  </span>
                  <span className="detail-conf-text">
                    Confidence: <strong>{(activeDefect.confidence * 100).toFixed(0)}%</strong>
                    {' '}· Sightings: <strong>{activeDefect.sighting_count}×</strong>
                  </span>
                  <span className="detail-geo-text mono">
                    📍 {activeDefect.latitude.toFixed(5)}, {activeDefect.longitude.toFixed(5)}
                  </span>
                </div>
              </div>

              <div className="detail-img-preview-box">
                <img
                  src={getIncidentPhoto(activeDefect.object_type)}
                  alt="Incident Visual"
                  className="detail-preview-img"
                />
              </div>

              <button className="view-details-action-btn">View Full Report</button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
