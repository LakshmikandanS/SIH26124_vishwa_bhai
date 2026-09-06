/**
 * AI Video Intelligence — RouteSense Screen 3
 * 100% live data from edge YOLO pipeline via WebSocket:
 *   - Real-time defect detections table (pothole, waterlogging, traffic)
 *   - Live vehicle count by type from traffic survey detections
 *   - Live confidence gauge
 *   - Live detections-over-time sparkline
 *   - Processing status from actual data flow
 */

import React, { useState, useEffect, useRef } from 'react'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { Upload, CheckCircle, Car, Bus, Truck, Bike, AlertCircle, Activity, Wifi, WifiOff } from 'lucide-react'
import type { DefectMarker, AlertEvent, Vehicle } from '../types'
import { formatObjectType, getSeverityColor, getSeverity, timeAgo } from '../types'

interface VideoIntelligenceProps {
  defects: DefectMarker[]
  vehicles: Vehicle[]
  alerts: AlertEvent[]
  isConnected: boolean
}

type TimePoint = { time: string; Pothole: number; Traffic: number; Hazard: number; Other: number }

const DEFECT_BADGE: Record<string, string> = {
  pothole:         '#3b82f6',
  road_hazard:     '#f43f5e',
  accident:        '#ec4899',
  waterlogging:    '#06b6d4',
  traffic_density: '#a855f7',
  traffic_survey:  '#64748b',
}

