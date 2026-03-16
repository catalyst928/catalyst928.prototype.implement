## Why

CC-server is the sole orchestrator of the A2A business flow, but its directory (`app/CC/CC-server/`) is currently empty. Without CC-server running on port 8001, no subsystem can be exercised end-to-end: WebRTC signaling has no relay, the A2A orchestration sequence cannot execute, and both CC-client and CC-gui have no backend to connect to. Implementing CC-server is the critical-path blocker for the demo.

## What Changes

- **New FastAPI application** at `app/CC/CC-server/` serving on port 8001
- **WebSocket signaling endpoint** (`ws://localhost:8001/ws/signal`) relaying WebRTC messages (offer, answer, ice-candidate, call-start, call-end) between CC-client and CC-gui
- **A2A orchestration flow** triggered by `call-start`: sequentially calls Profiling Agent (`query_customer`), Usage Agent (`query_bill`), AI Management Agent (`get_ai_model_status`), and Recommendation Agent (`get_nbo`) via `a2a-python` SDK, with concurrent execution of steps 3 and 3.5
- **Progress and payload push** to CC-gui via WebSocket (`progress`, `business_payload`, `order_result`, `error` message types)
- **REST endpoint** `POST /order/create` for order placement flow (verify_identity → create_order → send_notification)
- **Communication Agent** (`/communication/a2a`) hosting `send_notification` skill (TMF681) for post-order notifications
- **CORS enabled** on all endpoints
- **Dockerfile** and **pyproject.toml** for containerized deployment

## Non-goals

- Changes to CRM-server or Billing-server implementations
- CC-client or CC-gui frontend work
- Ollama integration (CC-server does not call Ollama directly)
- STUN/TURN server configuration

## Capabilities

### New Capabilities
- `cc-server`: CC-server FastAPI application — WebSocket signaling relay, A2A orchestration flow, REST order endpoint, and Communication Agent

### Modified Capabilities
_(none — CC spec requirements are unchanged; this is a greenfield implementation of existing requirements)_

## Impact

- **Subsystem**: CC only
- **CC orchestration**: Yes — this IS the orchestration implementation
- **APIs**: New WebSocket endpoint, new REST endpoint, new A2A Communication Agent
- **Dependencies**: `fastapi`, `uvicorn`, `a2a-python`, `pydantic`, `httpx` (via uv)
- **TMForum alignment**: TMF681 (Communication Management) for `send_notification`; aggregated payload uses TMF629/637/677/678/701/620 field names from upstream agents
