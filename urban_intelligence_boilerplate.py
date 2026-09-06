"""
AI-Powered Urban Intelligence Platform - Architecture Boilerplate
This boilerplate demonstrates the integration of:
1. Hexagonal Architecture (Ports & Adapters)
2. MAPE-K Loop (Dynamic Software Product Line - DSPL for Edge-AI)
3. Microkernel Monolith (Plugin System Lifecycle)

Run this script directly to see a live execution trace of the architecture.
"""

import uuid
import logging
import time
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

# Configure logging to show the clean architectural execution flow
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("UrbanIntelligence")


# =====================================================================
# 1. CORE DOMAIN LAYER (Pure Logic - Zero Framework Dependencies)
# =====================================================================

class TelemetryPayload:
    """Domain Entity representing live data gathered from an on-bus edge sensor."""
    def __init__(self, vehicle_id: str, latitude: float, longitude: float, 
                 lux_level: float, vibration_g: float, network_signal_db: float):
        self.payload_id = str(uuid.uuid4())
        self.vehicle_id = vehicle_id
        self.latitude = latitude
        self.longitude = longitude
        self.lux_level = lux_level          # Light sensor (lux)
        self.vibration_g = vibration_g      # Acceleration vibration threshold (g-force)
        self.network_signal_db = network_signal_db  # Signal strength (dBm)
        self.timestamp = time.time()

    def __repr__(self):
        return f"<Telemetry Vehicle={self.vehicle_id} Lat/Lon=({self.latitude},{self.longitude}) Lux={self.lux_level} Vib={self.vibration_g}g>"


class EdgeAIConfig:
    """Domain Value Object controlling the runtime behavior of the Edge AI device."""
    def __init__(self, yolo_confidence_threshold: float, frame_sampling_rate_fps: int, 
                 enable_night_pipeline: bool, edge_compression_level: int):
        self.yolo_confidence_threshold = yolo_confidence_threshold
        self.frame_sampling_rate_fps = frame_sampling_rate_fps
        self.enable_night_pipeline = enable_night_pipeline
        self.edge_compression_level = edge_compression_level

    def __repr__(self):
        return (f"<EdgeAIConfig YOLO-Conf={self.yolo_confidence_threshold} "
                f"FPS={self.frame_sampling_rate_fps} NightPipeline={self.enable_night_pipeline} "
                f"Compression={self.edge_compression_level}>")


# =====================================================================
# 2. PORTS (Hexagonal Boundaries - Interface Contracts)
# =====================================================================

# --- Driving (Inbound) Ports: Defining how clients interact with the domain ---
class ITelemetryIngressPort(ABC):
    """Driving Port: Exposes functionality to ingest new bus telemetry and process alerts."""
    @abstractmethod
    def ingest_telemetry(self, payload: TelemetryPayload) -> Dict[str, Any]:
        pass


# --- Driven (Outbound) Ports: Defining how the domain interacts with external systems ---
class ITelemetryRepository(ABC):
    """Driven Port: Abstract interface for database operations (PostgreSQL/PostGIS, etc.)."""
    @abstractmethod
    def save(self, payload: TelemetryPayload) -> None:
        pass


class IEdgeDeviceController(ABC):
    """Driven Port: Abstract interface for communicating back with physical bus edge hardware."""
    @abstractmethod
    def push_configuration(self, vehicle_id: str, config: EdgeAIConfig) -> bool:
        pass


# =====================================================================
# 3. CORE DOMAIN IMPLEMENTATION (Use Cases)
# =====================================================================

class TelemetryIngressService(ITelemetryIngressPort):
    """Use Case Implementation: Coordinates core business rules, database saves, and MAPE-K adjustments."""
    def __init__(self, repository: ITelemetryRepository, edge_controller: IEdgeDeviceController):
        self._repository = repository
        self._edge_controller = edge_controller
        self._mape_k_engine: Optional['MapeKEngine'] = None

    def register_mape_k_engine(self, engine: 'MapeKEngine'):
        self._mape_k_engine = engine

    def ingest_telemetry(self, payload: TelemetryPayload) -> Dict[str, Any]:
        logger.info(f"[Core Domain] Received ingestion request for vehicle {payload.vehicle_id}")
        
        # Rule 1: Always persist incoming telemetry via our Outbound Port (Database Adapter)
        self._repository.save(payload)

        # Rule 2: Evaluate telemetry through the Dynamic Software Product Line (MAPE-K engine)
        alerts = []
        if self._mape_k_engine:
            alerts = self._mape_k_engine.process_environment_telemetry(payload)

        return {
            "status": "INGESTED",
            "payload_id": payload.payload_id,
            "processed_alerts": alerts
        }


