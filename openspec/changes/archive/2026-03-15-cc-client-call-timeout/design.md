## Context

CC-client currently has no timeout on the `dialing`/`ringing` states. Once `startCall()` is invoked, the `RTCPeerConnection` and signaling channel wait indefinitely for an SDP answer. Additionally, after a call ends (any path: user click, server `call-end`, WebRTC failure), the `callState` stays at `'ended'` or `'error'` — there is no automatic return to `'idle'`, so the dial pad stays disabled.

Two closely related problems are fixed together:
1. **Timeout**: auto-abort after 30 s if no `'connected'` state is reached.
2. **Reset to idle**: after any terminal state (`'ended'`, `'error'`, timeout), automatically (or via a button) return to `'idle'` so the user can dial again.

## Goals / Non-Goals

**Goals:**
- Start a 30 s countdown when `startCall()` is called; cancel it if `'connected'` is reached
- On timeout: call `endCall()` internally (teardown PC + streams), set `callState = 'ended'`, set `errorMessage = 'No Answer'`
- After reaching `'ended'` or `'error'`: after a brief pause (2 s) or immediately on user action, reset `callState` back to `'idle'` so the dial pad re-enables
- Show a countdown in `CallStatus` during `dialing`/`ringing` states: "Connecting… (28s)"

**Non-Goals:**
- No configurable timeout
- No retry logic
- No backend changes

## Decisions

### 1. Timeout lives in `useWebRTC.ts`

A `setTimeout` (30 s) is created in `startCall()` and stored in a module-level ref. It is cleared:
- Immediately when `onconnectionstatechange → 'connected'` fires
- When `endCall()` is called by the user before timeout

On fire: call `_endCallInternal(false)` + set `errorMessage = 'No Answer'`.

**Why**: The composable already owns the `RTCPeerConnection` lifecycle; the timeout is part of that lifecycle. No need to put it in the store.

### 2. Countdown displayed via a `setInterval` in `callStore`

`callStore` gains a `timeoutRemaining` ref (number, seconds). `useWebRTC.startCall()` sets it to 30 and starts a 1 s interval that decrements it. Cleared when timeout fires or call connects.

**Why**: `CallStatus` already reads from the store; it just needs one more reactive field.

### 3. Reset to idle: auto-reset after 2 s on `'ended'`/`'error'`

After `callState` transitions to `'ended'` or `'error'`, `useWebRTC` schedules a `setTimeout(2000)` that sets `callState = 'idle'` and clears `errorMessage` and `timeoutRemaining`. The user can also see the "No Answer" / "Call Ended" message during the 2 s window.

**Why**: Avoids requiring a manual "Dismiss" button; keeps UX simple for demo. The 2 s window is enough to see the final status.

## Risks / Trade-offs

- **Race: user clicks "Call" again during 2 s reset window** → Prevented by only resetting to `'idle'` after the delay; the dial pad is disabled in `'ended'`/`'error'` states until the reset fires.
- **`setInterval` drift** → Acceptable for a visual countdown; not safety-critical.
- **2 s feels too short or too long** → Simple constant; can be adjusted if needed.
