## ADDED Requirements

### Requirement: FastAPI application setup
The system SHALL be a FastAPI application serving on port 8001 with CORS enabled for all origins. The application SHALL mount all routers (WebSocket signaling, REST order endpoint, Communication Agent A2A).

#### Scenario: Server starts and accepts requests
- **WHEN** CC-server is started with `uv run uvicorn main:app --port 8001`
- **THEN** the server SHALL respond to HTTP requests on port 8001 with CORS headers allowing cross-origin access

### Requirement: WebSocket signaling endpoint
The system SHALL provide a WebSocket endpoint at `ws://localhost:8001/ws/signal` that accepts connections from CC-client and CC-gui with role-based identification.

#### Scenario: CC-client connects to signaling
- **WHEN** CC-client opens a WebSocket connection to `/ws/signal?role=client`
- **THEN** the server SHALL register the connection in the `client` slot and relay subsequent messages to the `gui` slot

#### Scenario: CC-gui connects to signaling
- **WHEN** CC-gui opens a WebSocket connection to `/ws/signal?role=gui`
- **THEN** the server SHALL register the connection in the `gui` slot and relay subsequent messages to the `client` slot

#### Scenario: WebRTC offer relay
- **WHEN** CC-client sends `{ "type": "offer", "data": { "sdp": "..." } }` via WebSocket
- **THEN** the server SHALL forward the message to CC-gui's WebSocket connection

#### Scenario: WebRTC answer relay
- **WHEN** CC-gui sends `{ "type": "answer", "data": { "sdp": "..." } }` via WebSocket
- **THEN** the server SHALL forward the message to CC-client's WebSocket connection

#### Scenario: ICE candidate relay
- **WHEN** either party sends `{ "type": "ice-candidate", "data": { "candidate": "..." } }` via WebSocket
- **THEN** the server SHALL forward the message to the other party's WebSocket connection

#### Scenario: Call end relay
- **WHEN** CC-client sends `{ "type": "call-end", "data": {} }` via WebSocket
- **THEN** the server SHALL forward the message to CC-gui's WebSocket connection

### Requirement: A2A business flow triggered by call-start
On receiving a `call-start` message from CC-client, the system SHALL initiate the A2A orchestration sequence using the `a2a-python` SDK client for all outbound A2A calls.

#### Scenario: Successful end-to-end business flow
- **WHEN** CC-client sends `{ "type": "call-start", "data": { "phone": "13800000001" } }` via WebSocket
- **THEN** the server SHALL execute the following steps in order:
  1. Push `progress` (step: `query_customer`, status: `running`) to CC-gui
  2. Call Profiling Agent `query_customer` with `{ "phone": "13800000001" }`
  3. Push `progress` (step: `query_customer`, status: `done`) to CC-gui
  4. Concurrently execute: push `progress` (step: `query_bill`, status: `running`) + call Usage Agent `query_bill`; and push `progress` (step: `get_ai_model_status`, status: `running`) + call AI Management Agent `get_ai_model_status`
  5. Push `progress` for both completed steps
  6. Push `progress` (step: `get_nbo`, status: `running`) to CC-gui
  7. Call Recommendation Agent `get_nbo`
  8. Push `progress` (step: `get_nbo`, status: `done`) to CC-gui
  9. Push `business_payload` message with aggregated customer, bill, and nbo data to CC-gui

#### Scenario: CRM service unavailable during query_customer
- **WHEN** the A2A call to Profiling Agent `query_customer` fails
- **THEN** the server SHALL push `{ "type": "error", "step": "query_customer", "code": -32001, "message": "..." }` to CC-gui and abort the flow

#### Scenario: AI model inactive — NBO fallback
- **WHEN** AI Management Agent returns `status: "inactive"` for the NBO model
- **THEN** the server SHALL set `nbo_fallback=true` and `nbo_fallback_reason="model_inactive"`, and call Recommendation Agent with `{ "customer_id": "...", "fallback": true }`

### Requirement: Concurrent execution of independent steps
Steps `query_bill` and `get_ai_model_status` SHALL be executed concurrently via `asyncio.gather()` since both depend only on `customer_id` from step 2.

