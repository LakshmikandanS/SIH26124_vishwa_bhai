/**
 * useRestApi — fetch initial state from our FastAPI server on mount & periodic poll
 * Provides vehicles, defects, and system health.
 */

import { useEffect, useState } from 'react'
import type { Vehicle, DefectMarker, HealthInfo } from '../types'

const API_FALLBACK = 'http://localhost:8000'

interface RestApiState {
  vehicles: Vehicle[]
  defects: DefectMarker[]
  health: HealthInfo | null
  loading: boolean
  error: string | null
}

async function safeFetch(path: string) {
  try {
    const res = await fetch(`/api${path}`)
    if (res.ok) return await res.json()
  } catch {
    // try direct fallback
  }
  try {
    const res = await fetch(`${API_FALLBACK}${path}`)
    if (res.ok) return await res.json()
  } catch {
    // offline
  }
  return null
}

export function useRestApi(): RestApiState {
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [defects, setDefects] = useState<DefectMarker[]>([])
  const [health, setHealth] = useState<HealthInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    const fetchAll = async () => {
      try {
        const [vData, dData, hData] = await Promise.all([
          safeFetch('/vehicles'),
          safeFetch('/defects'),
          safeFetch('/health'),
        ])

        if (!mounted) return

        if (vData && Array.isArray(vData.vehicles)) {
          setVehicles(vData.vehicles)
        } else if (vData && Array.isArray(vData)) {
          setVehicles(vData)
        }

        if (dData && Array.isArray(dData.defects)) {
          setDefects(dData.defects)
        } else if (dData && Array.isArray(dData)) {
          setDefects(dData)
        }

        if (hData) {
          setHealth(hData)
          setError(null)
        } else {
          // If server is unreachable on mount and state is empty, seed demo data
          setVehicles(prev => prev.length > 0 ? prev : DEMO_VEHICLES)
          setDefects(prev => prev.length > 0 ? prev : DEMO_DEFECTS)
        }
      } catch (e) {
        if (mounted) {
          setError('Running in presentation fallback mode')
          setVehicles(prev => prev.length > 0 ? prev : DEMO_VEHICLES)
          setDefects(prev => prev.length > 0 ? prev : DEMO_DEFECTS)
        }
      } finally {
        if (mounted) setLoading(false)
      }
    }

    // Initial fetch
    fetchAll()

    // 3-second live sync interval
    const interval = setInterval(fetchAll, 3000)

    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [])

  return { vehicles, defects, health, loading, error }
}

// ── Demo data for offline/presentation mode ──────────────────────────────────
const now = Date.now()

export const DEMO_VEHICLES: Vehicle[] = [
  { bus_id: 'bus_1', latitude: 28.6315, longitude: 77.2167, last_seen: now - 5_000 },
  { bus_id: 'bus_2', latitude: 28.6215, longitude: 77.2267, last_seen: now - 12_000 },
  { bus_id: 'bus_3', latitude: 28.6415, longitude: 77.2067, last_seen: now - 3_000 },
  { bus_id: 'bus_4', latitude: 28.6115, longitude: 77.2367, last_seen: now - 45_000 },
  { bus_id: 'bus_5', latitude: 28.6515, longitude: 77.1967, last_seen: now - 2_000 },
]

export const DEMO_DEFECTS: DefectMarker[] = [
  { defect_id: 'd1', latitude: 28.6300, longitude: 77.2200, object_type: 'pothole',     confidence: 0.92, sighting_count: 5, bus_id: 'bus_1', last_seen_ms: now - 30_000 },
  { defect_id: 'd2', latitude: 28.6250, longitude: 77.2150, object_type: 'road_hazard', confidence: 0.78, sighting_count: 2, bus_id: 'bus_2', last_seen_ms: now - 90_000 },
  { defect_id: 'd3', latitude: 28.6350, longitude: 77.2250, object_type: 'pothole',     confidence: 0.65, sighting_count: 1, bus_id: 'bus_3', last_seen_ms: now - 180_000 },
  { defect_id: 'd4', latitude: 28.6200, longitude: 77.2100, object_type: 'pothole',     confidence: 0.95, sighting_count: 8, bus_id: 'bus_1', last_seen_ms: now - 15_000 },
  { defect_id: 'd5', latitude: 28.6400, longitude: 77.2050, object_type: 'road_hazard', confidence: 0.82, sighting_count: 3, bus_id: 'bus_5', last_seen_ms: now - 60_000 },
  { defect_id: 'd6', latitude: 28.6180, longitude: 77.2320, object_type: 'pothole',     confidence: 0.55, sighting_count: 1, bus_id: 'bus_4', last_seen_ms: now - 300_000 },
  { defect_id: 'd7', latitude: 28.6440, longitude: 77.2180, object_type: 'pothole',     confidence: 0.88, sighting_count: 4, bus_id: 'bus_3', last_seen_ms: now - 45_000 },
  { defect_id: 'd8', latitude: 28.6280, longitude: 77.2300, object_type: 'road_hazard', confidence: 0.71, sighting_count: 2, bus_id: 'bus_2', last_seen_ms: now - 120_000 },
]
