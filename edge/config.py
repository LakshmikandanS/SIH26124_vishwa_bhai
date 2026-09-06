"""
PAIR A — Edge Configuration Constants
"""

# ── MQTT ──────────────────────────────────────────
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC_TELEMETRY = "fleet/{bus_id}/telemetry"
MQTT_TOPIC_COMMAND   = "fleet/{bus_id}/command"
MQTT_TOPIC_HEARTBEAT = "fleet/{bus_id}/heartbeat"
MQTT_QOS = 1

# ── YOLO ──────────────────────────────────────────
YOLO_MODEL_PATH = "yolov8n.pt"          # Downloaded automatically by ultralytics
YOLO_CONFIDENCE_THRESHOLD = 0.50       # Minimum confidence to publish an event
YOLO_TARGET_FPS = 10                   # Process every Nth frame to reduce CPU load

# ── Edge MAPE-K Thresholds ────────────────────────
LUX_NIGHT_THRESHOLD = 15.0             # Below this → activate night pipeline
VIBRATION_THRESHOLD_G = 2.5           # Above this → reduce FPS
SIGNAL_WEAK_DBM = -90.0               # Below this → increase compression
