# CC-gui Spec

## Overview

CC-gui is the agent-side Vue 3 operator dashboard and WebRTC receiver. It connects to CC-server at `ws://localhost:8001/ws/signal` for signaling, accepts incoming WebRTC calls from CC-client, and displays the aggregated A2A business payload (customer, bill, NBO). The agent uses CC-gui to review customer data, select a recommendation, place an order, and monitor notification delivery. Desktop-first layout, served on port 5173.

---

## Requirements

### Requirement: Project scaffold
The system SHALL be a Vue 3 + Vite + TypeScript project at `app/CC/CC-gui/` with Pinia for state management, served on port 5173 via `vite.config.ts`.

#### Scenario: Dev server starts on correct port
- **WHEN** `npm run dev` is executed in `app/CC/CC-gui/`
- **THEN** the Vite dev server binds to port 5173

### Requirement: WebSocket signaling client
The system SHALL implement `src/api/signaling.ts` as a WebSocket client that connects to `ws://localhost:8001/ws/signal` and exposes `connect()`, `send(msg)`, and `onMessage(handler)` functions. The client follows the same pattern as CC-client's signaling module.

#### Scenario: Connect to CC-server signaling
- **WHEN** `connect()` is called
- **THEN** a WebSocket connection is established to `ws://localhost:8001/ws/signal`

#### Scenario: Send signaling message
- **WHEN** `send({ type: 'answer', data: { sdp: '...' } })` is called
- **THEN** the JSON-serialized message is sent over the WebSocket

#### Scenario: Receive signaling message
- **WHEN** a message arrives over the WebSocket
- **THEN** all registered `onMessage` handlers are called with the parsed JSON object

#### Scenario: Handle all inbound message types
- **WHEN** messages arrive with types `offer`, `ice-candidate`, `call-start`, `call-end`, `progress`, `business_payload`, `order_result`, or `error`
- **THEN** each is parsed and dispatched to the appropriate handler

### Requirement: WebRTC peer connection lifecycle (receiver/answerer)
The system SHALL implement `src/composables/useWebRTC.ts` that manages the `RTCPeerConnection` with `iceServers: []` as the **answerer** — receiving an SDP offer, creating an answer, relaying ICE candidates, and capturing local media via `getUserMedia`.

#### Scenario: Receive offer and send answer
- **WHEN** a `{ type: 'offer', data: { sdp } }` message is received via the signaling client
- **THEN** the composable creates an `RTCPeerConnection` with `iceServers: []`, calls `getUserMedia({ audio: true, video: true })`, sets the offer as remote description, creates an SDP answer, sets it as local description, and sends `{ type: 'answer', data: { sdp } }` via the signaling client

#### Scenario: Relay ICE candidates
- **WHEN** the local `RTCPeerConnection` fires an `icecandidate` event
- **THEN** the composable sends `{ type: 'ice-candidate', data: { candidate } }` via the signaling client

#### Scenario: Apply remote ICE candidate
- **WHEN** a `{ type: 'ice-candidate', data: { candidate } }` message is received
- **THEN** `addIceCandidate` is called on the `RTCPeerConnection`

#### Scenario: Buffer ICE candidates before offer
- **WHEN** ICE candidates are received before `setRemoteDescription` has been called
- **THEN** they are buffered and applied after `setRemoteDescription` resolves

