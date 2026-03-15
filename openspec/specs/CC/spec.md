# CC Spec

## Overview

The CC (Call Center) subsystem is the sole orchestrator of the A2A business flow. It consists of three components: CC-server (FastAPI backend, WebRTC signaling relay, A2A orchestrator), CC-gui (agent operator dashboard, WebRTC receiver), and CC-client (customer-side Vue 3 GUI, WebRTC caller). CC-server is the only component permitted to call CRM-server or Billing-server.

CC does not own most TMForum domain resources directly — it orchestrates across TMF629, TMF620, TMF622, TMF637, and TMF677 by consuming the skills exposed by CRM-server and Billing-server. CC-server also hosts the **Communication Agent** (`/communication`), which implements TMF681 Communication Management to deliver post-order notifications to the customer.

---

## TMForum Field Mapping

CC-server aggregates data from CRM and Billing skills. The aggregated session payload returned to CC-gui uses TMF-aligned field names consistent with the source skills.

### Aggregated Session Payload (CC-server → CC-gui)

| Payload Field | Source Skill | TMF Resource |
|---|---|---|
| `customer.id` | `query_customer` | TMF629 `Customer.id` |
| `customer.name` | `query_customer` | TMF629 `Customer.name` |
| `customer.customer_category` | `query_customer` | TMF629 `Customer.customerCategory` |
| `customer.product_name` | `query_customer` | TMF637 `Product.name` |
| `bill.bucket_balance` | `query_bill` | TMF677 `bucket.remainingValue.amount` |
| `bill.bucket_balance_unit` | `query_bill` | TMF677 `bucket.remainingValue.units` |
| `bill.due_date` | `query_bill` | TMF678 `CustomerBill.paymentDueDate` |
| `bill.bill_amount` | `query_bill` | TMF678 `CustomerBill.amountDue.value` |
| `bill.bill_amount_unit` | `query_bill` | TMF678 `CustomerBill.amountDue.unit` |
| `bill.plan_usage_pct` | `query_bill` | TMF677 derived usage percentage |
| `nbo.id` | `get_nbo` | TMF701 `Recommendation.id` |
| `nbo.recommendation_item[]` | `get_nbo` | TMF701 `Recommendation.recommendationItem[]` |
| `nbo.recommendation_item[].id` | `get_nbo` | TMF701 `RecommendationItem.id` |
| `nbo.recommendation_item[].priority` | `get_nbo` | TMF701 `RecommendationItem.priority` |
| `nbo.recommendation_item[].offering_id` | `get_nbo` | TMF620 `ProductOffering.id` |
| `nbo.recommendation_item[].name` | `get_nbo` | TMF620 `ProductOffering.name` |
| `nbo.recommendation_item[].description` | `get_nbo` | TMF620 `ProductOffering.description` |
| `nbo.recommendation_item[].price` | `get_nbo` | TMF620 `ProductOffering.productOfferingPrice[0].price.value` |
| `nbo.recommendation_item[].price_unit` | `get_nbo` | TMF620 `ProductOffering.productOfferingPrice[0].price.unit` |
| `nbo_fallback` | CC-server internal | `true` if NBO recommendations are from the fallback path |
| `nbo_fallback_reason` | CC-server internal | `"model_inactive"` (Step 3.5: TMF915 status inactive) \| `"ollama_unavailable"` (Recommendation Agent: Ollama unreachable at runtime). Only present when `nbo_fallback=true` |

### Order Request (CC-gui → CC-server)

| Field | TMF Resource |
|---|---|
| `customer_id` | TMF622 `ProductOrder.relatedParty[role=customer].id` |
| `offer_id` | TMF622 `ProductOrder.productOrderItem[0].productOffering.id` |

### Order Response (CC-server → CC-gui)

| Field | TMF Resource |
|---|---|
| `order_id` | TMF622 `ProductOrder.id` |
| `state` | TMF622 `ProductOrder.state` (initial: `"acknowledged"`) |
| `order_date` | TMF622 `ProductOrder.orderDate` (ISO 8601) |

### Notification Response (CC-server → CC-gui, after `send_notification`)

