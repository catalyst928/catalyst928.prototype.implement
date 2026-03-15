# CC Bugfix TODO

## Critical

- [x] 1. WebSocket slot overwrite — old connection's disconnect handler nulls the new active slot (`CC-server/ws_signal.py`) — **Fixed:** only clear slot if `_connections[role] is websocket`
- [x] 2. CC-client missing `?role=client` query param — auto-assigns as `gui` if it connects first (`CC-client/src/api/signaling.ts`) — **Fixed:** added `?role=client` to WS URL

## High

- [x] 3. `resp.json()` called outside `async with` context manager (`CC-server/a2a_client.py`) — **Fixed:** moved inside `async with` block
- [x] 4. `call-start` from gui silently dropped; unknown message types silently swallowed (`CC-server/ws_signal.py`) — **Fixed:** added `else` clause with warning log
- [x] 5. No WebSocket reconnection logic in CC-gui or CC-client (both `signaling.ts`) — **Fixed:** added exponential backoff reconnection (1s–10s) + `onerror` handler
- [ ] 6. `call-start` timing — sent after WebRTC connected, races with A2A flow (`CC-client/src/composables/useWebRTC.ts:47`) — **Won't fix:** per CC spec line 232, `call-start` is sent on `connected` state; race is acceptable on LAN

## Medium

- [x] 7. `useMessageHandler` stacks duplicate handlers on HMR re-mount (`CC-gui/src/composables/useMessageHandler.ts`) — **Fixed:** added `onUnmounted(unsubscribe)` cleanup
- [x] 8. Same handler stacking issue in CC-client (`CC-client/src/composables/useWebRTC.ts:77`) — **Fixed:** added `onUnmounted(unsubscribe)` cleanup
- [x] 9. Duplicate 10s reset timers — both DashboardView and useWebRTC schedule reset (`CC-gui/src/views/DashboardView.vue` + `CC-gui/src/composables/useWebRTC.ts`) — **Fixed:** removed `scheduleReset()` from useWebRTC; DashboardView watcher is the single source
- [x] 10. `POST /order/create` returns HTTP 200 for errors instead of 4xx/5xx (`CC-server/order.py`) — **Fixed:** returns 502 for upstream errors, 403 for identity failure
- [x] 11. Communication agent called via HTTP loopback to self (`CC-server/order.py:9`) — **Fixed:** call `send_notification()` directly instead of HTTP round-trip

## Low

- [x] 12. Hardcoded JSON-RPC `"id": 1` on all A2A requests (`CC-server/a2a_client.py:22`) — **Fixed:** use `itertools.count(1)` for unique IDs
- [x] 13. `asyncio.create_task` without error handling (`CC-server/ws_signal.py`) — **Fixed:** added `add_done_callback` for error logging
- [x] 14. `formatPhone` only handles 11-digit numbers (`CC-gui/src/views/DashboardView.vue:175`) — **Fixed:** strips non-digits, handles 10/11/12-digit formats
- [x] 15. No `onerror` handler on WebSocket (both `signaling.ts`) — **Fixed:** added in bug 5 reconnection fix
