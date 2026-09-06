# Smart India Hackathon (SIH) Technical Project Plan
## Urban AI Fleet Intelligence (Edge-Cloud Distributed Hybrid Architecture)

This document contains the complete production-grade blueprint, structural layout, distributed dual MAPE-K state loops, and 6-member parallel workflow designed to pass industrial-grade evaluation and run seamlessly as a prototype on a single demonstration laptop.

---

## 🗺️ 1. Complete System Architecture Matrix

The architecture runs as a performant **Monolith** within a single process memory space on the server, partitioned via the **Microkernel Plugin** pattern and bounded by **Hexagonal Layers**, receiving binary telemetry from independent **Edge Capture Nodes**.

```
                     [ URBAN AI FLEET INTELLIGENCE ARCHITECTURE ]
  ==================================================================================

                     +---------------------------------------+
                     |         EDGE CAPTURE ENVIRONMENT      |
                     |  (Simulated via Multi-Vehicle Docker) |
                     +---------------------------------------+
                                         │
                                         │ Continuous Streaming
                                         │ (Protobuf over MQTT QoS 1)
                                         ▼
                     +---------------------------------------+
                     |        INGRESS & ADAPTER LAYER        |
                     |     (Eclipse Mosquitto MQTT Broker)   |
                     +---------------------------------------+
                                         │
                                         │ Deserialized Events
                                         ▼
  ┌────────────────────────────────────────────────────────────────────────────────┐
  │                        HYBRID CORE MONOLITH ENGINE                             │
  │                                                                                │
  │   +------------------------------------------------------------------------+   │
  │   |                    HEXAGONAL INBOUND PORTS MANAGEMENT                  |   │
  │   | - IngestTelemetryPort                                                  |   │
  │   +------------------------------------------------------------------------+   │
  │                                       │                                        │
  │                                       ▼                                        │
  │   +------------------------------------------------------------------------+   │
  │   |                 MICROKERNEL CORE (SHARED KNOWLEDGE)                    |   │
  │   | - Thread-Safe Concurrent KD-Tree Spatial Map                           |   │
  │   | - High-Throughput Zero-Copy In-Memory Event Bus                       |   │
  │   +------------------------------------------------------------------------+   │
  │                                       │                                        │
  │                   ┌───────────────────┴───────────────────┐                    │
  │                   ▼                                       ▼                    │
  │   +-------------------------------+       +--------------------------------+   │
  │   |   SERVER-SIDE PLUGIN: MAPE    |       |     SERVER-SIDE PLUGIN: K-M    |   │
  │   |  (Spatial Deduplication)      |       |  (Adaptive Media Orchestration)|   │
  │   | - 3-Meter Radius Consolidator |       | - Command Topic Signal Router  |   │
  │   | - Sliding Window Aggregator   |       | - Media Sync Request Evaluator |   │
  │   +-------------------------------+       +--------------------------------+   │
  │                                       │                                        │
  │                                       ▼                                        │
  │   +------------------------------------------------------------------------+   │
  │   |                    HEXAGONAL OUTBOUND PORTS PIPELINE                   |   │
  │   | - BroadcastDashboardPort              - SpatialPersistencePort         |   │
  │   +----------------────────────────────────────────────────────────--------+   │
  └───────────────────────────────────────┬────────────────────────────────────────┘
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
+------------------------------------+        +------------------------------------+
|         OUTBOUND ADAPTERS          |        |         OUTBOUND ADAPTERS          |
|    (WebSockets Broker Backend)     |        |   (PostGIS / TimescaleDB Storage)  |
+------------------------------------+        +------------------------------------+
                  │                                               │
                  │ Async Broadcast                               │ Persistent Archival
                  ▼                                               ▼
+------------------------------------+        +------------------------------------+
|       REAL-TIME WEB FRONTEND       |        |      MUNICIPAL DATA WAREHOUSE      |
|    (Uber H3 Hex Heatmap Panel)     |        |    (Historical Analytics Node)     |
+------------------------------------+        +------------------------------------+
```

---

## 📋 2. Complete Component & Feature Breakdown

### 2.1 Edge Capture Environment (Simulated Multi-Vehicle Node)
*   **Video Ingestion Engine (OpenCV Loop):** Iterates frame-by-frame over pre-recorded driving dashcam clips to simulate camera feeds on transit buses. It handles resolution scaling and drops computational frames when hardware bounds are exceeded to prevent processing drift.
*   **Quantized Model Execution (YOLOv8-Nano INT8):** Runs optimized object detection targeting infrastructure defects. Quantization keeps processor loads down so multiple vehicle instances can execute concurrently on a single presentation laptop.
*   **Virtual GPS Map Matrix (CSV/GPX Trajectory Sync):** Synchronizes spatial tracking with the active frame timeline of the input video. It translates camera relative pixel space into actual physical latitude and longitude arrays.
*   **Local Telemetry Cache (SQLite Circuit Breaker):** Acts as a temporary storage buffer during network drops. Payload packets map to a local database storage instance instead of dropping when wireless communication is disrupted.
*   **Binary Packet Encoder (Protobuf Serializer):** Transforms structured domain objects into packed raw bytes. This ensures telemetry footprints do not exceed the targeted **~40-byte scale**, minimizing simulated cellular bandwidth consumption.

### 2.2 Ingress & Adapter Layer (MQTT Transport Bridge)
*   **Persistent Topic Ingestion (`fleet/+/edge_telemetry`):** Collects and filters high-frequency vehicle metrics. Wildcard matching dynamically tracks incoming routes without modifying ingestion configurations.
*   **Connection Resilience Network (MQTT QoS 1):** Guarantees delivery via handshakes. If a vehicle reconnects after a signal drop, the broker ensures queued packets are successfully delivered to the core monolith.
*   **State Retention Manager (Clean Sessions = False):** Maintains client state profiles at the broker boundary. This preserves unacknowledged edge queues during brief cellular dropouts.

### 2.3 Hexagonal Inbound Ports Management
*   **Domain Protocol Translators (`IngestTelemetryPort`):** Separates external wire transport protocols from internal business code. It strips MQTT headers and validates binary arrays before converting data into clean Data Transfer Objects (DTOs).
*   **Payload Boundary Sanitizer:** Evaluates field constraints, filters out coordinate errors, and flags invalid telemetry profiles before data enters the core execution space.

### 2.4 Microkernel Core (Shared Knowledge Layer)
*   **Thread-Safe Spatial Indexing (`KD-Tree` Cache):** An in-memory, thread-safe indexing grid that retains global vehicle coordinates and infrastructure defect matrices. Microsecond execution speeds allow rapid proximity lookups across the system.
*   **Zero-Copy In-Memory Event Bus:** Dispatches notifications across plugins using direct memory reference pointers, avoiding network serialization bottlenecks within the monolith.
*   **Dynamic Component Registry & Lifecycle Controller:** Manages plugin execution hooks, handles error domains, and isolates runtime issues to prevent individual module failures from crashing the core engine.

### 2.5 Server-Side Plugin: Monitor-Analyze-Plan-Execute (MAPE Cloud Loop)
*   **Spatial Deduplication Evaluator (3-Meter Proximity Match):** Prevents duplicate entries when multiple vehicles pass the same street fault. It checks existing coordinates within a **3-meter radius** using a fast spatial lookup to group new reports into a single tracking event.
*   **Sliding Window Aggregator (5-Minute Temporal Grid):** Computes confidence averages across a sliding window, balancing outlier alerts to filter out camera glare or temporary vehicle blockages.
*   **Uber H3 Grid Macro Projector:** Groups raw vehicle density indicators onto hexagonal indexes to build macro traffic flow profiles without storing individual vehicle paths.

### 2.6 Server-Side Plugin: Knowledge-Media (K-M Loop)
*   **Command Topic Signal Router (`MediaSyncRequest`):** Generates remote commands sent via a dedicated outbound MQTT channel (`fleet/{vehicle_id}/command`).
*   **Adaptive Media Request Evaluator:** Triggers a 2-second high-definition clip request *only* when an anomaly configuration matches severe or unverified defect profiles.

### 2.7 Hexagonal Outbound Ports & Adapters
*   **Egress Interface Managers (`BroadcastDashboardPort` & `SpatialPersistencePort`):** Standardizes outbound data pipelines, ensuring core changes do not break database schemas or web client integrations.
*   **WebSocket Long-Poll Server Engine:** Manages continuous client web sessions, streaming data packets directly to frontend dashboards as events occur.
*   **Spatial Database Persistence Node (PostGIS & TimescaleDB):** Converts transient memory events into indexed records for long-term municipal planning and historical trend analytics.

### 2.8 Real-Time Web Frontend Dashboard
*   **Map Rendering Interface (Leaflet.js / Mapbox GL):** Displays simulated vehicles moving across urban transport routes alongside active infrastructure health markers.
*   **H3 Hexagonal Heatmap Visualizer:** Colors and scales hexagonal zones dynamically based on aggregate traffic counts to reveal city congestion profiles.

---

## 🔄 3. Hierarchical Dual-Control Loops & Flows

To run an industrial-grade system, the control architecture is split into two specialized loops: an **Autonomic Edge Loop** for local hardware/environmental management, and a **Monolithic Cloud Loop** for central data orchestration.

