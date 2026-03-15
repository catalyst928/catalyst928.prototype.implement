"""A2A business flow orchestration for CC-server."""

import asyncio
import json
from typing import Callable, Awaitable

from a2a_client import a2a_call

# A2A agent endpoints
PROFILING_URL = "http://localhost:8002/profiling/a2a"
USAGE_URL = "http://localhost:8003/usage/a2a"
AI_MGMT_URL = "http://localhost:8002/ai-management/a2a"
RECOMMENDATION_URL = "http://localhost:8002/recommendation/a2a"

# Model ID used for NBO AI model status check
NBO_MODEL_ID = "nbo_model_01"

SendFn = Callable[[dict], Awaitable[None]]


async def run_business_flow(phone: str, send_to_gui: SendFn) -> None:
    """Execute the full A2A business flow triggered by call-start.

    Steps:
    1. query_customer (Profiling Agent)
    2. query_bill (Usage Agent) + get_ai_model_status (AI Management Agent) — concurrent
    3. get_nbo (Recommendation Agent)
    4. Push business_payload to CC-gui
    """

    # Step 1: query_customer
    await send_to_gui({"type": "progress", "step": "query_customer", "status": "running"})
    try:
        customer = await a2a_call(PROFILING_URL, "query_customer", {"phone": phone})
    except Exception as e:
        await send_to_gui({
            "type": "error", "step": "query_customer",
            "code": -32001, "message": str(e),
        })
        return
    await send_to_gui({"type": "progress", "step": "query_customer", "status": "done"})

    customer_id = customer.get("customer_id") or customer.get("id")

    # Steps 2 + 3.5 (concurrent): query_bill + get_ai_model_status
    nbo_fallback = False
    nbo_fallback_reason = None

    async def step_query_bill():
        await send_to_gui({"type": "progress", "step": "query_bill", "status": "running"})
        try:
            result = await a2a_call(USAGE_URL, "query_bill", {"customer_id": customer_id})
        except Exception as e:
            await send_to_gui({
                "type": "error", "step": "query_bill",
                "code": -32001, "message": str(e),
            })
            raise
        await send_to_gui({"type": "progress", "step": "query_bill", "status": "done"})
        return result

    async def step_get_ai_model_status():
        nonlocal nbo_fallback, nbo_fallback_reason
        await send_to_gui({"type": "progress", "step": "get_ai_model_status", "status": "running"})
        try:
            result = await a2a_call(AI_MGMT_URL, "get_ai_model_status", {"model_id": NBO_MODEL_ID})
            if result.get("status") == "inactive":
                nbo_fallback = True
                nbo_fallback_reason = "model_inactive"
        except Exception:
            # AI model status check is optional — don't abort flow
            pass
        await send_to_gui({"type": "progress", "step": "get_ai_model_status", "status": "done"})

    try:
        bill, _ = await asyncio.gather(step_query_bill(), step_get_ai_model_status())
    except Exception:
        return  # query_bill failure already sent error to gui

    # Step 3: get_nbo
    await send_to_gui({"type": "progress", "step": "get_nbo", "status": "running"})
    nbo_input = {"customer_id": customer_id}
    if nbo_fallback:
        nbo_input["fallback"] = True
    try:
        nbo = await a2a_call(RECOMMENDATION_URL, "get_nbo", nbo_input)
    except Exception as e:
        await send_to_gui({
            "type": "error", "step": "get_nbo",
            "code": -32001, "message": str(e),
        })
        return

    # Check if Recommendation Agent itself set fallback
    if nbo.get("nbo_fallback"):
        nbo_fallback = True
        nbo_fallback_reason = nbo.get("nbo_fallback_reason", "ollama_unavailable")

    await send_to_gui({"type": "progress", "step": "get_nbo", "status": "done"})

    # Build and push business_payload
    payload = {
        "type": "business_payload",
        "data": {
            "customer": {
                "id": customer_id,
                "name": customer.get("name"),
                "customer_category": customer.get("customer_category"),
                "product_name": customer.get("product_name"),
            },
            "bill": {
                "bucket_balance": bill.get("bucket_balance"),
                "bucket_balance_unit": bill.get("bucket_balance_unit"),
                "due_date": bill.get("due_date"),
                "bill_amount": bill.get("bill_amount"),
                "bill_amount_unit": bill.get("bill_amount_unit"),
                "plan_usage_pct": bill.get("plan_usage_pct"),
            },
            "nbo": {
                "id": nbo.get("id"),
                "recommendation_item": nbo.get("recommendation_item", []),
            },
            "nbo_fallback": nbo_fallback,
            "nbo_fallback_reason": nbo_fallback_reason,
        },
    }
    await send_to_gui(payload)
