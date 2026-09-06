/**
 * H3HexLayer — renders H3 hexagonal density cells as Leaflet Polygon overlays
 * Called by MapView with a map of h3_index → defect count
 */

import { Polygon, Tooltip } from 'react-leaflet'
import { cellToBoundary } from 'h3-js'
import type { LatLngExpression } from 'leaflet'

interface H3HexLayerProps {
  /** h3_index → count of defects in that cell */
  densityMap: Map<string, number>
}

function getHexColor(count: number): { color: string; fill: string; opacity: number } {
  if (count >= 5) return { color: '#ef4444', fill: '#ef4444', opacity: 0.55 }
  if (count >= 3) return { color: '#f97316', fill: '#f97316', opacity: 0.45 }
  if (count >= 2) return { color: '#f59e0b', fill: '#f59e0b', opacity: 0.35 }
  return { color: '#06b6d4', fill: '#06b6d4', opacity: 0.25 }
}

function H3HexLayer({ densityMap }: H3HexLayerProps) {
  if (densityMap.size === 0) return null

  return (
    <>
      {Array.from(densityMap.entries()).map(([h3Index, count]) => {
        try {
          // cellToBoundary returns [lat, lng][] — already correct for Leaflet
          const boundary = cellToBoundary(h3Index) as [number, number][]
          const positions: LatLngExpression[] = boundary.map(([lat, lng]) => [lat, lng])
          const { color, fill, opacity } = getHexColor(count)

          return (
            <Polygon
              key={h3Index}
              positions={positions}
              pathOptions={{
                color,
                fillColor: fill,
                fillOpacity: opacity,
                weight: 1,
                opacity: 0.8,
              }}
            >
              <Tooltip sticky>
                <div style={{ fontFamily: 'Inter, sans-serif', fontSize: 12 }}>
                  <strong>{count} defect{count !== 1 ? 's' : ''}</strong> in zone
                </div>
              </Tooltip>
            </Polygon>
          )
        } catch {
          return null
        }
      })}
    </>
  )
}

export default H3HexLayer
