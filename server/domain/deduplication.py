"""
Server-Side Spatial Deduplication Engine with In-Memory KD-Tree
==============================================================
Strictly implements Section 1, 2.5, and 5.2 of Master Plan:
  - Thread-Safe Concurrent In-Memory Spatial Map
  - Scipy KD-Tree indexing in 3D Cartesian Earth-centered coordinates
  - 3-Meter Radius Consolidation (Merges repeat detections within 3m)
  - Running weighted confidence & sighting count aggregation
"""

import math
import uuid
import time
import logging
import threading
from typing import Optional, List, Tuple, Dict
import numpy as np
from scipy.spatial import KDTree

from domain.models import DefectMarker, TelemetryReading
from config import DEDUP_RADIUS_METERS

logger = logging.getLogger("SpatialDeduplication")

EARTH_RADIUS_METERS = 6371000.0


def gps_to_cartesian(lat_deg: float, lon_deg: float) -> np.ndarray:
    """Converts (lat, lon) in degrees to 3D Cartesian coordinates (x, y, z) on Earth sphere."""
    lat_rad = math.radians(lat_deg)
    lon_rad = math.radians(lon_deg)
    x = EARTH_RADIUS_METERS * math.cos(lat_rad) * math.cos(lon_rad)
    y = EARTH_RADIUS_METERS * math.cos(lat_rad) * math.sin(lon_rad)
    z = EARTH_RADIUS_METERS * math.sin(lat_rad)
    return np.array([x, y, z], dtype=np.float64)


class SpatialDeduplicationEngine:
    """
    High-throughput thread-safe spatial deduplication engine.
    Maintains an active KD-Tree of infrastructure defect markers.
    """

    def __init__(self, radius_meters: float = DEDUP_RADIUS_METERS):
        self.radius_meters = radius_meters
        self._lock = threading.Lock()

        # Storage
        self._markers: Dict[str, DefectMarker] = {}          # defect_id -> DefectMarker
        self._marker_ids: List[str] = []                     # Index in KD-Tree array -> defect_id
        self._cartesian_points: List[np.ndarray] = []        # Index in KD-Tree array -> [x, y, z]
        self._kdtree: Optional[KDTree] = None

        logger.info(f"[Dedup] KD-Tree Deduplication Engine initialized (Radius: {radius_meters}m)")

    def process(self, reading: TelemetryReading) -> Tuple[str, DefectMarker]:
        """
        Ingests a telemetry reading, searches within radius_meters using KD-Tree.
        Returns:
            ("updated", merged_marker) if found within 3 meters
            ("new", new_marker) if no match found
        """
        point = gps_to_cartesian(reading.latitude, reading.longitude)

        with self._lock:
            # Query KD-Tree if populated
            match_marker = None
            if self._kdtree is not None and len(self._cartesian_points) > 0:
                indices = self._kdtree.query_ball_point(point, r=self.radius_meters)
                if indices:
                    # Filter for same object type if applicable, or pick closest
                    for idx in indices:
                        candidate_id = self._marker_ids[idx]
                        candidate = self._markers[candidate_id]
                        if candidate.object_type.lower() == reading.object_type.lower():
                            match_marker = candidate
                            break

            if match_marker:
                # ── CONSOLIDATE (Section 5.2 / 11A) ───────────
                prev_sightings = match_marker.sighting_count
                new_sightings = prev_sightings + 1

                # Running weighted average of confidence
                match_marker.confidence = (
                    (match_marker.confidence * prev_sightings + reading.confidence) / new_sightings
                )
                match_marker.sighting_count = new_sightings
                match_marker.last_seen_ms = reading.timestamp_ms

                # Running average of GPS coordinates to refine centroid
                match_marker.latitude = (
                    (match_marker.latitude * prev_sightings + reading.latitude) / new_sightings
                )
                match_marker.longitude = (
                    (match_marker.longitude * prev_sightings + reading.longitude) / new_sightings
                )

                logger.debug(
                    f"[Dedup] Merged reading into {match_marker.defect_id} "
                    f"(sightings: {new_sightings}, conf: {match_marker.confidence:.2f})"
                )
                return "updated", match_marker

            else:
                # ── INSTANTIATE NEW MARKER (Section 5.2 / 11B) ──
                marker_id = str(uuid.uuid4())
                marker = DefectMarker(
                    defect_id=marker_id,
                    latitude=reading.latitude,
                    longitude=reading.longitude,
                    object_type=reading.object_type,
                    confidence=reading.confidence,
                    sighting_count=1,
                    first_seen_ms=reading.timestamp_ms,
                    last_seen_ms=reading.timestamp_ms,
                )

                self._markers[marker_id] = marker
                self._marker_ids.append(marker_id)
                self._cartesian_points.append(point)

                # Rebuild KD-Tree index
                self._kdtree = KDTree(np.array(self._cartesian_points))

                logger.info(
                    f"[Dedup] New defect registered: {marker_id[:8]}.. "
                    f"[{marker.object_type}] at ({marker.latitude:.5f}, {marker.longitude:.5f})"
                )
                return "new", marker

    def get_all_markers(self) -> List[DefectMarker]:
        with self._lock:
            return list(self._markers.values())

    def get_marker_count(self) -> int:
        with self._lock:
            return len(self._markers)