| Field | TMF Resource |
|---|---|
| `message_id` | TMF681 `CommunicationMessage.id` |
| `status` | TMF681 `CommunicationMessage.state` (enum: `sent`, `failed`) |
| `sent_at` | TMF681 `CommunicationMessage.sendTime` (ISO 8601) |

---

## Requirements

### CC-server: Orchestration
- The system SHALL be the sole entry point for the A2A business flow
- The system SHALL orchestrate calls to CRM-server and Billing-server in sequence via A2A
- The system SHALL aggregate all subsystem results and return them to CC-gui using TMF-aligned field names
- The system SHALL NOT be called by CRM-server or Billing-server
- The system SHALL use `httpx.AsyncClient` with `timeout=10.0` for all outbound A2A calls
- The system SHALL enable CORS on all endpoints to allow local GUI access
- The system SHALL handle A2A call failures gracefully and return a standard JSON-RPC error object

### CC-server: WebRTC Signaling
- The system SHALL provide a WebSocket endpoint at `ws://localhost:8001/ws/signal`
- The system SHALL relay WebRTC signaling messages between CC-client and CC-gui
- Supported message types: `offer`, `answer`, `ice-candidate`, `call-start`, `call-end`
- On receiving a `call-start` message, the system SHALL extract the caller's `phone` number and initiate the A2A business flow
- The system SHALL NOT configure any STUN or TURN servers — demo uses direct WebRTC connection only

### CC-server: WebSocket Message Envelope

All messages over `ws://localhost:8001/ws/signal` SHALL include a `type` field as the top-level discriminator. The `type` field determines how CC-server, CC-client, and CC-gui route and handle the message.

#### Message Type Reference

| `type` | Direction | Description |
|--------|-----------|-------------|
| `offer` | CC-client → CC-server → CC-gui | WebRTC SDP offer |
| `answer` | CC-gui → CC-server → CC-client | WebRTC SDP answer |
| `ice-candidate` | CC-client ↔ CC-server ↔ CC-gui | ICE candidate relay |
| `call-start` | CC-client → CC-server | Call initiated; triggers A2A business flow |
| `call-end` | CC-client → CC-server → CC-gui | Call terminated |
| `progress` | CC-server → CC-gui | A2A flow step status update |
| `business_payload` | CC-server → CC-gui | Aggregated A2A result (customer + bill + nbo) |
| `order_result` | CC-server → CC-gui | Order placement + notification result |
| `error` | CC-server → CC-gui | Flow failure notification |

#### Envelope Schemas

**Signaling messages** (`offer`, `answer`, `ice-candidate`, `call-start`, `call-end`) carry their payload under a `data` key:
```json
{ "type": "offer", "data": { "sdp": "..." } }
{ "type": "call-start", "data": { "phone": "13800000001" } }
{ "type": "ice-candidate", "data": { "candidate": "..." } }
```

**`progress` message** — emitted by CC-server before and after each A2A step:
```json
{ "type": "progress", "step": "query_customer", "status": "running" }
{ "type": "progress", "step": "query_customer", "status": "done" }
```
Valid `step` values: `query_customer`, `query_bill`, `get_ai_model_status`, `get_nbo`, `verify_identity`, `create_order`, `send_notification`

**`business_payload` message** — emitted after `get_nbo` completes (step 4):
```json
{
  "type": "business_payload",
  "data": {
    "customer": { "id": "...", "name": "...", "customer_category": "...", "product_name": "..." },
    "bill": { "bucket_balance": 35.50, "bucket_balance_unit": "EUR", "due_date": "2026-04-05", "bill_amount": 99.00, "bill_amount_unit": "EUR", "plan_usage_pct": 72 },
    "nbo": { "id": "...", "recommendation_item": [ "..." ] },
    "nbo_fallback": false,
    "nbo_fallback_reason": null
  }
}
```

**`order_result` message** — emitted after `send_notification` completes:
```json
{
  "type": "order_result",
  "data": {
    "order": { "order_id": "...", "state": "acknowledged", "order_date": "..." },
    "notification": { "message_id": "...", "status": "sent", "sent_at": "..." }
  }
}
```

