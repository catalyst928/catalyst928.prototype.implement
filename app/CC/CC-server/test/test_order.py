"""Tests for POST /order/create endpoint."""

from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_order_create_success(client: TestClient):
    """Test successful order creation flow."""
    with (
        patch("src.orchestration.order.a2a.verify_identity", new_callable=AsyncMock) as mock_verify,
        patch("src.orchestration.order.a2a.create_order", new_callable=AsyncMock) as mock_order,
        patch("src.orchestration.order.a2a.send_notification", new_callable=AsyncMock) as mock_notif,
        patch("src.orchestration.order.manager.send_to_gui", new_callable=AsyncMock),
    ):
        mock_verify.return_value = {
            "identity_id": "id_001",
            "verified": True,
            "confidence_score": 0.99,
            "verified_at": "2026-03-16T10:00:00Z",
        }
        mock_order.return_value = {
            "order_id": "ord_001",
            "state": "acknowledged",
            "order_date": "2026-03-16T10:00:01Z",
        }
        mock_notif.return_value = {
            "message_id": "msg_001",
            "status": "sent",
            "sent_at": "2026-03-16T10:00:02Z",
        }

        response = client.post(
            "/order/create",
            json={"customer_id": "cust_001", "offer_id": "po_001"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "order" in data
        assert data["order"]["order_id"] == "ord_001"
        assert data["order"]["state"] == "acknowledged"
        assert "notification" in data
        assert data["notification"]["status"] == "sent"


def test_order_create_identity_failure(client: TestClient):
    """Test order blocked when identity verification fails."""
    with (
        patch("src.orchestration.order.a2a.verify_identity", new_callable=AsyncMock) as mock_verify,
        patch("src.orchestration.order.manager.send_to_gui", new_callable=AsyncMock),
    ):
        mock_verify.return_value = {
            "identity_id": "id_001",
            "verified": False,
            "confidence_score": 0.3,
            "verified_at": "2026-03-16T10:00:00Z",
        }

        response = client.post(
            "/order/create",
            json={"customer_id": "cust_001", "offer_id": "po_001"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32001
        assert data["error"]["step"] == "verify_identity"
        assert "order" not in data


def test_order_create_notification_failure(client: TestClient):
    """Test order succeeds even when notification fails."""
    with (
        patch("src.orchestration.order.a2a.verify_identity", new_callable=AsyncMock) as mock_verify,
        patch("src.orchestration.order.a2a.create_order", new_callable=AsyncMock) as mock_order,
        patch("src.orchestration.order.a2a.send_notification", new_callable=AsyncMock) as mock_notif,
        patch("src.orchestration.order.manager.send_to_gui", new_callable=AsyncMock),
    ):
        mock_verify.return_value = {"identity_id": "id_001", "verified": True, "confidence_score": 0.99, "verified_at": "2026-03-16T10:00:00Z"}
        mock_order.return_value = {"order_id": "ord_001", "state": "acknowledged", "order_date": "2026-03-16T10:00:01Z"}
        mock_notif.side_effect = Exception("Notification service down")

        response = client.post(
            "/order/create",
            json={"customer_id": "cust_001", "offer_id": "po_001"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "order" in data
        assert data["order"]["order_id"] == "ord_001"
        assert data["notification"]["status"] == "failed"
