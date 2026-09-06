/**
 * useWebSocket — fully implemented auto-reconnect WebSocket hook
 * Connects to /ws/dashboard on our FastAPI server.
 * Dispatches events to provided callbacks.
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import type { Vehicle, DefectMarker, WSEvent } from '../types'

const WS_URL = '/ws/dashboard'
const RECONNECT_DELAY_MS = 3000
const PING_INTERVAL_MS = 25000

interface UseWebSocketOptions {
  onVehicleMoved?: (data: Vehicle) => void
  onDefectNew?: (data: DefectMarker) => void
  onDefectUpdated?: (data: DefectMarker) => void
}

interface UseWebSocketReturn {
  isConnected: boolean
  lastEventAt: number | null
}

export function useWebSocket({
  onVehicleMoved,
  onDefectNew,
  onDefectUpdated,
}: UseWebSocketOptions = {}): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false)
  const [lastEventAt, setLastEventAt] = useState<number | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pingTimer = useRef<ReturnType<typeof setInterval> | null>(null)

  const connect = useCallback(() => {
    const host = window.location.hostname || 'localhost'
    const wsUrl = `ws://${host}:8000/ws/dashboard`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('[WS] ✅ Connected to Urban AI Fleet server')
      setIsConnected(true)
      // Start keepalive pings
      pingTimer.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send('ping')
      }, PING_INTERVAL_MS)
    }

    ws.onmessage = (event) => {
      try {
        const msg: WSEvent = JSON.parse(event.data)
        setLastEventAt(Date.now())
        switch (msg.event) {
          case 'vehicle_moved':
            if (onVehicleMoved && msg.data) onVehicleMoved(msg.data as Vehicle)
            break
          case 'defect_new':
            if (onDefectNew && msg.data) onDefectNew(msg.data as DefectMarker)
            break
          case 'defect_updated':
            if (onDefectUpdated && msg.data) onDefectUpdated(msg.data as DefectMarker)
            break
          case 'pong':
            break
          default:
            console.log('[WS] Event:', msg.event, msg)
        }
      } catch {
        console.warn('[WS] Non-JSON message:', event.data)
      }
    }

    ws.onclose = () => {
      setIsConnected(false)
      if (pingTimer.current) clearInterval(pingTimer.current)
      console.warn(`[WS] Disconnected — reconnecting in ${RECONNECT_DELAY_MS}ms`)
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY_MS)
    }

    ws.onerror = (err) => {
      console.error('[WS] Connection error:', err)
      ws.close()
    }
  }, [onVehicleMoved, onDefectNew, onDefectUpdated])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      if (pingTimer.current) clearInterval(pingTimer.current)
    }
  }, [connect])

  return { isConnected, lastEventAt }
}
