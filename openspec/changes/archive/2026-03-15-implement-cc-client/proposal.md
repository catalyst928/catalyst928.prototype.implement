## Why

CC-client is the missing customer-side Vue 3 GUI required to complete the end-to-end CC demo flow. Without it, there is no WebRTC caller to initiate the signaling handshake and trigger the A2A business flow on CC-server. This must be built to enable full demonstration of the call center scenario.

## What Changes

- Create `app/CC/CC-client/` as a new Vue 3 + Vite project served on port 5172
- Implement a dial pad UI allowing the customer to enter a phone number and initiate a WebRTC call
- Implement WebSocket signaling client connecting to `ws://localhost:8001/ws/signal`
- Implement `RTCPeerConnection` lifecycle: create SDP offer, handle answer, relay ICE candidates
- Send `call-start { phone }` message to CC-server upon WebRTC connection establishment
- Display live call state (idle → dialing → ringing → connected → ended / error)
- Show local and remote video streams in connected state (picture-in-picture layout)

## Capabilities

### New Capabilities
- `cc-client`: Customer-side WebRTC caller GUI; single-page dialer with WebSocket signaling, WebRTC P2P video, and call state management

### Modified Capabilities
<!-- None — CC-server signaling and CC-gui already handle their sides; no spec-level requirement changes -->

## Impact

- **New code**: `app/CC/CC-client/` (Vue 3 project: components, composables, store, signaling client)
- **CC-server**: No changes required; signaling relay already defined in spec
- **CC-gui**: No changes required; already handles `offer`, `answer`, `ice-candidate`, `call-start`, `call-end`
- **Port 5172** must be free (reserved in port allocation)
- **Dependencies**: Vue 3, Vite, Pinia, TypeScript — no new backend dependencies

## Non-goals

- CC-client will make no REST HTTP calls; all interaction is WebSocket-only
- No STUN/TURN configuration (direct LAN WebRTC only)
- No authentication or session management
- No integration with CRM-server or Billing-server
- Desktop/tablet responsive layout not required (mobile-first portrait only)
