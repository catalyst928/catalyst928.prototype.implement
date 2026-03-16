"""Tests for A2A orchestration flow."""

from unittest.mock import AsyncMock, patch

import pytest

from src.a2a_client.client import A2AError
from src.orchestration.flow import run_business_flow


@pytest.mark.asyncio
async def test_happy_path_flow():
    """Test successful end-to-end business flow."""
    manager = AsyncMock()
    manager.send_to_gui = AsyncMock()

    with (
        patch("src.orchestration.flow.a2a.query_customer", new_callable=AsyncMock) as mock_cust,
        patch("src.orchestration.flow.a2a.query_bill", new_callable=AsyncMock) as mock_bill,
        patch("src.orchestration.flow.a2a.get_ai_model_status", new_callable=AsyncMock) as mock_ai,
        patch("src.orchestration.flow.a2a.get_nbo", new_callable=AsyncMock) as mock_nbo,
    ):
        mock_cust.return_value = {
            "customer_id": "cust_001",
            "name": "Alice",
            "customer_category": "gold",
            "product_name": "Plan-50G",
        }
        mock_bill.return_value = {
            "bucket_balance": 35.50,
            "bucket_balance_unit": "EUR",
            "due_date": "2026-04-05",
            "bill_amount": 99.00,
            "bill_amount_unit": "EUR",
            "plan_usage_pct": 72,
        }
        mock_ai.return_value = {"model_id": "nbo-model-v1", "status": "active"}
        mock_nbo.return_value = {
            "id": "rec_001",
            "recommendation_item": [
                {"id": "ri_001", "priority": 1, "offering_id": "po_001", "name": "Plan-100G", "description": "Upgrade", "price": 139.0, "price_unit": "EUR"},
            ],
        }

        await run_business_flow("13800000001", manager)

        # Check business_payload was sent
        calls = manager.send_to_gui.call_args_list
        payload_calls = [c for c in calls if c.args[0].get("type") == "business_payload"]
        assert len(payload_calls) == 1
        data = payload_calls[0].args[0]["data"]
        assert data["customer"]["name"] == "Alice"
        assert data["bill"]["bucket_balance"] == 35.50
        assert data["nbo"]["id"] == "rec_001"
        assert data["nbo_fallback"] is False


@pytest.mark.asyncio
async def test_crm_unavailable():
    """Test error pushed when query_customer fails."""
    manager = AsyncMock()
    manager.send_to_gui = AsyncMock()

    with patch("src.orchestration.flow.a2a.query_customer", new_callable=AsyncMock) as mock_cust:
        mock_cust.side_effect = A2AError(
            step="query_customer", code=-32001, message="Customer not found"
        )

        await run_business_flow("0000000000", manager)

        calls = manager.send_to_gui.call_args_list
        error_calls = [c for c in calls if c.args[0].get("type") == "error"]
        assert len(error_calls) == 1
        assert error_calls[0].args[0]["step"] == "query_customer"


@pytest.mark.asyncio
async def test_nbo_fallback_model_inactive():
    """Test NBO fallback when AI model is inactive."""
    manager = AsyncMock()
    manager.send_to_gui = AsyncMock()

    with (
        patch("src.orchestration.flow.a2a.query_customer", new_callable=AsyncMock) as mock_cust,
        patch("src.orchestration.flow.a2a.query_bill", new_callable=AsyncMock) as mock_bill,
        patch("src.orchestration.flow.a2a.get_ai_model_status", new_callable=AsyncMock) as mock_ai,
        patch("src.orchestration.flow.a2a.get_nbo", new_callable=AsyncMock) as mock_nbo,
    ):
        mock_cust.return_value = {"customer_id": "cust_001", "name": "Alice", "customer_category": "gold", "product_name": "Plan-50G"}
        mock_bill.return_value = {"bucket_balance": 35.50, "bucket_balance_unit": "EUR", "due_date": "2026-04-05", "bill_amount": 99.00, "bill_amount_unit": "EUR", "plan_usage_pct": 72}
        mock_ai.return_value = {"model_id": "nbo-model-v1", "status": "inactive"}
        mock_nbo.return_value = {"id": "rec_fallback", "recommendation_item": [{"id": "ri_f01", "priority": 1, "offering_id": "po_cheap", "name": "Plan-Budget", "description": "Budget plan", "price": 49.0, "price_unit": "EUR"}]}

        await run_business_flow("13800000001", manager)

        # get_nbo should have been called with fallback=True
        mock_nbo.assert_called_once_with("cust_001", fallback=True)

        # Check business_payload has fallback flag
        calls = manager.send_to_gui.call_args_list
        payload_calls = [c for c in calls if c.args[0].get("type") == "business_payload"]
        assert len(payload_calls) == 1
        data = payload_calls[0].args[0]["data"]
        assert data["nbo_fallback"] is True
        assert data["nbo_fallback_reason"] == "model_inactive"
