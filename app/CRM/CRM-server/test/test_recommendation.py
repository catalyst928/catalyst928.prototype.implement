"""Tests for Recommendation Agent — get_nbo skill with Ollama integration."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from test.helpers import extract_artifact_data, extract_error_status, make_a2a_request
from src.agents.recommendation.skills.get_nbo import (
    NBO_PROMPT_TEMPLATE,
    _parse_offering_ids,
    get_nbo,
)


class TestGetNboViaA2A:
    def test_nbo_with_mocked_ollama(self, client):
        """Test NBO with a valid Ollama response returning valid offering IDs."""
        mock_response = httpx.Response(
            200,
            json={"response": '["po_004", "po_005"]'},
            request=httpx.Request("POST", "http://test/api/generate"),
        )
        with patch.object(
            client.app.state.ollama_client,
            "post",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            resp = make_a2a_request(
                client, "/recommendation", "get_nbo",
                {"customer_id": "cust_001"},
            )
        assert resp.status_code == 200
        data = extract_artifact_data(resp.json())
        assert "id" in data
        assert len(data["recommendation_item"]) >= 1
        # Verify priority ordering
        priorities = [item["priority"] for item in data["recommendation_item"]]
        assert priorities == sorted(priorities)
        # Should not contain customer's current plan (Plan-50G = po_001)
        offering_ids = [item["offering_id"] for item in data["recommendation_item"]]
        assert "po_001" not in offering_ids

    def test_nbo_customer_not_found(self, client):
        resp = make_a2a_request(
            client, "/recommendation", "get_nbo",
            {"customer_id": "nonexistent"},
        )
        assert resp.status_code == 200
        status = extract_error_status(resp.json())
        assert status.get("state") == "failed"
        assert "Customer not found" in (status.get("message") or "")

    def test_nbo_ollama_connection_error(self, client):
        """When Ollama is unreachable, fallback to price-sorted offerings."""
        with patch.object(
            client.app.state.ollama_client,
            "post",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            resp = make_a2a_request(
                client, "/recommendation", "get_nbo",
                {"customer_id": "cust_001"},
            )
        assert resp.status_code == 200
        data = extract_artifact_data(resp.json())
        assert len(data["recommendation_item"]) >= 1
        # Fallback should be price-sorted (ascending)
        prices = [item["price"] for item in data["recommendation_item"]]
        assert prices == sorted(prices)

    def test_unknown_skill_returns_error(self, client):
        resp = make_a2a_request(client, "/recommendation", "nonexistent_skill", {})
        assert resp.status_code == 200
        status = extract_error_status(resp.json())
        assert status.get("state") == "failed"
        assert "Unknown skill" in (status.get("message") or "")


class TestParseOfferingIds:
    def test_valid_json_array(self):
        result = _parse_offering_ids('["po_001", "po_002"]')
        assert result == ["po_001", "po_002"]

    def test_prose_wrapped_json(self):
        text = 'Here are my recommendations: ["po_002", "po_003", "po_001"] based on the customer profile.'
        result = _parse_offering_ids(text)
        assert result == ["po_002", "po_003", "po_001"]

    def test_unparseable_response(self):
        result = _parse_offering_ids("I cannot provide recommendations today.")
        assert result is None

    def test_invalid_json_in_brackets(self):
        result = _parse_offering_ids("[not valid json]")
        assert result is None


class TestInventoryExclusion:
    @pytest.mark.asyncio
    async def test_current_plan_filtered(self):
        """Customer A's plan (Plan-50G = po_001) should be excluded from results."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = httpx.Response(
            200,
            json={"response": '["po_001", "po_002", "po_003"]'},
            request=httpx.Request("POST", "http://test/api/generate"),
        )
        mock_client.post.return_value = mock_response

        result = await get_nbo({"customer_id": "cust_001"}, mock_client)
        offering_ids = [item.offering_id for item in result.recommendation_item]
        assert "po_001" not in offering_ids
        assert len(result.recommendation_item) >= 1


class TestNboAllInvalidIds:
    @pytest.mark.asyncio
    async def test_all_invalid_ids_trigger_fallback(self):
        """When Ollama returns all-invalid IDs, fallback to price-sorted."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = httpx.Response(
            200,
            json={"response": '["fake_001", "fake_002"]'},
            request=httpx.Request("POST", "http://test/api/generate"),
        )
        mock_client.post.return_value = mock_response

        result = await get_nbo({"customer_id": "cust_001"}, mock_client)
        assert len(result.recommendation_item) >= 1
        prices = [item.price for item in result.recommendation_item]
        assert prices == sorted(prices)


class TestPromptTemplate:
    def test_prompt_contains_required_fields(self):
        assert "{customer_id}" in NBO_PROMPT_TEMPLATE
        assert "{customer_category}" in NBO_PROMPT_TEMPLATE
        assert "{product_name}" in NBO_PROMPT_TEMPLATE
        assert "{offerings_json}" in NBO_PROMPT_TEMPLATE
