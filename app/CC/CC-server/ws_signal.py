"""WebSocket signaling relay for CC-server.

Maintains two WebSocket slots: 'client' and 'gui'.
Relays messages between them and triggers A2A flow on call-start.
"""

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from a2a_flow import run_business_flow

logger = logging.getLogger(__name__)

router = APIRouter()

# WebSocket connection slots
_connections: dict[str, Optional[WebSocket]] = {
    "client": None,
    "gui": None,
}


async def send_to_gui(msg: dict) -> None:
    """Send a JSON message to the gui WebSocket if connected."""
    ws = _connections.get("gui")
    if ws:
        await ws.send_json(msg)


def get_gui_sender():
    """Return the send_to_gui function for use by other modules."""
    return send_to_gui


@router.websocket("/ws/signal")
async def signaling_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Determine slot via query param ?role=client|gui
    role = websocket.query_params.get("role")
    if role not in ("client", "gui"):
        # Auto-assign: if gui slot is empty, assign as gui; otherwise client
        if _connections.get("gui") is None:
            role = "gui"
        else:
            role = "client"

    _connections[role] = websocket
    other = "gui" if role == "client" else "client"
    logger.info("WebSocket connected: role=%s", role)

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            msg_type = msg.get("type")

            if msg_type == "call-start" and role == "client":
                # Relay to gui
                other_ws = _connections.get("gui")
                if other_ws:
                    await other_ws.send_json(msg)
                # Trigger A2A business flow
                phone = msg.get("data", {}).get("phone", "")
                task = asyncio.create_task(run_business_flow(phone, send_to_gui))
                task.add_done_callback(_log_task_error)

            elif msg_type in ("offer", "answer", "ice-candidate", "call-end"):
                # Relay to the other peer
                other_ws = _connections.get(other)
                if other_ws:
                    await other_ws.send_json(msg)

            else:
                logger.warning("Unknown or unhandled message type=%s from role=%s", msg_type, role)

    except WebSocketDisconnect:
        # Only clear slot if this websocket still owns it (avoid nulling a replacement)
        if _connections.get(role) is websocket:
            _connections[role] = None
        logger.info("WebSocket disconnected: role=%s", role)
    except Exception:
        if _connections.get(role) is websocket:
            _connections[role] = None
        logger.exception("WebSocket error: role=%s", role)


def _log_task_error(task: asyncio.Task) -> None:
    if task.cancelled():
        return
    exc = task.exception()
    if exc:
        logger.error("Business flow task failed: %s", exc)
