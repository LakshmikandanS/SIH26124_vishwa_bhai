# Smart India Hackathon (SIH) Project Plan: Industrial-Grade Edge AI Fleet Intelligence
## Upgrading the Architectural Blueprint from 8.5 to 10/10

This blueprint outlines how to convert the conceptual design into an industrial-grade, production-ready system while creating a fully functional, lightweight prototype environment executable on a standard developer laptop for the **Smart India Hackathon (SIH)** evaluation.

---

## 🛠️ 1. Core Engineering Upgrades for Industrial Grade (The 10/10 Formula)

To achieve a true industrial-grade rating, the architecture must solve real-world field deployment challenges like unstable connectivity, bandwidth cost constraints, and predictive hardware maintenance.

### 1.1 Edge Connection Resilience (Network Fault Tolerance)
* **The Real-World Problem:** Transit vehicles move through underground tunnels, under heavy flyovers, and into cellular dead zones. If connectivity drops, standard real-time web-streaming solutions drop packets, corrupting historical analysis.
* **The 10/10 Solution:** 
  * Configure the MQTT client on the vehicle with **QoS 1 (At Least Once Delivery)** and establish **Persistent Sessions (`clean_session=false`)**.
  * Integrate an on-board **SQLite buffer database** at the edge layer. When cellular networks drop, the K-MAPE Monitor loop serializes the Protobuf arrays and writes them directly to local disk storage. 
  * Upon network restoration, the system triggers a background worker thread to burst-upload the backlogged chronological logs to the central monolith, guaranteeing zero data loss.

### 1.2 Command-Driven Adaptive Video Pulling
* **The Real-World Problem:** Continuously streaming raw high-definition video feeds over 4G/5G mobile networks chokes regional infrastructure and leads to massive cellular data bills.
* **The 10/10 Solution:** 
  * Execute a **circular ring buffer** in the edge device's RAM, keeping strictly the last **30 seconds** of raw video tracking locally. 
  * When a high-confidence infrastructure anomaly is identified, only the 40-byte Protobuf text payload is sent to the server.
  * If the Monolithic Core evaluates that the anomaly is severe, unique, or needs human audit, it publishes an outbound message to a dedicated command topic via the `MediaSyncRequest` data schema. 
  * The edge device catches this instruction, crops exactly **2 seconds** around the target timestamp, compresses it to an H.265/HEVC container, and uploads it asynchronously to the cloud storage layer (AWS S3/MinIO).

### 1.3 Edge Diagnostics & Remote Heartbeat Monitoring
* **The Real-World Problem:** In large municipal operations, system engineers do not know if an onboard camera is blurred, dusty, disconnected, or if the edge NPU is overheating until vital telemetry is missed.
* **The 10/10 Solution:** 
  * Introduce an isolated diagnostic lifecycle thread inside the microkernel framework. 
  * Every 10 seconds, the edge hardware broadcasts a tiny `Heartbeat` packet containing thermal state parameters, RAM consumption, camera stream validation checks, and current YOLO model operational FPS.

---

## 💻 2. The SIH Multi-Vehicle Simulation Topology (Laptop Mockup)

You do not need real transit buses or dedicated NVIDIA Jetson Orin hardware to impress the SIH jury. By utilizing a containerized architecture on a single developer laptop, you can emulate a real-world municipal infrastructure.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        YOUR LAPTOP (DOCKER ENVIRONMENT)                │
│                                                                        │
│ ┌─────────────────────────┐  (Protobuf)  ┌───────────────────────────┐ │
│ │ Bus Emulators (x5)      │ ───────────> │ Eclipse Mosquitto         │ │
│ │ - OpenCV Video Feed     │     MQTT     │ (MQTT Broker Container)   │ │
│ │ - YOLOv8-Nano (INT8)    │              └─────────────┬─────────────┘ │
│ └─────────────────────────┘                            │               │
│                                                        ▼               │
│ ┌─────────────────────────┐  (WebSockets)┌───────────────────────────┐ │
│ │ React/HTML5 Map UI      │ <─────────── │ Monolithic Core Server    │ │
│ │ - Leaflet / Mapbox Map  │              │ - FastAPI/Go Ingestion    │ │
│ │ - Uber H3 Hex Grids     │              │ - In-Memory KD-Tree Cache │ │
│ └─────────────────────────┘              └───────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.1 The Bus Emulator Layer (`bus_emulator.py`)
* **How it operates:** Instead of a physical camera, write a Python script that reads a pre-recorded dashcam video file of an Indian street scene using **OpenCV (`cv2.VideoCapture`)**.
* **AI Execution:** Feed the frames directly into a highly compressed, optimized **YOLOv8-Nano (`yolov8n.pt`)** model. This runs comfortably on standard laptop CPUs at high frame-rates.
* **Spatial Mapping:** Read spatial positions sequentially from a pre-defined mock GPS track file (a simple CSV array storing coordinates along a real city route).
* **Transmission:** When YOLO detects a road defect, match it to the active CSV row coordinate, compile it via the `EdgeTelemetryPacket` Protobuf compiler, and publish it immediately.

### 2.2 Ingress Protocol Layer (The Local Broker)
* Spin up a local **Eclipse Mosquitto MQTT Broker** inside a lightweight Docker container. 
* This container isolates network ingestion, processing thousands of simulated messages over `localhost:1883` with zero compute overhead.

### 2.3 The High-Performance Core Monolith Server
* Construct your ingestion core using **Python (FastAPI)** or **Go**.
* **Zero-Network Deduplication:** Maintain an active in-memory spatial grid using a **KD-Tree (`scipy.spatial.KDTree`)** for rapid 3-meter spatial distance checking, alongside the **Uber H3 Index** library to accumulate macro density scores.
* **Egress Engine:** Push real-time, consolidated changes directly to the web dashboard through a persistent WebSocket loop.

### 2.4 The Presentation Front-End Web Dashboard
* Create a single-page interactive interface using **Leaflet.js** or **Mapbox GL JS**.
* Display the **5 virtual buses** moving along their designated coordinate routes simultaneously.
* As defects are uncovered in the video container track, real-time alert pins materialize on the map instantly, and relevant H3 index tiles dynamically transition color based on traffic concentration.

---

## 🏆 3. The SIH Pitch & Jury Demonstration Strategy

To maximize evaluation scoring, focus the presentation around scalable engineering, fiscal logic, and system resilience.

1. **The Economic Value Argument:** 
   * *"Sir/Ma'am, traditional architectures stream raw high-definition video to remote clouds, costing transit authorities thousands of rupees per month per vehicle in cellular data billing. Our architecture processes frames locally on the edge and transmits ultra-compressed 40-byte Protobuf payloads, slashing operating network billing by over 90% while relieving pressure on central servers."*
2. **Demonstrate Scale via Concurrency:** 
   * Open up your terminal or Docker dashboard interface for the judges. Show **5 parallel terminal threads/containers** processing individual live video streams concurrently, proving that your server architecture handles high-velocity incoming streaming data easily inside unified memory.
3. **The Chaos Engineering Test (The Winning Move):** 
   * During evaluation, manually sever your laptop's Wi-Fi link or kill one of the active bus emulator scripts. 
   * Demonstrate how the edge emulator smoothly switches to saving telemetry locally inside SQLite, and how the core server monolithic architecture maintains system uptime without crashing. This confirms to the jury that the project is completely industrial grade.