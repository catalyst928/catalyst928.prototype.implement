## 1. Project Scaffold

- [x] 1.1 Create `app/CC/CC-server/requirements.txt` with dependencies: fastapi, uvicorn[standard], httpx, websockets
- [x] 1.2 Create `app/CC/CC-server/main.py` with FastAPI app, CORS middleware (allow all origins), and uvicorn entry point on port 8001

## 2. A2A Client Helper

- [x] 2.1 Create `app/CC/CC-server/a2a_client.py` with `a2a_call(url, skill, input_data)` function using `httpx.AsyncClient(timeout=10.0)` that sends JSON-RPC `skills/call` requests and returns the result or raises on error

## 3. WebSocket Signaling Relay

- [x] 3.1 Create `app/CC/CC-server/ws_signal.py` with WebSocket endpoint at `/ws/signal` that maintains two slots (client, gui) and relays messages between them
- [x] 3.2 On receiving `call-start` message, extract `phone` from data and trigger A2A business flow asynchronously, pushing progress/results to gui WebSocket

## 4. A2A Business Flow

- [x] 4.1 Create `app/CC/CC-server/a2a_flow.py` with `run_business_flow(phone, send_to_gui)` that implements the full sequence: query_customer → (query_bill + get_ai_model_status concurrent) → get_nbo → push business_payload
- [x] 4.2 Implement progress messages: push `{ type: "progress", step, status }` before and after each A2A call
- [x] 4.3 Implement error handling: on A2A failure, push `{ type: "error", step, code, message }` to gui and abort flow
- [x] 4.4 Implement NBO fallback logic: if `get_ai_model_status` returns inactive, set `nbo_fallback=true` and pass `fallback: true` to `get_nbo`

## 5. Order Endpoint

- [x] 5.1 Create `app/CC/CC-server/order.py` with `POST /order/create` accepting `{ customer_id, offer_id }`
- [x] 5.2 Implement order flow: verify_identity → create_order → send_notification (via local Communication Agent)
- [x] 5.3 Push progress messages and `order_result` to gui WebSocket after order completion
- [x] 5.4 Handle identity verification failure: return error response and abort order

## 6. Communication Agent

- [x] 6.1 Create `app/CC/CC-server/communication.py` with mock A2A endpoint at `POST /communication/a2a` implementing `send_notification` skill
- [x] 6.2 Add agent card endpoint at `GET /communication/.well-known/agent.json`

## 7. Wire Everything Together

- [x] 7.1 Register all routers and WebSocket endpoints in `main.py`
- [x] 7.2 Verify the app starts with `python main.py` and all endpoints are accessible
