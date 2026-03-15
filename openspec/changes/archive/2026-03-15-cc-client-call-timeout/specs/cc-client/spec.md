## MODIFIED Requirements

### Requirement: UI state machine
The system SHALL implement the full call state machine driven by `callStore.callState`:

| State | Trigger | Display |
|---|---|---|
| `idle` | App loads; or 2 s after `ended`/`error` auto-reset | DialPad enabled; "Call" button active; CallStatus hidden |
| `dialing` | User clicks "Call" | "Call" button disabled; CallStatus shows "Connecting… (Ns)" countdown |
| `ringing` | SDP offer sent, waiting for answer | CallStatus shows "Ringing… (Ns)" countdown |
| `connected` | WebRTC `connectionstatechange → "connected"` | Countdown cancelled; CallStatus shows "Call Connected"; VideoStream visible |
| `ended` | User clicks "End Call"; `call-end` WS event; timeout fires | CallStatus shows "Call Ended" or "No Answer"; DialPad disabled; after 2 s auto-reset to `idle` |
| `error` | WebRTC failure or disconnect | CallStatus shows error message; after 2 s auto-reset to `idle` |

#### Scenario: Transition from idle to dialing on Call click
- **WHEN** the user enters a phone number and clicks "Call"
- **THEN** `callState` changes to `"dialing"` and the "Call" button is disabled

#### Scenario: Transition to connected state
- **WHEN** WebRTC `connectionstatechange` fires with `"connected"`
- **THEN** `callState` changes to `"connected"` and `VideoStream` tiles become visible

#### Scenario: Transition to ended on End Call click
- **WHEN** the user clicks "End Call"
- **THEN** `callState` changes to `"ended"`, streams are released, `VideoStream` tiles are hidden

#### Scenario: Auto-reset to idle after ended
- **WHEN** `callState` transitions to `"ended"` or `"error"`
- **THEN** after 2 seconds `callState` automatically resets to `"idle"` and `phoneNumber` is cleared

#### Scenario: Re-dial after call ends
- **WHEN** `callState` has auto-reset to `"idle"` after a previous call
- **THEN** the dial pad is re-enabled and the user can enter a number and click "Call" again

### Requirement: Call timeout
The system SHALL automatically abort a call that has not reached `"connected"` state within 30 seconds of `startCall()` being invoked.

#### Scenario: Timeout fires with no answer
- **WHEN** `startCall()` is called and no WebRTC connection is established within 30 seconds
- **THEN** the system tears down the `RTCPeerConnection`, releases all media streams, sets `callState` to `"ended"`, and sets `errorMessage` to `"No Answer"`

#### Scenario: Timeout cancelled on connection
- **WHEN** the WebRTC connection reaches `"connected"` state before 30 seconds
- **THEN** the timeout timer is cancelled and the call proceeds normally

#### Scenario: Timeout cancelled on manual end
- **WHEN** the user clicks "End Call" before the 30-second timeout fires
- **THEN** the timeout timer is cancelled and `callState` transitions to `"ended"` normally

### Requirement: Countdown display
The system SHALL display a live countdown (in seconds) in `CallStatus` while `callState` is `"dialing"` or `"ringing"`.

#### Scenario: Countdown shown while dialing
- **WHEN** `callState` is `"dialing"` or `"ringing"`
- **THEN** `CallStatus` displays "Connecting… (28s)" (or "Ringing… (22s)") with the remaining seconds decrementing each second

#### Scenario: Countdown hidden when connected
- **WHEN** `callState` transitions to `"connected"`
- **THEN** the countdown is no longer displayed
