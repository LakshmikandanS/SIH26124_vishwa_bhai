"""
Urban AI Fleet Intelligence — Edge Bus Emulator
===============================================
Production-grade Edge Transit Node implementation aligning with:
  - Section 2.1 (Edge Capture Environment)
  - Section 5.1 (Local Edge MAPE-K Loop for Night Adaptation & Self-Healing)
  - Section 5.2 (Protobuf Serialization + SQLite Circuit Breaker)
"""

import sys
import os
import argparse
import csv
import time
import logging
import cv2
import numpy as np

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from edge.config import (
    MQTT_BROKER_HOST,
    MQTT_BROKER_PORT,
    LUX_NIGHT_THRESHOLD,
    VIBRATION_THRESHOLD_G,
)
from edge.mape_k_edge import EdgeMAPELoop
from edge.inference import EdgeMultiModelEngine
from edge.network.mqtt_client import EdgeMQTTClient
from edge.storage.cache import EdgeTelemetryCache

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("BusEmulator")


def load_gps_track(csv_path: str) -> list[dict]:
    """Loads mock GPS coordinate sequence from CSV."""
    track = []
    if not os.path.exists(csv_path):
        logger.warning(f"[GPS] Track file {csv_path} not found — generating fallback Delhi coordinates")
        return [{"latitude": 28.614506, "longitude": 77.210812}]

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                track.append({
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"]),
                })
            except (ValueError, KeyError):
                continue

    if not track:
        track.append({"latitude": 28.614506, "longitude": 77.210812})
    logger.info(f"[GPS] Loaded {len(track)} coordinate waypoints from {csv_path}")
    return track


def run_emulator(
    bus_id: str,
    video_path: str,
    route_csv: str,
    target_fps: int = 15,
    loop_video: bool = True,
    save_video_path: str = None,
):
    logger.info(f"[{bus_id}] Initializing Edge Transit Node...")
    gps_track = load_gps_track(route_csv)

    # Initialize Edge Modules
    cache = EdgeTelemetryCache(db_path=f"edge/storage/{bus_id}_cache.db")
    mqtt_client = EdgeMQTTClient(
        bus_id=bus_id,
        broker_host=MQTT_BROKER_HOST,
        broker_port=MQTT_BROKER_PORT,
        cache=cache,
    )
    mqtt_client.start()

    mape_loop = EdgeMAPELoop(
        lux_night_threshold=LUX_NIGHT_THRESHOLD,
        vibration_blur_threshold_g=VIBRATION_THRESHOLD_G,
        target_fps=float(target_fps),
    )

    inference_engine = EdgeMultiModelEngine(models_dir="edge/models")

    # Open Video Source
    if not os.path.exists(video_path):
        logger.error(f"[{bus_id}] Video source not found at: {video_path}")
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"[{bus_id}] OpenCV failed to open video source: {video_path}")
        return

    fps_in = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    logger.info(f"[{bus_id}] Video stream opened: {width}x{height} @ {fps_in:.1f} FPS ({total_frames} frames)")

    video_writer = None
    if save_video_path:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        video_writer = cv2.VideoWriter(save_video_path, fourcc, fps_in, (width, height))
        logger.info(f"[{bus_id}] Recording annotated feed to {save_video_path}")

    frame_index = 0
    last_frame_time = time.time()
    last_heartbeat_time = time.time()

    # Frame processing interval
    frame_step = max(1, int(fps_in / target_fps))

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                if loop_video:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    frame_index = 0
                    continue
                else:
                    break

            frame_index += 1
            if frame_index % frame_step != 0:
                continue

            # ── 1. LOCAL EDGE MAPE-K LOOP ─────────────────────────
            metrics = mape_loop.monitor(frame, last_frame_time=last_frame_time)
            analysis = mape_loop.analyze(metrics)
            plan = mape_loop.plan(analysis)
            adaptation = mape_loop.execute(plan)

            if adaptation["drop_frame"]:
                logger.warning(f"[{bus_id}] Dropping frame #{frame_index} due to excessive vibration blur")
                continue

            # ── 2. MULTI-MODEL INFERENCE (ADAPTIVE NIGHT SWITCH) ───
            infer_result = inference_engine.detect(
                frame,
                is_night_mode=adaptation["is_night_mode"],
            )

            # ── 3. GPS MATRIX SYNCHRONIZATION ─────────────────────
            # 1 GPS waypoint per second (or cycle through track)
            gps_idx = (frame_index // int(fps_in)) % len(gps_track)
            current_gps = gps_track[gps_idx]

            # ── 4. PROTOBUF SERIALIZATION & TRANSMISSION ──────────
            vehicle_count = infer_result["vehicles"]
            defects = infer_result["defects"]

            # If defects were found, publish an edge telemetry packet for each
            if defects:
                for defect in defects:
                    mqtt_client.publish_telemetry(
                        latitude=current_gps["latitude"],
                        longitude=current_gps["longitude"],
                        object_type=defect["type"],
                        confidence=defect["confidence"],
                        vehicle_count=vehicle_count,
                        lux_level=metrics["lux"],
                    )
            else:
                # Still publish periodic vehicle presence/traffic telemetry every 30 frames
                if frame_index % (frame_step * 5) == 0:
                    mqtt_client.publish_telemetry(
                        latitude=current_gps["latitude"],
                        longitude=current_gps["longitude"],
                        object_type="traffic_survey",
                        confidence=1.0,
                        vehicle_count=vehicle_count,
                        lux_level=metrics["lux"],
                    )

            # ── 5. EDGE HEARTBEAT EMISSION ────────────────────────
            now = time.time()
            if now - last_heartbeat_time >= 5.0:
                mqtt_client.publish_heartbeat(yolo_fps=metrics["fps"])
                last_heartbeat_time = now

            # Optional video annotation writing
            if video_writer:
                for d in defects:
                    b = d["bbox"]
                    cv2.rectangle(frame, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), (0, 0, 255), 2)
                    cv2.putText(
                        frame,
                        f"{d['type']} {d['confidence']:.2f}",
                        (int(b[0]), int(b[1]) - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 0, 255),
                        2,
                    )
                video_writer.write(frame)

            last_frame_time = time.time()

            # Dynamic pacing
            time.sleep(1.0 / target_fps)

    except KeyboardInterrupt:
        logger.info(f"[{bus_id}] Interrupted by user.")
    finally:
        cap.release()
        if video_writer:
            video_writer.release()
        mqtt_client.stop()
        logger.info(f"[{bus_id}] Edge Transit Node shut down cleanly.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Urban AI Fleet — Edge Bus Emulator")
    parser.add_argument("--bus-id", default="bus_1", help="Unique identifier for this transit bus")
    parser.add_argument("--video", default="edge/assets/test_dashcam.mp4", help="Path to input dashcam video")
    parser.add_argument("--route", default="edge/gps_tracks/route_1.csv", help="Path to GPS trajectory CSV")
    parser.add_argument("--fps", type=int, default=10, help="Target inference FPS")
    parser.add_argument("--save-video", default=None, help="Optional output path for annotated video")
    args = parser.parse_args()

    run_emulator(
        bus_id=args.bus_id,
        video_path=args.video,
        route_csv=args.route,
        target_fps=args.fps,
        save_video_path=args.save_video,
    )