**`error` message** — emitted when a flow step fails unrecoverably:
```json
{ "type": "error", "step": "query_customer", "code": -32001, "message": "Customer not found" }
```

### CC-server: Business Flow Sequence
1. Receive `call-start` event from CC-client via WebSocket with `{ "phone": "..." }`
   → push `{ "type": "progress", "step": "query_customer", "status": "running" }` to CC-gui
2. Call **Profiling Agent** (`POST http://localhost:8002/profiling/a2a`) `skill=query_customer` with `{ "phone" }` → receive `customer_id`, `name`, `customer_category` (TMF629), `product_name` (TMF637)
   → push `{ "type": "progress", "step": "query_customer", "status": "done" }` to CC-gui
   → push `{ "type": "progress", "step": "query_bill", "status": "running" }` to CC-gui
3. Call **Usage Agent** (`POST http://localhost:8003/usage/a2a`) `skill=query_bill` with `{ "customer_id" }` → receive `bucket_balance`, `bucket_balance_unit`, `due_date`, `bill_amount`, `bill_amount_unit`, `plan_usage_pct` (TMF677/678)
   → push `{ "type": "progress", "step": "query_bill", "status": "done" }` to CC-gui
3.5. *(Optional)* push `{ "type": "progress", "step": "get_ai_model_status", "status": "running" }` to CC-gui; Call **AI Management Agent** (`POST http://localhost:8002/ai-management/a2a`) `skill=get_ai_model_status` with `{ "model_id": "<nbo_model_id>" }` → receive `status` (TMF915 `AIModel`). If `status == "inactive"`, set `nbo_fallback=true`, `nbo_fallback_reason="model_inactive"`; push `{ "type": "progress", "step": "get_ai_model_status", "status": "done" }` to CC-gui

> **Note:** Steps 3 (`query_bill`) and 3.5 (`get_ai_model_status`) are independent — both depend only on `customer_id` from step 2. Implementations MAY execute them concurrently via `asyncio.gather()` to reduce total latency before the Ollama call.

4. push `{ "type": "progress", "step": "get_nbo", "status": "running" }` to CC-gui; Call **Recommendation Agent** (`POST http://localhost:8002/recommendation/a2a`) `skill=get_nbo` with `{ "customer_id" }` (or `{ "customer_id", "fallback": true }` if `nbo_fallback=true`) → receive TMF701 `Recommendation` object (`id` + `recommendation_item[]` ordered by priority). If Recommendation Agent used Ollama fallback internally, it sets `nbo_fallback=true`, `nbo_fallback_reason="ollama_unavailable"` in its response.
   → push `{ "type": "progress", "step": "get_nbo", "status": "done" }` to CC-gui
   → push `business_payload` message (see envelope schema above) to CC-gui
5. On agent selection of an offer: receive `POST /order/create { customer_id, offer_id }` from CC-gui
6. push `{ "type": "progress", "step": "verify_identity", "status": "running" }` to CC-gui; Call **Profiling Agent** (`POST http://localhost:8002/profiling/a2a`) `skill=verify_identity` with `{ "customer_id", "verification_method": "otp" }` → receive TMF720 `DigitalIdentity` status. If `verified == false`, return identity verification failure to CC-gui and abort order placement
7. push `{ "type": "progress", "step": "create_order", "status": "running" }` to CC-gui; Call **Order Agent** (`POST http://localhost:8002/order/a2a`) `skill=create_order` with `{ customer_id, offer_id }` → receive `order_id`, `state: "acknowledged"`, `order_date` (TMF622)
8. push `{ "type": "progress", "step": "send_notification", "status": "running" }` to CC-gui; Call **Communication Agent** (`POST http://localhost:8001/communication/a2a`) `skill=send_notification` with `{ "customer_id", "channel", "message" }` → receive `message_id`, `status`, `sent_at` (TMF681 `CommunicationMessage`)
   → push `order_result` message (see envelope schema above) to CC-gui

### CC-server: REST Endpoints

#### POST /order/create

Triggered by CC-gui when the agent selects an NBO offer and places an order.

**Request Body:**
```json
{
  "customer_id": "string (TMF622 ProductOrder.relatedParty[role=customer].id)",
  "offer_id": "string (TMF620 ProductOffering.id)"
}
```

