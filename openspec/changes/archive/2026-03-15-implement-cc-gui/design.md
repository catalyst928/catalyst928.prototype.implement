## Context

CC-server (FastAPI, port 8001) and CC-client (Vue 3, port 5172) are already implemented. CC-gui is the missing agent dashboard that completes the end-to-end demo. The full CC-gui spec exists at `openspec/specs/CC/cc-gui/spec.md` defining all components, state machine, layout, and interaction flows.

CC-gui is a pure frontend — no backend changes needed. It connects to CC-server via WebSocket (signaling + business data) and one REST endpoint (`POST /order/create`). No cross-subsystem imports introduced. No A2A skill schemas change.

## Goals / Non-Goals

**Goals:**
- Implement a desktop-first agent dashboard at `app/CC/CC-gui/` served on port 5173
- Reuse CC-client's established Vue 3 + Vite + Pinia + TypeScript patterns
- Handle all WebSocket message types defined in CC spec (progress, business_payload, order_result, error)
- Implement WebRTC answerer flow (inverse of CC-client's offerer pattern)
- Deliver polished UI with real-time progress tracking, data cards, and order workflow

**Non-Goals:**
- No backend changes to CC-server, CRM-server, or Billing-server
- No Ollama integration (CC-gui doesn't call LLM — NBO comes via CC-server)
- No mobile/tablet responsive layout
- No authentication, mute controls, or video quality settings

## Decisions

### 1. Reuse CC-client's signaling module pattern
**Decision:** Copy the `signaling.ts` pattern (connect/send/onMessage singleton) from CC-client.
**Why:** Proven pattern already working in CC-client → CC-server communication. Identical WebSocket protocol.
**Alternative considered:** Using a WebSocket library (socket.io). Rejected — CC-server uses raw WebSocket, adding socket.io would require server changes.

### 2. Separate message handler composable
**Decision:** Create `useMessageHandler.ts` to dispatch WS messages to store, separate from WebRTC composable.
**Why:** CC-gui receives many more message types than CC-client (progress, business_payload, order_result, error). Mixing dispatch logic into the WebRTC composable would bloat it. Separation of concerns keeps both composables focused.
**Alternative considered:** Handle all messages in a single composable. Rejected — too many responsibilities.

### 3. Sidebar + main two-column CSS Grid layout
**Decision:** 320px fixed left sidebar (video + progress + call controls) with flex main content area.
**Why:** Operator dashboards need persistent context (video, progress) alongside scrollable data. Two-column grid gives the agent a stable reference point in the sidebar while reviewing data in the main area.
**Alternative considered:** Three-column layout (video | data | NBO). Rejected — over-segments the content and requires wider viewport.

### 4. Single Pinia store for all session state
**Decision:** One `sessionStore` with all fields (callState, customer, bill, nbo, order, notification, progressSteps, error).
**Why:** All state is scoped to a single call session and resets together. Multiple stores would add complexity with no benefit since there's no independent lifecycle.
**Alternative considered:** Separate stores for call state vs business data. Rejected — they're tightly coupled (callState drives what data is visible).

### 5. Order placement via REST with WS-driven UI updates
**Decision:** Send `POST /order/create` via fetch, but update UI based on WebSocket `progress` and `order_result` messages rather than the REST response.
**Why:** CC-server already pushes progress and results via WebSocket to CC-gui. The REST response is redundant for UI updates. Using WS keeps the UI consistent with the progress tracker flow.
**Alternative considered:** Use REST response to update UI directly. Rejected — would bypass the progress tracker and create inconsistent update paths.

### 6. No Element Plus — scoped CSS only
**Decision:** Use custom scoped CSS matching CC-client's styling approach instead of Element Plus.
**Why:** CC-client uses custom scoped CSS. Mixing Element Plus components into CC-gui while CC-client uses raw CSS would create visual inconsistency. The component count (12) is small enough to style manually.
**Alternative considered:** Element Plus for cards, buttons, steppers. Rejected — visual mismatch with CC-client, additional dependency for limited benefit.

## Risks / Trade-offs

- **[WebRTC answerer timing]** CC-gui must be connected to WS before CC-client sends an offer. → Mitigation: CC-gui connects on app load; if WS disconnects, show reconnection banner.
- **[Single WS slot per role]** CC-server only tracks one gui connection. If CC-gui refreshes, the old slot may not be cleaned up. → Mitigation: CC-server's `WebSocketDisconnect` handler already clears the slot.
- **[No fallback for WS messages]** If CC-gui misses a `business_payload` (e.g., WS reconnect during flow), there's no way to re-request it. → Mitigation: Acceptable for demo — agent restarts the call. Not a production concern.
- **[10s auto-reset]** After call ends, session resets in 10 seconds. Agent may want more review time. → Mitigation: 10s is configurable in the store; can be extended if needed.
