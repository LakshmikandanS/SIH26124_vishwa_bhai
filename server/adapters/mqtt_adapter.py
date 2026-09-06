"""
Server-Side MQTT Ingress Adapter with Protobuf Deserialization
=============================================================
Strictly implements Section 1 & 2.2 of Master Plan:
  - Subscribes to fleet/+/telemetry and fleet/+/heartbeat
  - Deserializes binary Protobuf EdgeTelemetryPacket
  - Bridges into Hexagonal Ingestion Port
  - Supports publishing command messages (K-M Plugin)
"""

import sys
import os
import json
import logging
from typing import Callable, Optional

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from proto import telemetry_pb2

from paho.mqtt import client as mqtt

from config import (
    MQTT_BROKER_HOST,
    MQTT_BROKER_PORT,
    MQTT_CLIENT_ID,
    MQTT_TOPIC_SUBSCRIBE,
    MQTT_QOS,
)
from domain.models import TelemetryReading

logger = logging.getLogger("MQTTAdapter")


class MQTTInboundAdapter:
    def __init__(
        self,
        on_telemetry: Optional[Callable[[TelemetryReading], None]] = None,
        on_heartbeat: Optional[Callable[[dict], None]] = None,
    ):
        self._on_telemetry = on_telemetry
        self._on_heartbeat = on_heartbeat

        try:
            from paho.mqtt.enums import CallbackAPIVersion
            self._client = mqtt.Client(
                callback_api_version=CallbackAPIVersion.VERSION1,
                client_id=MQTT_CLIENT_ID,
                clean_session=False,
            )
        except (ImportError, AttributeError):
            self._client = mqtt.Client(
                client_id=MQTT_CLIENT_ID,
                clean_session=False,
            )

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect
        self._connected = False

    def start(self):
        logger.info(f"[MQTT] Connecting to broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}...")
        try:
            self._client.connect_async(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=60)
            self._client.loop_start()
            logger.info("[MQTT] ✅ Broker connection loop initiated")
        except Exception as e:
            logger.error(f"[MQTT] ❌ Failed to initiate connection: {e}")

    def stop(self):
        self._client.loop_stop()
        self._client.disconnect()
        logger.info("[MQTT] Adapter disconnected.")

    def publish_command(self, bus_id: str, defect_id: str, timestamp_ms: int, clip_duration: int = 2):
        """Sends a MediaSyncRequest Protobuf packet to an edge transit node (K-M Plugin)."""
        req = telemetry_pb2.MediaSyncRequest()
        req.bus_id = bus_id
        req.defect_id = defect_id
        req.timestamp_ms = timestamp_ms
        req.clip_duration = clip_duration

        payload = req.SerializeToString()
        topic = f"fleet/{bus_id}/command"
        self._client.publish(topic, payload, qos=MQTT_QOS)
        logger.info(f"[MQTT] Dispatched MediaSyncRequest to {topic} for defect {defect_id}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            logger.info(f"[MQTT] ✅ Connected to broker. Subscribing to: {MQTT_TOPIC_SUBSCRIBE}")
            client.subscribe(MQTT_TOPIC_SUBSCRIBE, qos=MQTT_QOS)
            client.subscribe("fleet/+/heartbeat", qos=0)
        else:
            logger.error(f"[MQTT] ❌ Connection failed with return code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        if rc != 0:
            logger.warning(f"[MQTT] Broker connection lost (rc={rc}) — auto-reconnecting...")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload

        if "/heartbeat" in topic:
            self._handle_heartbeat(payload)
            return

        reading = self._parse_telemetry(payload)
        if reading and self._on_telemetry:
            self._on_telemetry(reading)

    def _parse_telemetry(self, raw: bytes) -> Optional[TelemetryReading]:
        """Deserializes Protobuf payload, falling back to JSON for test convenience."""
        # 1. Attempt Protobuf Deserialization
        try:
            packet = telemetry_pb2.EdgeTelemetryPacket()
            packet.ParseFromString(raw)
            return TelemetryReading(
                bus_id=packet.bus_id,
                latitude=float(packet.latitude),
                longitude=float(packet.longitude),
                object_type=packet.object_type,
                confidence=float(packet.confidence),
                timestamp_ms=int(packet.timestamp_ms),
                vehicle_count=int(packet.vehicle_count),
                lux_level=float(packet.lux_level),
                vibration_g=float(packet.vibration_g),
                network_signal_db=float(packet.network_signal_db),
            )
        except Exception:
            pass

        # 2. Fallback JSON Parsing
        try:
            data = json.loads(raw.decode("utf-8"))
            return TelemetryReading(
                bus_id=data["bus_id"],
                latitude=float(data["latitude"]),
                longitude=float(data["longitude"]),
                object_type=data.get("object_type", "unknown"),
                confidence=float(data.get("confidence", 0.5)),
                timestamp_ms=int(data.get("timestamp_ms", 0)),
                vehicle_count=int(data.get("vehicle_count", 1)),
                lux_level=float(data.get("lux_level", 100.0)),
                vibration_g=float(data.get("vibration_g", 0.0)),
                network_signal_db=float(data.get("network_signal_db", -75.0)),
            )
        except Exception as e:
            logger.warning(f"[MQTT] Failed to deserialize payload: {e}")
            return None

    def _handle_heartbeat(self, raw: bytes):
        try:
            hb = telemetry_pb2.HeartbeatPacket()
            hb.ParseFromString(raw)
            if self._on_heartbeat:
                self._on_heartbeat({
                    "bus_id": hb.bus_id,
                    "cpu_temp_c": hb.cpu_temp_c,
                    "ram_usage_mb": hb.ram_usage_mb,
                    "yolo_fps": hb.yolo_fps,
                    "camera_ok": hb.camera_ok,
                    "timestamp_ms": hb.timestamp_ms,
                })
        except Exception:
            pass
