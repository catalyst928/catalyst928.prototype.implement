## Why

CC-gui is the agent operator dashboard required to complete the end-to-end CC demo flow. Without it, there is no WebRTC receiver to accept customer calls and no dashboard for the agent to view customer data, select NBO recommendations, or place orders. CC-server and CC-client are already implemented — CC-gui is the remaining piece.

## What Changes

- Create `app/CC/CC-gui/` as a new Vue 3 + Vite + TypeScript project served on port 5173
- Implement WebSocket signaling client connecting to `ws://localhost:8001/ws/signal`
- Implement WebRTC receiver (answerer): accept SDP offer, send answer, relay ICE candidates
- Implement agent dashboard with customer card, bill summary, NBO list, order actions, and notification status
- Implement real-time A2A progress tracker (vertical stepper for 7 flow steps)
- Implement incoming call banner with explicit "Answer" button (no auto-answer)
- Implement order placement via `POST /order/create { customer_id, offer_id }`
- Display error/warning banners for flow errors, identity failures, notification failures, and NBO fallback notices

## Capabilities

### New Capabilities
- `cc-gui`: Agent operator dashboard — WebRTC receiver, A2A progress tracker, customer/bill/NBO display, order placement, notification status

### Modified Capabilities
<!-- None — CC-server and CC-client already handle their sides; no spec-level requirement changes -->

## Impact

- **New code**: `app/CC/CC-gui/` (Vue 3 project: 12 components, 2 composables, 1 Pinia store, signaling client, order API)
- **CC-server**: No changes required; WebSocket relay and REST endpoints already implemented
- **CC-client**: No changes required; already sends offer/ICE/call-start
- **Port 5173** must be free (reserved in port allocation)
- **Dependencies**: Vue 3, Vite, Pinia, TypeScript — no new backend dependencies
- **TMForum alignment**: Dashboard displays TMF-aligned field names (TMF629, TMF637, TMF677/678, TMF701, TMF622, TMF681)

## Non-goals

- No direct connections to CRM-server or Billing-server (all data via CC-server)
- No STUN/TURN server configuration (direct LAN WebRTC only)
- No authentication or session management
- No mobile/tablet responsive layout (desktop-first operator tool)
- No mute/unmute or video quality controls in v1
