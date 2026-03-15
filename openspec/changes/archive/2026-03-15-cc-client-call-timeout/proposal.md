## Why

After clicking "Call", CC-client enters `dialing`/`ringing` state indefinitely if CC-gui is not connected or does not answer. There is no automatic recovery, leaving the user stuck with no way to retry without refreshing the page. A 30-second call timeout and a clean reset-to-idle flow are needed.

## What Changes

- Add a 30-second timeout starting when "Call" is clicked; if no WebRTC connection is established within 30 s, automatically abort and show "No Answer"
- On timeout, cleanly tear down the `RTCPeerConnection` and release media streams
- After timeout OR after clicking "End Call" OR after receiving `call-end` from server, transition back to `idle` state so the user can immediately dial again
- Display a countdown (or at minimum a timeout notice) in `CallStatus` while waiting

## Capabilities

### New Capabilities

<!-- None — this is a pure behavior enhancement to the existing cc-client capability -->

### Modified Capabilities

- `cc-client`: Add `call-timeout` state/behavior — call auto-aborts after 30 s with no answer; after any call termination (timeout, end, remote hang-up) the UI resets to `idle` to allow re-dialing

## Impact

- **Modified files**: `src/composables/useWebRTC.ts` (timeout logic), `src/stores/callStore.ts` (optional `timeoutSeconds` counter), `src/components/CallStatus.vue` (display countdown or "No Answer" message), `src/views/DialerView.vue` (reset to idle after ended/timeout)
- **No backend changes** — CC-server, CC-gui, CRM-server, Billing-server unaffected
- **No new dependencies**

## Non-goals

- No configurable timeout value in UI (hardcoded 30 s)
- No retry-with-backoff logic
- No changes to CC-server or CC-gui
