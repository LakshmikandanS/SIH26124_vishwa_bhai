/**
 * Analytics Dashboard — RouteSense Screen 5
 * Shows 100% LIVE data from backend: real defect counts, vehicle stats,
 * events by type computed from actual defect feed, and live density chart.
 */

import React, { useEffect, useState } from 'react'
import {
  PieChart, Pie, Cell, ResponsiveContainer,
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip,
} from 'recharts'
import { Download, TrendingUp, Activity, AlertTriangle, MapPin } from 'lucide-react'
import type { DefectMarker, Vehicle, HealthInfo } from '../types'
import { formatObjectType } from '../types'

interface AnalyticsProps {
  defects: DefectMarker[]
  vehicles: Vehicle[]
  health: HealthInfo | null
  isConnected: boolean
}

const VEHICLE_COLORS: Record<string, string> = {
  car:        '#3b82f6',
  motorcycle: '#a855f7',
  bus:        '#10b981',
  truck:      '#f97316',
  bicycle:    '#06b6d4',
}

const DEFECT_COLORS: Record<string, string> = {
  pothole:         '#3b82f6',
  traffic_density: '#a855f7',
  road_hazard:     '#f43f5e',
  accident:        '#ec4899',
  waterlogging:    '#06b6d4',
  traffic_survey:  '#64748b',
  other:           '#6366f1',
}