# =====================================================================
# 4. MAPE-K CONTROL LOOP (Dynamic Software Product Line Adaptation)
# =====================================================================

class MapeKEngine:
    """
    Autonomic Control Loop implementing Dynamic Software Product Line (DSPL) principles.
    Adapts the Edge-AI configurations runtime based on ambient external environmental factors.
    """
    def __init__(self, edge_controller: IEdgeDeviceController):
        self._edge_controller = edge_controller

    def process_environment_telemetry(self, payload: TelemetryPayload) -> List[str]:
        alerts = []
        
        # --- 1. MONITOR ---
        # The sensor data has been gathered from TelemetryPayload
        lux = payload.lux_level
        vibration = payload.vibration_g
        signal = payload.network_signal_db
        
        # --- 2. ANALYZE ---
        # Evaluate context state and check if adaptation criteria are satisfied
        reconfig_needed = False
        target_yolo_conf = 0.60
        target_fps = 10
        target_night_pipeline = False
        target_compression = 1  # 1 = Low, 3 = High

        # Scene context: Poor visibility
        if lux < 15.0:
            alerts.append("CONTEXT_CHANGE: Low ambient light detected on route.")
            target_night_pipeline = True
            target_yolo_conf = 0.45  # Relax confidence bounds to capture faint features
            reconfig_needed = True

        # Infrastructure context: Excessive road vibration (e.g., severe potholes or dirt roads)
        if vibration > 2.5:
            alerts.append("CONTEXT_CHANGE: Severe mechanical vibration encountered.")
            target_fps = 5  # Reduce framerate to avoid processing blurry, degraded frames
            reconfig_needed = True

        # Network bandwidth context: Weak signal coverage
        if signal < -90.0:
            alerts.append("CONTEXT_CHANGE: Degraded cellular network signal detected.")
            target_compression = 3  # Increase local compression to reduce outbound payload sizes
            reconfig_needed = True

        # --- 3. PLAN & 4. EXECUTE ---
        if reconfig_needed:
            new_config = EdgeAIConfig(
                yolo_confidence_threshold=target_yolo_conf,
                frame_sampling_rate_fps=target_fps,
                enable_night_pipeline=target_night_pipeline,
                edge_compression_level=target_compression
            )
            logger.info(f"[MAPE-K] Reconfiguration plan generated: {new_config}")
            
            # Commit adaptation back to edge device via Driven Port
            success = self._edge_controller.push_configuration(payload.vehicle_id, new_config)
            if success:
                logger.info(f"[MAPE-K] Execution phase success: Edge system updated on {payload.vehicle_id}")
                alerts.append("ADAPTATION_EXECUTED: Edge device adjusted.")
            else:
                logger.error(f"[MAPE-K] Adaptation execution failed for {payload.vehicle_id}")
                
        return alerts


# =====================================================================
# 5. MICROKERNEL PLUGINS (Platform Extensibility)
# =====================================================================

