## ADDED Requirements

### Requirement: Project scaffold
The system SHALL be a Vue 3 + Vite + TypeScript project at `app/CC/CC-gui/` with Pinia for state management, served on port 5173 via `vite.config.ts`.

#### Scenario: Dev server starts on correct port
- **WHEN** `npm run dev` is executed in `app/CC/CC-gui/`
- **THEN** the Vite dev server binds to port 5173

### Requirement: WebSocket signaling client
The system SHALL implement `src/api/signaling.ts` as a WebSocket client that connects to `ws://localhost:8001/ws/signal` and exposes `connect()`, `send(msg)`, and `onMessage(handler)` functions.

#### Scenario: Connect to CC-server signaling
- **WHEN** `connect()` is called
- **THEN** a WebSocket connection is established to `ws://localhost:8001/ws/signal`

#### Scenario: Send signaling message
- **WHEN** `send({ type: 'answer', data: { sdp: '...' } })` is called
- **THEN** the JSON-serialized message is sent over the WebSocket

#### Scenario: Receive and dispatch messages
- **WHEN** a message arrives with type `offer`, `ice-candidate`, `call-start`, `call-end`, `progress`, `business_payload`, `order_result`, or `error`
- **THEN** all registered `onMessage` handlers are called with the parsed JSON object

### Requirement: WebRTC peer connection lifecycle (receiver/answerer)
The system SHALL implement `src/composables/useWebRTC.ts` that manages the `RTCPeerConnection` with `iceServers: []` as the answerer — receiving an SDP offer, creating an answer, and relaying ICE candidates.

#### Scenario: Receive offer and send answer
- **WHEN** a `{ type: 'offer', data: { sdp } }` message is received
- **THEN** the composable creates an `RTCPeerConnection({ iceServers: [] })`, calls `getUserMedia({ audio: true, video: true })`, sets the offer as remote description, creates an SDP answer, sets it as local description, and sends `{ type: 'answer', data: { sdp } }` via the signaling client

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
- **THEN** the remote stream is stored in `sessionStore.remoteStream`

#### Scenario: Handle call-end teardown
- **WHEN** `endCall()` is invoked or a `call-end` message is received
- **THEN** the `RTCPeerConnection` is closed, all tracks stopped, streams set to null

### Requirement: Session store
The system SHALL implement `src/stores/sessionStore.ts` as a Pinia store with state fields: `callState` (GuiCallState), `localStream`, `remoteStream`, `customer`, `bill`, `nbo`, `nboFallback`, `nboFallbackReason`, `selectedOfferId`, `progressSteps`, `order`, `notification`, `errorMessage`, `errorStep`.

#### Scenario: Initial state is idle
- **WHEN** the app loads
- **THEN** `callState` is `'idle'`, all data fields are `null`, all 7 progress steps are `'pending'`

### Requirement: UI state machine
The system SHALL implement the call state machine with 8 states: `idle`, `ringing`, `call_active`, `data_loaded`, `ordering`, `order_complete`, `call_ended`, `error`.

#### Scenario: Transition from idle to ringing
- **WHEN** an `offer` message arrives while `callState` is `'idle'`
- **THEN** `callState` changes to `'ringing'` and `IncomingCallBanner` appears

#### Scenario: Transition from ringing to call_active
- **WHEN** the agent clicks "Answer" and WebRTC connection is established
- **THEN** `callState` changes to `'call_active'`, banner disappears, video panel visible

#### Scenario: Transition to data_loaded
- **WHEN** a `business_payload` message is received
- **THEN** `callState` changes to `'data_loaded'` and customer, bill, NBO data populates cards

#### Scenario: Transition to ordering
- **WHEN** the agent selects an NBO and clicks "Place Order"
- **THEN** `callState` changes to `'ordering'` and `POST /order/create` is sent

#### Scenario: Transition to order_complete
- **WHEN** an `order_result` message is received
- **THEN** `callState` changes to `'order_complete'` and order/notification data is displayed

#### Scenario: Transition to call_ended
- **WHEN** the agent clicks "End Call" or `call-end` message received
- **THEN** `callState` changes to `'call_ended'`, streams released, video hidden, data visible

#### Scenario: Auto-reset to idle
- **WHEN** `callState` transitions to `'call_ended'` or `'error'`
- **THEN** after 10 seconds, `callState` resets to `'idle'` and session data is cleared

### Requirement: Incoming call handling
The system SHALL display an `IncomingCallBanner` overlay with "Answer" button when an SDP offer arrives. The agent SHALL explicitly click to accept.

#### Scenario: Incoming call banner shown
- **WHEN** an `offer` message arrives and `callState` is `'idle'`
- **THEN** `IncomingCallBanner` appears centered over the dashboard with an "Answer" button

#### Scenario: Agent answers call
- **WHEN** the agent clicks "Answer"
- **THEN** WebRTC answer flow executes, banner disappears, `callState` transitions to `'call_active'`

#### Scenario: Caller hangs up before answer
- **WHEN** a `call-end` message arrives while `callState` is `'ringing'`
- **THEN** banner disappears and `callState` transitions to `'call_ended'`

