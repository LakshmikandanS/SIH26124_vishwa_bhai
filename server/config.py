"""
PAIR B — Server Configuration Constants
"""

import os

# ── MQTT ──────────────────────────────────────────
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_CLIENT_ID   = os.getenv("MQTT_CLIENT_ID", "sih_server_core")
MQTT_TOPIC_SUBSCRIBE = "fleet/+/telemetry"   # Wildcard: all buses
MQTT_TOPIC_COMMAND   = "fleet/{bus_id}/command"
MQTT_QOS = 1

# ── FastAPI Server ────────────────────────────────
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# ── Spatial Deduplication ─────────────────────────
DEDUP_RADIUS_METERS = 3.0         # Group defects within 3 meters
DEDUP_WINDOW_SECONDS = 300        # 5-minute sliding window

# ── H3 Hexagonal Grid ────────────────────────────
H3_RESOLUTION = 9                 # ~174m edge-length hex cells

# ── WebSocket ────────────────────────────────────
WS_ENDPOINT = "/ws/dashboard"
