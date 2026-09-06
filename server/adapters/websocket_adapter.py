"""
PAIR B — WebSocket Outbound Adapter
=====================================
Day 1: Register endpoint at /ws/dashboard (accepts connections, echoes back pings).
Day 2: Broadcast real-time DefectMarker + VehiclePosition events to all connected clients.

All connected frontend clients receive the same broadcast stream.
"""

import asyncio
import json
import logging
from dataclasses import asdict
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("WebSocketAdapter")


class WebSocketBroadcastAdapter:
    """
    Manages a pool of connected WebSocket clients and broadcasts JSON events.

    Usage in FastAPI route:
        ws_adapter = WebSocketBroadcastAdapter()

        @app.websocket("/ws/dashboard")
        async def ws_endpoint(websocket: WebSocket):
            await ws_adapter.handle_connection(websocket)
    """

    def __init__(self):
        self._active_connections: list[WebSocket] = []
        logger.info("[WebSocket] BroadcastAdapter initialized")

    async def handle_connection(self, websocket: WebSocket):
        """Accept a new client connection and keep it alive until disconnect."""
        await websocket.accept()
        self._active_connections.append(websocket)
        client_host = websocket.client.host if websocket.client else "unknown"
        logger.info(f"[WebSocket] ✅ Client connected: {client_host} (total={len(self._active_connections)})")

        # Send initial state snapshot to newly connected client
        await websocket.send_json({
            "event": "connected",
            "message": "Urban AI Fleet Intelligence — Live Dashboard",
            "client_count": len(self._active_connections),
        })

        try:
            # Keep connection alive — listen for client pings
            while True:
                data = await websocket.receive_text()
                logger.debug(f"[WebSocket] Ping from {client_host}: {data}")
                await websocket.send_json({"event": "pong"})

        except WebSocketDisconnect:
            self._active_connections.remove(websocket)
            logger.info(f"[WebSocket] Client disconnected: {client_host} (remaining={len(self._active_connections)})")

    async def broadcast(self, event_type: str, data: Any):
        """
        Broadcast a JSON event to ALL connected dashboard clients.
        Called by the server core whenever a new defect or vehicle update occurs.

        Event types:
            "defect_new"      — new DefectMarker created
            "defect_updated"  — existing DefectMarker updated (confidence merged)
            "vehicle_moved"   — bus position updated
            "system_status"   — heartbeat / server stats
        """
        if not self._active_connections:
            return  # No clients — nothing to do

        message = json.dumps({
            "event": event_type,
            "data": data if isinstance(data, dict) else asdict(data),
        })

        # Broadcast to all, remove dead connections
        dead = []
        for ws in self._active_connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self._active_connections.remove(ws)
            logger.warning("[WebSocket] Removed dead connection")

        if self._active_connections:
            logger.debug(f"[WebSocket] Broadcasted '{event_type}' to {len(self._active_connections)} clients")

    def get_connection_count(self) -> int:
        return len(self._active_connections)
