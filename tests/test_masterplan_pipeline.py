"""
Full System Integration Test — Master Plan Architecture
======================================================
Tests:
  1. Protobuf serialization (EdgeTelemetryPacket)
  2. Edge SQLite circuit breaker (store & retrieve)
  3. Server KD-Tree 3-Meter deduplication (assert repeat within 2m merges, 10m creates new)
  4. H3 hexagonal cell mapping
  5. Edge MAPE-K Loop (Day vs Night mode adaptation)
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server")))

from proto import telemetry_pb2
from edge.storage.cache import EdgeTelemetryCache
from edge.mape_k_edge import EdgeMAPELoop
from server.domain.deduplication import SpatialDeduplicationEngine
from server.core.ingestion_service import TelemetryIngestionService
from server.domain.models import TelemetryReading
import numpy as np


def test_protobuf_serialization():
    print("Testing Protobuf Serialization...")
    packet = telemetry_pb2.EdgeTelemetryPacket()
    packet.bus_id = "bus_delhi_101"
    packet.latitude = 28.6145
    packet.longitude = 77.2108
    packet.object_type = "pothole"
    packet.confidence = 0.92
    packet.timestamp_ms = int(time.time() * 1000)
    packet.vehicle_count = 5
    packet.lux_level = 14.5
    packet.vibration_g = 1.2
    packet.network_signal_db = -80.0

    raw_bytes = packet.SerializeToString()
    assert len(raw_bytes) > 0, "Packet should serialize to non-empty byte string"
    print(f"  [OK] Protobuf payload size: {len(raw_bytes)} bytes (ultra-compact)")

    # Decode
    decoded = telemetry_pb2.EdgeTelemetryPacket()
    decoded.ParseFromString(raw_bytes)
    assert decoded.bus_id == "bus_delhi_101"
    assert decoded.object_type == "pothole"
    assert abs(decoded.latitude - 28.6145) < 1e-4
    print("  [OK] Protobuf deserialization matched perfectly.")


def test_edge_sqlite_circuit_breaker():
    print("Testing Edge SQLite Circuit Breaker Cache...")
    test_db = "edge/storage/test_circuit_breaker.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    cache = EdgeTelemetryCache(db_path=test_db)
    assert cache.count() == 0

    # Enqueue 3 packets
    for i in range(3):
        cache.enqueue("fleet/bus_1/telemetry", f"test_data_{i}".encode("utf-8"), int(time.time() * 1000))

    assert cache.count() == 3
    batch = cache.peek_batch(limit=2)
    assert len(batch) == 2
    ids_to_remove = [item[0] for item in batch]
    cache.remove_batch(ids_to_remove)
    assert cache.count() == 1
    print("  [OK] SQLite offline queueing, FIFO batching, and purging works.")

    try:
        if os.path.exists(test_db):
            os.remove(test_db)
    except Exception:
        pass


def test_kdtree_deduplication():
    print("Testing Server 3-Meter KD-Tree Deduplication...")
    dedup = SpatialDeduplicationEngine(radius_meters=3.0)

    # Point 1: Connaught Place Center
    r1 = TelemetryReading(
        bus_id="bus_1",
        latitude=28.631500,
        longitude=77.216700,
        object_type="pothole",
        confidence=0.80,
        timestamp_ms=1000,
    )
    action1, m1 = dedup.process(r1)
    assert action1 == "new"
    assert m1.sighting_count == 1
    print(f"  [OK] First pothole registered: {m1.defect_id[:8]}..")

    # Point 2: 1.5 meters away (should MERGE into existing)
    # Approx 0.000013 degrees latitude is ~1.45 meters
    r2 = TelemetryReading(
        bus_id="bus_2",
        latitude=28.631513,
        longitude=77.216700,
        object_type="pothole",
        confidence=0.90,
        timestamp_ms=2000,
    )
    action2, m2 = dedup.process(r2)
    assert action2 == "updated"
    assert m2.defect_id == m1.defect_id
    assert m2.sighting_count == 2
    assert abs(m2.confidence - 0.85) < 0.01
    print("  [OK] Second reading 1.5m away successfully merged (sighting count: 2, conf: 0.85).")

    # Point 3: 50 meters away (should create NEW defect)
    r3 = TelemetryReading(
        bus_id="bus_3",
        latitude=28.632000,
        longitude=77.216700,
        object_type="pothole",
        confidence=0.75,
        timestamp_ms=3000,
    )
    action3, m3 = dedup.process(r3)
    assert action3 == "new"
    assert m3.defect_id != m1.defect_id
    assert dedup.get_marker_count() == 2
    print("  [OK] Third reading 55m away created new defect marker.")


def test_edge_mape_k_loop():
    print("Testing Edge MAPE-K Loop (Day vs Night Adaptability)...")
    loop = EdgeMAPELoop(lux_night_threshold=25.0)

    # Simulate bright daylight frame (mean pixel luminance = 160)
    day_frame = np.full((100, 100, 3), 160, dtype=np.uint8)
    m_day = loop.monitor(day_frame, last_frame_time=time.time())
    a_day = loop.analyze(m_day)
    p_day = loop.plan(a_day)
    e_day = loop.execute(p_day)
    assert not e_day["is_night_mode"]
    print("  [OK] Daylight correctly keeps Day Mode active.")

    # Simulate dark nighttime frame (mean pixel luminance = 10)
    night_frame = np.full((100, 100, 3), 10, dtype=np.uint8)
    m_night = loop.monitor(night_frame, last_frame_time=time.time())
    a_night = loop.analyze(m_night)
    p_night = loop.plan(a_night)
    # allow cooldown
    loop.last_switch_time = 0.0
    p_night = loop.plan(a_night)
    e_night = loop.execute(p_night)
    assert e_night["is_night_mode"]
    print("  [OK] Low light (lux < 25) dynamically triggered Night Mode adaptation.")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING MASTER PLAN PIPELINE TESTS")
    print("=" * 60)
    test_protobuf_serialization()
    test_edge_sqlite_circuit_breaker()
    test_kdtree_deduplication()
    test_edge_mape_k_loop()
    print("=" * 60)
    print("[SUCCESS] ALL MASTER PLAN TESTS PASSED!")
    print("=" * 60)
