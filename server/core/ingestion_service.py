"""
Server Core: Telemetry Ingestion Service
========================================
Coordinates the full ingestion pipeline:
  1. Updates vehicle position in memory
  2. Updates Uber H3 hexagonal spatial density index
  3. Executes KD-Tree 3-Meter Spatial Deduplication
  4. Triggers K-M plugin for video sync if confidence is high
  5. Broadcasts real-time events to frontend via WebSockets
"""

import asyncio
import logging
import time
from dataclasses import asdict
from typing import Optional, Dict, List, Any
import h3

from domain.models import TelemetryReading, DefectMarker, VehiclePosition
from domain.deduplication import SpatialDeduplicationEngine

logger = logging.getLogger("IngestionService")


class TelemetryIngestionService:
    def __init__(
        self,
        dedup_engine: SpatialDeduplicationEngine,
        ws_broadcast=None,
        km_plugin=None,
        h3_resolution: int = 8,
    ):
        self._dedup = dedup_engine
        self._ws_broadcast = ws_broadcast
        self._km_plugin = km_plugin
        self.h3_resolution = h3_resolution

        self._vehicle_positions: Dict[str, VehiclePosition] = {}
        self._vehicle_health: Dict[str, dict] = {}
        self._h3_density: Dict[str, int] = {}  # h3_index -> defect/traffic count

        logger.info(f"[IngestionService] Initialized with H3 resolution={h3_resolution}")

    def set_ws_broadcast(self, broadcast_fn):
        self._ws_broadcast = broadcast_fn

    def set_km_plugin(self, km_plugin):
        self._km_plugin = km_plugin

    def handle_heartbeat(self, hb: dict):
        bus_id = hb.get("bus_id", "unknown")
        self._vehicle_health[bus_id] = hb

    def handle_telemetry_sync(self, reading: TelemetryReading, loop: Optional[asyncio.AbstractEventLoop] = None):
        """Thread-safe synchronous wrapper called by MQTT thread."""
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(self.handle_telemetry(reading), loop)
        else:
            # Run without async broadcast if loop not provided
            self._process_reading_sync(reading)

    def _process_reading_sync(self, reading: TelemetryReading):
        # 1. Update vehicle position
        self._update_vehicle_position(reading)

        # 2. Update H3 cell count
        try:
            h3_index = h3.latlng_to_cell(reading.latitude, reading.longitude, self.h3_resolution)
            self._h3_density[h3_index] = self._h3_density.get(h3_index, 0) + 1
        except Exception as e:
            logger.debug(f"[H3] Error computing cell: {e}")

        # 3. Spatial Deduplication (if it's a defect)
        if reading.object_type != "traffic_survey":
            action, marker = self._dedup.process(reading)
            return action, marker
        return None, None

    async def handle_telemetry(self, reading: TelemetryReading):
        action, marker = self._process_reading_sync(reading)

        # Broadcast vehicle movement
        if self._ws_broadcast:
            veh_data = asdict(self._vehicle_positions[reading.bus_id])
            veh_data["lux"] = reading.lux_level
            veh_data["vibration_g"] = reading.vibration_g
            await self._ws_broadcast("vehicle_moved", veh_data)

            # Broadcast defect event
            if marker:
                event_name = "defect_new" if action == "new" else "defect_updated"
                await self._ws_broadcast(event_name, asdict(marker))

        # Trigger K-M Media Orchestration Plugin (Day 3 / Master Plan)
        if marker and self._km_plugin and marker.confidence >= 0.75 and action == "new":
            self._km_plugin.request_media_sync(
                bus_id=reading.bus_id,
                defect_id=marker.defect_id,
                timestamp_ms=reading.timestamp_ms,
            )

    def _update_vehicle_position(self, reading: TelemetryReading):
        self._vehicle_positions[reading.bus_id] = VehiclePosition(
            bus_id=reading.bus_id,
            latitude=reading.latitude,
            longitude=reading.longitude,
            timestamp_ms=reading.timestamp_ms,
        )

    def get_all_vehicles(self) -> List[VehiclePosition]:
        return list(self._vehicle_positions.values())

    def get_all_defects(self) -> List[DefectMarker]:
        return self._dedup.get_all_markers()

    def get_h3_grid(self) -> List[Dict[str, Any]]:
        """Returns H3 density hexes with boundary polygons for Leaflet rendering."""
        cells = []
        for h3_id, count in self._h3_density.items():
            try:
                boundary = h3.cell_to_boundary(h3_id)  # [(lat, lng), ...]
                cells.append({
                    "h3_index": h3_id,
                    "count": count,
                    "coordinates": boundary,
                })
            except Exception:
                continue
        return cells

    def get_stats(self) -> dict:
        return {
            "active_vehicles": len(self._vehicle_positions),
            "total_defects": self._dedup.get_marker_count(),
            "h3_clusters": len(self._h3_density),
            "uptime_s": int(time.time()),
        }
