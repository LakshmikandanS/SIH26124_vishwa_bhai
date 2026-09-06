# 🖥️ SURADAK — Command & Analytics Dashboard

> **Midnight-Neon Real-Time Public Fleet Tracking, AI Defect Mapping & Municipal Analytics Console**  
> *Component of SURADAK Urban AI Fleet Intelligence*

---

## 📌 Overview

The **SURADAK Dashboard** (`frontend/`) is a high-performance, reactive single-page web console built with **React 18, TypeScript, and Vite**. Designed with a modern **Midnight-Neon** dark mode aesthetic, it connects to the FastAPI backend via **WebSockets** and **REST APIs**, transforming raw edge vision detections into actionable geospatial intelligence for municipal road engineers and transit dispatchers.

---

## 🎨 The 6 Core Dashboard Screens

```
                                    ┌───────────────────────┐
                                    │    SURADAK SIDEBAR    │
                                    └──────────┬────────────┘
         ┌──────────────────┬──────────────────┼──────────────────┬──────────────────┐
         ▼                  ▼                  ▼                  ▼                  ▼
┌──────────────────┐┌──────────────────┐┌──────────────────┐┌──────────────────┐┌──────────────────┐
│  Command Center  ││  Fleet Tracking  ││  AI Intelligence ││   Urban Events   ││    Analytics     │
│ • Full city map  ││ • Live bus roster││ • Live detection ││ • Filterable feed││ • Defect donuts  │
│ • Pulsing buses  ││ • Route timeline ││   stream         ││ • Collapsible    ││ • Hourly density │
│ • Hazard alerts  ││ • Docked HUD     ││ • Centered gauge ││   sidebar [X]    ││ • Problem routes │
└──────────────────┘└──────────────────┘└──────────────────┘└──────────────────┘└──────────────────┘
```

### 1. Command Center (`pages/CommandCenter.tsx`)
- **Interactive Leaflet Map Canvas**:
  - Dark Esri base-tiles with glowing route traces.
  - **Neon Pill Bus Badges**: Animated pill markers with live pulsing LEDs showing bus IDs.
  - **Animated Hazard Pins**: Radar wave animations highlighting pothole severity in real time.
- **Executive Metric Cards**: Active transit units, verified defect clusters, high-risk zones, and live telemetry feed status.
- **Bottom Intelligence Cards**: Recent detected events feed, fleet operational status donut chart, and live traffic density area curves.

### 2. Fleet Tracking (`pages/FleetTracking.tsx`)
- **Active Bus Roster**: Lists live vehicles connected via MQTT with search filtering.
- **Integrated Docked HUD Panel**: Positioned cleanly below the map inside an acrylic dark glass container:
  - Header with vehicle ID, route name, and live pulse indicator.
  - Telemetry metrics: **Speed (km/h)**, **ETA Next Stop**, **Distance**, **Next Stop**, and **Defects Sighted**.
  - **Station Progression Timeline**: Glowing milestone nodes tracking bus progress along stops (e.g., Central Station → Nehru Place).

### 3. AI Video Intelligence (`pages/VideoIntelligence.tsx`)
- **Real-Time Edge Telemetry Banner**: Displays connected bus ID, connection status, total detections, and average model confidence.
- **Live Detection Feed Table**: Chronological log of recent object classifications, bounding box coordinates, and timestamps.
- **Traffic Density Gauge Card**: Centered vertical stack featuring a glowing **circular score ring**, density level badge (`HIGH` / `MODERATE` / `LOW`), and summary event statistics.
- **Live Detection Timeline**: Interactive Recharts timeline tracking pothole and traffic detections over time.

### 4. Urban Events (`pages/UrbanEvents.tsx`)
- **Categorical Filtering**: Filter road hazards by type (*All Types, Potholes, Road Hazards, Accidents, Waterlogging*).
- **Collapsible Events Panel**: Features a toggle button and a dedicated sticky header with a **Close `[X]`** button.
- **Floating Detail Card**: Clicking any hazard displays photographic previews, confidence percentages, sighting counts, and exact GPS coordinates.

### 5. Analytics (`pages/Analytics.tsx`)
- Macro-level municipal road health reports:
  - Defect severity breakdown donut charts (Critical, High, Medium, Low).
  - Hourly traffic density bar charts.
  - Problematic corridor leaderboard ranking city roads by defect density.

### 6. System Settings (`pages/Settings.tsx`)
- Municipal configuration panel:
  - System branding customization (`SURADAK`).
  - Unit selections (Kilometers/Miles, km/h vs. mph).
  - Data refresh intervals, backup triggers, and system diagnostics.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Framework** | React 18 (`react`, `react-dom`) | Modern component-based UI |
| **Language** | TypeScript 5.5 | Type safety across WebSocket & REST schemas |
| **Bundler & Tooling**| Vite 5.4 | Instant HMR (Hot Module Replacement) and fast builds |
| **Mapping Engine** | Leaflet & React-Leaflet | Hardware-accelerated geospatial visualization |
| **Data Charts** | Recharts 3.10 | Responsive SVG charts (Donut, Area, Line, Bar) |
| **Iconography** | Lucide React | Clean, minimalist SVG icons |
| **Styling** | Vanilla CSS (Midnight-Neon) | Pure CSS design system (`index.css`) with zero runtime overhead |

---

## 🚀 Execution Guide

### 1. Install Dependencies
```powershell
cd frontend
npm install
```

### 2. Start Development Server
```powershell
npm run dev
```
> *Open **`http://localhost:5173`** in your web browser.*

### 3. Build for Production
```powershell
npm run build
```
> *Compiles and type-checks the application into the optimized **`dist/`** bundle.*

---

## 📁 Directory Structure

```
frontend/
├── src/
│   ├── components/               # Reusable UI components
│   │   ├── CommandCenterCards.tsx# Bottom analytic cards (Recent events, donut, area chart)
│   │   ├── H3HexLayer.tsx        # Uber H3 hexagonal density polygon renderer
│   │   ├── MapView.tsx           # Leaflet canvas with custom neon bus & hazard markers
│   │   └── Sidebar.tsx           # SURADAK brand header, navigation menu & status
│   ├── data/
│   │   ├── mockPhotos.ts         # High-resolution hazard preview images
│   │   └── routeData.ts          # Route 17 waypoints, stations, and bus details
│   ├── hooks/
│   │   ├── useRestApi.ts         # Initial seed hook fetching /vehicles and /defects
│   │   └── useWebSocket.ts       # Live WebSocket subscription hook (/ws/dashboard)
│   ├── pages/                    # The 6 core application views
│   │   ├── Analytics.tsx         # Macro reports & defect breakdown
│   │   ├── CommandCenter.tsx     # Executive command overview map
│   │   ├── FleetTracking.tsx     # Bus roster & docked HUD timeline panel
│   │   ├── Settings.tsx          # System configuration & preferences
│   │   ├── UrbanEvents.tsx       # Collapsible defect feed & hazard detail card
│   │   └── VideoIntelligence.tsx # Detection tables, traffic gauge & timeline
│   ├── App.tsx                   # Master state orchestrator & navigation router
│   ├── index.css                 # Midnight-Neon complete CSS design system
│   ├── main.tsx                  # React DOM entry point
│   └── types.ts                  # Shared TypeScript interfaces & severity helpers
├── index.html                    # HTML root with Inter & JetBrains Mono typography
├── package.json                  # Dependencies & npm scripts
└── vite.config.ts                # Vite configuration with backend proxy
```
