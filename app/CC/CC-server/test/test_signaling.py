"""Tests for WebSocket signaling relay."""

import json

import pytest
from starlette.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_client_gui_relay_offer(client: TestClient):
    """Test that offer from client is relayed to gui."""
    with client.websocket_connect("/ws/signal?role=gui") as gui_ws:
        with client.websocket_connect("/ws/signal?role=client") as client_ws:
            # Client sends offer
            offer = {"type": "offer", "data": {"sdp": "test-sdp-offer"}}
            client_ws.send_json(offer)

            # Gui receives it
            msg = gui_ws.receive_json()
            assert msg["type"] == "offer"
            assert msg["data"]["sdp"] == "test-sdp-offer"


def test_gui_client_relay_answer(client: TestClient):
    """Test that answer from gui is relayed to client."""
    with client.websocket_connect("/ws/signal?role=client") as client_ws:
        with client.websocket_connect("/ws/signal?role=gui") as gui_ws:
            # Gui sends answer
            answer = {"type": "answer", "data": {"sdp": "test-sdp-answer"}}
            gui_ws.send_json(answer)

            # Client receives it
            msg = client_ws.receive_json()
            assert msg["type"] == "answer"
            assert msg["data"]["sdp"] == "test-sdp-answer"


def test_ice_candidate_relay(client: TestClient):
    """Test ICE candidate relay from client to gui."""
    with client.websocket_connect("/ws/signal?role=gui") as gui_ws:
        with client.websocket_connect("/ws/signal?role=client") as client_ws:
            ice = {"type": "ice-candidate", "data": {"candidate": "test-candidate"}}
            client_ws.send_json(ice)

            msg = gui_ws.receive_json()
            assert msg["type"] == "ice-candidate"
            assert msg["data"]["candidate"] == "test-candidate"


def test_call_end_relay(client: TestClient):
    """Test call-end relay from client to gui."""
    with client.websocket_connect("/ws/signal?role=gui") as gui_ws:
        with client.websocket_connect("/ws/signal?role=client") as client_ws:
            end = {"type": "call-end", "data": {}}
            client_ws.send_json(end)

            msg = gui_ws.receive_json()
            assert msg["type"] == "call-end"