#### Scenario: Expose remote stream
- **WHEN** the `RTCPeerConnection` fires an `ontrack` event
- **THEN** the remote stream (customer's video/audio) is stored in `sessionStore.remoteStream`

#### Scenario: Handle call-end teardown
- **WHEN** `endCall()` is invoked or a `{ type: 'call-end' }` message is received
- **THEN** the `RTCPeerConnection` is closed, all tracks on local/remote streams are stopped, streams are set to null

### Requirement: Session store
The system SHALL implement `src/stores/sessionStore.ts` as a Pinia store with the following state fields:

| Field | Type | Default |
|-------|------|---------|
| `callState` | `GuiCallState` | `'idle'` |
| `localStream` | `MediaStream \| null` | `null` |
| `remoteStream` | `MediaStream \| null` | `null` |
| `customer` | `{ id, name, customer_category, product_name } \| null` | `null` |
| `bill` | `{ bucket_balance, bucket_balance_unit, due_date, bill_amount, bill_amount_unit, plan_usage_pct } \| null` | `null` |
| `nbo` | `{ id, recommendation_item[] } \| null` | `null` |
| `nboFallback` | `boolean` | `false` |
| `nboFallbackReason` | `string \| null` | `null` |
| `selectedOfferId` | `string \| null` | `null` |
| `progressSteps` | `Record<string, 'pending' \| 'running' \| 'done' \| 'error'>` | all 7 steps `'pending'` |
| `order` | `{ order_id, state, order_date } \| null` | `null` |
| `notification` | `{ message_id, status, sent_at } \| null` | `null` |
| `errorMessage` | `string` | `''` |
| `errorStep` | `string \| null` | `null` |

`GuiCallState` is a union type: `'idle' | 'ringing' | 'call_active' | 'data_loaded' | 'ordering' | 'order_complete' | 'call_ended' | 'error'`

Progress step keys (ordered): `query_customer`, `query_bill`, `get_ai_model_status`, `get_nbo`, `verify_identity`, `create_order`, `send_notification`

#### Scenario: Initial state is idle
- **WHEN** the app loads
- **THEN** `callState` is `'idle'`, all data fields are `null`, all 7 progress steps are `'pending'`

#### Scenario: Reset clears all session data
- **WHEN** the store `reset()` action is called
- **THEN** all fields return to their defaults and progress steps reset to `'pending'`

### Requirement: UI state machine
The system SHALL implement the following call state machine driven by `sessionStore.callState`:

| State | Trigger | Display |
|---|---|---|
| `idle` | App loads; or after `call_ended` auto-reset (10 s) | Empty dashboard; "Waiting for incoming call" message; all data panels hidden |
| `ringing` | `offer` message received via WS | `IncomingCallBanner` overlay with "Answer" button |
| `call_active` | Agent clicks "Answer" (WebRTC handshake completes) | Video panel visible; progress tracker visible showing steps streaming; data panels hidden until payload arrives |
| `data_loaded` | `business_payload` message received | Customer card, bill card, NBO list populated; NBO items selectable; "Place Order" button visible (disabled until selection) |
| `ordering` | Agent clicks "Place Order" | "Place Order" button disabled/loading; progress tracker shows steps 5–7 running |
| `order_complete` | `order_result` message received | Order confirmation card visible; notification status visible; "Place Order" hidden |
| `call_ended` | Agent clicks "End Call" or `call-end` WS event | Video hidden; all data remains visible (read-only review); after 10 s auto-reset to `idle` |
| `error` | `error` message received, or WebRTC failure | Error banner with step name and message; partial data preserved if available; after 10 s auto-reset to `idle` |

#### Scenario: Transition from idle to ringing on offer
- **WHEN** an `offer` message arrives while `callState` is `'idle'`
- **THEN** `callState` changes to `'ringing'` and `IncomingCallBanner` appears

#### Scenario: Transition from ringing to call_active on answer
- **WHEN** the agent clicks "Answer" and the WebRTC connection is established
- **THEN** `callState` changes to `'call_active'`, the banner disappears, and the video panel becomes visible

#### Scenario: Transition to data_loaded on business_payload
- **WHEN** a `business_payload` message is received
- **THEN** `callState` changes to `'data_loaded'` and customer, bill, and NBO data populates the cards

#### Scenario: Transition to ordering on Place Order
- **WHEN** the agent selects an NBO and clicks "Place Order"
- **THEN** `callState` changes to `'ordering'` and a `POST /order/create` request is sent

#### Scenario: Transition to order_complete on order_result
- **WHEN** an `order_result` message is received
- **THEN** `callState` changes to `'order_complete'` and order/notification data is displayed

#### Scenario: Transition to call_ended on End Call
- **WHEN** the agent clicks "End Call" or a `call-end` message is received
- **THEN** `callState` changes to `'call_ended'`, streams are released, video is hidden, data remains visible

#### Scenario: Auto-reset to idle after call_ended
- **WHEN** `callState` transitions to `'call_ended'` or `'error'`
- **THEN** after 10 seconds, `callState` automatically resets to `'idle'` and all session data is cleared

#### Scenario: Re-accept call after reset
- **WHEN** `callState` has auto-reset to `'idle'` after a previous call
- **THEN** the dashboard shows "Waiting for incoming call" and can accept a new `offer`

### Requirement: Incoming call handling
The system SHALL display an `IncomingCallBanner` overlay when an SDP `offer` arrives. The agent must explicitly click "Answer" to accept the call. There is no auto-answer.

#### Scenario: Incoming call banner shown
- **WHEN** an `offer` message arrives and `callState` is `'idle'`
- **THEN** the `IncomingCallBanner` appears centered over the dashboard with an "Answer" button

#### Scenario: Agent answers call
- **WHEN** the agent clicks "Answer"
- **THEN** the WebRTC answer flow executes, the banner disappears, and `callState` transitions to `'call_active'`

#### Scenario: Caller hangs up before answer
- **WHEN** a `call-end` message arrives while `callState` is `'ringing'`
- **THEN** the banner disappears and `callState` transitions to `'call_ended'`

### Requirement: Progress tracker
The system SHALL implement `src/components/ProgressTracker.vue` as a vertical stepper displaying the 7 A2A flow steps with real-time status updates.

**Step labels (human-readable):**

| Step Key | Label |
|----------|-------|
| `query_customer` | Query Customer |
| `query_bill` | Query Bill |
| `get_ai_model_status` | Check AI Model |
| `get_nbo` | Get Recommendations |
| `verify_identity` | Verify Identity |
| `create_order` | Create Order |
| `send_notification` | Send Notification |

**Status display per step:**
- `pending` — Gray circle icon, muted text
- `running` — Animated spinner icon, normal text
- `done` — Green check icon, normal text
- `error` — Red X icon, red text

#### Scenario: Progress step starts running
- **WHEN** a `{ type: 'progress', step: 'query_customer', status: 'running' }` message is received
- **THEN** the "Query Customer" step shows an animated spinner

#### Scenario: Progress step completes
- **WHEN** a `{ type: 'progress', step: 'query_customer', status: 'done' }` message is received
- **THEN** the "Query Customer" step shows a green check

#### Scenario: Concurrent steps
- **WHEN** `query_bill` and `get_ai_model_status` both receive `status: 'running'`
- **THEN** both steps display spinners simultaneously

#### Scenario: Error on a step
- **WHEN** an `error` message is received with `step: 'query_customer'`
- **THEN** the "Query Customer" step shows a red X and the error message is displayed

### Requirement: WebSocket message dispatching
The system SHALL implement `src/composables/useMessageHandler.ts` that routes inbound WebSocket messages to store mutations and WebRTC actions.

| Message `type` | Action |
|---|---|
| `offer` | Set `callState = 'ringing'`, buffer SDP for answer flow |
| `ice-candidate` | Relay to WebRTC composable |
| `call-start` | (Informational — CC-gui may display caller phone from `data.phone`) |
| `call-end` | Tear down WebRTC, set `callState = 'call_ended'` |
| `progress` | Update `progressSteps[msg.step] = msg.status` |
| `business_payload` | Populate `customer`, `bill`, `nbo`, `nboFallback`, `nboFallbackReason` from `msg.data`; set `callState = 'data_loaded'` |
| `order_result` | Populate `order`, `notification` from `msg.data`; set `callState = 'order_complete'` |
| `error` | Set `errorMessage = msg.message`, `errorStep = msg.step`; update `progressSteps[msg.step] = 'error'`; set `callState = 'error'` |

#### Scenario: business_payload dispatched to store
- **WHEN** a `business_payload` message arrives
- **THEN** `customer`, `bill`, `nbo` fields in sessionStore are populated from `msg.data` and `callState` becomes `'data_loaded'`

#### Scenario: error dispatched to store
- **WHEN** an `error` message arrives with `{ step: 'query_bill', code: -32001, message: 'Service unavailable' }`
- **THEN** `errorStep` is `'query_bill'`, `errorMessage` is `'Service unavailable'`, and `progressSteps.query_bill` is `'error'`

### Requirement: NBO selection and order placement
The system SHALL allow the agent to select a recommendation item from the NBO list and trigger order placement via `POST http://localhost:8001/order/create`.

Implement the REST call in `src/api/orderApi.ts` using `fetch`.

#### Scenario: Agent selects NBO item
- **WHEN** the agent clicks a recommendation row in `NboList`
- **THEN** the row is highlighted with a radio selection and `selectedOfferId` is set to the item's `offering_id`

#### Scenario: Place Order sends REST request
- **WHEN** the agent clicks "Place Order" with a valid `selectedOfferId`
- **THEN** `POST /order/create { customer_id: sessionStore.customer.id, offer_id: selectedOfferId }` is sent to CC-server

#### Scenario: Order result arrives via WebSocket
- **WHEN** an `order_result` message arrives after a successful order
- **THEN** `order` and `notification` are populated in the store and the UI transitions to `order_complete`

#### Scenario: Identity verification fails
- **WHEN** the REST response contains `{ error: { code: -32001, step: 'verify_identity' } }`
- **THEN** an error banner displays "Identity verification failed" and the order is aborted; `callState` transitions to `'error'`

### Requirement: Call controls
The system SHALL implement `src/components/CallControls.vue` with an "End Call" button visible during active call states (`call_active`, `data_loaded`, `ordering`, `order_complete`).

#### Scenario: End Call terminates call
- **WHEN** the agent clicks "End Call"
- **THEN** `{ type: 'call-end', data: {} }` is sent via WebSocket, WebRTC is torn down, and `callState` transitions to `'call_ended'`

#### Scenario: Remote call-end terminates call
- **WHEN** a `{ type: 'call-end' }` message arrives from CC-server
- **THEN** the same teardown occurs and `callState` transitions to `'call_ended'`

### Requirement: Handle call-start info
The system SHALL display the caller's phone number when a `call-start` message is received, showing it in the header or sidebar for agent reference.

#### Scenario: Caller phone displayed
- **WHEN** a `{ type: 'call-start', data: { phone: '13800000001' } }` message is received
- **THEN** the phone number is displayed as "Caller: 138-0000-0001" in the dashboard

---

## Component Inventory

| Component | File | Responsibility |
|---|---|---|
| Page view | `src/views/DashboardView.vue` | Root view; two-column CSS grid layout; composes all panels |
| Incoming call banner | `src/components/IncomingCallBanner.vue` | Full-screen overlay with "Answer" button; visible only in `ringing` state |
| Video panel | `src/components/VideoPanel.vue` | Two `<video>` elements: remote (customer, large) + local (agent, small PIP); visible from `call_active` through `order_complete` |
| Progress tracker | `src/components/ProgressTracker.vue` | Vertical stepper showing 7 A2A steps with status icons (pending/running/done/error) |
| Customer card | `src/components/CustomerCard.vue` | Displays customer `name`, `customer_category` (as badge), `product_name` |
| Bill summary card | `src/components/BillSummaryCard.vue` | Displays `bucket_balance`, `due_date`, `bill_amount`, `plan_usage_pct` (as progress bar) |
| NBO list | `src/components/NboList.vue` | Selectable list of `recommendation_item[]` ordered by priority; each row shows `name`, `description`, `price`; radio selection |
| NBO fallback notice | `src/components/NboFallbackNotice.vue` | Info banner when `nboFallback=true`; text driven by `nboFallbackReason` |
| Order action bar | `src/components/OrderActionBar.vue` | "Place Order" button; disabled until NBO selected; hidden after `order_complete` |
| Order result card | `src/components/OrderResultCard.vue` | Displays `order_id`, `state`, `order_date` + notification `message_id`, `status`, `sent_at` |
| Error banner | `src/components/ErrorBanner.vue` | Red/amber banner for flow errors, identity failures, notification failures |
| Call controls | `src/components/CallControls.vue` | "End Call" button; visible during active call states |

**Supporting files:**

| File | Responsibility |
|---|---|
| `src/api/signaling.ts` | WebSocket client: connect, send, onMessage |
| `src/api/orderApi.ts` | `POST /order/create` REST call |
| `src/composables/useWebRTC.ts` | `RTCPeerConnection` lifecycle (receiver/answerer variant) |
| `src/composables/useMessageHandler.ts` | Routes inbound WS messages to store mutations |
| `src/stores/sessionStore.ts` | Pinia store for all session state |

---

## Layout — DashboardView

Desktop-first, minimum 1024px viewport width. CSS Grid two-column layout.

```
+-----------------------------------------------+
| Header: "CC-gui — Agent Dashboard"   [Caller]  |
+---------------+-------------------------------+
| LEFT SIDEBAR  | MAIN CONTENT                  |
| (320px fixed) | (flex: 1)                     |
|               |                               |
| [Video Panel] | [Customer Card] [Bill Card]   |
| (16:9 ratio)  |        (side-by-side)         |
|               |                               |
| [Progress     | [NBO Fallback Notice]         |
|  Tracker]     | [NBO Recommendation List]     |
|               | [Order Action Bar]            |
| [Call         | [Order Result Card]           |
|  Controls]    | [Error Banner]                |
+---------------+-------------------------------+
```

### Left sidebar (320px fixed)

- **Video panel** at top: remote stream (customer) fills a 16:9 aspect-ratio container; local stream (agent) as small PIP overlay at bottom-right (25% of remote container). Visible from `call_active` through `order_complete`.
- **Progress tracker** below video: vertical stepper, compact, showing all 7 steps. Steps 1–4 activate during `call_active`; steps 5–7 activate during `ordering`.
- **Call controls** at bottom: "End Call" button. Visible during active call states.

### Main content area (flex: 1)

- Vertical stack of data cards with 16px gap.
- **Customer card + Bill card** in a side-by-side 2-column sub-grid when viewport ≥ 1200px; stacked vertically below 1200px.
- **NBO fallback notice** — full width, above NBO list (only when `nboFallback=true`).
- **NBO list** — full width. Each row: radio selector, priority rank, name, description (truncated), price.
- **Order action bar** — below NBO list; "Place Order" button right-aligned.
- **Order result card** — replaces order action bar after `order_complete`.
- **Error banner** — appears at top of main content area when errors occur.
- Cards animate in with a fade/slide transition as data arrives.

### Incoming call banner

Full-viewport centered overlay (semi-transparent backdrop), above all content. Contains:
- "Incoming Call" title
- Caller phone number (if available from prior `call-start`)
- Large "Answer" button (green, prominent)
- Disappears immediately on click

### Idle state

When `callState === 'idle'`, the main content area shows a centered "Waiting for incoming call" message with a subtle pulsing indicator. Sidebar shows empty video placeholder and dimmed progress tracker.

---

## Data Formatting

| Field | Format | Example |
|---|---|---|
| Currency amounts (`bucket_balance`, `bill_amount`, `price`) | `{unit} {value}` with 2 decimal places | `EUR 35.50` |
| Dates (`due_date`, `order_date`, `sent_at`) | `DD MMM YYYY` (for dates) or `DD MMM YYYY HH:mm` (for timestamps) | `05 Apr 2026`, `14 Mar 2026 10:00` |
| `plan_usage_pct` | Horizontal progress bar + percentage text. Color: green (<70%), amber (70–90%), red (>90%) | `[███████░░░] 72%` |
| `customer_category` | Capitalized text inside a colored badge. Colors: gold → `#f59e0b`, silver → `#9ca3af`, bronze → `#cd7f32` | Gold badge |
| NBO priority | Implicit via list order (sorted by ascending priority). Optional `#1`, `#2` rank prefix | `#1 Plan-100G` |
| NBO `description` | Truncate at 120 characters with `…`; full text on hover tooltip | |
| `order.state` | Capitalized status badge (blue background) | `Acknowledged` |
| `notification.status` | `sent` → green badge "Sent"; `failed` → red badge "Failed" | |

---

## Error & Warning States

| Error Type | Severity | Component | Display | Persistent? |
|---|---|---|---|---|
| A2A flow error (`error` msg) | Error | `ErrorBanner` | Red banner at top of main content; shows step name + message | Yes (until new call) |
| Identity verification failure | Error | `ErrorBanner` | Red banner: "Identity verification failed — order blocked" | Yes |
| Notification failure (`status: 'failed'`) | Warning | Inline in `OrderResultCard` | Amber "Notification Failed" badge; order itself shown as successful | Yes |
| NBO fallback (`nbo_fallback=true`) | Info | `NboFallbackNotice` | Blue info banner above NBO list; text from `nbo_fallback_reason`: `"model_inactive"` → "AI model inactive — fallback used"; `"ollama_unavailable"` → "NBO engine unavailable — fallback used" | Yes |
| WebRTC connection failure | Error | `ErrorBanner` | Red banner: "Connection lost" | Yes |
| WebSocket disconnect | Error | `ErrorBanner` | Red banner: "Server connection lost — reconnecting…" | Until reconnected |

---

## Interaction Flows

### Flow 1: Accept incoming call

1. App is in `idle` state, showing "Waiting for incoming call"
2. `offer` message arrives via WebSocket → `callState = 'ringing'`
3. `IncomingCallBanner` overlay appears with "Answer" button
4. Agent clicks "Answer" → WebRTC answer flow executes (create answer SDP, send to server)
5. WebRTC connection established → `callState = 'call_active'`
6. Banner disappears; video panel activates; progress tracker shows steps running
7. A2A progress messages stream automatically (no agent action needed)
8. `business_payload` arrives → `callState = 'data_loaded'`; data cards populate

### Flow 2: Select NBO and place order

1. `data_loaded` state — customer, bill, and NBO cards are visible
2. Agent reviews customer data and NBO recommendations
3. Agent clicks a recommendation row → row highlights with radio selection; `selectedOfferId` set
4. Agent clicks "Place Order" → `callState = 'ordering'`; button shows loading state
5. `POST /order/create { customer_id, offer_id }` sent to CC-server
6. Progress tracker shows steps 5–7 streaming (verify_identity → create_order → send_notification)
7. `order_result` arrives → `callState = 'order_complete'`
8. Order confirmation card appears with order details + notification status
9. "Place Order" button is hidden

**No confirmation dialog** — the identity verification step on the server acts as the safeguard. A client-side dialog would be redundant and slow down agent workflow.

### Flow 3: End call

1. Agent clicks "End Call" in sidebar call controls (available in any active state)
2. `{ type: 'call-end', data: {} }` sent via WebSocket
3. WebRTC connection torn down; streams released
4. `callState = 'call_ended'` — video hidden, all data remains visible for review
5. After 10 seconds, auto-reset to `idle` (all session data cleared)

Alternatively: if `call-end` arrives from server (customer hung up), same teardown occurs automatically.

---

## Styling

### Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| Primary | `#1e40af` | Header background, primary buttons |
| Success | `#22c55e` | Connected state, done steps, "Sent" badge, "Answer" button |
| Error | `#ef4444` | Error banners, failed steps, "Failed" badge, "End Call" button |
| Warning | `#f59e0b` | Notification failure, usage bar (70–90%), gold badge |
| Info | `#3b82f6` | NBO fallback notice, info badges |
| Neutral | `#9ca3af` | Pending steps, silver badge, muted text |
| Background | `#f3f4f6` | Page background |
| Surface | `#ffffff` | Card backgrounds |
| Text | `#111827` | Primary text |
| Text muted | `#6b7280` | Labels, secondary text |
| Border | `#e5e7eb` | Card borders, dividers |

### Typography

- Font stack: `system-ui, 'Segoe UI', Roboto, sans-serif`
- Card section titles: `0.85rem`, uppercase, `#6b7280`, `font-weight: 600`, `letter-spacing: 0.05em`
- Data values: `1rem`, `#111827`
- Large values (currency amounts): `1.5rem`, `font-weight: 700`
- Header title: `1.125rem`, `#ffffff`, `font-weight: 600`

### Component Styling

- Cards: `background: #fff`, `border: 1px solid #e5e7eb`, `border-radius: 12px`, `padding: 20px`
- Buttons: `border-radius: 24px`, `padding: 10px 24px`, `font-weight: 600`
- Badges: `border-radius: 9999px`, `padding: 2px 10px`, `font-size: 0.75rem`, `font-weight: 600`
- NBO list rows: `padding: 12px 16px`, hover `background: #f9fafb`, selected `background: #eff6ff`, `border-left: 3px solid #3b82f6`
- Progress tracker steps: `padding: 8px 0`, icon `20px`, connecting line between steps (2px, gray when pending, green when done)

---

## Accessibility

- All interactive elements have descriptive `aria-label` attributes
- NBO list items are keyboard-navigable (arrow keys + Enter to select)
- "Answer" and "Place Order" buttons have contextual `aria-label` (e.g., `aria-label="Answer incoming call"`)
- Progress tracker steps use `aria-live="polite"` for screen reader updates
- Video elements have `aria-label="Customer video"` / `"Agent video (you)"`
- Color is never the sole status indicator — icons accompany all colored states
- Focus outlines visible on all interactive elements (`outline: 2px solid #3b82f6`)

---

## Port & Endpoint Reference

| Item | Value |
|---|---|
| CC-gui dev server | Port 5173 |
| CC-server WebSocket | `ws://localhost:8001/ws/signal` |
| Order placement | `POST http://localhost:8001/order/create` |
