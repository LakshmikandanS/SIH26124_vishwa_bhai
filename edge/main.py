"""
RouteSense Urban AI Fleet Intelligence — Edge Transit Node Main Runner
=====================================================================
Usage:
    python main.py --source test2.mp4 --show-video --verbose
    python edge/main.py --source edge/assets/test_dashcam.mp4 --show-video --verbose

Features:
  - 3 YOLO Models running in parallel (Traffic, Pothole, Hazard/Segmentation)
  - Real-time OpenCV video detection window with Top & Bottom HUD banners
  - Structured live telemetry terminal output matching edge format:
    [{timestamp}] Heading: {heading} | GPS: ({lat}, {lon}) | Defects: {defects} | Traffic: {traffic} | Net: {net_status}
  - Protobuf serialization over MQTT with SQLite offline circuit breaker cache
"""

import sys
import os
import argparse
import time
import math
import csv
from datetime import datetime, timezone
import cv2
import numpy as np

from typing import Union, Optional, Tuple
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

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

try:
    from edge.video_ingestor import VideoIngestor, parse_aspect_ratio
except ImportError:
    from video_ingestor import VideoIngestor, parse_aspect_ratio


def calculate_heading(lat1: float, lon1: float, lat2: float, lon2: float) -> str:
    """Calculates 8-point compass heading between two GPS points."""
    if lat1 == lat2 and lon1 == lon2:
        return "NE"
    d_lon = math.radians(lon2 - lon1)
    y = math.sin(d_lon) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - \
        math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(d_lon)
    bearing = (math.degrees(math.atan2(y, x)) + 360) % 360
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = int((bearing + 22.5) / 45) % 8
    return directions[idx]


def load_gps_track(csv_path: str) -> list[dict]:
    """Loads mock GPS coordinate sequence from CSV or falls back to coordinates."""
    track = []
    if os.path.exists(csv_path):
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
        # Default route sequence
        track = [
            {"latitude": 28.614506, "longitude": 77.210812},
            {"latitude": 28.615200, "longitude": 77.211500},
            {"latitude": 28.616100, "longitude": 77.212400},
            {"latitude": 28.617000, "longitude": 77.213200},
            {"latitude": 28.618100, "longitude": 77.214100},
            {"latitude": 28.619200, "longitude": 77.215300},
        ]
    return track


