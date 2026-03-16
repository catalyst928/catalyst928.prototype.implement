"""Pydantic models for WebSocket message types."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SignalingMessage(BaseModel):
    """Base signaling message (offer, answer, ice-candidate, call-start, call-end)."""

    type: str = Field(description="Message type discriminator")
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Message payload",
    )


class ProgressMessage(BaseModel):
    """Progress update pushed to CC-gui during A2A flow."""

    type: str = Field(default="progress", description="Always 'progress'")
    step: str = Field(
        description="A2A step name (query_customer, query_bill, get_ai_model_status, get_nbo, verify_identity, create_order, send_notification)"
    )
    status: str = Field(description="Step status: running | done")


class BusinessPayloadMessage(BaseModel):
    """Aggregated A2A result pushed to CC-gui after get_nbo completes."""

    type: str = Field(default="business_payload", description="Always 'business_payload'")
    data: dict[str, Any] = Field(description="Aggregated customer + bill + nbo data")


class OrderResultMessage(BaseModel):
    """Order + notification result pushed to CC-gui."""

    type: str = Field(default="order_result", description="Always 'order_result'")
    data: dict[str, Any] = Field(description="Order and notification result data")


class ErrorMessage(BaseModel):
    """Error message pushed to CC-gui when a flow step fails."""

    type: str = Field(default="error", description="Always 'error'")
    step: str = Field(description="The A2A step that failed")
    code: int = Field(description="JSON-RPC error code")
    message: str = Field(description="Human-readable error description")
