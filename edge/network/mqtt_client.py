"""
Edge MQTT Client with Protobuf Serialization & Offline Burst Recovery
======================================================================
Strictly implements Section 2.1 & 5.2 of Master Plan:
  - Encodes telemetry as binary Protobuf EdgeTelemetryPacket
  - Uses MQTT QoS 1 for reliable delivery
  - Integrates with SQLite cache when offline
  - Bursts queued offline records on reconnection
"""

import sys
import os
import time
import logging
import threading
from typing import Optional, Callable

# Add project root to sys.path to allow proto imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from proto import telemetry_pb2

from paho.mqtt import client as mqtt
from edge.storage.cache import EdgeTelemetryCache

logger = logging.getLogger("EdgeMQTT")


class EdgeMQTTClient:
    def __init__(
        self,
        bus_id: str,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        cache: Optional[EdgeTelemetryCache] = None,
        on_command: Optional[Callable[[dict], None]] = None,
    ):
        self.bus_id = bus_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.cache = cache or EdgeTelemetryCache()
        self.on_command = on_command

        self._connected = False
        self._lock = threading.Lock()

        client_uid = f"edge_{bus_id}_{os.getpid()}"
        try:
            from paho.mqtt.enums import CallbackAPIVersion
            self._client = mqtt.Client(
                callback_api_version=CallbackAPIVersion.VERSION1,
                client_id=client_uid,
                clean_session=False,
            )
        except (ImportError, AttributeError):
            self._client = mqtt.Client(
                client_id=client_uid,
                clean_session=False,
            )

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

    def start(self):
        logger.info(f"[{self.bus_id}] Connecting to MQTT broker at {self.broker_host}:{self.broker_port}...")
        try:
            self._client.connect_async(self.broker_host, self.broker_port, keepalive=60)
            self._client.loop_start()
        except Exception as e:
            logger.warning(f"[{self.bus_id}] Initial MQTT connection failed: {e}. Offline buffer active.")

    def stop(self):
        self._client.loop_stop()
        self._client.disconnect()
        logger.info(f"[{self.bus_id}] MQTT client disconnected.")

    @property
    def is_connected(self) -> bool:
        return self._connected

    def publish_telemetry(
        self,
        latitude: float,
        longitude: float,
        object_type: str,
        confidence: float,
        vehicle_count: int,
        lux_level: float,
        vibration_g: float = 0.0,
        network_signal_db: float = -75.0,
        timestamp_ms: Optional[int] = None,
    ):
        ts = timestamp_ms or int(time.time() * 1000)

        # 1. Build Protobuf message
        packet = telemetry_pb2.EdgeTelemetryPacket()
        packet.bus_id = self.bus_id
        packet.latitude = float(latitude)
        packet.longitude = float(longitude)
        packet.object_type = str(object_type)
        packet.confidence = float(confidence)
        packet.timestamp_ms = int(ts)
        packet.vehicle_count = int(vehicle_count)
        packet.lux_level = float(lux_level)
        packet.vibration_g = float(vibration_g)
        packet.network_signal_db = float(network_signal_db)

        payload_bytes = packet.SerializeToString()
        topic = f"fleet/{self.bus_id}/telemetry"

        # 2. Transmit or buffer
        if self._connected:
            info = self._client.publish(topic, payload_bytes, qos=1)
            if info.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"[{self.bus_id}] Published Protobuf packet ({len(payload_bytes)} bytes)")
                return
            else:
                logger.warning(f"[{self.bus_id}] Publish failed (rc={info.rc}), buffering to SQLite...")

        # If disconnected or publish returned error: buffer into SQLite circuit breaker
        self.cache.enqueue(topic, payload_bytes, ts)
        logger.info(f"[{self.bus_id}] 📴 Buffered offline Protobuf packet to SQLite (Queue: {self.cache.count()})")

    def publish_heartbeat(self, yolo_fps: float, cpu_temp_c: float = 48.0, camera_ok: bool = True):
        """Publishes edge health diagnostics as Protobuf HeartbeatPacket."""
        if not self._connected:
            return

        heartbeat = telemetry_pb2.HeartbeatPacket()
        heartbeat.bus_id = self.bus_id
        heartbeat.cpu_temp_c = float(cpu_temp_c)
        heartbeat.ram_usage_mb = 350.0
        heartbeat.yolo_fps = float(yolo_fps)
        heartbeat.camera_ok = bool(camera_ok)
        heartbeat.timestamp_ms = int(time.time() * 1000)

        payload = heartbeat.SerializeToString()
        topic = f"fleet/{self.bus_id}/heartbeat"
        self._client.publish(topic, payload, qos=0)

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            logger.info(f"[{self.bus_id}] ✅ Connected to MQTT broker (QoS 1)")
            # Subscribe to inbound command topic from server (K-M Plugin)
            command_topic = f"fleet/{self.bus_id}/command"
            self._client.subscribe(command_topic, qos=1)
            logger.info(f"[{self.bus_id}] Subscribed to commands on {command_topic}")

            # Burst upload any buffered offline telemetry
            threading.Thread(target=self._burst_offline_cache, daemon=True).start()
        else:
            logger.error(f"[{self.bus_id}] MQTT connection rejected (rc={rc})")

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        logger.warning(f"[{self.bus_id}] ❌ MQTT disconnected (rc={rc}) — switching to SQLite offline cache")

    def _on_message(self, client, userdata, msg):
        try:
            req = telemetry_pb2.MediaSyncRequest()
            req.ParseFromString(msg.payload)
            logger.info(f"[{self.bus_id}] 📹 Received MediaSyncRequest from server for defect: {req.defect_id}")
            if self.on_command:
                self.on_command({
                    "bus_id": req.bus_id,
                    "timestamp_ms": req.timestamp_ms,
                    "clip_duration": req.clip_duration,
                    "defect_id": req.defect_id,
                })
        except Exception as e:
            logger.error(f"[{self.bus_id}] Failed to parse incoming command: {e}")

    def _burst_offline_cache(self):
        """Burst-uploads queued packets upon reconnection (Section 5.2)."""
        pending = self.cache.count()
        if pending == 0:
            return

        logger.info(f"[{self.bus_id}] 🚀 Reconnected! Bursting {pending} buffered offline packets to broker...")
        while self._connected:
            batch = self.cache.peek_batch(limit=25)
            if not batch:
                break

            success_ids = []
            for record_id, topic, payload in batch:
                if not self._connected:
                    break
                info = self._client.publish(topic, payload, qos=1)
                info.wait_for_publish(timeout=2.0)
                if info.is_published():
                    success_ids.append(record_id)

            self.cache.remove_batch(success_ids)
            time.sleep(0.05)  # Slight throttle to prevent network flooding

        logger.info(f"[{self.bus_id}] ✅ Offline cache burst upload complete.")
