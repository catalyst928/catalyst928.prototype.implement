"""A2A business flow orchestration (steps 1-4).

Triggered by call-start. Executes:
1. query_customer
2. concurrent(query_bill, get_ai_model_status)
3. get_nbo
Then pushes business_payload to CC-gui.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from src.a2a_client.client import A2AError
from src.a2a_client import client as a2a
from src import config

logger = logging.getLogger(__name__)


async def run_business_flow(phone: str, manager: Any) -> None:
    """Execute the full A2A business flow and push results to CC-gui.

    Args:
        phone: Customer phone number from call-start event.
        manager: WebSocket ConnectionManager for pushing messages to gui.
    """
    nbo_fallback = False
    nbo_fallback_reason: str | None = None

    try:
        # Step 1: query_customer
        await manager.send_to_gui(
            {"type": "progress", "step": "query_customer", "status": "running"}
        )
        customer = await a2a.query_customer(phone)
        await manager.send_to_gui(
            {"type": "progress", "step": "query_customer", "status": "done"}
        )

        customer_id = customer["customer_id"]

        # Steps 2 & 2.5 (concurrent): query_bill + get_ai_model_status
        await manager.send_to_gui(
            {"type": "progress", "step": "query_bill", "status": "running"}
        )
        await manager.send_to_gui(
            {"type": "progress", "step": "get_ai_model_status", "status": "running"}
        )

        bill_result, ai_model_result = await asyncio.gather(
            _query_bill_safe(customer_id),
            _get_ai_model_status_safe(),
            return_exceptions=False,
        )

        # Handle query_bill result (non-fatal — billing server may not be running)
        if isinstance(bill_result, A2AError):
            logger.warning("query_bill failed (non-fatal): %s", bill_result)
            bill_result = {
                "bucket_balance": None,
                "bucket_balance_unit": None,
                "due_date": None,
                "bill_amount": None,
                "bill_amount_unit": None,
                "plan_usage_pct": None,
            }
            await manager.send_to_gui(
                {"type": "progress", "step": "query_bill", "status": "skipped"}
            )
        else:
            await manager.send_to_gui(
                {"type": "progress", "step": "query_bill", "status": "done"}
            )

        # Handle get_ai_model_status result
        await manager.send_to_gui(
            {"type": "progress", "step": "get_ai_model_status", "status": "done"}
        )
        if isinstance(ai_model_result, dict):
            model_status = ai_model_result.get("status", "active")
            if model_status == "inactive":
                nbo_fallback = True
                nbo_fallback_reason = "model_inactive"
        elif isinstance(ai_model_result, A2AError):
            # AI model status check failure is non-fatal — proceed without fallback info
            logger.warning("get_ai_model_status failed: %s", ai_model_result)

        # Step 3: get_nbo
        await manager.send_to_gui(
            {"type": "progress", "step": "get_nbo", "status": "running"}
        )
        nbo = await a2a.get_nbo(customer_id, fallback=nbo_fallback)
        await manager.send_to_gui(
            {"type": "progress", "step": "get_nbo", "status": "done"}
        )

        # Check if Recommendation Agent flagged its own fallback
        if nbo.get("nbo_fallback"):
            nbo_fallback = True
            nbo_fallback_reason = nbo.get("nbo_fallback_reason", "ollama_unavailable")

        # Push aggregated business_payload to CC-gui
        payload = {
            "type": "business_payload",
            "data": {
                "customer": {
                    "id": customer.get("customer_id"),
                    "name": customer.get("name"),
                    "customer_category": customer.get("customer_category"),
                    "product_name": customer.get("product_name"),
                },
                "bill": {
                    "bucket_balance": bill_result.get("bucket_balance"),
                    "bucket_balance_unit": bill_result.get("bucket_balance_unit"),
                    "due_date": bill_result.get("due_date"),
                    "bill_amount": bill_result.get("bill_amount"),
                    "bill_amount_unit": bill_result.get("bill_amount_unit"),
                    "plan_usage_pct": bill_result.get("plan_usage_pct"),
                },
                "nbo": {
                    "id": nbo.get("id"),
                    "recommendation_item": nbo.get("recommendation_item", []),
                },
                "nbo_fallback": nbo_fallback,
                "nbo_fallback_reason": nbo_fallback_reason,
            },
        }
        await manager.send_to_gui(payload)

    except A2AError as e:
        await _push_error(manager, e)
    except Exception:
        logger.exception("Unexpected error in business flow")
        await manager.send_to_gui(
            {
                "type": "error",
                "step": "unknown",
                "code": -32000,
                "message": "Internal orchestration error",
            }
        )


async def _query_bill_safe(customer_id: str) -> dict[str, Any] | A2AError:
    """Call query_bill, catching errors to allow gather to continue."""
    try:
        return await a2a.query_bill(customer_id)
    except A2AError as e:
        return e
    except Exception as e:
        logger.warning("query_bill connection error: %s", e)
        return A2AError(step="query_bill", code=-32000, message=str(e))


async def _get_ai_model_status_safe() -> dict[str, Any] | A2AError:
    """Call get_ai_model_status, catching errors since it's optional."""
    try:
        return await a2a.get_ai_model_status(config.NBO_MODEL_ID)
    except A2AError as e:
        return e
    except Exception as e:
        logger.warning("get_ai_model_status unexpected error: %s", e)
        return A2AError(
            step="get_ai_model_status", code=-32000, message=str(e)
        )


async def _push_error(manager: Any, error: A2AError) -> None:
    """Push an error message to CC-gui."""
    await manager.send_to_gui(
        {
            "type": "error",
            "step": error.step,
            "code": error.code,
            "message": str(error),
        }
    )
