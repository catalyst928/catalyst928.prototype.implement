"""Tests for Order Agent — create_order skill."""

from test.helpers import extract_artifact_data, extract_error_status, make_a2a_request


class TestCreateOrder:
    def test_success(self, client):
        resp = make_a2a_request(
            client, "/order", "create_order",
            {"customer_id": "cust_001", "offer_id": "po_002"},
        )
        assert resp.status_code == 200
        data = extract_artifact_data(resp.json())
        assert data["state"] == "acknowledged"
        assert "order_id" in data
        assert "order_date" in data

    def test_invalid_customer(self, client):
        resp = make_a2a_request(
            client, "/order", "create_order",
            {"customer_id": "nonexistent", "offer_id": "po_001"},
        )
        assert resp.status_code == 200
        status = extract_error_status(resp.json())
        assert status.get("state") == "failed"
        assert "Customer not found" in (status.get("message") or "")

    def test_invalid_offering(self, client):
        resp = make_a2a_request(
            client, "/order", "create_order",
            {"customer_id": "cust_001", "offer_id": "po_999"},
        )
        assert resp.status_code == 200
        status = extract_error_status(resp.json())
        assert status.get("state") == "failed"
        assert "ProductOffering not found" in (status.get("message") or "")


class TestUnknownSkill:
    def test_unknown_skill_returns_error(self, client):
        resp = make_a2a_request(client, "/order", "nonexistent_skill", {})
        assert resp.status_code == 200
        status = extract_error_status(resp.json())
        assert status.get("state") == "failed"
        assert "Unknown skill" in (status.get("message") or "")
