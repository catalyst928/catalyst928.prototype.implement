"""Shared test helpers for A2A JSON-RPC requests."""

import uuid


def make_a2a_request(client, prefix, skill, input_data):
    """Send a JSON-RPC message/send request to an A2A endpoint.

    Uses the correct a2a-python SDK wire format:
    - method: "message/send"
    - params: MessageSendParams with Message containing DataPart
    """
    return client.post(
        f"{prefix}/",
        json={
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "kind": "message",
                    "messageId": str(uuid.uuid4()),
                    "parts": [
                        {
                            "kind": "data",
                            "data": {"skill": skill, **input_data},
                        }
                    ],
                }
            },
        },
    )


def extract_artifact_data(response_json):
    """Extract the data from the first artifact in a successful A2A response."""
    result = response_json["result"]
    artifacts = result.get("artifacts", [])
    assert len(artifacts) >= 1, f"Expected artifacts, got: {result}"
    return artifacts[0]["parts"][0]["data"]


def extract_error_status(response_json):
    """Extract the status from a failed A2A response.

    Returns a dict with 'state' and 'message' (extracted text from the Message object).
    """
    result = response_json["result"]
    status = result.get("status", {})
    # The 'message' field is a Message object with parts, extract the text
    msg = status.get("message")
    if isinstance(msg, dict) and "parts" in msg:
        texts = [p.get("text", "") for p in msg["parts"] if p.get("kind") == "text"]
        status = dict(status)
        status["message"] = " ".join(texts)
    return status
