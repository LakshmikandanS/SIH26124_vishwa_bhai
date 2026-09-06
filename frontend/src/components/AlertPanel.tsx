/**
 * AlertPanel — live scrolling defect event feed
 * Shows each defect_new event as an animated card
 */

import type { AlertEvent } from '../types'
import { getSeverity, getSeverityColor, formatObjectType, timeAgo } from '../types'

interface AlertPanelProps {
  alerts: AlertEvent[]
  onClear: () => void
}

const SEVERITY_ICONS: Record<string, string> = {
  critical: '🔴',
  high:     '🟠',
  medium:   '🟡',
  low:      '🟢',
}

const TYPE_ICONS: Record<string, string> = {
  pothole:    '🕳️',
  road_hazard: '⚠️',
  accident:   '💥',
  default:    '📍',
}

function AlertPanel({ alerts, onClear }: AlertPanelProps) {
  return (
    <div className="alert-panel">
      <div className="panel-header">
        <div className="panel-header-left">
          <span className="panel-icon">⚡</span>
          <span className="panel-title">Live Alerts</span>
        </div>
        <div className="panel-header-right">
          {alerts.length > 0 && (
            <span className="alert-count-badge">{alerts.length}</span>
          )}
          {alerts.length > 0 && (
            <button className="clear-btn" onClick={onClear} title="Clear all">✕</button>
          )}
        </div>
      </div>

      <div className="alert-scroll">
        {alerts.length === 0 ? (
          <div className="empty-state">
            <div className="empty-radar">
              <div className="radar-ring r1"></div>
              <div className="radar-ring r2"></div>
              <div className="radar-ring r3"></div>
              <span className="radar-icon">📡</span>
            </div>
            <p>Monitoring active</p>
            <small>Alerts will appear here in real-time</small>
          </div>
        ) : (
          alerts.map(alert => {
            const sev = getSeverity(alert.confidence)
            const color = getSeverityColor(sev)
            const typeIcon = TYPE_ICONS[alert.object_type] ?? TYPE_ICONS.default

            return (
              <div key={alert.defect_id + alert.received_at} className="alert-card" style={{ '--sev-color': color } as React.CSSProperties}>
                <div className="alert-card-top">
                  <span className="alert-icon">{typeIcon}</span>
                  <div className="alert-info">
                    <div className="alert-type-name">{formatObjectType(alert.object_type)}</div>
                    <div className="alert-bus">{alert.bus_id ?? 'Unknown bus'}</div>
                  </div>
                  <div className="alert-right">
                    <span className="alert-sev-icon">{SEVERITY_ICONS[sev]}</span>
                    <span className="alert-conf" style={{ color }}>{(alert.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>
                <div className="alert-card-bottom">
                  <span className="alert-coords">
                    {alert.latitude.toFixed(4)}°N, {alert.longitude.toFixed(4)}°E
                  </span>
                  <span className="alert-time">{timeAgo(alert.received_at)}</span>
                </div>
                <div className="alert-severity-bar" style={{ background: color }}></div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

export default AlertPanel
