from dataclasses import dataclass, field
from typing import Optional
import time


@dataclass
class TelemetryReading:
    """
    Clean Domain Transfer Object (DTO) — the internal representation of
    an incoming bus telemetry event. Decoupled from transport (MQTT/JSON).
    """
    bus_id: str
    latitude: float
    longitude: float
    object_type: str
    confidence: float
    timestamp_ms: int
    vehicle_count: int = 1
    lux_level: float = 100.0
    vibration_g: float = 0.0
    network_signal_db: float = -75.0


@dataclass
class DefectMarker:
    """
    Represents a deduplicated infrastructure defect on the city map.
    Created/updated by the deduplication engine.
    """
    defect_id: str
    latitude: float
    longitude: float
    object_type: str
    confidence: float             # Running weighted average
    sighting_count: int = 1       # How many buses reported this
    first_seen_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    last_seen_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    clip_url: Optional[str] = None  # Set by K-M plugin on Day 3


@dataclass
class VehiclePosition:
    """Tracks the last known position of each bus on the map."""
    bus_id: str
    latitude: float
    longitude: float
    timestamp_ms: int
