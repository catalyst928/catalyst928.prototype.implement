"""A2A JSON-RPC client helper using httpx."""

import itertools

import httpx

_id_counter = itertools.count(1)


async def a2a_call(url: str, skill: str, input_data: dict) -> dict:
    """Send a JSON-RPC skills/call request to an A2A agent.

    Args:
        url: The A2A endpoint URL (e.g. http://localhost:8002/profiling/a2a)
        skill: The skill name (e.g. query_customer)
        input_data: The input payload for the skill

    Returns:
        The result dict from the JSON-RPC response.

    Raises:
        Exception: On HTTP errors or JSON-RPC errors.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": next(_id_counter),
        "method": "skills/call",
        "params": {
            "name": skill,
            "input": input_data,
        },
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        body = resp.json()

    if "error" in body:
        err = body["error"]
        raise Exception(f"A2A error ({err.get('code', -1)}): {err.get('message', 'Unknown')}")

    return body.get("result", {})
