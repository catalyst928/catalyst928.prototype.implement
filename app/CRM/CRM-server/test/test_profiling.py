"""Tests for Profiling Agent — query_customer and verify_identity skills."""

from test.helpers import extract_artifact_data, extract_error_status, make_a2a_request


class TestQueryCustomer:
    def test_success(self, client):
        resp = make_a2a_request(client, "/profiling", "query_customer", {"phone": "13800000001"})
        assert resp.status_code == 200
        data = extract_artifact_data(resp.json())
        assert data["customer_id"] == "cust_001"
        assert data["customer_category"] == "gold"
        assert data["product_name"] == "Plan-50G"

    def test_customer_not_found(self, client):
        resp = make_a2a_request(client, "/profiling", "query_customer", {"phone": "00000000000"})
        assert resp.status_code == 200
        status = extract_error_status(resp.json())
        assert status.get("state") == "failed"
        assert "Customer not found" in (status.get("message") or "")


class TestVerifyIdentity:
    def test_verified_true(self, client):
        resp = make_a2a_request(
            client, "/profiling", "verify_identity",
            {"customer_id": "cust_001", "verification_method": "otp"},
        )
        assert resp.status_code == 200
        data = extract_artifact_data(resp.json())
        assert data["verified"] is True
        assert data["confidence_score"] == 0.95

    def test_verified_false(self, client):
        resp = make_a2a_request(
            client, "/profiling", "verify_identity",
            {"customer_id": "cust_003", "verification_method": "otp"},
        )
        assert resp.status_code == 200
        data = extract_artifact_data(resp.json())
        assert data["verified"] is False
        assert data["confidence_score"] == 0.20

    def test_customer_not_found(self, client):
        resp = make_a2a_request(
            client, "/profiling", "verify_identity",
            {"customer_id": "nonexistent", "verification_method": "otp"},
        )
        assert resp.status_code == 200
        status = extract_error_status(resp.json())
        assert status.get("state") == "failed"
        assert "Customer not found" in (status.get("message") or "")


class TestUnknownSkill:
    def test_unknown_skill_returns_error(self, client):
        resp = make_a2a_request(client, "/profiling", "nonexistent_skill", {})
        assert resp.status_code == 200
        status = extract_error_status(resp.json())
        assert status.get("state") == "failed"
        assert "Unknown skill" in (status.get("message") or "")
