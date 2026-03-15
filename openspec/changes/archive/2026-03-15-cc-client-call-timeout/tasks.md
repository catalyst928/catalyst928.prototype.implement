## 1. Store — add timeoutRemaining

- [x] 1.1 Add `timeoutRemaining` ref (number) to `callStore.ts`; initial value `0`

## 2. WebRTC composable — timeout logic

- [x] 2.1 In `startCall()`: start a `setInterval` (1 s) that decrements `callStore.timeoutRemaining`; store the interval ID in a module-level variable; set `timeoutRemaining` to `30` before starting
- [x] 2.2 In `startCall()`: start a `setTimeout` (30 000 ms) that calls `_endCallInternal(false)` and sets `callStore.errorMessage = 'No Answer'`; store the timer ID in a module-level variable
- [x] 2.3 Create a `clearTimers()` helper that clears both the countdown interval and the 30 s timeout; call it in: `onconnectionstatechange → 'connected'`, `endCall()`, and `_endCallInternal()`
- [x] 2.4 In `_endCallInternal()`: after setting `callStore.callState = 'ended'`, schedule a `setTimeout(2000)` that resets `callStore.callState = 'idle'`, clears `callStore.errorMessage`, clears `callStore.phoneNumber`, and sets `callStore.timeoutRemaining = 0`

## 3. CallStatus — countdown display

- [x] 3.1 Update `CallStatus.vue` status label logic: when `callState` is `'dialing'` show `"Connecting… (${timeoutRemaining}s)"` and when `'ringing'` show `"Ringing… (${timeoutRemaining}s)"`; read `timeoutRemaining` from store

## 4. DialPad — disable during ended/error

- [x] 4.1 Update `DialPad.vue`: ensure "Call" button is disabled when `callState` is `'ended'` or `'error'` (in addition to existing non-idle check) so user cannot re-dial during the 2 s reset window
