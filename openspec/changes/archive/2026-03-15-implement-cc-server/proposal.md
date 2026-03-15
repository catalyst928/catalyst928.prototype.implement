## Why

CC-server is the core FastAPI backend that orchestrates the entire A2A business flow, relays WebRTC signaling between CC-client and CC-gui, and hosts the Communication Agent. Without it, no calls can be placed, no customer data can be aggregated, and no orders can be processed.

## What Changes

- Create `app/CC/CC-server/` as a FastAPI application served on port 8001
- Implement WebSocket signaling relay at `/ws/signal` between CC-client and CC-gui
- Implement A2A business flow orchestration (query_customer → query_bill → get_ai_model_status → get_nbo)
- Implement REST endpoint `POST /order/create` for order placement with identity verification
- Implement Communication Agent at `/communication/a2a` for post-order notifications
- Use `httpx.AsyncClient` with `timeout=10.0` for all outbound A2A calls
- Enable CORS on all endpoints

## Capabilities

### New Capabilities
- `cc-server`: FastAPI backend — WebRTC signaling relay, A2A orchestrator, Communication Agent, order endpoint

### Modified Capabilities
<!-- None — CC-client and CC-gui are already built to talk to CC-server -->

## Impact

- **New code**: `app/CC/CC-server/` (FastAPI app, WebSocket handler, A2A flow logic, Communication Agent)
- **CC-client**: No changes required; already connects to `ws://localhost:8001/ws/signal`
- **CC-gui**: No changes required; already connects to CC-server endpoints
- **Port 8001** must be free
- **Dependencies**: FastAPI, uvicorn, httpx, websockets

## Non-goals

- No database or persistent storage
- No authentication or session management
- No STUN/TURN server configuration
- CRM-server and Billing-server implementation (separate subsystems)