**Response — Success (HTTP 200):**
```json
{
  "order": {
    "order_id": "string (TMF622 ProductOrder.id)",
    "state": "acknowledged",
    "order_date": "string (ISO 8601)"
  },
  "notification": {
    "message_id": "string (TMF681 CommunicationMessage.id)",
    "status": "sent | failed",
    "sent_at": "string (ISO 8601)"
  }
}
```

**Response — Identity Verification Failure (HTTP 200 with error body):**
```json
{
  "error": {
    "code": -32001,
    "message": "Identity verification failed",
    "step": "verify_identity"
  }
}
```

**Response — Flow Error (HTTP 200 with error body):**
```json
{
  "error": {
    "code": -32000,
    "message": "string",
    "step": "string (name of the A2A step that failed)"
  }
}
```

- The system SHALL call `verify_identity` before `create_order`; if `verified == false`, return the identity failure response and abort
- The system SHALL always attempt `send_notification` after a successful `create_order`; a notification failure (`status: "failed"`) SHALL NOT roll back the order

### CC-client (Vue 3 GUI — WebRTC Caller)
- The client SHALL be a Vue 3 frontend GUI accessible at port 5172
- The client SHALL connect to CC-server WebSocket at `ws://localhost:8001/ws/signal` for signaling
- The client SHALL initiate a WebRTC `RTCPeerConnection` with `iceServers: []` (no STUN/TURN)
- The client SHALL allow the user to enter a phone number and initiate a call
- On call initiation, the client SHALL send an SDP `offer` to CC-server via WebSocket
- On receiving an SDP `answer`, the client SHALL complete the WebRTC handshake
- On ICE candidate events, the client SHALL relay candidates to CC-server
- On call connected, the client SHALL send `call-start` with `{ "phone": "<entered_number>" }` to CC-server
- The client SHALL NOT connect to CRM-server or Billing-server
- The client SHALL make **no REST HTTP calls** to CC-server — all interaction is via WebSocket signaling only; no `src/api/` HTTP files are needed beyond the WebSocket client (`signaling.ts`)

#### CC-client: Component Inventory

| Component | File | Responsibility |
|---|---|---|
| Page view | `src/views/DialerView.vue` | Single-page root view; composes all components; manages UI state |
| Keypad | `src/components/DialPad.vue` | Numeric keypad (3×4 grid) + phone number text input + Call / End buttons |
| State display | `src/components/CallStatus.vue` | Displays current call state label + visual indicator dot |
| Video tiles | `src/components/VideoStream.vue` | Two `<video>` elements: local stream (`getUserMedia`, muted) + remote stream (`RTCPeerConnection`); both hidden until `connected` state |

**Supporting files:**
- `src/api/signaling.ts` — WebSocket client: connect, send, receive signaling messages
- `src/composables/useWebRTC.ts` — `RTCPeerConnection` lifecycle: create offer, handle answer, relay ICE, track connection state, capture `localStream` via `getUserMedia`
- `src/stores/callStore.ts` — Pinia store: `callState`, `phoneNumber`, `localStream`, `remoteStream`

### CC-client: UI States & Layout

#### UI State Machine

| State | Trigger | Display |
|---|---|---|
| `idle` | App loads | DialPad visible; "Call" button enabled; no status shown |
| `dialing` | User clicks "Call" | "Call" button disabled; CallStatus shows "Connecting…"; WebRTC offer sent |
| `ringing` | SDP offer sent, waiting for answer | CallStatus shows "Ringing…" |
| `connected` | WebRTC `connectionstatechange` → `"connected"` | CallStatus shows "Call Connected"; VideoStream tiles visible; `call-start` sent to CC-server |
| `ended` | User clicks "End Call" or `call-end` WS event received | CallStatus shows "Call Ended"; DialPad re-enabled; VideoStream tiles hidden; streams released |
| `error` | WebRTC failure or WebSocket disconnect | CallStatus shows error message; "Retry" or re-dial option available |

#### Layout — `DialerView.vue`

- **Mobile-first, portrait layout only** — no desktop/tablet breakpoints needed
- Full-viewport single column, optimized for ~375–430 px wide screens