def run_edge_node(
    source: str,
    show_video: bool = False,
    verbose: bool = True,
    bus_id: str = "bus_1",
    route_csv: str = "edge/gps_tracks/route_1.csv",
    target_fps: int = 15,
    save_video: str = None,
    broker_host: str = MQTT_BROKER_HOST,
    broker_port: int = MQTT_BROKER_PORT,
    max_frames: int = None,
    target_aspect_ratio: Optional[Union[float, str]] = "16:9",
    crop_anchor: str = "center",
    loop_video: bool = True,
    **kwargs,
):
    # Support format / aspect_ratio alias from kwargs if provided
    if "aspect_ratio" in kwargs and kwargs["aspect_ratio"] is not None:
        target_aspect_ratio = kwargs["aspect_ratio"]
    if "format" in kwargs and kwargs["format"] is not None:
        target_aspect_ratio = kwargs["format"]
    if "video_format" in kwargs and kwargs["video_format"] is not None:
        target_aspect_ratio = kwargs["video_format"]

    # Resolve source path if not a hardware camera index or network stream
    str_source = str(source).strip()
    is_live_stream = str_source.isdigit() or str_source.startswith(("rtsp://", "http://", "https://"))
    if not is_live_stream and not os.path.exists(source):
        # Check if file exists in assets/ or edge/assets/
        candidate1 = os.path.join(os.path.dirname(__file__), "assets", source)
        candidate2 = os.path.join(BASE_DIR, "edge", "assets", source)
        if os.path.exists(candidate1):
            source = candidate1
        elif os.path.exists(candidate2):
            source = candidate2
        else:
            default_asset = os.path.join(os.path.dirname(__file__), "assets", "test_dashcam.mp4")
            if not os.path.exists(default_asset):
                default_asset = os.path.join(BASE_DIR, "edge", "assets", "test_dashcam.mp4")
            if os.path.exists(default_asset):
                print(f"[Notice] Source '{source}' not found. Falling back to default: {default_asset}")
                source = default_asset
            else:
                print(f"[Error] Video source '{source}' not found!")
                return

    # Resolve route CSV path
    if not os.path.exists(route_csv):
        candidate_route = os.path.join(BASE_DIR, route_csv)
        if os.path.exists(candidate_route):
            route_csv = candidate_route

    gps_track = load_gps_track(route_csv)

    # Initialize Edge Storage & MQTT
    cache_path = os.path.join(BASE_DIR, "edge", "storage", f"{bus_id}_cache.db")
    cache = EdgeTelemetryCache(db_path=cache_path)
    mqtt_client = EdgeMQTTClient(
        bus_id=bus_id,
        broker_host=broker_host,
        broker_port=broker_port,
        cache=cache,
    )
    mqtt_client.start()

    # Initialize MAPE-K & Parallel Inference Engine
    mape_loop = EdgeMAPELoop(
        lux_night_threshold=LUX_NIGHT_THRESHOLD,
        vibration_blur_threshold_g=VIBRATION_THRESHOLD_G,
        target_fps=float(target_fps),
    )
    models_dir = os.path.join(BASE_DIR, "edge", "models")
    inference_engine = EdgeMultiModelEngine(models_dir=models_dir)

    # Open Video Source using VideoIngestor
    ingestor = VideoIngestor(
        source=source,
        loop_video=loop_video,
        target_aspect_ratio=target_aspect_ratio,
        crop_anchor=crop_anchor,
    )
    if not ingestor.open():
        print(f"[Error] Failed to open video source: {source}")
        mqtt_client.stop()
        return

    cap = ingestor.cap
    fps_in = ingestor.fps
    width, height = ingestor.dimensions
    total_frames = ingestor.frame_count

    if verbose:
        print(f"================================================================================")
        print(f" RouteSense Urban AI Edge Node [{bus_id.upper()}] Initialized")
        format_info = f" -> Format: {width}x{height} (Aspect: {ingestor.target_aspect_ratio:.2f}, Anchor: {crop_anchor})" if ingestor.target_aspect_ratio else ""
        print(f" Source: {source} ({ingestor.orig_dimensions[0]}x{ingestor.orig_dimensions[1]} @ {fps_in:.1f} FPS, {total_frames} frames){format_info}")
        print(f" Models: 3 Concurrent YOLO Engines (Traffic + Pothole + Segmentation)")
        print(f" GUI Display: {'ENABLED' if show_video else 'DISABLED (Headless)'}")
        print(f"================================================================================")

    writer = None
    if save_video:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(save_video, fourcc, fps_in, (width, height))

    window_name = f"RouteSense AI Edge Node — [{bus_id.upper()}] Real-Time Detection"
    if show_video:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 1020, 620)

    frame_index = 0
    processed_count = 0
    frame_step = max(1, int(fps_in / target_fps))
    last_frame_time = time.time()
    last_heartbeat_time = time.time()

    try:
        while True:
            ret, frame = ingestor.read()
            if not ret or frame is None:
                break

            frame_index += 1
            if frame_index % frame_step != 0:
                continue

            processed_count += 1
            if max_frames and processed_count > max_frames:
                break

            now_t = time.time()
            instant_fps = 1.0 / max(0.001, (now_t - last_frame_time))

            # ── 1. Local Edge MAPE-K Loop ─────────────────────────────
            metrics = mape_loop.monitor(frame, last_frame_time=last_frame_time)
            analysis = mape_loop.analyze(metrics)
            plan = mape_loop.plan(analysis)
            adaptation = mape_loop.execute(plan)

            if adaptation["drop_frame"]:
                continue

            # ── 2. Parallel 3-Model Inference ─────────────────────────
            results = inference_engine.detect_parallel(
                frame,
                is_night_mode=adaptation["is_night_mode"],
            )

            # ── 3. GPS & Heading Calculation ──────────────────────────
            # Monotonically advance GPS waypoint across video loops so the bus travels steadily forward
            gps_idx = (processed_count // max(1, int(target_fps))) % len(gps_track)
            next_idx = (gps_idx + 1) % len(gps_track)
            curr_gps = gps_track[gps_idx]
            next_gps = gps_track[next_idx]
            heading = calculate_heading(
                curr_gps["latitude"], curr_gps["longitude"],
                next_gps["latitude"], next_gps["longitude"],
            )

            # ── 4. Network Status & Protobuf Telemetry Publishing ──────
            is_online = mqtt_client.is_connected
            cached_count = cache.count()
            if is_online:
                net_status = "ONLINE (MQTT)"
            else:
                net_status = "OFFLINE (CACHED)"

            # Publish defect telemetry
            if results["defects"]:
                for defect in results["defects"]:
                    mqtt_client.publish_telemetry(
                        latitude=curr_gps["latitude"],
                        longitude=curr_gps["longitude"],
                        object_type=defect["type"],
                        confidence=defect["confidence"],
                        vehicle_count=results["vehicles_count"],
                        lux_level=metrics["lux"],
                    )
            elif frame_index % (frame_step * 5) == 0:
                mqtt_client.publish_telemetry(
                    latitude=curr_gps["latitude"],
                    longitude=curr_gps["longitude"],
                    object_type="traffic_survey",
                    confidence=1.0,
                    vehicle_count=results["vehicles_count"],
                    lux_level=metrics["lux"],
                )

            # Publish Heartbeat
            if now_t - last_heartbeat_time >= 5.0:
                mqtt_client.publish_heartbeat(yolo_fps=instant_fps)
                last_heartbeat_time = now_t

            # ── 5. Terminal Output (Exact Match with Reference Photo) ──
            if verbose:
                iso_ts = datetime.now(timezone.utc).isoformat()
                
                # Format Defects string
                def_names = results["defect_names"]
                if def_names:
                    defects_str = f"{len(def_names)} found: {def_names}"
                else:
                    defects_str = "None"

                # Format Traffic breakdown string
                total_veh = results["vehicles_count"]
                bk = results["vehicle_breakdown"]
                active_bk = [f"{v} {k}" for k, v in bk.items() if v > 0]
                if active_bk:
                    traffic_str = f"{total_veh} vehicles ({', '.join(active_bk)})"
                else:
                    traffic_str = f"{total_veh} vehicles"

                # Output single line exactly like the reference screenshot
                print(f"[{iso_ts}] Heading: {heading} | GPS: ({curr_gps['latitude']:.6f}, {curr_gps['longitude']:.6f}) | Defects: {defects_str} | Traffic: {traffic_str} | Net: {net_status}")

            # ── 6. Real-time Video Rendering & GUI Window ──────────────
            annotated_frame = inference_engine.render_hud(
                frame=results["processed_frame"],
                results=results,
                bus_id=bus_id,
                gps=curr_gps,
                heading=heading,
                fps=instant_fps,
                lux=metrics["lux"],
                net_status=net_status,
                cached_count=cached_count,
            )

            if writer:
                writer.write(annotated_frame)

            if show_video:
                cv2.imshow(window_name, annotated_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q") or key == 27:  # 'q' or ESC
                    print("\n[Notice] Video stream stopped by user.")
                    break
                elif key == ord(" "):  # Space to pause/resume
                    cv2.waitKey(0)

            last_frame_time = time.time()
            time.sleep(max(0.001, (1.0 / target_fps) - (time.time() - now_t)))

    except KeyboardInterrupt:
        print("\n[Notice] Interrupted by user.")
    finally:
        ingestor.release()
        if writer:
            writer.release()
        if show_video:
            cv2.destroyAllWindows()
        mqtt_client.stop()
        print(f"[Notice] Edge Node [{bus_id.upper()}] stopped cleanly.")


def main():
    parser = argparse.ArgumentParser(
        description="RouteSense Urban AI — Edge Transit Multi-Model Detection Node",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--source", "--video",
        dest="source",
        default="edge/assets/test_dashcam.mp4",
        help="Path to dashcam video file (e.g. test2.mp4 or edge/assets/test_dashcam.mp4)",
    )
    parser.add_argument(
        "--format", "--aspect-ratio", "--target-aspect-ratio",
        dest="aspect_ratio",
        default="16:9",
        help="Target aspect ratio format of source video (e.g. '16:9', '4:3', '1:1', '9:16', '21:9', or 'original'/'none')",
    )
    parser.add_argument(
        "--crop-anchor",
        default="center",
        choices=["center", "middle", "bottom", "top", "left", "right"],
        help="Anchor position when cropping video to target aspect ratio format ('center', 'bottom', 'top', etc.)",
    )
    parser.add_argument(
        "--loop-video",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether to continuously loop video upon reaching EOF",
    )
    parser.add_argument(
        "--show-video",
        action="store_true",
        default=False,
        help="Display OpenCV real-time video window with bounding boxes & HUD overlay",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Print real-time telemetry output stream to terminal",
    )
    parser.add_argument(
        "--bus-id",
        default="bus_1",
        help="Unique Edge Transit Node ID",
    )
    parser.add_argument(
        "--route",
        default="edge/gps_tracks/route_1.csv",
        help="Path to GPS coordinates track CSV",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=15,
        help="Target inference processing FPS",
    )
    parser.add_argument(
        "--save-video",
        default=None,
        help="Optional path to save annotated output video (.mp4)",
    )
    parser.add_argument(
        "--broker-host",
        default=MQTT_BROKER_HOST,
        help="MQTT broker IP/hostname",
    )
    parser.add_argument(
        "--broker-port",
        type=int,
        default=MQTT_BROKER_PORT,
        help="MQTT broker port",
    )

    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Optional limit on number of frames to process before stopping",
    )

    args = parser.parse_args()

    run_edge_node(
        source=args.source,
        show_video=args.show_video,
        verbose=args.verbose,
        bus_id=args.bus_id,
        route_csv=args.route,
        target_fps=args.fps,
        save_video=args.save_video,
        broker_host=args.broker_host,
        broker_port=args.broker_port,
        max_frames=args.max_frames,
        target_aspect_ratio=args.aspect_ratio,
        crop_anchor=args.crop_anchor,
        loop_video=args.loop_video,
    )


if __name__ == "__main__":
    main()
