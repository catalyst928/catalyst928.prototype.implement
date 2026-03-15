"""POST /order/create endpoint for CC-server."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from a2a_client import a2a_call
from communication import send_notification

PROFILING_URL = "http://localhost:8002/profiling/a2a"
ORDER_URL = "http://localhost:8002/order/a2a"

router = APIRouter()


class OrderRequest(BaseModel):
    customer_id: str
    offer_id: str


# Reference to the gui websocket send function, set by ws_signal module
_send_to_gui = None


def set_gui_sender(fn):
    global _send_to_gui
    _send_to_gui = fn


async def _push_progress(step: str, status: str):
    if _send_to_gui:
        await _send_to_gui({"type": "progress", "step": step, "status": status})


@router.post("/order/create")
async def create_order(req: OrderRequest):
    # Step 6: verify_identity
    await _push_progress("verify_identity", "running")
    try:
        identity = await a2a_call(
            PROFILING_URL, "verify_identity",
            {"customer_id": req.customer_id, "verification_method": "otp"},
        )
    except Exception as e:
        await _push_progress("verify_identity", "done")
        return JSONResponse(
            status_code=502,
            content={
                "error": {
                    "code": -32000,
                    "message": str(e),
                    "step": "verify_identity",
                }
            },
        )
    await _push_progress("verify_identity", "done")

    if not identity.get("verified", False):
        error_data = {
            "code": -32001,
            "message": "Identity verification failed",
            "step": "verify_identity",
        }
        if _send_to_gui:
            await _send_to_gui({"type": "error", **error_data})
        return JSONResponse(
            status_code=403,
            content={"error": error_data},
        )

    # Step 7: create_order
    await _push_progress("create_order", "running")
    try:
        order = await a2a_call(
            ORDER_URL, "create_order",
            {"customer_id": req.customer_id, "offer_id": req.offer_id},
        )
    except Exception as e:
        await _push_progress("create_order", "done")
        return JSONResponse(
            status_code=502,
            content={
                "error": {
                    "code": -32000,
                    "message": str(e),
                    "step": "create_order",
                }
            },
        )
    await _push_progress("create_order", "done")

    # Step 8: send_notification (direct call, no HTTP loopback)
    await _push_progress("send_notification", "running")
    try:
        notification = send_notification({
            "customer_id": req.customer_id,
            "channel": "sms",
            "message": "Your order has been confirmed.",
        })
    except Exception:
        # Notification failure does not roll back the order
        notification = {"message_id": "", "status": "failed", "sent_at": ""}
    await _push_progress("send_notification", "done")

    result = {
        "order": {
            "order_id": order.get("order_id") or order.get("id"),
            "state": order.get("state", "acknowledged"),
            "order_date": order.get("order_date"),
        },
        "notification": {
            "message_id": notification.get("message_id"),
            "status": notification.get("status"),
            "sent_at": notification.get("sent_at"),
        },
    }

    # Push order_result to gui
    if _send_to_gui:
        await _send_to_gui({"type": "order_result", "data": result})

    return result