### 3.1 The Local Edge MAPE-K Loop (Device Self-Healing Brain)
Lives entirely on the bus's edge processor. It ensures the YOLO model receives high-quality frames and protects the hardware rig.
*   **Monitor:** Tracks device metrics via onboard sensors (ambient light metadata, CPU core temperatures, IMU/vibration sensor data, cellular signal strength).
*   **Analyze:** Evaluates if thresholds are breached (e.g., *Is CPU hitting 80°C? Is frame blur too high? Is it dark?*).
*   **Plan:** Formulates hardware or software adjustment rules.
*   **Execute:** Adjusts parameters directly on the vehicle:
    *   *Night Mode:* Switches camera to infrared / toggles low-light enhancement filters.
    *   *Thermal Throttling:* Switches YOLO from 30 FPS down to 10 FPS eco-mode and engages cooling pins.
    *   *Vibration Correction:* Appies digital image stabilization or drops heavily blurred frames to avoid false positive data.

### 3.2 End-to-End System State Machine & Flowchart

```
       [ 1. EDGE TRANSIT STATE ]
                  │
                  ▼
       [ 2. IMAGE CAPTURE STATE ]
                  │
                  ▼
       [ 3. INFERENCE STATE (YOLOv8) ]
                  │
                  ├─► (No Defect Found) ──► [ 4A. SYSTEM IDLE STATE ] ──► (Loop Retain)
                  │
                  └─► (Defect Found) ─────► [ 4B. LOCAL TELEMETRY COMPILATION STATE ]
                                                        │
                                                        ▼
                                            [ 5. NETWORK VERIFICATION STATE ]
                                                        │
                   ┌────────────────────────────────────┴────────────────────────────────────┐
                   ▼ (Network Unavailable)                                                   ▼ (Network Connected)
       [ 6A. DATA OFFLINE QUEUE STATE ]                                          [ 6B. PROTOBUF BINARY EMISSION STATE ]
       (Cache in Local SQLite Matrix)                                                        │
                   │                                                                         ▼
                   └───────────► (On Reconnection, Burst Queue) ──────────────────────────► [ 7. MQTT BROKER INGRESS STATE ]
                                                                                             │
                                                                                             ▼
                                                                                 [ 8. PORT ADAPTER TRANSLATION STATE ]
                                                                                             │
                                                                                             ▼
                                                                                 [ 9. CORE BUS EVENT DISPATCH STATE ]
                                                                                             │
                                                                                             ▼
                                                                                 [ 10. SPATIAL PROXIMITY EVALUATION STATE ]
                                                                                             │
                                           ┌─────────────────────────────────────────────────┴─────────────────────────────────────────────────┐
                                           ▼ (Proximity Match <= 3 Meters Found)                                                               ▼ (Proximity Match > 3 Meters Clear)
                             [ 11A. RECORD CONSOLIDATION STATE ]                                                                 [ 11B. NEW MARKER INGESTION STATE ]
                             (Merge Coordinates & Update Confidence)                                                             (Instantiate Asset Entry inside KD-Tree Cache)
                                           │                                                                                                   │
                                           └────────────────────────────────────────┬──────────────────────────────────────────────────────────┘
                                                                                    │
                                                                                    ▼
                                                                       [ 12. H3 DENSITY MATRIX UPDATE ]
                                                                                    │
                                                                                    ▼
                                                                       [ 13. ADAPTIVE MEDIA INSPECTION STATE ]
                                                                                    │
                                           ┌────────────────────────────────────────┴────────────────────────────────────────┐
                                           ▼ (Confidence High / Known Defect)                                                ▼ (Confidence Edge-Case / Severe Disruption)
                             [ 14A. SKIP STRIP LOGIC STATE ]                                                    [ 14B. MEDIA REQUEST TRIGGER STATE ]
                             (No Video Upload - Retain Binary Payload Only)                                     (Publish MediaSyncRequest back to Specific Vehicle ID)
                                           │                                                                                 │
                                           │                                                                                 ▼
                                           │                                                                    [ 14C. BUS LOCAL VIDEO COMPRESSION STATE ]
                                           │                                                                    (Crop 2-Second Segment & Stream to Object Storage)
                                           │                                                                                 │
                                           │                                                                                 ▼
                                           │                                                                    [ 14D. RE-LINK META ASSET LINK STATE ]
                                           │                                                                    (Append Storage URL to Monolith Cache Defect)
                                           │                                                                                 │
                                           └────────────────────────────────────────┬────────────────────────────────────────┘
                                                                                    │
                                                                                    ▼
                                                                       [ 15. WEBSOCKET BROADCAST OUTBOUND STATE ]
                                                                                    │
                                                                                    ▼
                                                                       [ 16. CLIENT DASHBOARD RENDERING STATE ]
```

