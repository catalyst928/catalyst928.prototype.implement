## ADDED Requirements

### Requirement: Project scaffold
The system SHALL be a Vue 3 + Vite + TypeScript project at `app/CC/CC-client/` with Pinia for state management, served on port 5172 via `vite.config.ts`.

#### Scenario: Dev server starts on correct port
- **WHEN** `npm run dev` is executed in `app/CC/CC-client/`
- **THEN** the Vite dev server binds to port 5172

### Requirement: WebSocket signaling client
The system SHALL implement `src/api/signaling.ts` as a WebSocket client that connects to `ws://localhost:8001/ws/signal` and exposes `connect()`, `send(msg)`, and `onMessage(handler)` functions.

#### Scenario: Connect to CC-server signaling
- **WHEN** `connect()` is called
- **THEN** a WebSocket connection is established to `ws://localhost:8001/ws/signal`

#### Scenario: Send signaling message
- **WHEN** `send({ type: 'offer', data: { sdp: '...' } })` is called
- **THEN** the JSON-serialized message is sent over the WebSocket

#### Scenario: Receive signaling message
- **WHEN** a message arrives over the WebSocket
- **THEN** all registered `onMessage` handlers are called with the parsed JSON object

### Requirement: WebRTC peer connection lifecycle
The system SHALL implement `src/composables/useWebRTC.ts` that manages the `RTCPeerConnection` with `iceServers: []`, creates an SDP offer, handles the remote answer, relays ICE candidates, and captures local media via `getUserMedia`.

#### Scenario: Create and send offer
- **WHEN** `startCall()` is called
- **THEN** the composable calls `getUserMedia`, creates an `RTCPeerConnection` with `iceServers: []`, creates an SDP offer, sets it as local description, and sends `{ type: 'offer', data: { sdp } }` via the signaling client

#### Scenario: Handle SDP answer
- **WHEN** a `{ type: 'answer', data: { sdp } }` message is received via the signaling client
- **THEN** `setRemoteDescription` is called with the answer SDP

#### Scenario: Relay ICE candidates
- **WHEN** the local `RTCPeerConnection` fires an `icecandidate` event
- **THEN** the composable sends `{ type: 'ice-candidate', data: { candidate } }` via the signaling client

#### Scenario: Apply remote ICE candidate
- **WHEN** a `{ type: 'ice-candidate', data: { candidate } }` message is received
- **THEN** `addIceCandidate` is called on the `RTCPeerConnection`

#### Scenario: Buffer ICE candidates before answer
- **WHEN** ICE candidates are received before `setRemoteDescription` has been called
- **THEN** they are buffered and applied after `setRemoteDescription` resolves

#### Scenario: Expose remote stream
- **WHEN** the `RTCPeerConnection` fires an `ontrack` event
- **THEN** the remote stream is stored in `callStore.remoteStream`

### Requirement: Send call-start after connection
The system SHALL send `{ type: 'call-start', data: { phone } }` to CC-server via WebSocket when the `RTCPeerConnection.connectionState` transitions to `"connected"`.

#### Scenario: call-start sent on WebRTC connected
- **WHEN** `RTCPeerConnection.onconnectionstatechange` fires with state `"connected"`
- **THEN** `{ type: 'call-start', data: { phone: <phoneNumber from store> } }` is sent via the signaling client

### Requirement: Call state store
The system SHALL implement `src/stores/callStore.ts` as a Pinia store with state fields: `callState` (enum: `idle | dialing | ringing | connected | ended | error`), `phoneNumber` (string), `localStream` (MediaStream | null), `remoteStream` (MediaStream | null).

#### Scenario: Initial state is idle
- **WHEN** the app loads
- **THEN** `callState` is `"idle"`, `phoneNumber` is `""`, both streams are `null`

### Requirement: UI state machine
The system SHALL implement the full call state machine in `DialerView.vue` driven by `callStore.callState`:

| State | Display |
|---|---|
| `idle` | DialPad enabled; "Call" button active; CallStatus hidden |
| `dialing` | "Call" button disabled; CallStatus shows "Connecting…" |
| `ringing` | CallStatus shows "Ringing…" |
| `connected` | CallStatus shows "Call Connected"; VideoStream tiles visible |
| `ended` | CallStatus shows "Call Ended"; DialPad re-enabled; VideoStream hidden; streams released |
| `error` | CallStatus shows error message |

#### Scenario: Transition from idle to dialing on Call click
- **WHEN** the user enters a phone number and clicks "Call"
- **THEN** `callState` changes to `"dialing"` and the "Call" button is disabled

#### Scenario: Transition to connected state
- **WHEN** WebRTC `connectionstatechange` fires with `"connected"`
- **THEN** `callState` changes to `"connected"` and `VideoStream` tiles become visible

#### Scenario: Transition to ended on End Call click
- **WHEN** the user clicks "End Call"
- **THEN** `callState` changes to `"ended"`, streams are released, `VideoStream` tiles are hidden

### Requirement: DialPad component
The system SHALL implement `src/components/DialPad.vue` with a 3×4 numeric keypad (digits 0–9, `*`, `#`), a phone number text input above the grid, and "Call" / "End Call" buttons below.

#### Scenario: Phone number input updated by keypad
- **WHEN** the user taps a digit key
- **THEN** the digit is appended to the phone number input

#### Scenario: Call button initiates call
- **WHEN** the user clicks "Call" with a non-empty phone number
- **THEN** `useWebRTC.startCall()` is invoked

#### Scenario: End Call button terminates call
- **WHEN** the user clicks "End Call" during an active call
- **THEN** `useWebRTC.endCall()` is invoked and `call-end` is sent to CC-server

### Requirement: CallStatus component
The system SHALL implement `src/components/CallStatus.vue` displaying the current call state label and a colored indicator dot.

#### Scenario: Status label matches state
- **WHEN** `callState` is `"connected"`
- **THEN** the component displays "Call Connected" with a green indicator dot

#### Scenario: Status hidden in idle
- **WHEN** `callState` is `"idle"`
- **THEN** the status section is not visible

### Requirement: VideoStream component
The system SHALL implement `src/components/VideoStream.vue` with two `<video>` elements: local stream (muted, labeled "You", smaller tile) and remote stream (labeled "Agent", larger tile). Both are hidden unless `callState` is `"connected"`.

#### Scenario: Video tiles visible in connected state
- **WHEN** `callState` is `"connected"` and both streams are set
- **THEN** both video tiles render with their respective streams

#### Scenario: Video tiles hidden when not connected
- **WHEN** `callState` is not `"connected"`
- **THEN** the VideoStream section is not rendered in the DOM

### Requirement: Layout — DialerView
The system SHALL implement `src/views/DialerView.vue` as a mobile-first portrait single-column layout (~375–430 px) with sections top-to-bottom: header bar, VideoStream section, DialPad section, CallStatus section.

#### Scenario: Header displays app title
- **WHEN** the page loads
- **THEN** the header bar shows "CC-client — Customer Caller"

### Requirement: Handle call-end from server
The system SHALL transition to `"ended"` state and release streams when a `{ type: 'call-end' }` message is received via WebSocket.

#### Scenario: Remote call-end terminates call
- **WHEN** a `{ type: 'call-end' }` message arrives from CC-server
- **THEN** `callState` transitions to `"ended"` and media streams are released
