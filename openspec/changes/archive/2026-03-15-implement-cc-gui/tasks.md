## 1. Project Scaffold

- [x] 1.1 Initialize Vue 3 + Vite + TypeScript project at `app/CC/CC-gui/` with `npm create vite`
- [x] 1.2 Install dependencies: `pinia` and dev deps
- [x] 1.3 Configure `vite.config.ts` to set `server.port: 5173`
- [x] 1.4 Clean up default Vite scaffold: remove boilerplate, wire `App.vue` to render `DashboardView`
- [x] 1.5 Add global CSS reset and base styles (`src/style.css`): font stack, background color, box-sizing

## 2. Pinia Session Store

- [x] 2.1 Create `src/stores/sessionStore.ts` with all state fields: `callState` (GuiCallState union), `localStream`, `remoteStream`, `customer`, `bill`, `nbo`, `nboFallback`, `nboFallbackReason`, `selectedOfferId`, `progressSteps` (Record with 7 steps, default 'pending'), `order`, `notification`, `errorMessage`, `errorStep`
- [x] 2.2 Add `reset()` action that clears all fields to defaults

## 3. Signaling Client

- [x] 3.1 Create `src/api/signaling.ts` with `connect()`, `send(msg: object)`, and `onMessage(handler)` functions; connect to `ws://localhost:8001/ws/signal?role=gui`

## 4. WebRTC Composable (Answerer)

- [x] 4.1 Create `src/composables/useWebRTC.ts` with `answerCall(offerSdp)` function: create `RTCPeerConnection({ iceServers: [] })`, call `getUserMedia({ audio: true, video: true })`, store `localStream` in store
- [x] 4.2 In `answerCall()`: set offer as remote description, create SDP answer, set as local description, send `{ type: 'answer', data: { sdp } }` via signaling
- [x] 4.3 Handle `onicecandidate`: send `{ type: 'ice-candidate', data: { candidate } }` via signaling
- [x] 4.4 Handle incoming `ice-candidate` messages: add to `RTCPeerConnection`; buffer if remote description not yet set
- [x] 4.5 Handle `ontrack` event: store remote stream in `sessionStore.remoteStream`
- [x] 4.6 Handle `onconnectionstatechange → "connected"`: update `callState` to `'call_active'`
- [x] 4.7 Implement `endCall()`: send `{ type: 'call-end', data: {} }`, close RTCPeerConnection, stop all tracks, set streams to null, update `callState` to `'call_ended'`
- [x] 4.8 Handle `onconnectionstatechange → "failed"/"disconnected"`: set `callState` to `'error'`, set `errorMessage`

## 5. Message Handler Composable

- [x] 5.1 Create `src/composables/useMessageHandler.ts` that registers an `onMessage` handler dispatching by message `type`
- [x] 5.2 Handle `offer`: set `callState = 'ringing'`, buffer SDP for answer flow
- [x] 5.3 Handle `ice-candidate`: relay to WebRTC composable
- [x] 5.4 Handle `call-start`: store caller phone number in session
- [x] 5.5 Handle `call-end`: invoke WebRTC `endCall()` logic
- [x] 5.6 Handle `progress`: update `progressSteps[msg.step] = msg.status`
- [x] 5.7 Handle `business_payload`: populate `customer`, `bill`, `nbo`, `nboFallback`, `nboFallbackReason`; set `callState = 'data_loaded'`
- [x] 5.8 Handle `order_result`: populate `order`, `notification`; set `callState = 'order_complete'`
- [x] 5.9 Handle `error`: set `errorMessage`, `errorStep`, update `progressSteps[step] = 'error'`; set `callState = 'error'`

## 6. Order API

- [x] 6.1 Create `src/api/orderApi.ts` with `placeOrder(customerId, offerId)` function using `fetch` to POST to `http://localhost:8001/order/create`

## 7. UI Components

