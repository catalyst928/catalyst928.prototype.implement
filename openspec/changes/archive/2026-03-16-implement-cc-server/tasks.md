## 1. Project Setup

- [x] 1.1 Create `app/CC/CC-server/pyproject.toml` with dependencies: fastapi, uvicorn, a2a-python, pydantic, httpx
- [x] 1.2 Run `uv sync` to install dependencies and create lock file
- [x] 1.3 Create `app/CC/CC-server/src/config.py` with env var configuration (CRM_SERVER_URL, BILLING_SERVER_URL, NBO_MODEL_ID) and localhost defaults
- [x] 1.4 Create `app/CC/CC-server/main.py` — FastAPI app with CORS middleware, mount all routers

## 2. Communication Agent (Agent Card first, then skill)

- [x] 2.1 Create `src/communication/models.py` — Pydantic `SendNotificationInput` and `SendNotificationOutput` models (TMF681 fields)
- [x] 2.2 Create `src/communication/agent.py` — Communication Agent Card definition at `/communication/.well-known/agent.json` with `send_notification` skill schema using a2a-python SDK
- [x] 2.3 Implement `send_notification` skill handler — generate message_id, return sent status with ISO 8601 timestamp (demo stub)
- [x] 2.4 Register Communication Agent routes on the FastAPI app (`/communication/a2a`, `/communication/.well-known/agent.json`)

## 3. WebSocket Signaling

- [x] 3.1 Create `src/ws/messages.py` — Pydantic models for all WebSocket message types (offer, answer, ice-candidate, call-start, call-end, progress, business_payload, order_result, error)
- [x] 3.2 Create `src/ws/signaling.py` — WebSocket connection manager with role-based slots (client/gui), connect/disconnect handling
- [x] 3.3 Implement message relay logic — route signaling messages (offer, answer, ice-candidate, call-end) between client and gui slots
- [x] 3.4 Implement `call-start` handler — extract phone number, trigger A2A orchestration flow asynchronously, push progress to gui

## 4. A2A Client Wrapper

- [x] 4.1 Create `src/a2a_client/client.py` — async helper functions wrapping a2a-python SDK client for calling each downstream agent (query_customer, query_bill, get_ai_model_status, get_nbo, verify_identity, create_order, send_notification)

## 5. A2A Orchestration Flow (CC-server orchestration)

- [x] 5.1 Create `src/orchestration/flow.py` — implement business flow steps 1-4: query_customer → concurrent(query_bill, get_ai_model_status) → get_nbo, with progress push and error handling
- [x] 5.2 Implement NBO fallback logic — if get_ai_model_status returns inactive, set nbo_fallback=true and pass fallback flag to get_nbo
- [x] 5.3 Implement business_payload aggregation — combine customer, bill, nbo data and push to CC-gui via WebSocket
- [x] 5.4 Implement error handling — catch A2A call failures and push error messages to CC-gui

## 6. REST Order Endpoint (CC-server orchestration)

- [x] 6.1 Create `src/orchestration/order.py` — implement `POST /order/create` with Pydantic request/response models
- [x] 6.2 Implement verify_identity gate — call Profiling Agent verify_identity before proceeding; return error on verification failure
- [x] 6.3 Implement create_order + send_notification sequence — call Order Agent, then Communication Agent; push order_result via WebSocket
- [x] 6.4 Handle notification failure gracefully — include failed status in response without rolling back order

## 7. Dockerfile & Deployment

- [x] 7.1 Create `app/CC/CC-server/Dockerfile` — python:3.11-slim, uv, uvicorn on port 8001

## 8. Tests

- [x] 8.1 Create `app/CC/CC-server/test/test_signaling.py` — WebSocket signaling relay tests (connect, relay offer/answer/ice-candidate, call-end)
- [x] 8.2 Create `app/CC/CC-server/test/test_communication.py` — Communication Agent Card discovery and send_notification skill tests
- [x] 8.3 Create `app/CC/CC-server/test/test_order.py` — POST /order/create tests (success, identity failure, notification failure)
- [x] 8.4 Create `app/CC/CC-server/test/test_flow.py` — A2A orchestration flow tests with mocked downstream agents (happy path, CRM unavailable, NBO fallback)