class IPlugin(ABC):
    """Stable abstraction contract that all hot-swappable plugins must implement."""
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def on_init(self) -> None:
        pass

    @abstractmethod
    def execute_event(self, event_type: str, data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def on_shutdown(self) -> None:
        pass


class MicrokernelHost:
    """Microkernel Monolith orchestrating Core operations and Plugin Lifecycle hooks."""
    def __init__(self):
        self._plugins: Dict[str, IPlugin] = {}

    def register_plugin(self, plugin: IPlugin) -> None:
        logger.info(f"[Microkernel] Discovering and initializing plugin: '{plugin.name}'")
        plugin.on_init()
        self._plugins[plugin.name] = plugin

    def dispatch_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Dispatches telemetry data to active tenant extension plugins asynchronously."""
        for plugin_name, plugin in self._plugins.items():
            try:
                plugin.execute_event(event_type, data)
            except Exception as e:
                logger.error(f"[Microkernel] Error running extension plugin '{plugin_name}': {e}")

    def shutdown(self) -> None:
        logger.info("[Microkernel] Starting graceful shutdown of all registered plugins")
        for name, plugin in list(self._plugins.items()):
            plugin.on_shutdown()
            del self._plugins[name]


# --- A Concrete Plugin Implementation ---
class EVRouteChargingOptimizerPlugin(IPlugin):
    """Tenant-specific optional plugin to predict optimal EV charging slots."""
    @property
    def name(self) -> str:
        return "EVRouteChargingOptimizer"

    def on_init(self) -> None:
        logger.info(f"[{self.name}] Connecting to external State-of-Charge (SoC) API...")

    def execute_event(self, event_type: str, data: Dict[str, Any]) -> None:
        if event_type == "TELEMETRY_INGESTED":
            vehicle_id = data.get("vehicle_id")
            logger.info(f"[{self.name}] Event Intercepted: Calculating EV discharge profile for {vehicle_id}...")

    def on_shutdown(self) -> None:
        logger.info(f"[{self.name}] Disconnecting, freeing thread pools and cleaning up state.")


# =====================================================================
# 6. OUTBOUND ADAPTERS (Infrastructure Implementation)
# =====================================================================

class PostgresPostgisAdapter(ITelemetryRepository):
    """Driven Adapter implementing telemetry saves to PostgreSQL/PostGIS database."""
    def save(self, payload: TelemetryPayload) -> None:
        # Mocking an INSERT query utilizing PostGIS spatial points
        logger.info(f"[Adapter -> Postgres] Executed spatial transaction: "
                    f"INSERT INTO bus_telemetry (vehicle_id, geom) VALUES ('{payload.vehicle_id}', ST_SetSRID(ST_MakePoint({payload.longitude}, {payload.latitude}), 4326));")


class GRPCEdgeDeviceAdapter(IEdgeDeviceController):
    """Driven Adapter communicating with physical edge cameras using high-performance gRPC streams."""
    def push_configuration(self, vehicle_id: str, config: EdgeAIConfig) -> bool:
        # Simulate pushing RPC protobuf message to the on-board computer
        logger.info(f"[Adapter -> gRPC] Dispatched EdgeAIConfig payload via protobuf stream to target device '{vehicle_id}'.")
        return True


# =====================================================================
# 7. EXECUTION ORCHESTRATOR (Live Architecture Verification Trace)
# =====================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("      AI-POWERED URBAN INTELLIGENCE: ARCHITECTURAL BLUEPRINT VERIFICATION      ")
    print("="*80 + "\n")

    # Step A: Instantiate Core Host and Infrastructure Adapters
    postgres_adapter = PostgresPostgisAdapter()
    grpc_controller_adapter = GRPCEdgeDeviceAdapter()
    
    # Step B: Instantiate Domain Services and Register Inbound Ports
    telemetry_ingress_service = TelemetryIngressService(
        repository=postgres_adapter, 
        edge_controller=grpc_controller_adapter
    )

    # Step C: Instantiate and Register the MAPE-K (DSPL) Adaptation Control Loop
    mape_k_control_loop = MapeKEngine(edge_controller=grpc_controller_adapter)
    telemetry_ingress_service.register_mape_k_engine(mape_k_control_loop)

    # Step D: Setup Microkernel and Register Extensibility Plugins
    kernel_host = MicrokernelHost()
    ev_plugin = EVRouteChargingOptimizerPlugin()
    kernel_host.register_plugin(ev_plugin)

    print("\n" + "-"*50)
    print(" SCENARIO 1: Standard Daytime Bus Route Operation (No Adaptation)")
    print("-"*50)
    # Vehicle operating under optimal conditions
    normal_payload = TelemetryPayload(
        vehicle_id="BUS-DL-01-4402", 
        latitude=28.6139, longitude=77.2090, 
        lux_level=200.0, vibration_g=0.4, network_signal_db=-65.0
    )
    result1 = telemetry_ingress_service.ingest_telemetry(normal_payload)
    kernel_host.dispatch_event("TELEMETRY_INGESTED", {"vehicle_id": normal_payload.vehicle_id})
    print(f"Ingestion Result: {result1}")

    print("\n" + "-"*50)
    print(" SCENARIO 2: Adverse Environmental Dynamic Adaptations (Rain, Shocks, Network Drops)")
    print("-"*50)
    # Vehicle enters a low light tunnel / dark night, encounters deep potholes (high vibration), and experiences bad coverage
    adverse_payload = TelemetryPayload(
        vehicle_id="BUS-DL-01-4402", 
        latitude=28.6180, longitude=77.2150, 
        lux_level=8.5, vibration_g=3.8, network_signal_db=-98.0
    )
    result2 = telemetry_ingress_service.ingest_telemetry(adverse_payload)
    kernel_host.dispatch_event("TELEMETRY_INGESTED", {"vehicle_id": adverse_payload.vehicle_id})
    print(f"Ingestion Result: {result2}")

    print("\n" + "-"*50)
    print(" SHUTDOWN: Cleaning Up Plugin Contexts")
    print("-"*50)
    kernel_host.shutdown()
    print("\n" + "="*80 + "\n")