- [x] 7.1 Create `src/components/IncomingCallBanner.vue`: full-viewport overlay with "Incoming Call" title and "Answer" button; visible only when `callState === 'ringing'`; emits `answer` event
- [x] 7.2 Create `src/components/VideoPanel.vue`: two `<video>` elements — remote (customer, large 16:9) and local (agent, small PIP bottom-right); visible from `call_active` through `order_complete`
- [x] 7.3 Create `src/components/ProgressTracker.vue`: vertical stepper for 7 steps with human-readable labels; status icons: gray circle (pending), animated spinner (running), green check (done), red X (error); connecting lines between steps
- [x] 7.4 Create `src/components/CustomerCard.vue`: displays `name`, `customer_category` (colored badge: gold/silver/bronze), `product_name`
- [x] 7.5 Create `src/components/BillSummaryCard.vue`: displays `bucket_balance` + unit (formatted), `due_date` (formatted), `bill_amount` + unit (formatted), `plan_usage_pct` (colored progress bar + text)
- [x] 7.6 Create `src/components/NboList.vue`: selectable list of `recommendation_item[]` ordered by priority; each row: radio selector, rank, name, truncated description, price; selected row highlighted with blue left border
- [x] 7.7 Create `src/components/NboFallbackNotice.vue`: blue info banner; text from `nboFallbackReason`: "model_inactive" → "AI model inactive — fallback used", "ollama_unavailable" → "NBO engine unavailable — fallback used"; visible only when `nboFallback === true`
- [x] 7.8 Create `src/components/OrderActionBar.vue`: "Place Order" button (right-aligned); disabled until `selectedOfferId` is set; hidden after `order_complete`; shows loading state during `ordering`
- [x] 7.9 Create `src/components/OrderResultCard.vue`: displays order `order_id`, `state` (badge), `order_date` (formatted) + notification `message_id`, `status` (green/red badge), `sent_at` (formatted); amber "Notification Failed" inline warning when `status === 'failed'`
- [x] 7.10 Create `src/components/ErrorBanner.vue`: red banner at top of main content; shows step name + error message; persistent until new call
- [x] 7.11 Create `src/components/CallControls.vue`: "End Call" button (red); visible during `call_active`, `data_loaded`, `ordering`, `order_complete`

## 8. Dashboard Layout

- [x] 8.1 Create `src/views/DashboardView.vue`: CSS Grid two-column layout — left sidebar (320px) with VideoPanel, ProgressTracker, CallControls; main content (flex) with data cards, NBO, order bar
- [x] 8.2 Add header bar: "CC-gui — Agent Dashboard" title + caller phone display area
- [x] 8.3 Wire sidebar: VideoPanel at top, ProgressTracker below, CallControls at bottom
- [x] 8.4 Wire main content: ErrorBanner at top, CustomerCard + BillSummaryCard side-by-side (sub-grid at ≥1200px), NboFallbackNotice, NboList, OrderActionBar, OrderResultCard
- [x] 8.5 Add idle state: centered "Waiting for incoming call" message with pulsing indicator when `callState === 'idle'`
- [x] 8.6 Wire IncomingCallBanner overlay for `ringing` state; on "Answer" click invoke `useWebRTC.answerCall()`
- [x] 8.7 Wire NBO selection to `sessionStore.selectedOfferId`; wire "Place Order" click to `orderApi.placeOrder()` and set `callState = 'ordering'`
- [x] 8.8 Add 10-second auto-reset timer: when `callState` enters `'call_ended'` or `'error'`, start timer that calls `sessionStore.reset()`
- [x] 8.9 Add card fade/slide-in transitions when data panels appear

## 9. Styling & Polish

- [x] 9.1 Apply color palette: primary #1e40af, success #22c55e, error #ef4444, warning #f59e0b, info #3b82f6, background #f3f4f6, surface #fff
- [x] 9.2 Style cards: white background, #e5e7eb border, 12px border-radius, 20px padding, section titles uppercase 0.85rem muted
- [x] 9.3 Style buttons: 24px border-radius pill shape, 600 weight; Answer (green), End Call (red), Place Order (primary blue)
- [x] 9.4 Style NBO list rows: hover background, selected row blue left border + light blue background
- [x] 9.5 Style progress tracker: connecting vertical line, icon sizing 20px, green/gray/red per status
- [x] 9.6 Style badges: customer category (gold/silver/bronze), order state (blue), notification status (green/red)
- [x] 9.7 Add ARIA labels to interactive elements, keyboard navigation for NBO list, focus outlines

## 10. Integration Verification

- [x] 10.1 Verify app starts with `npm run dev` on port 5173
- [x] 10.2 Verify WebSocket connects to CC-server and receives messages
- [x] 10.3 Verify full flow: incoming call → answer → data display → NBO select → place order → result display → end call → reset
