## Context

CC-server is the central orchestrator in the A2A demo — it relays WebRTC signaling between CC-client and CC-gui, drives the full business flow by calling CRM and Billing agents via A2A, and hosts the Communication Agent for post-order notifications. The directory `app/CC/CC-server/` is currently empty. CRM-server and Billing-server are also not yet implemented, but CC-server must be built against their published A2A skill schemas so it can be tested independently (with mocks or once they're available).

No cross-subsystem Python imports are introduced. CC-server communicates with CRM-server and Billing-server exclusively via `a2a-python` SDK client calls over HTTP.

## Goals / Non-Goals

**Goals:**
- Implement a fully functional CC-server FastAPI application on port 8001
- WebSocket signaling relay at `/ws/signal` supporting all defined message types
- A2A orchestration flow triggered by `call-start`, with progress push to CC-gui
- REST `POST /order/create` endpoint with identity verification gate
- Communication Agent (`/communication/a2a`) with `send_notification` skill (TMF681)
- Dockerfile for containerized deployment

**Non-Goals:**
- Implementing CRM-server or Billing-server
- CC-client or CC-gui frontend code
- Ollama integration (CC-server never calls Ollama directly)
- Persistent session storage beyond in-memory state
- Production-grade authentication or rate limiting

## Decisions

### 1. WebSocket connection management — role-based slots

**Decision**: Maintain two named WebSocket slots: `client` and `gui`. First connection identifying as each role takes the slot; messages are relayed between them.

**Rationale**: The spec defines exactly two participants (CC-client and CC-gui). Named slots are simpler than room-based routing and match the 1:1 signaling model. No need for multi-session support in demo scope.

**Alternative considered**: Room/session-based WebSocket management — rejected as over-engineering for the demo's single-session model.

### 2. A2A client calls — use `a2a-python` SDK

**Decision**: Use `a2a-python` SDK's `A2AClient` for all outbound A2A calls to CRM-server and Billing-server. No raw `httpx` for A2A.

**Rationale**: Architecture rule mandates SDK usage. SDK handles JSON-RPC envelope construction, error parsing, and timeouts.

### 3. Concurrent execution of steps 3 and 3.5

**Decision**: Use `asyncio.gather()` to run `query_bill` (Billing) and `get_ai_model_status` (CRM) concurrently after `query_customer` completes.

**Rationale**: Spec explicitly notes these steps are independent and MAY run concurrently. Reduces total flow latency by ~50% for these two steps.

### 4. Communication Agent — co-hosted in CC-server process

**Decision**: The Communication Agent runs inside the CC-server FastAPI process, mounted at `/communication`. It uses `a2a-python` SDK for Agent Card serving and skill dispatch.

**Rationale**: Spec places the Communication Agent on CC-server (port 8001). Co-hosting avoids a separate process while keeping the A2A contract clean — CC-server orchestration calls it via the same A2A SDK client interface.

**Alternative considered**: Separate process on a different port — rejected as unnecessary for a single-skill agent in demo scope.

### 5. Configuration — environment variables with defaults

**Decision**: All external service URLs configured via env vars with localhost defaults:
- `CRM_SERVER_URL` (default: `http://localhost:8002`)
- `BILLING_SERVER_URL` (default: `http://localhost:8003`)
- `NBO_MODEL_ID` (default: `nbo-model-v1`) — used for `get_ai_model_status` calls

**Rationale**: Docker Compose can override these; manual startup works with defaults. No hardcoded URLs.

### 6. Project structure

```
app/CC/CC-server/
├── pyproject.toml
├── Dockerfile
├── main.py                  # FastAPI app, CORS, mount routers
└── src/
    ├── config.py            # Env var config constants
    ├── ws/
    │   ├── signaling.py     # WebSocket endpoint + connection manager
    │   └── messages.py      # Pydantic models for WS message types
    ├── orchestration/
    │   ├── flow.py          # A2A business flow (steps 1-4)
    │   └── order.py         # Order flow (steps 5-8)
    ├── a2a_client/
    │   └── client.py        # A2A SDK client wrapper for outbound calls
    └── communication/
        ├── agent.py         # Communication Agent Card + skill registration
        └── models.py        # SendNotification input/output Pydantic models
```

## A2A Skill Schema Changes

**No existing A2A skill schemas change.** This is a greenfield implementation consuming existing skill contracts.

**New A2A skill introduced:**

Communication Agent `send_notification` (TMF681):
```json
{
  "inputSchema": {
    "type": "object",
    "properties": {
      "customer_id": { "type": "string" },
      "channel": { "type": "string", "enum": ["sms", "email", "push"] },
      "message": { "type": "string" }
    },
    "required": ["customer_id", "channel", "message"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "message_id": { "type": "string" },
      "status": { "type": "string", "enum": ["sent", "failed"] },
      "sent_at": { "type": "string", "format": "date-time" }
    },
    "required": ["message_id", "status", "sent_at"]
  }
}
```

No Ollama prompt template is needed — CC-server does not call Ollama.

## Fallback Behavior

| Dependency | Failure mode | Fallback |
|---|---|---|
| CRM Profiling Agent (`query_customer`) | A2A call fails | Return `error` message to CC-gui; abort flow |
| Billing Usage Agent (`query_bill`) | A2A call fails | Return `error` message to CC-gui; abort flow |
| CRM AI Management Agent (`get_ai_model_status`) | A2A call fails or returns `inactive` | Set `nbo_fallback=true`, `nbo_fallback_reason="model_inactive"`; continue to `get_nbo` with `fallback: true` |
| CRM Recommendation Agent (`get_nbo`) | A2A call fails | Return `error` message to CC-gui; abort flow |
| CRM Profiling Agent (`verify_identity`) | Returns `verified: false` | Return identity failure to CC-gui; abort order |
| CRM Order Agent (`create_order`) | A2A call fails | Return `error` message to CC-gui; abort order |
| Communication Agent (`send_notification`) | A2A call fails or returns `status: "failed"` | Include failure status in `order_result`; do NOT roll back the order |

## Risks / Trade-offs

- **[Single WebSocket session]** Only one client + one gui connection at a time. → Acceptable for demo; first-come-first-served slot model.
- **[In-memory connection state]** WebSocket slots are lost on restart. → Acceptable for demo; no persistence needed.
- **[Communication Agent self-call]** CC-server calls its own `/communication/a2a` via HTTP loopback. → Minor overhead but maintains clean A2A contract boundaries. Could optimize to direct function call if latency matters.
- **[No retry on A2A failures]** Single-attempt calls. → Demo scope; adding retry would complicate error reporting to CC-gui.
