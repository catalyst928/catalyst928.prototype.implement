"""REST endpoint POST /order/create.

Handles order placement flow:
verify_identity → create_order → send_notification
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.a2a_client.client import A2AError
from src.a2a_client import client as a2a
from src.ws.signaling import manager

logger = logging.getLogger(__name__)

router = APIRouter()


class OrderCreateRequest(BaseModel):
    """Request body for POST /order/create."""

    customer_id: str = Field(
        description="TMF622 ProductOrder.relatedParty[role=customer].id"
    )
    offer_id: str = Field(description="TMF620 ProductOffering.id")


class OrderData(BaseModel):
    """Order result data."""

    order_id: str = Field(description="TMF622 ProductOrder.id")
    state: str = Field(description="TMF622 ProductOrder.state")
    order_date: str = Field(description="TMF622 ProductOrder.orderDate (ISO 8601)")


class NotificationData(BaseModel):
    """Notification result data."""

    message_id: str = Field(description="TMF681 CommunicationMessage.id")
    status: str = Field(description="TMF681 CommunicationMessage.state")
    sent_at: str = Field(description="TMF681 CommunicationMessage.sendTime (ISO 8601)")


class OrderErrorData(BaseModel):
    """Error response data."""

    code: int = Field(description="JSON-RPC error code")
    message: str = Field(description="Error description")
    step: str = Field(description="Name of the A2A step that failed")


class OrderCreateSuccessResponse(BaseModel):
    """Successful order creation response."""

    order: OrderData
    notification: NotificationData


class OrderCreateErrorResponse(BaseModel):
    """Error order creation response."""

    error: OrderErrorData


@router.post("/order/create")
async def create_order(
    request: OrderCreateRequest,
) -> OrderCreateSuccessResponse | OrderCreateErrorResponse:
    """Place an order: verify identity, create order, send notification."""

    try:
        # Step 1: Verify identity
        await manager.send_to_gui(
            {"type": "progress", "step": "verify_identity", "status": "running"}
        )
        identity_result = await a2a.verify_identity(
            request.customer_id, "otp"
        )
        await manager.send_to_gui(
            {"type": "progress", "step": "verify_identity", "status": "done"}
        )

        if not identity_result.get("verified", False):
            error_resp = OrderCreateErrorResponse(
                error=OrderErrorData(
                    code=-32001,
                    message="Identity verification failed",
                    step="verify_identity",
                )
            )
            await manager.send_to_gui(
                {"type": "error", **error_resp.error.model_dump()}
            )
            return error_resp

        # Step 2: Create order
        await manager.send_to_gui(
            {"type": "progress", "step": "create_order", "status": "running"}
        )
        order_result = await a2a.create_order(
            request.customer_id, request.offer_id
        )
        await manager.send_to_gui(
            {"type": "progress", "step": "create_order", "status": "done"}
        )

        order_data = OrderData(
            order_id=order_result["order_id"],
            state=order_result["state"],
            order_date=order_result["order_date"],
        )

        # Step 3: Send notification (failure does NOT roll back order)
        await manager.send_to_gui(
            {"type": "progress", "step": "send_notification", "status": "running"}
        )
        try:
            notif_result = await a2a.send_notification(
                request.customer_id,
                "sms",
                "Your order has been confirmed.",
            )
            notification_data = NotificationData(
                message_id=notif_result["message_id"],
                status=notif_result["status"],
                sent_at=notif_result["sent_at"],
            )
        except (A2AError, Exception) as e:
            logger.warning("send_notification failed: %s", e)
            notification_data = NotificationData(
                message_id="",
                status="failed",
                sent_at="",
            )

        await manager.send_to_gui(
            {"type": "progress", "step": "send_notification", "status": "done"}
        )

        response = OrderCreateSuccessResponse(
            order=order_data,
            notification=notification_data,
        )

        # Push order_result via WebSocket
        await manager.send_to_gui(
            {
                "type": "order_result",
                "data": {
                    "order": order_data.model_dump(),
                    "notification": notification_data.model_dump(),
                },
            }
        )

        return response

    except A2AError as e:
        error_resp = OrderCreateErrorResponse(
            error=OrderErrorData(
                code=e.code,
                message=str(e),
                step=e.step,
            )
        )
        await manager.send_to_gui(
            {"type": "error", **error_resp.error.model_dump()}
        )
        return error_resp
    except Exception as e:
        logger.exception("Unexpected error in order creation")
        error_resp = OrderCreateErrorResponse(
            error=OrderErrorData(
                code=-32000,
                message="Internal error during order creation",
                step="unknown",
            )
        )
        return error_resp
