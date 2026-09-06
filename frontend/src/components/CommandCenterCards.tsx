/**
 * RouteSense Command Center Bottom Analytics Cards
 * 1. Recent Events List (with status badges & severity)
 * 2. Fleet Summary Donut Chart (Total in center + category breakdown)
 * 3. Traffic Density (Live) Gradient Area Chart
 */

import React from 'react'
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts'
import type { DefectMarker } from '../types'
import { formatObjectType, getSeverityColor, getSeverity } from '../types'

// ── 1. Recent Events Card ──────────────────────────────────────
export function RecentEventsCard({ defects }: { defects: DefectMarker[] }) {
  const events = defects.slice(0, 4)

  return (
    <div className="routesense-card recent-events-card">
      <div className="card-header-bar">
        <span className="card-title">Recent Events</span>
        <span className="card-sub-link">View All</span>
      </div>
      <div className="recent-events-table">
        {events.length === 0 ? (
          <div className="empty-event-note">Scanning road network for events...</div>
        ) : (
          events.map((d, i) => {
            const sev = getSeverity(d.confidence)
            const color = getSeverityColor(sev)
            const busId = d.bus_id ? d.bus_id.replace('bus_', 'BUS-10') : `BUS-10${(i % 3) + 1}`

            return (
              <div key={d.defect_id} className="recent-event-row">
                <div className="event-icon-box" style={{ color }}>
                  {d.object_type.includes('pothole') ? '🕳️' : d.object_type.includes('traffic') ? '🚦' : '⚠️'}
                </div>
                <div className="event-info-cell">
                  <div className="event-name">{formatObjectType(d.object_type)}</div>
                  <div className="event-sub">{busId} • 10:42 AM • {(d.confidence * 100).toFixed(0)}%</div>
                </div>
                <span className="event-open-badge">OPEN</span>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

// ── 2. Fleet Summary Donut Chart ───────────────────────────────
const FLEET_DONUT_DATA = [
  { name: 'On Route',   value: 65, color: '#10b981' },
  { name: 'In Transit', value: 20, color: '#3b82f6' },
  { name: 'Idle',       value: 10, color: '#f59e0b' },
  { name: 'Offline',    value: 5,  color: '#ef4444' },
]

export function FleetSummaryCard({ vehicleCount = 20 }: { vehicleCount?: number }) {
  return (
    <div className="routesense-card fleet-summary-card">
      <div className="card-header-bar">
        <span className="card-title">Fleet Summary</span>
      </div>
      <div className="donut-chart-wrapper">
        <div className="donut-chart-container">
          <ResponsiveContainer width={120} height={120}>
            <PieChart>
              <Pie
                data={FLEET_DONUT_DATA}
                innerRadius={38}
                outerRadius={56}
                paddingAngle={3}
                dataKey="value"
              >
                {FLEET_DONUT_DATA.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} stroke="transparent" />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="donut-center-label">
            <span className="donut-number">1,842</span>
            <span className="donut-sub">Total Buses</span>
          </div>
        </div>

        <div className="donut-legend-col">
          <div className="donut-legend-item"><span className="legend-dot green"></span>On Route (75%)</div>
          <div className="donut-legend-item"><span className="legend-dot blue"></span>In Transit (17%)</div>
          <div className="donut-legend-item"><span className="legend-dot amber"></span>Idle (5%)</div>
          <div className="donut-legend-item"><span className="legend-dot red"></span>Offline (3%)</div>
        </div>
      </div>
    </div>
  )
}

// ── 3. Live Traffic Density Area Chart ─────────────────────────
const TRAFFIC_CURVE_DATA = [
  { time: '08:00', density: 30 },
  { time: '08:30', density: 55 },
  { time: '09:00', density: 85 },
  { time: '09:30', density: 92 },
  { time: '10:00', density: 78 },
  { time: '10:30', density: 88 },
  { time: '11:00', density: 65 },
]

export function TrafficDensityCard() {
  return (
    <div className="routesense-card traffic-density-card">
      <div className="card-header-bar">
        <span className="card-title">Traffic Density (Live)</span>
        <span className="density-alert-pill high">HIGH</span>
      </div>
      <div className="traffic-area-container">
        <ResponsiveContainer width="100%" height={90}>
          <AreaChart data={TRAFFIC_CURVE_DATA} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
            <defs>
              <linearGradient id="trafficGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f97316" stopOpacity={0.6} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="time" stroke="#64748b" fontSize={9} tickLine={false} />
            <YAxis stroke="#64748b" fontSize={9} domain={[0, 100]} tickLine={false} />
            <Tooltip
              contentStyle={{ background: '#0d1526', border: '1px solid #1e293b', borderRadius: '6px', fontSize: '11px' }}
            />
            <Area type="monotone" dataKey="density" stroke="#f97316" strokeWidth={2} fillOpacity={1} fill="url(#trafficGradient)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
