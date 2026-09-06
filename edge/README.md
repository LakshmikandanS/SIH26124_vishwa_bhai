# 🚍 SURADAK — Edge Transit AI Node

> **Real-Time On-Device Multi-Model Computer Vision, Autonomic MAPE-K Adaptation & Resilient Telemetry Streaming**  
> *Component of SURADAK Urban AI Fleet Intelligence*

---

## 📌 Overview

The **Edge Transit AI Node** (`edge/`) is designed to run directly on municipal transit buses equipped with forward-facing dashcams. Instead of uploading massive streams of raw video to the cloud, the edge node performs **on-device parallel neural inference**, detecting road surface defects and analyzing traffic density in real time.

Detections are packaged into ultra-compact **Google Protocol Buffers** and published over **MQTT**. If a bus enters a cellular dead zone, an on-device **SQLite circuit breaker** automatically buffers all telemetry and flushes it upon reconnection.

---

## 🧠 Core Features & Architecture

### 1. Parallel 3-Model YOLO Vision Engine (`inference.py`)
The node executes three specialized neural network pipelines concurrently:
- **Model A — Pothole Detection**: Identifies road cavities, asphalt voids, and surface depressions.
- **Model B — Traffic Survey & Breakdown**: Detects, tracks, and classifies surrounding vehicles (cars, buses, trucks, motorcycles, bicycles).
- **Model C — Road Hazard Segmentation**: Detects waterlogging, open manholes, and debris using polygon segmentation masks.

### 2. Autonomic MAPE-K Control Loop (`mape_k_edge.py`)
Implements an autonomic feedback loop that continuously optimizes edge computing performance:
- **Monitor**: Measures frame luminosity (LUX) and bus vibration ($G$).
- **Analyze**: Identifies low-light conditions ($\text{LUX} < 30$) or severe vibrations ($G > 2.5$) caused by rough terrain.
- **Plan & Execute**: 
  - Automatically activates **Night Vision Enhancement** (CLAHE contrast equalization) when driving in dark tunnels or at night.
  - Dynamically throttles processing or drops degraded blur frames to prevent thermal throttling and conserve GPU/CPU cycles.

### 3. Offline Circuit Breaker & Protocol Buffers (`storage/cache.py`)
- Serializes telemetry into binary **Google Protocol Buffers** (`proto/telemetry.proto`), cutting cellular payload size by ~80% compared to standard JSON.
- If MQTT broker connection drops, packets are automatically saved to a local SQLite database (`edge/storage/telemetry_cache.db`).
- Once cellular connectivity returns, cached packets are systematically flushed in FIFO order.

### 4. Monotonic GPS Tracking & Route Waypoints (`gps_tracks/`)
Coordinates advance monotonically along real-world urban bus routes:
- `route_1.csv`: Northeast Delhi transit trajectory (102 waypoints)
- `route_2.csv`: South Delhi transit trajectory (102 waypoints)
- `route_3.csv`: Northwest Delhi transit trajectory (102 waypoints)
*The GPS index advances smoothly across video loops (`processed_count // target_fps`), ensuring the bus travels steadily forward along the route without snapping back.*

---

## 🚀 Execution Guide

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Run the Edge Node
From the project root:

```powershell
python main.py --source edge/assets/test_dashcam.mp4 --fps 10 --show-video --verbose
```

### CLI Command Options

| Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--source` / `--video` | `str` | `edge/assets/test_dashcam.mp4` | Path to dashcam video file (e.g. `edge/assets/test2.mp4`) or camera index |
| `--format` / `--aspect-ratio` | `str` | `16:9` | Target format/aspect ratio (`16:9`, `4:3`, `1:1`, `9:16`, `21:9`, `original`/`none`) |
| `--crop-anchor` | `str` | `center` | Crop anchor when adjusting aspect ratio (`center`, `bottom`, `top`, `left`, `right`) |
| `--loop-video` | `flag` | `True` | Automatically rewinds video to beginning upon EOF |
| `--fps` | `int` | `15` | Target inference frame rate |
| `--show-video` | `flag` | `False` | Opens real-time OpenCV desktop window with bounding boxes and HUD overlay |
| `--verbose` | `flag` | `True` | Streams structured telemetry output directly to the terminal |
| `--bus-id` | `str` | `bus_1` | Unique bus identifier (e.g. `bus_1`, `bus_2`) |
| `--route` | `str` | `edge/gps_tracks/route_1.csv` | GPS waypoint CSV file |
| `--broker-host` | `str` | `localhost` | MQTT broker hostname / IP address |
| `--broker-port` | `int` | `1883` | MQTT broker listening port |
| `--save-video` | `str` | `None` | Optional path to export annotated output video (`.mp4`) |

---

## 🖥️ Live Terminal Telemetry Format

When running with `--verbose`, the edge node streams clean, single-line telemetry records:

```text
[2026-09-06T10:15:30Z] Heading: NE | GPS: (28.614506, 77.210812) | Defects: 2 found: ['Pothole', 'Pothole'] | Traffic: 4 vehicles (3 cars, 1 bus) | Net: ONLINE (MQTT)
```

---

## 📁 Directory Structure

```
edge/
├── assets/                  # Test dashcam videos (test_dashcam.mp4, etc.)
├── config.py                # Edge thresholds (Lux, Vibration, Broker settings)
├── gps_tracks/              # Real-world waypoint CSV tracks
│   ├── route_1.csv          # Delhi Route 1 (102 waypoints)
│   ├── route_2.csv          # Delhi Route 2 (102 waypoints)
│   └── route_3.csv          # Delhi Route 3 (102 waypoints)
├── inference.py             # Parallel multi-YOLO inference & HUD overlay rendering
├── main.py                  # Edge transit node execution loop
├── mape_k_edge.py           # Autonomic MAPE-K adaptation loop (Lux & Vibration)
├── network/
│   └── mqtt_client.py       # Paho MQTT publisher with auto-reconnection
└── storage/
    └── cache.py             # SQLite offline circuit breaker storage
```
