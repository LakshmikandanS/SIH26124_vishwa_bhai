# 3-Day MVP Sprint Plan: Urban AI Fleet Intelligence

## Internal Hackathon Presentation Strategy

This document establishes the high-velocity sprint plan, minimum software requirements, and 6-member workflow to build a fully functional, real-time presentation prototype within 72 hours.

---

## 🛠️ 1. Minimum System Requirements (The Stripped-Down Stack)

To guarantee everything compiles and runs smoothly on a single presentation laptop without configuration issues, use this exact minimalist software footprint:

- **Edge/Bus Simulator Node:** A single Python 3.10+ script using `opencv-python` and the `ultralytics` package. It runs the pre-trained, standard **YOLOv8-Nano (`yolov8n.pt`)** model file out-of-the-box (no custom model training required; detect standard cars, trucks, or pedestrians to prove the visual processing concept). Telemetry packets are structured as standard Python dictionaries compressed to raw bytes over the wire.
- **Ingress Message Broker:** A standard **Eclipse Mosquitto MQTT** broker running locally inside a single-line Docker container.
- **Monolith Backend Core:** A **Python FastAPI** application running locally. All active spatial mapping and 3-meter deduplication are calculated dynamically in-memory using native mathematical list lookups.
- **Live Web Frontend:** A clean, single-page **React** application built using **Leaflet.js** (utilizing free OpenStreetMap tile layers) communicating with the backend over native WebSockets.

---

## 👥 2. 6-Member Tactical Pair Segregation

Divide your 6-member team into **three specialized, 2-person strike pairs**. This isolates development boundaries so everyone can write code in parallel without blocking one another:

- **Pair A: Edge Systems (Members 1 & 2)**
  - _Focus:_ OpenCV loop integration + YOLOv8 inference execution + CSV GPS coordinate tracking sync + MQTT publication layer.
- **Pair B: Server Core (Members 3 & 4)**
  - _Focus:_ MQTT broker configuration + FastAPI server setup + 3-meter in-memory mathematical deduplication plugin + WebSocket broadcast engine.
- **Pair C: Frontend UI & Pitch (Members 5 & 6)**
  - _Focus:_ React dashboard + Leaflet.js interactive map component + WebSockets event client receiver + Alert side-panel UI + Final pitch presentation slides.

---

## 📅 3. The 72-Hour Rapid MVP Timeline

### 🕐 Day 1: Isolated Code Skeletons (0 - 24 Hours)

_Goal: Get every individual layer running locally with mock inputs._

- **Pair A (Edge):** Write a Python script that opens a standard video file using OpenCV. Download the pre-trained `yolov8n.pt` weight file. Ensure the script prints `Object Detected!` in your terminal alongside the current frame index. Create a mock CSV file containing 100 rows of shifting latitudes and longitudes to simulate a bus path.
- **Pair B (Server):** Run the command `docker run -d -p 1883:1883 eclipse-mosquitto` to establish your broker. Write a bare-bones FastAPI app that connects to the broker using `paho-mqtt` and prints any incoming string message onto the terminal console.
- **Pair C (Frontend):** Initialize a React app. Install `leaflet` and `react-leaflet`. Code a fullscreen map centering over a city and place a static, hardcoded vehicle marker on it to verify the UI canvas renders correctly.

### 🕑 Day 2: Connecting the Data Pipeline (24 - 48 Hours)

_Goal: Establish end-to-end data flow (Edge ──► Broker ──► Server ──► Frontend)._

- **Pair A (Edge):** Connect the video frame index to the rows of your GPS CSV file. Every time YOLO detects an object, packetize the current `latitude`, `longitude`, and `object_type` into a tight JSON string (or compact byte structure) and publish it to the local MQTT broker topic `fleet/bus_1/telemetry`.
- **Pair B (Server):** Implement the 3-meter deduplication plugin inside FastAPI using quick flat-surface distance math:
  $$\Delta = \sqrt{(\text{lat}_1 - \text{lat}_2)^2 + (\text{lon}_1 - \text{lon}_2)^2}$$
  If an incoming alert is within the boundary of an existing marker in your memory list, update its timestamp instead of creating a new one. Open a FastAPI WebSocket channel.
- **Pair C (Frontend):** Replace the static map markers with a dynamic state array. Connect the frontend to the server's WebSocket endpoint. As coordinates stream across the WebSocket, update the map marker positions and populate alert pins instantly.

### 🕒 Day 3: UI Polish, Chaos Hardening, & Presentation Prep (48 - 72 Hours)

_Goal: Lock features, dress the interface, and script the evaluation run._

- **Pair A & B Integration:** Spin up **3 copies** of the edge Python script simultaneously on your laptop, each using a unique bus ID (`bus_1`, `bus_2`, `bus_3`) and slightly offset GPS CSV tracks. Verify that the single backend server processes all three simulated nodes concurrently without lag.
- **Pair C (Design Polish):** Add a sidebar alert log component that lights up red whenever a new defect pin is placed. Use customized vehicle icons for the moving bus nodes.
- **Full Team Chaos Drill:** Practice your presentation pitch. Script your exact live demonstration path:
  1. Start with an empty frontend map view.
  2. Execute the 3 bus terminal scripts simultaneously.
  3. Show the buses moving across the map panel and watch the defect pins drop in real-time.
  4. **The Clincher Move:** Terminate one edge terminal script mid-demo. Show the jury that the frontend map continues tracking the other two buses perfectly without freezing or throwing server exceptions.

---

## 🏆 4. Internal Presentation Evaluation Pitch Deck

To clearly convey your architectural design to the internal review panel, structure your presentation into exactly **three high-impact slides**:

1.  **Slide 1: Core Problem & Economic Rationale**
    Explain the financial advantage of edge compute models over raw cloud video streaming: _"Our system drops cellular network costs by over 90% by processing frame pixels directly at the edge node and transmitting lightweight telemetric coordinates instead of streaming continuous HD video chunks to a remote server."_
2.  **Slide 2: Architectural Framework Layout**
    Present the clean, layered **Hexagonal Monolith** diagram from your project documents. Emphasize that your system isolates communication channels via strict ports and processes calculations within a single, thread-safe memory matrix to ensure microsecond-level processing speed.
3.  **Slide 3: Simulated Operational Infrastructure**
    Highlight that your submission demonstrates full system concurrency by simulating an entire municipal route network right on your development machine using localized containerization.