### Requirement: Progress tracker
The system SHALL implement `src/components/ProgressTracker.vue` as a vertical stepper showing 7 A2A steps with real-time status (pending/running/done/error).

#### Scenario: Step starts running
- **WHEN** a `{ type: 'progress', step: 'query_customer', status: 'running' }` message is received
- **THEN** the "Query Customer" step shows an animated spinner

#### Scenario: Step completes
- **WHEN** a `{ type: 'progress', step: 'query_customer', status: 'done' }` message is received
- **THEN** the "Query Customer" step shows a green check

#### Scenario: Concurrent steps
- **WHEN** `query_bill` and `get_ai_model_status` both receive `status: 'running'`
- **THEN** both steps display spinners simultaneously

#### Scenario: Step error
- **WHEN** an `error` message is received with `step: 'query_customer'`
- **THEN** the "Query Customer" step shows a red X

### Requirement: WebSocket message dispatching
The system SHALL implement `src/composables/useMessageHandler.ts` that routes inbound WebSocket messages to store mutations.

#### Scenario: business_payload dispatched
- **WHEN** a `business_payload` message arrives
- **THEN** `customer`, `bill`, `nbo` in sessionStore are populated and `callState` becomes `'data_loaded'`

#### Scenario: error dispatched
- **WHEN** an `error` message arrives with step and message
- **THEN** `errorStep` and `errorMessage` are set, `progressSteps[step]` is `'error'`, `callState` is `'error'`

#### Scenario: progress dispatched
- **WHEN** a `progress` message arrives
- **THEN** `progressSteps[step]` is updated to the received status

### Requirement: NBO selection and order placement
The system SHALL allow the agent to select a recommendation item and trigger `POST http://localhost:8001/order/create { customer_id, offer_id }`.

#### Scenario: Agent selects NBO item
- **WHEN** the agent clicks a recommendation row
- **THEN** the row highlights and `selectedOfferId` is set to the item's `offering_id`

#### Scenario: Place Order sends REST request
- **WHEN** the agent clicks "Place Order" with a valid `selectedOfferId`
- **THEN** `POST /order/create { customer_id, offer_id }` is sent to CC-server

#### Scenario: Identity verification failure
- **WHEN** the REST response contains `{ error: { code: -32001, step: 'verify_identity' } }`
- **THEN** an error banner displays "Identity verification failed" and order is aborted

### Requirement: Call controls
The system SHALL implement "End Call" button visible during active call states (`call_active`, `data_loaded`, `ordering`, `order_complete`).

#### Scenario: End Call terminates call
- **WHEN** the agent clicks "End Call"
- **THEN** `call-end` is sent via WebSocket, WebRTC torn down, `callState` transitions to `'call_ended'`

#### Scenario: Remote call-end
- **WHEN** a `call-end` message arrives from CC-server
- **THEN** same teardown occurs and `callState` transitions to `'call_ended'`

### Requirement: Dashboard layout
The system SHALL implement `src/views/DashboardView.vue` as a desktop-first two-column CSS Grid layout (min 1024px): left sidebar (320px) with video, progress tracker, call controls; main content (flex) with data cards, NBO list, order bar.

#### Scenario: Two-column layout renders
- **WHEN** the dashboard loads on a 1024px+ viewport
- **THEN** left sidebar (320px) and main content area are displayed side by side

#### Scenario: Customer and bill cards side-by-side
- **WHEN** viewport is 1200px+ and `callState` is `'data_loaded'`
- **THEN** customer card and bill card render in a 2-column sub-grid

### Requirement: Data formatting
The system SHALL format TMF data fields: currency as `{unit} {value}` with 2 decimals, dates as `DD MMM YYYY`, usage percentage as a colored progress bar (green <70%, amber 70-90%, red >90%), customer category as a colored badge.

#### Scenario: Currency formatting
- **WHEN** `bucket_balance` is `35.5` and `bucket_balance_unit` is `EUR`
- **THEN** the display shows `EUR 35.50`

#### Scenario: Usage bar color
- **WHEN** `plan_usage_pct` is `72`
- **THEN** the progress bar is amber colored and shows `72%`

### Requirement: Error and warning display
The system SHALL display distinct visual treatments: red banners for flow errors and identity failures, amber inline notices for notification failures, blue info banners for NBO fallback.

#### Scenario: NBO fallback notice
- **WHEN** `nbo_fallback` is `true` and `nbo_fallback_reason` is `'model_inactive'`
- **THEN** a blue info banner shows "AI model inactive — fallback used" above the NBO list

#### Scenario: Notification failure warning
- **WHEN** `notification.status` is `'failed'`
- **THEN** an amber "Notification Failed" badge appears in the order result card; the order itself is shown as successful

### Requirement: Caller phone display
The system SHALL display the caller's phone number when a `call-start` message is received.

#### Scenario: Caller phone shown
- **WHEN** a `{ type: 'call-start', data: { phone: '13800000001' } }` message is received
- **THEN** "Caller: 138-0000-0001" is displayed in the dashboard header