export default function VideoIntelligence({ defects, vehicles, alerts, isConnected }: VideoIntelligenceProps) {
  const [liveTime, setLiveTime] = useState('')
  const [timeline, setTimeline] = useState<TimePoint[]>([])
  const prevDefectCount = useRef(0)

  useEffect(() => {
    const t = setInterval(() => setLiveTime(new Date().toLocaleTimeString('en-US', { hour12: true })), 1000)
    setLiveTime(new Date().toLocaleTimeString('en-US', { hour12: true }))
    return () => clearInterval(t)
  }, [])

  // Build live timeline whenever new defects arrive
  useEffect(() => {
    if (defects.length !== prevDefectCount.current) {
      prevDefectCount.current = defects.length
      const byType = { Pothole: 0, Traffic: 0, Hazard: 0, Other: 0 }
      for (const d of defects) {
        const t = d.object_type.toLowerCase()
        if (t === 'pothole') byType.Pothole++
        else if (t.startsWith('traffic')) byType.Traffic++
        else if (t === 'road_hazard' || t === 'accident') byType.Hazard++
        else byType.Other++
      }
      setTimeline(prev => [
        ...prev,
        {
          time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }),
          ...byType,
        },
      ].slice(-14))
    }
  }, [defects])

  // Derived counts
  const nonSurveyDefects = defects.filter(d => !d.object_type.toLowerCase().includes('survey'))
  const totalEvents = nonSurveyDefects.length
  const avgConf = totalEvents > 0
    ? nonSurveyDefects.reduce((s, d) => s + d.confidence, 0) / totalEvents
    : 0

  // Traffic survey detections carry vehicle class data (type_label field)
  const surveyDetections = defects.filter(d => d.object_type.toLowerCase().includes('traffic_survey'))
  const recentAlerts = alerts.slice(0, 8)

  // Vehicle class counts from vehicle objects
  const vehicleClassMap: Record<string, number> = {}
  for (const v of vehicles) {
    const cls = (v as any).vehicle_class ?? 'bus'
    vehicleClassMap[cls] = (vehicleClassMap[cls] ?? 0) + 1
  }

  // Density level
  const densityScore = Math.min(1, totalEvents * 0.04 + avgConf * 0.4)
  const densityLabel = densityScore > 0.75 ? 'HIGH' : densityScore > 0.4 ? 'MODERATE' : totalEvents === 0 ? 'NO DATA' : 'LOW'
  const densityColor = densityScore > 0.75 ? '#ef4444' : densityScore > 0.4 ? '#f97316' : '#10b981'

  // Most recent bus being tracked
  const trackedBus = vehicles[0]

  return (
    <div className="routesense-page video-intelligence-view">
      {/* Header */}
      <header className="routesense-page-header">
        <div className="header-left">
          <h2 className="header-main-title">AI Video Intelligence</h2>
          <p className="header-subtitle">Live YOLO edge detections — pothole · traffic · waterlogging</p>
        </div>
        <div className="header-right-meta">
          {trackedBus && (
            <div style={{ fontSize: 11, color: '#64748b', marginRight: 8 }}>
              📍 Bus: <strong style={{ color: '#f59e0b' }}>{trackedBus.bus_id}</strong>
            </div>
          )}
          <div className="live-status-chip">
            <span className={isConnected ? 'live-dot-green' : 'live-dot-red'}></span>
            <span className="live-text">{isConnected ? 'CONNECTED' : 'OFFLINE'}</span>
          </div>
          <div className="live-clock-text">{liveTime}</div>
          <div className="header-user-avatar">RK</div>
        </div>
      </header>

      {/* Connection Banner if offline */}
      {!isConnected && (
        <div style={{
          background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)',
          borderRadius: 8, padding: '10px 16px', margin: '0 0 12px',
          display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#f87171',
        }}>
          <WifiOff size={15} /> Not connected to backend. Start the server and edge emulator to see live data.
        </div>
      )}

      {/* Live Edge Status Bar */}
      <div className="video-main-container" style={{ marginBottom: 12 }}>
        <div className="routesense-card" style={{ display: 'flex', gap: 20, alignItems: 'center', padding: '14px 20px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {isConnected ? <Wifi size={16} color="#10b981" /> : <WifiOff size={16} color="#ef4444" />}
            <span style={{ fontSize: 13, fontWeight: 600, color: isConnected ? '#10b981' : '#ef4444' }}>
              Edge Pipeline {isConnected ? 'Active' : 'Offline'}
            </span>
          </div>
          <div style={{ fontSize: 12, color: '#94a3b8' }}>
            Detections: <strong style={{ color: '#f8fafc' }}>{totalEvents}</strong>
          </div>
          <div style={{ fontSize: 12, color: '#94a3b8' }}>
            Vehicles tracked: <strong style={{ color: '#f8fafc' }}>{vehicles.length}</strong>
          </div>
          <div style={{ fontSize: 12, color: '#94a3b8' }}>
            Avg confidence: <strong style={{ color: '#f8fafc' }}>{avgConf > 0 ? (avgConf * 100).toFixed(1) + '%' : '—'}</strong>
          </div>
          <div style={{ flex: 1 }} />
          <div style={{
            background: densityScore > 0 ? `${densityColor}22` : 'rgba(100,116,139,0.2)',
            border: `1px solid ${densityColor}`,
            borderRadius: 999, padding: '4px 14px',
            fontSize: 12, fontWeight: 700, color: densityColor,
          }}>
            {densityLabel}
          </div>
        </div>
      </div>

      {/* Bottom Intelligence Grid */}
      <div className="video-analytics-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))' }}>

        {/* Card 1: Live Detection Feed */}
        <div className="routesense-card detections-table-card" style={{ gridColumn: 'span 2' }}>
          <div className="card-header-bar">
            <span className="card-title">Live Detection Feed</span>
            <span style={{ fontSize: 10, color: '#64748b' }}>Most recent {recentAlerts.length} events</span>
          </div>
          {recentAlerts.length > 0 ? (
            <table className="detections-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Confidence</th>
                  <th>Sightings</th>
                  <th>Bus</th>
                  <th>Coords</th>
                  <th>When</th>
                </tr>
              </thead>
              <tbody>
                {recentAlerts.map(d => {
                  const sev = getSeverity(d.confidence)
                  const color = getSeverityColor(sev)
                  return (
                    <tr key={d.defect_id}>
                      <td>
                        <span style={{
                          background: `${DEFECT_BADGE[d.object_type.toLowerCase()] ?? '#6366f1'}22`,
                          color: DEFECT_BADGE[d.object_type.toLowerCase()] ?? '#a5b4fc',
                          borderRadius: 999, padding: '2px 8px', fontSize: 11, fontWeight: 600,
                        }}>
                          {formatObjectType(d.object_type)}
                        </span>
                      </td>
                      <td style={{ color, fontWeight: 600 }}>{(d.confidence * 100).toFixed(0)}%</td>
                      <td>{d.sighting_count}</td>
                      <td style={{ fontFamily: 'monospace', fontSize: 11, color: '#f59e0b' }}>{d.bus_id ?? '—'}</td>
                      <td style={{ fontFamily: 'monospace', fontSize: 10, color: '#64748b' }}>
                        {d.latitude.toFixed(4)}, {d.longitude.toFixed(4)}
                      </td>
                      <td style={{ fontSize: 11, color: '#64748b' }}>
                        {d.last_seen_ms ? timeAgo(d.last_seen_ms) : timeAgo(d.received_at)}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          ) : (
            <div className="empty-event-note" style={{ padding: '30px 0', textAlign: 'center' }}>
              <Activity size={28} color="#334155" style={{ marginBottom: 8 }} />
              <div style={{ color: '#64748b', fontSize: 13 }}>No detections yet</div>
              <div style={{ color: '#475569', fontSize: 11, marginTop: 4 }}>
                Run: <code style={{ background: '#1e293b', padding: '2px 6px', borderRadius: 4 }}>python main.py --source test2.mp4</code>
              </div>
            </div>
          )}
        </div>

        {/* Card 2: Detection Counters */}
        <div className="routesense-card live-stats-card">
          <div className="card-header-bar"><span className="card-title">Detection Totals</span></div>
          <div className="stats-classes-grid" style={{ flexDirection: 'column', gap: 10 }}>
            {Object.entries(
              defects.reduce((acc, d) => {
                const k = d.object_type.toLowerCase()
                acc[k] = (acc[k] ?? 0) + 1
                return acc
              }, {} as Record<string, number>)
            ).sort(([,a],[,b]) => b - a).map(([type, count]) => (
              <div key={type} className="class-chip" style={{ justifyContent: 'space-between' }}>
                <span style={{
                  display: 'inline-block', width: 10, height: 10, borderRadius: 3,
                  background: DEFECT_BADGE[type] ?? '#6366f1', flexShrink: 0,
                }}></span>
                <span style={{ flex: 1, marginLeft: 6, fontSize: 11 }}>{formatObjectType(type)}</span>
                <strong style={{ color: '#f8fafc' }}>{count}</strong>
              </div>
            ))}
            {defects.length === 0 && (
              <div style={{ fontSize: 12, color: '#475569', padding: '8px 0' }}>Awaiting data...</div>
            )}
          </div>
        </div>

        {/* Card 3: Traffic Density Gauge */}
        <div className="routesense-card gauge-card">
          <div className="card-header-bar"><span className="card-title">Traffic Density</span></div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flex: 1, gap: 10, padding: '12px 8px' }}>
            {/* Score ring */}
            <div style={{
              width: 90, height: 90, borderRadius: '50%',
              border: `4px solid ${densityColor}`,
              boxShadow: `0 0 18px ${densityColor}55`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexDirection: 'column', gap: 2,
            }}>
              <span style={{ fontSize: 22, fontWeight: 800, color: densityColor, lineHeight: 1 }}>
                {densityScore.toFixed(2)}
              </span>
              <span style={{ fontSize: 9, color: '#94a3b8', letterSpacing: 1 }}>SCORE</span>
            </div>
            {/* Label badge */}
            <span style={{
              background: `${densityColor}22`, border: `1px solid ${densityColor}55`,
              borderRadius: 999, padding: '3px 14px',
              fontSize: 13, fontWeight: 700, color: densityColor,
            }}>
              {densityLabel}
            </span>
            {/* Stats row */}
            <div style={{ display: 'flex', gap: 12, fontSize: 11, color: '#64748b' }}>
              <span><strong style={{ color: '#f8fafc' }}>{totalEvents}</strong> events</span>
              <span><strong style={{ color: '#f8fafc' }}>{avgConf > 0 ? (avgConf * 100).toFixed(0) + '%' : '—'}</strong> avg conf</span>
            </div>
          </div>
        </div>

        {/* Card 4: Detections Over Time */}
        <div className="routesense-card detections-chart-card" style={{ gridColumn: 'span 2' }}>
          <div className="card-header-bar"><span className="card-title">Detections Over Time (live)</span></div>
          {timeline.length > 1 ? (
            <ResponsiveContainer width="100%" height={120}>
              <LineChart data={timeline}>
                <XAxis dataKey="time" stroke="#64748b" fontSize={9} />
                <YAxis stroke="#64748b" fontSize={9} />
                <Tooltip contentStyle={{ background: '#0d1526', border: '1px solid #1e293b', fontSize: 11 }} />
                <Legend wrapperStyle={{ fontSize: 10 }} />
                <Line type="monotone" dataKey="Pothole" stroke="#3b82f6" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Traffic" stroke="#a855f7" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Hazard" stroke="#f43f5e" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Other" stroke="#06b6d4" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: 120, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#475569', fontSize: 12 }}>
              Chart populates as edge detections arrive...
            </div>
          )}
        </div>

        {/* Card 5: Active Vehicles */}
        <div className="routesense-card video-meta-card">
          <div className="card-header-bar"><span className="card-title">Active Vehicles</span></div>
          {vehicles.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 200, overflowY: 'auto' }}>
              {vehicles.map(v => (
                <div key={v.bus_id} style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '8px 10px', borderRadius: 6,
                  background: 'rgba(251,191,36,0.06)', border: '1px solid rgba(251,191,36,0.12)',
                }}>
                  <Bus size={14} color="#f59e0b" />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: '#f8fafc' }}>{v.bus_id}</div>
                    {v.route_name && (
                      <div style={{ fontSize: 10, color: '#64748b' }}>{v.route_name}</div>
                    )}
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    {v.speed_kmh !== undefined && (
                      <div style={{ fontSize: 11, color: '#10b981' }}>{v.speed_kmh} km/h</div>
                    )}
                    <div style={{ fontSize: 10, color: '#64748b', fontFamily: 'monospace' }}>
                      {v.latitude.toFixed(4)}, {v.longitude.toFixed(4)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ fontSize: 12, color: '#475569', padding: '16px 0' }}>
              No vehicles detected yet...
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
