"""
NEURO_PREDICT_SYS — WebSocket Hub
Real-time communication between all modules.
"""
import asyncio
import json
import time
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from .config import get_settings

settings = get_settings()


class ConnectionManager:
    """Manages WebSocket connections across all modules."""

    def __init__(self):
        # module_name -> set of (websocket, user_id)
        self._connections: Dict[str, Set[tuple]] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket, module: str, user_id: str = "anonymous"):
        await websocket.accept()
        if module not in self._connections:
            self._connections[module] = set()
        self._connections[module].add((websocket, user_id))

        # Send welcome
        await self._send_to_ws(websocket, {
            "type": "connected",
            "module": module,
            "user_id": user_id,
            "server_time": time.time(),
            "active_connections": self.get_count(module),
        })

        # Broadcast join to module
        await self.broadcast(module, {
            "type": "user_joined",
            "user_id": user_id,
            "total_users": self.get_count(module),
        }, exclude=websocket)

    def disconnect(self, websocket: WebSocket, module: str):
        for module_name, conns in self._connections.items():
            conns_to_remove = [(ws, uid) for ws, uid in conns if ws == websocket]
            for ws, uid in conns_to_remove:
                conns.discard((ws, uid))

    async def broadcast(self, module: str, message: dict, exclude: WebSocket = None):
        if module not in self._connections:
            return
        dead = []
        for ws, uid in self._connections[module]:
            if ws == exclude:
                continue
            if not await self._send_to_ws(ws, message):
                dead.append((ws, uid))
        for d in dead:
            self._connections[module].discard(d)

    async def broadcast_all(self, message: dict, exclude: WebSocket = None):
        for module in self._connections:
            await self.broadcast(module, message, exclude)

    async def send_to_user(self, user_id: str, message: dict):
        for module, conns in self._connections.items():
            for ws, uid in conns:
                if uid == user_id:
                    await self._send_to_ws(ws, message)

    def get_count(self, module: str = None) -> int:
        if module:
            return len(self._connections.get(module, set()))
        return sum(len(c) for c in self._connections.values())

    def get_modules(self) -> list:
        return list(self._connections.keys())

    async def _send_to_ws(self, ws: WebSocket, message: dict) -> bool:
        try:
            await ws.send_json(message)
            return True
        except Exception:
            return False

    async def heartbeat_loop(self):
        """Periodic heartbeat to keep connections alive."""
        while True:
            await asyncio.sleep(settings.WS_HEARTBEAT_INTERVAL)
            for module, conns in self._connections.items():
                dead = []
                for ws, uid in conns:
                    if not await self._send_to_ws(ws, {"type": "heartbeat", "ts": time.time()}):
                        dead.append((ws, uid))
                for d in dead:
                    conns.discard(d)

    def start_heartbeat(self):
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self.heartbeat_loop())


# ── Event Types ───────────────────────────────────────────────────

class WSEvent:
    """Standardized WebSocket event types for inter-module communication."""
    # Analysis events
    ANALYSIS_STARTED = "analysis.started"
    ANALYSIS_PROGRESS = "analysis.progress"
    ANALYSIS_COMPLETE = "analysis.complete"
    ANALYSIS_ERROR = "analysis.error"

    # DARWIN events
    DARWIN_STARTED = "darwin.started"
    DARWIN_COMPLETE = "darwin.complete"

    # Patient events
    PATIENT_CREATED = "patient.created"
    PATIENT_UPDATED = "patient.updated"

    # Diagnosis events
    DIAGNOSIS_CREATED = "diagnosis.created"
    DIAGNOSIS_UPDATED = "diagnosis.updated"

    # OT events
    OT_BOOKING_CREATED = "ot.booking.created"
    OT_BOOKING_UPDATED = "ot.booking.updated"

    # Dashboard events
    DASHBOARD_STATS_UPDATE = "dashboard.stats.update"

    # System events
    SYSTEM_ALERT = "system.alert"
    SYSTEM_LOG = "system.log"


# ── Singleton ─────────────────────────────────────────────────────

manager = ConnectionManager()