**Top to bottom:**
1. **Header bar** — app title "CC-client — Customer Caller" (small, fixed height)
2. **VideoStream section** — stacked vertically; shown only in `connected` state:
   - **Remote video** (`remoteStream`) — larger tile (~60 vw square), centered; labeled "Agent"
   - **Local video** (`localStream`) — smaller tile (~28 vw square), overlaid at bottom-right corner of remote video (picture-in-picture); muted; labeled "You"
3. **DialPad section** — full-width numeric keypad (3×4 grid) with phone number display input above + Call / End button below
4. **CallStatus section** — single centered line: state label + indicator dot

### CC-gui (Vue 3 GUI — Agent Dashboard + WebRTC Receiver)
- The GUI SHALL be accessible at port 5173
- The GUI SHALL connect to CC-server for all data (port 8001)
- The GUI SHALL connect to CC-server WebSocket at `ws://localhost:8001/ws/signal` for signaling
- The GUI SHALL accept incoming WebRTC calls: receive SDP `offer`, send back SDP `answer`
- The GUI SHALL display the aggregated session payload using TMF-aligned labels:
  - Customer profile: `name`, `customer_category`, `product_name`
  - Bill summary: `bucket_balance`, `due_date`, `bill_amount`, `plan_usage_pct`
  - NBO list: `recommendation_item[]` ordered by `priority`, each showing `name`, `description`, `price`, `price_unit`
  - When `nbo_fallback=true` is set in the payload, display a fallback notice whose text is driven by `nbo_fallback_reason`: `"model_inactive"` → "AI model inactive – fallback used"; `"ollama_unavailable"` → "NBO engine unavailable – fallback used"
- The GUI SHALL allow the agent to select a recommendation and trigger order placement via `POST /order/create { customer_id, offer_id }`
- The GUI SHALL display an identity verification failure notice if `verify_identity` returns `verified == false`
- The GUI SHALL display the order confirmation: `order_id`, `state`, `order_date`
- The GUI SHALL display a "Notification Sent" status (with `message_id`, `sent_at`) alongside the order confirmation after `send_notification` completes
- The GUI SHALL display a "Notification Failed" warning if `send_notification` returns `status == "failed"`
- The GUI SHALL NOT connect to CRM-server or Billing-server directly

---

## Scenarios

### Scenario: Successful end-to-end call flow
- Given: All three servers (CC, CRM, Billing) are running and seeded; CC-gui is open and connected to signaling
- When: Agent opens CC-client, enters phone `"13800000001"`, and clicks "Call"
- Then:
  1. CC-client sends WebRTC offer → CC-server relays to CC-gui → CC-gui answers → P2P call established
  2. CC-client sends `call-start { phone: "13800000001" }` to CC-server
  3. CC-server completes A2A flow and pushes aggregated payload to CC-gui:
     ```json
     {
       "customer": { "id": "...", "name": "...", "customer_category": "gold", "product_name": "Plan-50G" },
       "bill": { "bucket_balance": 35.50, "bucket_balance_unit": "EUR", "due_date": "2026-04-05", "bill_amount": 99.00, "bill_amount_unit": "EUR", "plan_usage_pct": 72 },
       "nbo": {
         "id": "rec_001",
         "recommendation_item": [
           { "id": "ri_001", "priority": 1, "offering_id": "po_001", "name": "Plan-100G", "description": "...", "price": 139.0, "price_unit": "EUR" },
           { "id": "ri_002", "priority": 2, "offering_id": "po_002", "name": "Plan-200G", "description": "...", "price": 199.0, "price_unit": "EUR" }
         ]
       }
     }
     ```
  4. CC-gui displays customer info, bill summary, and NBO list

