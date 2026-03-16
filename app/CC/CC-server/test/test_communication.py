"""Tests for Communication Agent Card and send_notification skill."""

import pytest
from starlette.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_agent_card_discovery(client: TestClient):
    """Test GET /communication/.well-known/agent.json returns valid Agent Card."""
    response = client.get("/communication/.well-known/agent.json")
    assert response.status_code == 200
    card = response.json()
    assert card["name"] == "Communication Agent"
    assert len(card["skills"]) == 1
    assert card["skills"][0]["id"] == "send_notification"


def test_send_notification_via_a2a(client: TestClient):
    """Test POST /communication/a2a with send_notification skill."""
    import uuid

    request_body = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "messageId": str(uuid.uuid4()),
                "parts": [
                    {
                        "kind": "data",
                        "data": {
                            "skill": "send_notification",
                            "customer_id": "cust_001",
                            "channel": "sms",
                            "message": "Your order has been confirmed.",
                        },
                    }
                ],
            }
        },
    }

    # The SDK mounts JSON-RPC at the root of the mounted app.
    # Mounted at /communication, the endpoint is at /communication/
    response = client.post("/communication/", json=request_body)
    assert response.status_code == 200
    result = response.json()

    # Should be a successful JSON-RPC response
    assert "result" in result
    task = result["result"]
    assert task["status"]["state"] == "completed"

    # Check artifact has notification data
    assert len(task["artifacts"]) > 0
    artifact = task["artifacts"][0]
    data_parts = [p for p in artifact["parts"] if p.get("kind") == "data"]
    assert len(data_parts) > 0
    notif_data = data_parts[0]["data"]
    assert "message_id" in notif_data
    assert notif_data["status"] == "sent"
    assert "sent_at" in notif_data
