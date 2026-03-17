"""A2A SDK client wrapper for calling downstream agents.

All outbound A2A calls use the a2a-python SDK client.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import httpx
from a2a.client import A2AClient
from a2a.types import (
    DataPart,
    Message,
    MessageSendParams,
    SendMessageRequest,
    TaskState,
)

from src import config


async def _call_a2a(
    base_url: str,
    skill_id: str,
    input_data: dict[str, Any],
) -> dict[str, Any]:
    """Send an A2A message to a downstream agent and extract the result.

    Args:
        base_url: Agent base URL (e.g., http://localhost:8002/profiling)
        skill_id: The skill to invoke
        input_data: The input payload as a dict

    Returns:
        The output data dict from the agent's response artifact.

    Raises:
        A2AError: If the A2A call fails or returns an error state.
    """
    async with httpx.AsyncClient() as http_client:
        client = A2AClient(
            httpx_client=http_client,
            url=base_url,
        )

        request = SendMessageRequest(
            id=str(uuid.uuid4()),
            params=MessageSendParams(
                message=Message(
                    role="user",
                    message_id=str(uuid.uuid4()),
                    parts=[
                        DataPart(data={"skill": skill_id, **input_data}),
                    ],
                ),
            ),
        )

        response = await client.send_message(request)
        return _extract_result(response, skill_id)


class A2AError(Exception):
    """Error from an A2A call."""

    def __init__(self, step: str, code: int, message: str) -> None:
        self.step = step
        self.code = code
        super().__init__(message)


def _extract_result(response: Any, skill_id: str) -> dict[str, Any]:
    """Extract the data result from an A2A SendMessageResponse."""
    result = response.root

    # Check if it's an error response
    if hasattr(result, "error") and result.error is not None:
        raise A2AError(
            step=skill_id,
            code=result.error.code,
            message=str(result.error.message),
        )

    # Unwrap SendMessageSuccessResponse to get the Task
    task = result.result if hasattr(result, "result") else result
    if hasattr(task, "status") and task.status.state == TaskState.failed:
        msg_obj = task.status.message
        if msg_obj and hasattr(msg_obj, "parts"):
            texts = [
                p.root.text if hasattr(p, "root") else p.text
                for p in msg_obj.parts
                if hasattr(p.root if hasattr(p, "root") else p, "text")
            ]
            msg = " ".join(texts) or f"{skill_id} task failed"
        else:
            msg = str(msg_obj) if msg_obj else f"{skill_id} task failed"
        raise A2AError(step=skill_id, code=-32000, message=msg)

    # Extract data from artifacts
    if task.artifacts:
        for artifact in task.artifacts:
            for part in artifact.parts:
                inner = part.root if hasattr(part, "root") else part
                if hasattr(inner, "data") and inner.data is not None:
                    return inner.data
                if hasattr(inner, "text") and inner.text is not None:
                    return json.loads(inner.text)

    raise A2AError(
        step=skill_id,
        code=-32000,
        message=f"No result data in {skill_id} response",
    )


# --- Skill-specific client functions ---


async def query_customer(phone: str) -> dict[str, Any]:
    """Call Profiling Agent query_customer skill."""
    return await _call_a2a(
        config.PROFILING_A2A_URL,
        "query_customer",
        {"phone": phone},
    )


async def query_bill(customer_id: str) -> dict[str, Any]:
    """Call Usage Agent query_bill skill."""
    return await _call_a2a(
        config.USAGE_A2A_URL,
        "query_bill",
        {"customer_id": customer_id},
    )


async def get_ai_model_status(model_id: str) -> dict[str, Any]:
    """Call AI Management Agent get_ai_model_status skill."""
    return await _call_a2a(
        config.AI_MANAGEMENT_A2A_URL,
        "get_ai_model_status",
        {"model_id": model_id},
    )


async def get_nbo(
    customer_id: str, fallback: bool = False
) -> dict[str, Any]:
    """Call Recommendation Agent get_nbo skill."""
    input_data: dict[str, Any] = {"customer_id": customer_id}
    if fallback:
        input_data["fallback"] = True
    return await _call_a2a(
        config.RECOMMENDATION_A2A_URL,
        "get_nbo",
        input_data,
    )


async def verify_identity(
    customer_id: str, verification_method: str = "otp"
) -> dict[str, Any]:
    """Call Profiling Agent verify_identity skill."""
    return await _call_a2a(
        config.PROFILING_A2A_URL,
        "verify_identity",
        {
            "customer_id": customer_id,
            "verification_method": verification_method,
        },
    )


async def create_order(
    customer_id: str, offer_id: str
) -> dict[str, Any]:
    """Call Order Agent create_order skill."""
    return await _call_a2a(
        config.ORDER_A2A_URL,
        "create_order",
        {"customer_id": customer_id, "offer_id": offer_id},
    )


async def send_notification(
    customer_id: str, channel: str, message: str
) -> dict[str, Any]:
    """Call Communication Agent send_notification skill."""
    return await _call_a2a(
        config.COMMUNICATION_A2A_URL,
        "send_notification",
        {
            "customer_id": customer_id,
            "channel": channel,
            "message": message,
        },
    )