export default function Analytics({ defects, vehicles, health, isConnected }: AnalyticsProps) {
  const [liveTime, setLiveTime] = useState('')
  const [densityHistory, setDensityHistory] = useState<{ time: string; density: number }[]>([])

  useEffect(() => {
    const update = () => setLiveTime(new Date().toLocaleTimeString('en-US', { hour12: true }))
    update()
    const t = setInterval(update, 1000)
    return () => clearInterval(t)
  }, [])

  // Build live density history every time defects change
  useEffect(() => {
    const now = Date.now()
    const point = {
      time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }),
      density: Math.min(100, defects.length * 3.5),
    }
    setDensityHistory(prev => {
      const next = [...prev, point].slice(-12)
      return next
    })
  }, [defects.length])

  // Compute events by type from real defects
  const typeCountMap: Record<string, number> = {}
  for (const d of defects) {
    const key = d.object_type.toLowerCase()
    typeCountMap[key] = (typeCountMap[key] ?? 0) + 1
  }

  const eventsByType = Object.entries(typeCountMap)
    .filter(([k]) => k !== 'traffic_survey')
    .sort(([, a], [, b]) => b - a)
    .slice(0, 6)
    .map(([type, count]) => ({
      type: formatObjectType(type).replace(' Survey', ''),
      count,
      fill: DEFECT_COLORS[type] ?? '#6366f1',
    }))

  // Total non-survey defects
  const realEvents = defects.filter(d => d.object_type !== 'traffic_survey')
  const totalEvents = realEvents.length
  const totalVehicles = health?.active_vehicles ?? vehicles.length

  // Avg confidence as proxy for density
  const avgConf = realEvents.length > 0
    ? realEvents.reduce((s, d) => s + d.confidence, 0) / realEvents.length
    : 0
  const densityScore = Math.min(1, avgConf + defects.length * 0.01)

  // Top problematic GPS clusters (group defects within ~500m by rounding lat/lon)
  const geoCluster: Record<string, { count: number; type: string; lat: number; lon: number }> = {}
  for (const d of realEvents) {
    const key = `${d.latitude.toFixed(3)},${d.longitude.toFixed(3)}`
    if (!geoCluster[key]) {
      geoCluster[key] = { count: 0, type: d.object_type, lat: d.latitude, lon: d.longitude }
    }
    geoCluster[key].count++
  }
  const topLocations = Object.values(geoCluster)
    .sort((a, b) => b.count - a.count)
    .slice(0, 5)

  return (
    <div className="routesense-page analytics-view">
      {/* Header */}
      <header className="routesense-page-header">
        <div className="header-left">
          <h2 className="header-main-title">Analytics Dashboard</h2>
          <p className="header-subtitle">Live insights from urban AI edge pipeline</p>
        </div>
        <div className="header-right-meta">
          <button className="routesense-export-btn">
            <Download size={14} />
            <span>Export Report</span>
          </button>
          <div className="live-status-chip">
            <span className={isConnected ? 'live-dot-green' : 'live-dot-red'}></span>
            <span className="live-text">{isConnected ? 'LIVE' : 'OFFLINE'}</span>
          </div>
          <div className="live-clock-text">{liveTime}</div>
          <div className="header-user-avatar">RK</div>
        </div>
      </header>

      {/* 4 Live Metric Cards */}
      <div className="routesense-stats-row">
        <div className="routesense-metric-card">
          <div className="metric-info-col">
            <div className="metric-title">Active Vehicles</div>
            <div className="metric-value-row">
              <span className="metric-big-num">{totalVehicles}</span>
            </div>
            <div className="metric-sub-note green">
              <Activity size={12} /> Live tracking
            </div>
          </div>
          <div className="metric-icon-bubble green"><Activity size={22} /></div>
        </div>

        <div className="routesense-metric-card">
          <div className="metric-info-col">
            <div className="metric-title">Total Detected Events</div>
            <div className="metric-value-row">
              <span className="metric-big-num">{totalEvents}</span>
            </div>
            <div className="metric-sub-note amber">
              <AlertTriangle size={12} /> From edge YOLO
            </div>
          </div>
          <div className="metric-icon-bubble amber"><AlertTriangle size={22} /></div>
        </div>

        <div className="routesense-metric-card">
          <div className="metric-info-col">
            <div className="metric-title">Avg Detection Confidence</div>
            <div className="metric-value-row">
              <span className="metric-big-num">{avgConf > 0 ? (avgConf * 100).toFixed(0) + '%' : '—'}</span>
            </div>
            <div className={`metric-sub-note ${avgConf > 0.7 ? 'green' : 'amber'}`}>
              {avgConf > 0.7 ? '● High Accuracy' : realEvents.length === 0 ? '● Awaiting data' : '● Moderate'}
            </div>
          </div>
          <div className="metric-icon-bubble purple"><TrendingUp size={22} /></div>
        </div>

        <div className="routesense-metric-card">
          <div className="metric-info-col">
            <div className="metric-title">H3 Density Clusters</div>
            <div className="metric-value-row">
              <span className="metric-big-num">{health?.h3_clusters ?? 0}</span>
            </div>
            <div className="metric-sub-note purple">● Hex grid zones</div>
          </div>
          <div className="metric-icon-bubble purple"><MapPin size={22} /></div>
        </div>
      </div>

      {/* Mid Charts Row */}
      <div className="analytics-mid-grid">
        {/* Events by Type Donut */}
        <div className="routesense-card donut-analytics-card" style={{ minHeight: 200 }}>
          <div className="card-header-bar"><span className="card-title">Events by Type</span></div>
          {eventsByType.length > 0 ? (
            <div className="donut-analytics-layout" style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
              <div style={{ position: 'relative', width: 160, height: 160, flexShrink: 0 }}>
                <ResponsiveContainer width={160} height={160}>
                  <PieChart>
                    <Pie data={eventsByType} innerRadius={50} outerRadius={72} paddingAngle={4} dataKey="count">
                      {eventsByType.map((entry, idx) => (
                        <Cell key={`c-${idx}`} fill={entry.fill} stroke="transparent" />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ background: '#0d1526', border: '1px solid #1e293b', fontSize: 11 }} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="donut-center-stat">
                  <strong>{totalEvents}</strong>
                  <span>Events</span>
                </div>
              </div>
              <div className="donut-detail-legend" style={{ flex: 1, minWidth: 100 }}>
                {eventsByType.map(d => (
                  <div key={d.type} className="donut-detail-row">
                    <span className="dot" style={{ background: d.fill }}></span>
                    <span className="label">{d.type}</span>
                    <strong className="num">{d.count}</strong>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="empty-event-note">Waiting for edge detections…<br/><span style={{fontSize:11,color:'#475569'}}>Run the edge emulator to see data</span></div>
          )}
        </div>

        {/* Live Density Over Time Area Chart */}
        <div className="routesense-card traffic-time-card">
          <div className="card-header-bar">
            <span className="card-title">Live Detection Events Over Time</span>
            <span style={{ fontSize: 10, color: '#64748b' }}>Updated every ~3s</span>
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={densityHistory}>
              <defs>
                <linearGradient id="densityGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.6} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="time" stroke="#64748b" fontSize={10} />
              <YAxis stroke="#64748b" fontSize={10} />
              <Tooltip
                contentStyle={{ background: '#0d1526', border: '1px solid #1e293b', fontSize: 11 }}
                formatter={(v: unknown) => [`${Number(v).toFixed(0)} events`, 'Count']}
              />
              <Area type="monotone" dataKey="density" stroke="#3b82f6" strokeWidth={2} fill="url(#densityGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom Grid: Top Locations & Events Bar */}
      <div className="analytics-bottom-grid">
        <div className="routesense-card problematic-card" style={{ minHeight: 180 }}>
          <div className="card-header-bar"><span className="card-title">Top Detection Clusters</span></div>
          <div className="problem-locations-list" style={{ maxHeight: 160, overflowY: 'auto' }}>
            {topLocations.length > 0 ? topLocations.map((loc, i) => (
              <div key={i} className="problem-row">
                <span className="idx">{i + 1}.</span>
                <span className="loc" style={{ fontFamily: 'monospace', fontSize: 10 }}>
                  {loc.lat.toFixed(4)}, {loc.lon.toFixed(4)}
                </span>
                <span className="issue amber">{loc.count}× {formatObjectType(loc.type)}</span>
              </div>
            )) : (
              <div className="empty-event-note">No clusters yet — run the edge emulator</div>
            )}
          </div>
        </div>

        <div className="routesense-card events-type-card" style={{ minHeight: 180 }}>
          <div className="card-header-bar"><span className="card-title">Detections by Type</span></div>
          {eventsByType.length > 0 ? (
            <div style={{ width: '100%', height: 140 }}>
              <ResponsiveContainer width="100%" height={140}>
                <BarChart data={eventsByType} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                  <XAxis dataKey="type" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={10} />
                  <Tooltip contentStyle={{ background: '#0d1526', border: '1px solid #1e293b', fontSize: 11 }} />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {eventsByType.map((entry, index) => (
                      <Cell key={`bar-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="empty-event-note">Awaiting edge detections…</div>
          )}
        </div>
      </div>
    </div>
  )
}
