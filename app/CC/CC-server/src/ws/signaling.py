"""WebSocket signaling endpoint and connection manager.

Manages role-based slots (client/gui) and relays signaling messages
between CC-client and CC-gui. Triggers A2A orchestration on call-start.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()

# Signaling message types that are simply relayed between client and gui
RELAY_TYPES = {"offer", "answer", "ice-candidate", "call-end"}


class ConnectionManager:
    """Manages WebSocket connections for client and gui roles."""

    def __init__(self) -> None:
        self._slots: dict[str, WebSocket | None] = {
            "client": None,
            "gui": None,
        }

    async def connect(self, role: str, websocket: WebSocket) -> bool:
        """Register a WebSocket connection for the given role.

        Returns True if the connection was accepted, False if the role is invalid.
        """
        if role not in self._slots:
            return False
        await websocket.accept()
        self._slots[role] = websocket
        logger.info("WebSocket connected: role=%s", role)
        return True

    def disconnect(self, role: str, websocket: WebSocket) -> None:
        """Remove the WebSocket connection for the given role.

        Only clears the slot if it still holds the same WebSocket,
        preventing a stale disconnect from wiping a newer connection.
        """
        if role in self._slots and self._slots[role] is websocket:
            self._slots[role] = None
            logger.info("WebSocket disconnected: role=%s", role)

    def get_peer(self, role: str) -> WebSocket | None:
        """Get the WebSocket for the opposite role."""
        peer_role = "gui" if role == "client" else "client"
        return self._slots.get(peer_role)

    def get_gui(self) -> WebSocket | None:
        """Get the gui WebSocket connection."""
        return self._slots.get("gui")

    async def send_to_gui(self, message: dict[str, Any]) -> None:
        """Send a JSON message to the gui WebSocket."""
        ws = self._slots.get("gui")
        if ws is not None:
            try:
                await ws.send_json(message)
            except Exception:
                logger.exception("Failed to send message to gui")


# Singleton connection manager
manager = ConnectionManager()

# Reference to the orchestration flow function, set by main.py to avoid circular imports
_orchestration_flow_fn = None
_order_flow_fn = None


def set_orchestration_flow(fn: Any) -> None:
    """Set the orchestration flow function (called from main.py)."""
    global _orchestration_flow_fn
    _orchestration_flow_fn = fn


@router.websocket("/ws/signal")
async def websocket_signal(websocket: WebSocket, role: str = "client") -> None:
    """WebSocket signaling endpoint.

    Query param `role` identifies the connection as 'client' or 'gui'.
    """
    accepted = await manager.connect(role, websocket)
    if not accepted:
        await websocket.close(code=1008, reason=f"Invalid role: {role}")
        return

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type in RELAY_TYPES:
                # Relay signaling message to peer
                peer = manager.get_peer(role)
                if peer is not None:
                    await peer.send_json(msg)
                else:
                    logger.warning(
                        "No peer connected for relay: type=%s, from=%s",
                        msg_type,
                        role,
                    )

            elif msg_type == "call-start" and role == "client":
                # Extract phone and trigger A2A orchestration
                phone = msg.get("data", {}).get("phone", "")
                logger.info("call-start received: phone=%s", phone)
                if _orchestration_flow_fn is not None:
                    asyncio.create_task(
                        _orchestration_flow_fn(phone, manager)
                    )
                else:
                    logger.error("Orchestration flow function not registered")

            else:
                logger.warning(
                    "Unhandled message type=%s from role=%s", msg_type, role
                )

    except WebSocketDisconnect:
        manager.disconnect(role, websocket)
    except Exception:
        logger.exception("WebSocket error for role=%s", role)
        manager.disconnect(role, websocket)
