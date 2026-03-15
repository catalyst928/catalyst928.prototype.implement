## Context

CC-client is a new Vue 3 single-page application that acts as the customer-side WebRTC caller in the CC demo. It scaffolds from scratch under `app/CC/CC-client/`. The existing CC-server WebSocket signaling relay at `ws://localhost:8001/ws/signal` is already defined and implemented; CC-client simply needs to connect to it and participate in the signaling exchange. CC-gui already handles the agent side. This design focuses only on the CC-client frontend — no backend changes are required.

The project follows the established Vue 3 pattern used by CC-gui and CRM-gui: `<script setup lang="ts">`, Pinia store, Vite build tool, and component-based structure under `src/`.

## Goals / Non-Goals

**Goals:**
- Scaffold a Vite + Vue 3 + TypeScript project at `app/CC/CC-client/` served on port 5172
- Implement WebSocket signaling client (`src/api/signaling.ts`) connecting to `ws://localhost:8001/ws/signal`
- Implement `RTCPeerConnection` lifecycle composable (`src/composables/useWebRTC.ts`): create offer, set remote answer, relay ICE candidates, capture `getUserMedia` local stream, expose remote stream
- Implement Pinia call store (`src/stores/callStore.ts`): `callState`, `phoneNumber`, `localStream`, `remoteStream`
- Implement UI components: `DialPad.vue`, `CallStatus.vue`, `VideoStream.vue`, `DialerView.vue`
- Full UI state machine: `idle → dialing → ringing → connected → ended / error`
- Send `call-start { phone }` after WebRTC `connectionstatechange → "connected"`

**Non-Goals:**
- No REST HTTP calls from CC-client to CC-server or any other server
- No STUN/TURN server configuration
- No authentication
- No desktop responsive breakpoints
- No modifications to CC-server, CC-gui, or any backend code

## Decisions

### 1. WebSocket client as a plain TypeScript module (not a Vue plugin)

`src/api/signaling.ts` exports a singleton-like object with `connect()`, `send()`, and `onMessage()` functions. The composable `useWebRTC.ts` calls it directly.

**Why**: Simple, testable, matches the pattern in CC-gui. No need for a Vue plugin or provide/inject indirection for a single global socket.

**Alternative considered**: Pinia store owns the WebSocket — rejected because mixing transport state with UI state makes the store harder to reason about.

### 2. `useWebRTC.ts` composable owns `RTCPeerConnection` lifecycle

The composable creates and manages the `RTCPeerConnection` instance. It exposes `startCall()`, `endCall()`, and reactive `connectionState`. It reads/writes `callStore` for streams and state.

**Why**: Separates WebRTC logic from component code. `DialerView.vue` only calls `startCall()` and `endCall()` — it does not touch the `RTCPeerConnection` API directly.

### 3. `call-start` sent after `connectionstatechange → "connected"`

Per spec: "On call connected, the client SHALL send `call-start` with `{ phone }` to CC-server." The composable listens to `pc.onconnectionstatechange` and sends `call-start` when state transitions to `"connected"`.

**Why**: This is the correct ordering — ensure P2P is established before triggering the A2A business flow.

### 4. `iceServers: []` — no STUN/TURN

Per spec: "The client SHALL initiate a RTCPeerConnection with `iceServers: []`." Direct LAN connection assumed for demo purposes.

### 5. Vite config sets `server.port: 5172`

Port assigned in the project port allocation table. Set in `vite.config.ts` to avoid conflicts.

## Risks / Trade-offs

- **`getUserMedia` requires HTTPS or localhost** → No risk in demo (always runs on localhost). If deployed remotely, would need TLS.
- **WebSocket reconnection not implemented** → Demo scenario; if signal drops after offer, user must refresh. Acceptable for demo.
- **ICE candidate race** → Candidates may arrive before `setRemoteDescription` completes. Mitigation: buffer ICE candidates received before answer is set and add them after `setRemoteDescription` resolves.
- **Single peer connection instance** → Only supports one active call at a time. Correct for this use case.
