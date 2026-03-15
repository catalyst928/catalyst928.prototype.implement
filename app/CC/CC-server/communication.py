"""Communication Agent — mock A2A agent implementing TMF681 send_notification."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/communication")


@router.get("/.well-known/agent.json")
async def agent_card():
    return {
        "name": "Communication Agent",
        "description": "Delivers post-order notifications via SMS, email, or push (TMF681).",
        "url": "http://localhost:8001/communication/a2a",
        "version": "1.0.0",
        "skills": [
            {
                "name": "send_notification",
                "description": "Send a notification to a customer",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string"},
                        "channel": {"type": "string", "enum": ["sms", "email", "push"]},
                        "message": {"type": "string"},
                    },
                    "required": ["customer_id", "channel", "message"],
                },
                "outputSchema": {
                    "type": "object",
                    "properties": {
                        "message_id": {"type": "string"},
                        "status": {"type": "string", "enum": ["sent", "failed"]},
                        "sent_at": {"type": "string", "format": "date-time"},
                    },
                    "required": ["message_id", "status", "sent_at"],
                },
            }
        ],
    }


@router.post("/a2a")
async def a2a_endpoint(request: Request):
    body = await request.json()
    method = body.get("method")
    params = body.get("params", {})
    rpc_id = body.get("id", 1)

    if method != "skills/call" or params.get("name") != "send_notification":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {"code": -32601, "message": "Method not found"},
        })

    input_data = params.get("input", {})
    result = send_notification(input_data)

    return JSONResponse({
        "jsonrpc": "2.0",
        "id": rpc_id,
        "result": result,
    })


def send_notification(input_data: dict) -> dict:
    """Process a send_notification request directly (no HTTP round-trip).

    Args:
        input_data: Dict with customer_id, channel, message.

    Returns:
        Dict with message_id, status, sent_at.
    """
    return {
        "message_id": f"msg_{uuid.uuid4().hex[:8]}",
        "status": "sent",
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }
