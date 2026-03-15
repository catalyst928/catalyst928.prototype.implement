## Architecture

CC-server is a single FastAPI application with three main concerns:

1. **WebSocket Signaling Relay** (`/ws/signal`) — Maintains two WebSocket slots (client + gui). Messages from one are relayed to the other. On `call-start`, triggers the A2A business flow.

2. **A2A Business Flow Orchestrator** — Sequential/parallel calls to CRM-server (8002) and Billing-server (8003) agents, aggregating results into a `business_payload` pushed to CC-gui.

3. **REST Order Endpoint** (`POST /order/create`) — Handles identity verification, order creation, and notification sending.

4. **Communication Agent** (`/communication/a2a`) — Mock A2A agent implementing TMF681 `send_notification` skill.

## Module Layout

```
app/CC/CC-server/
├── main.py              # FastAPI app, CORS, uvicorn entry point
├── ws_signal.py         # WebSocket signaling relay + call-start trigger
├── a2a_flow.py          # A2A business flow orchestration
├── order.py             # POST /order/create endpoint
├── communication.py     # Communication Agent (/communication/a2a + agent card)
├── a2a_client.py        # httpx A2A client helper
└── requirements.txt     # Dependencies
```

## Key Design Decisions

- **Single-process**: All concerns live in one FastAPI process for demo simplicity.
- **In-memory WebSocket slots**: Only two connections tracked (client + gui) — no scaling needed.
- **Mock Communication Agent**: Returns hardcoded success responses since this is the local agent.
- **A2A JSON-RPC format**: All outbound A2A calls use `{ "jsonrpc": "2.0", "method": "skills/call", "params": { "name": "<skill>", "input": {...} } }` format.
- **Concurrent steps 3 + 3.5**: `query_bill` and `get_ai_model_status` run via `asyncio.gather()`.
