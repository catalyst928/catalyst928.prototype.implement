## 1. Project Scaffold

- [x] 1.1 Initialize Vite + Vue 3 + TypeScript project at `app/CC/CC-client/` with `npm create vite`
- [x] 1.2 Install dependencies: `pinia`, `vue-router` (optional), and dev deps
- [x] 1.3 Configure `vite.config.ts` to set `server.port: 5172`
- [x] 1.4 Clean up default Vite scaffold: remove `HelloWorld.vue`, default CSS, and App.vue boilerplate; wire `App.vue` to render `DialerView`

## 2. Pinia Store

- [x] 2.1 Create `src/stores/callStore.ts` with state: `callState` (`'idle' | 'dialing' | 'ringing' | 'connected' | 'ended' | 'error'`), `phoneNumber` (string), `localStream` (MediaStream | null), `remoteStream` (MediaStream | null), `errorMessage` (string)

## 3. Signaling Client

- [x] 3.1 Create `src/api/signaling.ts` with `connect()`, `send(msg: object)`, and `onMessage(handler)` functions; connect to `ws://localhost:8001/ws/signal`

## 4. WebRTC Composable

- [x] 4.1 Create `src/composables/useWebRTC.ts` with `startCall()` function: calls `getUserMedia`, creates `RTCPeerConnection({ iceServers: [] })`, stores `localStream` in store
- [x] 4.2 In `startCall()`: create SDP offer, set as local description, send `{ type: 'offer', data: { sdp } }` via signaling client; update `callState` to `'dialing'`
- [x] 4.3 Handle `onicecandidate`: send `{ type: 'ice-candidate', data: { candidate } }` via signaling client
- [x] 4.4 Handle incoming `answer` message: call `setRemoteDescription`; update `callState` to `'ringing'`
- [x] 4.5 Buffer incoming `ice-candidate` messages before `setRemoteDescription` is set; apply them after answer is processed
- [x] 4.6 Handle `ontrack` event: store remote stream in `callStore.remoteStream`
- [x] 4.7 Handle `onconnectionstatechange → "connected"`: update `callState` to `'connected'`; send `{ type: 'call-start', data: { phone: callStore.phoneNumber } }` via signaling
- [x] 4.8 Implement `endCall()`: send `{ type: 'call-end', data: {} }` via signaling, close `RTCPeerConnection`, stop all tracks on local/remote streams, set streams to null, update `callState` to `'ended'`
- [x] 4.9 Handle incoming `call-end` message: call `endCall()` logic (transition to `'ended'` and release streams)
- [x] 4.10 Handle `onconnectionstatechange → "failed"` or `"disconnected"`: update `callState` to `'error'`, set `errorMessage`

## 5. UI Components

- [x] 5.1 Create `src/components/CallStatus.vue`: show state label + colored indicator dot; hidden when `callState === 'idle'`
- [x] 5.2 Create `src/components/DialPad.vue`: 3×4 numeric grid (1–9, *, 0, #), phone number text input above grid, "Call" and "End Call" buttons below; emit call/end events; disable "Call" when not idle
- [x] 5.3 Create `src/components/VideoStream.vue`: two `<video>` elements — remote (larger, labeled "Agent") and local (muted, smaller, labeled "You", picture-in-picture); visible only when `callState === 'connected'`
- [x] 5.4 Create `src/views/DialerView.vue`: mobile-first portrait single-column layout; header "CC-client — Customer Caller"; compose `VideoStream`, `DialPad`, `CallStatus`; wire call/end button events to `useWebRTC` composable
- [x] 5.5 Add basic CSS: full-viewport column layout, mobile-first (~375 px), video PiP positioning, indicator dot color per state (green=connected, red=error, gray=idle/ended)
