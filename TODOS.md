# TODOS

## CC Spec

### WS Message Envelope Discriminator
**Priority:** P1
**What:** Define a `type` field discriminator in the CC spec for WebSocket messages — distinguish A2A business result pushes (e.g. `{ "type": "business_payload", "data": {...} }`) from WebRTC signaling messages (`offer`, `answer`, `ice-candidate`, `call-start`, `call-end`).
**Why:** Without a defined envelope format, implementers will invent their own scheme independently and CC-client, CC-gui, and CC-server will diverge. This is a spec gap that hits during implementation of Step 5 of the business flow.
**How to apply:** Add a "WebSocket Message Envelope" section to `openspec/specs/CC/spec.md` that lists all message `type` values, their payloads, and which direction (CC-server → CC-gui vs CC-client → CC-server) each travels.
**Depends on:** None — spec change only, before implementation starts.

### Loading/Progress State Push During A2A Flow
**Priority:** P1
**What:** Add progress notification messages from CC-server → CC-gui during the 7-step A2A orchestration. Example: `{ "type": "progress", "step": "query_customer", "status": "running" }` after each step starts, and `"status": "done"` when it completes.
**Why:** The Ollama `get_nbo` call takes 2–15 seconds depending on hardware. Without feedback, CC-gui displays a blank dashboard for 10+ seconds during a live demo, which actively undermines the demo's credibility. This is the most impactful UX gap in the current spec.
**How to apply:** Add progress message types to the WS envelope spec (see above TODO), and add Step 3a/3b progress push requirements to CC-server's business flow sequence in `openspec/specs/CC/spec.md`.
**Depends on:** WS Message Envelope Discriminator TODO above.

## CRM Spec

### Fallback Chain for All-Invalid LLM IDs in `get_nbo`
**Priority:** P2
**What:** Explicitly specify what happens when the Ollama LLM returns a JSON array of offering IDs that are all invalid (hallucinated IDs not in the ProductOffering table). After filtering, `recommendation_item[]` would be empty — violating the "SHALL return at least one item" requirement.
**Why:** The current spec handles "Ollama unreachable" (fall back to price-sort) and "LLM returns non-JSON" (fallback), but the hallucinated-ID-all-filtered case is a gap. The fallback chain should be: LLM path → filter invalid IDs → if empty, fall back to price-sort (same as Ollama-unavailable fallback).
**How to apply:** Add one sentence to the `get_nbo` Fallback section in `openspec/specs/CRM/spec.md`: "If all LLM-returned IDs fail the inventory filter, fall back to price-sort as if Ollama were unreachable."
**Depends on:** None.

## Infrastructure

## Testing

### CC-Server End-to-End Orchestration Integration Test
**Priority:** P2
**What:** Add an integration test (`test/test_orchestration.py` in CC-server) that exercises the full 7-step A2A business flow with mocked CRM and Billing responses. Test should cover: happy path, `query_customer` not found (abort), `verify_identity` fails (order blocked), and Ollama fallback path.
**Why:** Individual skill tests (`test_profiling.py`, etc.) don't catch orchestration bugs — e.g. wrong field passed between steps, incorrect conditional branching on `nbo_fallback`, or missing `send_notification` call after order. The orchestration flow is the core demo value and it needs a dedicated integration test.
**How to apply:** Use `pytest` with `respx` (httpx mock) to mock the A2A HTTP calls from CC-server. Each mock returns a valid JSON-RPC 2.0 success response. Assert the correct sequence of calls and the shape of the aggregated payload pushed to CC-gui.
**Depends on:** CC-server implementation complete.

### CC-Server Orchestration Integration Test
**Priority:** P1
**What:** Add `test/test_orchestration.py` to the CC-server directory spec. Required test cases: (1) happy path full 7-step flow, (2) `query_customer` not found → abort, (3) `verify_identity` returns `verified=false` → abort order, (4) `nbo_fallback=true` with `reason="model_inactive"`, (5) `nbo_fallback=true` with `reason="ollama_unavailable"`, (6) CRM unreachable during `query_bill` → error returned.
**Why:** CC-server has no test file in the current spec. The orchestration logic is the core of the demo and the hardest thing to get right. Bugs in step ordering or field mapping won't surface until the full demo is running.
**How to apply:** Use `pytest` + `respx` to mock all `httpx.AsyncClient` calls. Assert correct A2A call sequence, correct field mapping in aggregated payload, and correct conditional branching.
**Depends on:** CC-server initial implementation.

