// ================================================================
// Shared TypeScript interfaces — RouteSense Master Architecture
// ================================================================

/** Live vehicle position from WebSocket vehicle_moved event */
export interface Vehicle {
  bus_id: string
  latitude: number
  longitude: number
  route_name?: string
  speed_kmh?: number
  eta_min?: number
  passengers?: string
  next_stop?: string
  total_distance_km?: number
  status?: 'on_route' | 'in_transit' | 'idle' | 'offline'
  last_seen?: number // epoch ms
}

/** Defect marker from server domain layer */
export interface DefectMarker {
  defect_id: string
  latitude: number
  longitude: number
  object_type: string          // 'pothole' | 'road_hazard' | 'accident' | 'traffic_density'
  confidence: number           // 0.0 – 1.0
  sighting_count: number
  first_seen_ms?: number
  last_seen_ms?: number
  bus_id?: string
  status?: 'OPEN' | 'RESOLVED' | 'UNDER_REVIEW'
  image_url?: string
}

/** WebSocket event envelope */
export interface WSEvent {
  event: 'connected' | 'vehicle_moved' | 'defect_new' | 'defect_updated' | 'pong'
  data?: DefectMarker | Vehicle
  message?: string
  client_count?: number
}

/** Server health endpoint response */
export interface HealthInfo {
  status: string
  broker_connected: boolean
  mqtt_connected?: boolean
  ws_clients?: number
  uptime_seconds?: number
  defect_count?: number
  vehicle_count?: number
  active_vehicles?: number
  total_defects?: number
  h3_clusters?: number
}

/** UI alert item (subset of DefectMarker, used in feed) */
export interface AlertEvent extends DefectMarker {
  received_at: number  // timestamp when we got this alert
}

/** Nav page identifiers matching RouteSense 6-page architecture */
export type PageId = 'command' | 'fleet' | 'video' | 'events' | 'analytics' | 'settings'

/** Severity derived from confidence */
export type Severity = 'critical' | 'high' | 'medium' | 'low'

export function getSeverity(confidence: number): Severity {
  if (confidence >= 0.85) return 'critical'
  if (confidence >= 0.70) return 'high'
  if (confidence >= 0.50) return 'medium'
  return 'low'
}

export function getSeverityColor(severity: Severity): string {
  switch (severity) {
    case 'critical': return '#ef4444'
    case 'high':     return '#f97316'
    case 'medium':   return '#f59e0b'
    case 'low':      return '#10b981'
  }
}

export function formatObjectType(t: string): string {
  return t.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export function formatTime(ms: number): string {
  const d = new Date(ms)
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export function timeAgo(ms: number): string {
  const diff = Date.now() - ms
  if (diff < 60_000) return `${Math.floor(diff / 1000)}s ago`
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`
  return `${Math.floor(diff / 3_600_000)}h ago`
}