#### Scenario: Concurrent bill and AI model status queries
- **WHEN** `query_customer` completes successfully with a `customer_id`
- **THEN** the server SHALL launch `query_bill` and `get_ai_model_status` concurrently, waiting for both to complete before proceeding to `get_nbo`

### Requirement: REST order creation endpoint
The system SHALL expose `POST /order/create` accepting `{ "customer_id": "...", "offer_id": "..." }` and executing verify_identity → create_order → send_notification.

#### Scenario: Successful order placement
- **WHEN** CC-gui sends `POST /order/create { "customer_id": "cust_001", "offer_id": "po_001" }`
- **THEN** the server SHALL:
  1. Call `verify_identity` with `{ "customer_id": "cust_001", "verification_method": "otp" }`
  2. On `verified: true`, call `create_order` with `{ "customer_id": "cust_001", "offer_id": "po_001" }`
  3. Call `send_notification` with `{ "customer_id": "cust_001", "channel": "sms", "message": "Your order has been confirmed." }`
  4. Return `{ "order": { "order_id": "...", "state": "acknowledged", "order_date": "..." }, "notification": { "message_id": "...", "status": "sent", "sent_at": "..." } }`
  5. Push `order_result` message via WebSocket to CC-gui

#### Scenario: Identity verification fails
- **WHEN** `verify_identity` returns `{ "verified": false }`
- **THEN** the server SHALL return `{ "error": { "code": -32001, "message": "Identity verification failed", "step": "verify_identity" } }` and NOT proceed with order creation

#### Scenario: Notification fails but order stands
- **WHEN** `send_notification` returns `{ "status": "failed" }`
- **THEN** the server SHALL include the failed notification status in the response but SHALL NOT roll back the order

### Requirement: Progress messages pushed to CC-gui
The system SHALL push `{ "type": "progress", "step": "<step>", "status": "running" | "done" }` to CC-gui before and after each A2A step.

#### Scenario: Progress messages during business flow
- **WHEN** the A2A business flow executes
- **THEN** CC-gui SHALL receive progress messages with valid `step` values: `query_customer`, `query_bill`, `get_ai_model_status`, `get_nbo`, `verify_identity`, `create_order`, `send_notification`

### Requirement: Communication Agent hosting
The system SHALL host the Communication Agent at `/communication` with an Agent Card at `GET /communication/.well-known/agent.json` and A2A endpoint at `POST /communication/a2a`, exposing the `send_notification` skill (TMF681).

#### Scenario: Agent Card discovery
- **WHEN** a client sends `GET /communication/.well-known/agent.json`
- **THEN** the server SHALL return the Communication Agent Card with `send_notification` skill schema

#### Scenario: send_notification via A2A
- **WHEN** an A2A call is made to `POST /communication/a2a` with skill `send_notification` and input `{ "customer_id": "cust_001", "channel": "sms", "message": "Order confirmed." }`
- **THEN** the agent SHALL return `{ "message_id": "...", "status": "sent", "sent_at": "..." }` (TMF681 CommunicationMessage)

### Requirement: Configuration via environment variables
The system SHALL read external service URLs from environment variables with sensible localhost defaults. No hardcoded URLs.

#### Scenario: Default configuration for local development
- **WHEN** CC-server starts without environment variable overrides
- **THEN** it SHALL use `http://localhost:8002` for CRM-server and `http://localhost:8003` for Billing-server

#### Scenario: Docker Compose override
- **WHEN** `CRM_SERVER_URL` and `BILLING_SERVER_URL` environment variables are set
- **THEN** CC-server SHALL use those URLs for A2A calls

### Requirement: Dockerfile for containerized deployment
The system SHALL include a Dockerfile at `app/CC/CC-server/Dockerfile` following the backend template pattern (python:3.11-slim, uv, uvicorn on port 8001).

#### Scenario: Docker build and run
- **WHEN** the Dockerfile is built and the container is started
- **THEN** CC-server SHALL be accessible on port 8001 with all endpoints functional