### `test_recommendation.py` — Explicit Edge Case List
**Priority:** P2
**What:** Expand the `test_recommendation.py` test file reference to explicitly require: (1) Ollama returns hallucinated IDs → all filtered → price-sort fallback, (2) Ollama returns prose-wrapped JSON → regex extraction path, (3) Ollama timeout → fallback, (4) customer_id not found → -32001.
**Why:** The current spec says "incl. Ollama fallback" without naming the specific branches. Without explicit test cases these code paths won't be exercised and silent failures will reach the live demo.
**Depends on:** CRM-server initial implementation.

### `/order/create` REST Endpoint Schema
**Priority:** P1
**What:** Add a formal request/response schema for `POST /order/create` to `openspec/specs/CC/spec.md`. Request: `{ customer_id, offer_id }`. Response: `{ order: { order_id, state, order_date }, notification: { message_id, status, sent_at } }` — including the case where `notification.status == "failed"`.
**Why:** This is the key REST endpoint CC-gui calls, but only its existence is documented. CC-gui and CC-server will implement incompatible response shapes without a contract.
**Depends on:** None — spec change only.

### SQLite Table Schemas
**Priority:** P2
**What:** Add a `## Data Model` section to `openspec/specs/CRM/spec.md` and `openspec/specs/Billing/spec.md` listing table names and key columns for each SQLite database: customers, products, recommendations, orders, identities (CRM); bills, usage (Billing).
**Why:** Without a schema spec, `db.py` and `seed.py` implementations will use ad-hoc column names that diverge from Pydantic model field names, causing runtime AttributeErrors.
**Depends on:** None — spec change only.

### Parallelize Steps 2 + 3.5 in CC-Server
**Priority:** P3
**What:** Update CC-server Business Flow Sequence to run steps 2 (`query_bill`) and 3.5 (`get_ai_model_status`) concurrently via `asyncio.gather`, since both depend only on `customer_id` from step 1. Implementation: `bill_data, model_status = await asyncio.gather(query_bill(...), get_ai_model_status(...))`.
**Why:** Sequential execution adds ~500ms+ of unnecessary latency before the Ollama call. For a live demo where Ollama already takes 5–15s, every second of pre-NBO latency makes the demo feel slower.
**Depends on:** CC-server initial implementation (sequential version working first).

## Completed

### ✅ WS Message Envelope Discriminator (CC spec, P1)
Added `### CC-server: WebSocket Message Envelope` section with 9 message types table and full envelope schemas for all `type` values.

### ✅ Loading/Progress State Push During A2A Flow (CC spec, P1)
Added `progress` push annotations to every step in the Business Flow Sequence. Added `progress` message type to the WS envelope section.

### ✅ `/order/create` REST Endpoint Schema (CC spec, P1)
Added `### CC-server: REST Endpoints` section with full request/response schemas for `POST /order/create` (success, identity failure, flow error cases).

### ✅ Parallelize Steps 2 + 3.5 in CC-Server (CC spec, P3)
Added spec note after step 3.5: implementations MAY use `asyncio.gather()` for concurrent execution.

### ✅ Fallback Chain for All-Invalid LLM IDs in `get_nbo` (CRM spec, P2)
Appended hallucinated-ID fallback sentence to the LLM Integration Fallback requirement.

### ✅ SQLite Table Schemas — CRM (CRM spec, P2)
Added `## Data Model` section with 5 tables: `customers`, `product_offerings`, `orders`, `identities`, `ai_models`.

### ✅ SQLite Table Schemas — Billing (Billing spec, P2)
Added `## Data Model` section with `bills` table.

### ✅ Docker Compose — One-Command Startup (project.md, P1)
Added `## Getting Started` section to `openspec/project.md` specifying all 9 compose services, dependency ordering, env vars, Dockerfile templates, and manual startup fallback.