### Scenario: Agent places an order
- Given: CC-gui is displaying NBO recommendations after a successful call flow
- When: Agent selects the item with `offering_id: "po_001"` (priority 1) and clicks "Place Order"
- Then:
  1. CC-gui sends `POST /order/create { "customer_id": "...", "offer_id": "po_001" }` to CC-server
  2. CC-server calls `CRM:verify_identity` with `{ "customer_id": "...", "verification_method": "otp" }` → receives `{ "verified": true, ... }`
  3. CC-server calls `CRM:create_order` → CC-gui displays: `{ "order_id": "...", "state": "acknowledged", "order_date": "2026-03-14T10:00:00Z" }`
  4. CC-server calls `CC:send_notification` with `{ "customer_id": "...", "channel": "sms", "message": "Your order has been confirmed." }`
  5. CC-gui displays "Notification Sent" with `{ "message_id": "...", "status": "sent", "sent_at": "2026-03-14T10:00:05Z" }`

### Scenario: Identity verification fails — order blocked
- Given: CC-gui is displaying NBO recommendations; identity verification returns `verified == false`
- When: Agent clicks "Place Order"
- Then: CC-server calls `CRM:verify_identity` → receives `{ "verified": false, ... }` → CC-server returns identity failure to CC-gui → CC-gui displays an identity verification failure notice; order placement is aborted

### Scenario: Post-order notification delivery
- Given: An order has been successfully placed (`state: "acknowledged"`)
- When: CC-server completes the `create_order` call
- Then: CC-server calls `CC:send_notification` with `{ "customer_id", "channel": "sms", "message": "Order confirmed." }` → Communication Agent returns `{ "message_id": "...", "status": "sent", "sent_at": "..." }` → CC-gui displays "Notification Sent" alongside order confirmation

### Scenario: Post-order notification fails
- Given: An order has been successfully placed but the notification channel is unavailable
- When: CC-server calls `CC:send_notification`
- Then: Communication Agent returns `{ "status": "failed", ... }` → CC-gui displays a "Notification Failed" warning; the order itself is unaffected

### Scenario: NBO AI model unavailable — fallback used
- Given: AI Management Agent returns `{ "status": "inactive" }` for the NBO model
- When: CC-server calls `AI Management Agent` at step 3.5
- Then: CC-server sets `nbo_fallback=true`, `nbo_fallback_reason="model_inactive"` and calls `Recommendation Agent` for price-sorted fallback recommendations; CC-gui displays an "AI model inactive – fallback used" notice alongside the NBO list

### Scenario: CRM service unavailable during flow
- Given: CRM-server is down
- When: CC-server attempts to call `CRM:query_customer`
- Then: CC-server returns a JSON-RPC error to CC-gui indicating the service is unavailable; the flow does not proceed further

### Scenario: WebRTC direct connection (same LAN)
- Given: CC-client and CC-gui are running on the same machine or same LAN; no STUN server configured
- When: CC-client initiates a call
- Then: WebRTC P2P connection is established successfully via local ICE candidates; audio/video stream is active

---

## A2A Skill Schema

### Communication Agent — `send_notification`
```json
{
  "inputSchema": {
    "type": "object",
    "properties": {
      "customer_id": { "type": "string", "description": "TMF681 CommunicationMessage.receiver[].id — the customer to notify" },
      "channel":     { "type": "string", "description": "Delivery channel: sms | email | push (TMF681 CommunicationMessage.type)", "enum": ["sms", "email", "push"] },
      "message":     { "type": "string", "description": "Notification body text (TMF681 CommunicationMessage.content)" }
    },
    "required": ["customer_id", "channel", "message"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "message_id": { "type": "string", "description": "TMF681 CommunicationMessage.id" },
      "status":     { "type": "string", "description": "TMF681 CommunicationMessage.state", "enum": ["sent", "failed"] },
      "sent_at":    { "type": "string", "description": "TMF681 CommunicationMessage.sendTime (ISO 8601)", "format": "date-time" }
    },
    "required": ["message_id", "status", "sent_at"]
  }
}
```

---

## Port & Service Reference

| Module | Port |
|---|---|
| CC-server | 8001 |
| CC-client-gui | 5172 |
| CC-gui | 5173 |

| Endpoint | Description |
|---|---|
| `POST /order/create` | Triggered by CC-gui to place an order (`customer_id`, `offer_id`) |
| `WS /ws/signal` | WebRTC signaling relay between CC-client and CC-gui |

| Agent | Agent Card | A2A Endpoint |
|---|---|---|
| Communication Agent | `GET /communication/.well-known/agent.json` | `POST /communication/a2a` |