---

## 👥 4. 6-Member Parallel Hackathon Workflow Matrix

Using a **Hexagonal + Protobuf decoupling boundary** allows all 6 team members to write code simultaneously without blocking one another during the 36-hour hackathon.

```
               [ MILESTONE 1: CONTRACT LOCK ]
                              │
  ┌───────────────────────────┼───────────────────────────┐
  ▼ (Edge Team: M1 & M2)      ▼ (Server Team: M3 & M4)    ▼ (Full-Stack/DevOps: M5 & M6)
[Edge AI Ingestion Engine]  [Monolith Ingest Ports]     [Docker Environment setup]
[Quantized INT8 Model]      [In-Memory KD-Tree Cache]   [Map Interface Boilerplate]
  │                           │                           │
  └───────────────────────────┼───────────────────────────┘
                              │
               [ MILESTONE 2: LOCAL SIMULATION ]
                              │
  ┌───────────────────────────┼───────────────────────────┐
  ▼                           ▼                           ▼
[Local Edge MAPE-K Loop]    [3-Meter Deduplication]     [WebSocket Real-Time Adapter]
[SQLite Offline Queuing]    [Uber H3 Grid Processing]   [H3 Hex Heatmap Rendering]
  │                           │                           │
  └───────────────────────────┼───────────────────────────┘
                              │
               [ MILESTONE 3: PIPELINE INTEGRATION ]
                              │
                              ▼
               [ FULL SYSTEM TESTING & INTEGRATION ]
                              │
                              ▼
               [ MILESTONE 4: CHAOS & PITCH DRILLS ]
```

### 4.1 Granular Role Assignments

#### Member 1: Edge Systems Lead (Hardware & Local MAPE-K)
*   **Core Tasks:** Build the OpenCV frame ingestion loop, write the local hardware self-healing logic (thermal throttling simulation, night mode toggle, image stabilization triggers), and implement the offline SQLite failover query loop.

#### Member 2: Edge AI Engineer (Computer Vision Optimization)
*   **Core Tasks:** Fine-tune **YOLOv8-Nano** on infrastructure defects (potholes, faded lane markings, debris), compile the model down to **INT8 precision**, and construct the coordinate translation script mapping pixel bounds to relative distance offsets.

#### Member 3: Server Core Architect (Monolith Microkernel)
*   **Core Tasks:** Set up the **Eclipse Mosquitto MQTT Broker** via Docker, design the hexagonal inbound interface port (`IngestTelemetryPort`), and write the thread-safe **In-Memory Spatial Cache (KD-Tree)** inside the microkernel core.

#### Member 4: Cloud Data & Server MAPE-K Developer (Spatial Orchestration)
*   **Core Tasks:** Implement the server-side **3-Meter Spatial Deduplication Engine** algorithm, integrate **Uber's H3 Spatial Index** library for macro traffic clustering, and configure the outbound command handler (`MediaSyncRequest`).

#### Member 5: Full-Stack Web Developer (Real-Time UI & WebSockets)
*   **Core Tasks:** Construct the frontend application layout (**React/Vue**), embed **Leaflet.js / Mapbox GL** to display live vehicle positioning, and build the server's **Outbound WebSocket Adapter** to stream real-time map data.

#### Member 6: Database & DevOps Specialist (Integration & Chaos Testing)
*   **Core Tasks:** Maintain the **Docker Compose multi-container mesh** (Mosquitto, PostGIS/TimescaleDB), map the persistent storage pipeline from core to DB, compile mock GPS trajectory vectors, and manage presentation chaos triggers.

---

## 🏆 5. SIH Evaluation Pitch & Jury Strategy

To maximize scoring potential, the presentation must balance technical sophistication with economic real-world feasibility.

1.  **Lead with the Cellular Cost Reduction Metric:** Avoid presenting as a generic "AI on a map" project. Tell the judges: *"Standard streaming models cost municipalities thousands of rupees per bus in cellular data bills. Our distributed approach compresses data at the edge into 40-byte Protobuf payloads, reducing infrastructure bandwidth requirements by over 90%."*
2.  **Demonstrate Scalability via Containers:** Run your Docker multi-container mesh live. Show **5 distinct bus container instances** processing independent video files simultaneously on your laptop. This proves your architectural choice of a monolithic core handles real-world concurrency smoothly.
3.  **Execute the "Chaos Engineering" Test:** During the live evaluation, manually sever the network adapter connection on a mock bus node. Show the jury how the edge node switches immediately to its local SQLite failover buffer without data loss, and bursts the cached data chronologically once reconnected. This demonstrates high resilience and production readiness.