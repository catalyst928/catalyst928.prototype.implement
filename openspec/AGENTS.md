# AGENTS.md — AI Coding Assistant Instructions

> This file guides AI coding assistants (Claude Code, Cursor, Copilot, etc.) on how to work within this project using OpenSpec spec-driven development.

---

## Project Context

This is an **A2A Protocol Demo** project demonstrating end-to-end business flow across three subsystems:
- **CC** (Call Center) — Orchestrator, initiates the flow
- **CRM** — Customer info, NBO recommendation, order creation
- **Billing** — Bill and account balance query

Always read `openspec/project.md` first to understand the full system before making any changes.

---

## OpenSpec Instructions

<openspec-instructions>

### When to open AGENTS.md
Always open this file when the request:
- Mentions planning, proposals, spec, or change
- Introduces new A2A Skills, new subsystem interactions, or new business flow steps
- Involves cross-subsystem communication patterns
- Sounds ambiguous and you need the authoritative spec before coding

### How to Create a Change Proposal
Run `/opsx:propose "<your feature description>"` to generate:
- `openspec/changes/<change-name>/proposal.md` — what & why
- `openspec/changes/<change-name>/design.md` — technical approach
- `openspec/changes/<change-name>/tasks.md` — implementation checklist
- `openspec/changes/<change-name>/specs/<domain>/spec.md` — delta spec

Review and refine ALL documents before running `/opsx:apply`.

### How to Apply a Change
Run `/opsx:apply` — AI implements tasks from `tasks.md` one by one.

### How to Archive a Completed Change
Run `/opsx:archive` — delta specs merge into `openspec/specs/`, change moves to archive.

</openspec-instructions>

---

## Critical Architecture Rules

> ⚠️ These rules MUST be followed in every code generation. Never violate them.

### Rule 1: CC-server is the ONLY Orchestrator
- CC-server calls CRM-server and Billing-server via A2A
- CRM-server and Billing-server MUST NOT call each other directly
- All business flow changes go through CC-server's orchestration logic

### Rule 2: Agent Card First
- Before implementing any new A2A Skill, define its entry in `/.well-known/agent.json`
- Agent Card must include: `name`, `description`, `skills[].inputSchema`, `skills[].outputSchema`
- No Skill implementation without a registered Agent Card entry

### Rule 3: Subsystem Isolation
- Each subsystem (CC / CRM / Billing) is fully independent
- No Python cross-imports between subsystems
- Shared data contracts are defined only via A2A JSON Schema in Agent Cards

### Rule 4: GUI connects only to same-subsystem server
- CC-gui → CC-server only (port 8001)
- CRM-gui → CRM-server only (port 8002)
- Billing-gui → Billing-server only (port 8003)
- No GUI component calls a server of a different subsystem

### Rule 5: Use A2A SDK — do NOT reimplement protocol
- Use `a2a-python` SDK for all A2A server and client logic (Agent Card serving, skill registration, JSON-RPC dispatch, A2A client calls)
- Do NOT manually implement JSON-RPC envelope parsing, Agent Card endpoints, or A2A request routing
- Use `httpx.AsyncClient` only for non-A2A calls (e.g., Ollama)
- Never use synchronous `requests` library
- All A2A handler functions must be `async def`

### Rule 6: Use uv for Python package management
- Use `uv add` to manage dependencies, `uv sync` to install, `uv run` to execute
- Use `uvx` for running CLI tools
- Never use `pip install` directly (except `pip install uv` in Dockerfiles)
- Each Python service has a `pyproject.toml` managed by `uv`

---

## A2A Skill Implementation Checklist

When adding or modifying a Skill, verify ALL of the following:

- [ ] Skill registered via `a2a-python` SDK with full schema (Agent Card, input/output schemas)
- [ ] Pydantic `InputModel` and `OutputModel` defined in `models.py`
- [ ] Handler is `async def` and returns `OutputModel`
- [ ] Skill registered using `a2a-python` SDK's skill registration mechanism (do NOT manually implement JSON-RPC dispatch)
- [ ] CORS enabled on the FastAPI app
- [ ] Error handling uses `a2a-python` SDK error utilities (do NOT manually construct JSON-RPC error objects)
- [ ] Seed data updated in `seed.py` if new domain data is needed
- [ ] Field names and status enumerations align with the mapped TMF Open API (see TMForum Alignment table in `project.md`)
- [ ] Dependencies managed via `uv add` in `pyproject.toml` (including `a2a-python`)

---

## Directory Conventions

### Backend (FastAPI + a2a-python SDK) — CRM-server (multi-agent, single process)
```
CRM-server/
├── src/
│   ├── main.py                        # FastAPI app entry, CORS, registers agents via a2a-python SDK
│   ├── agents/
│   │   ├── profiling/                 # Profiling Agent
│   │   │   ├── agent.py               # Agent definition using a2a-python SDK (card + skill registration)
│   │   │   ├── models.py              # Pydantic models for query_customer
│   │   │   └── skills/
│   │   │       └── query_customer.py
│   │   ├── recommendation/            # Recommendation Agent
│   │   │   ├── agent.py               # Agent definition using a2a-python SDK
│   │   │   ├── models.py              # Pydantic models for get_nbo
│   │   │   └── skills/
│   │   │       └── get_nbo.py
│   │   ├── order/                     # Order Agent
│   │   │   ├── agent.py               # Agent definition using a2a-python SDK
│   │   │   ├── models.py              # Pydantic models for create_order
│   │   │   └── skills/
│   │   │       └── create_order.py
│   │   └── ai_management/             # AI Management Agent
│   │       ├── agent.py               # Agent definition using a2a-python SDK
│   │       ├── models.py              # Pydantic models for get_ai_model_status
│   │       └── skills/
│   │           └── get_ai_model_status.py
│   ├── db.py                          # Shared SQLite connection & table init
│   └── seed.py                        # Demo data seeding (all CRM data)
├── test/
│   ├── test_profiling.py              # Tests for query_customer and verify_identity skills
│   ├── test_recommendation.py         # Tests for get_nbo skill (incl. Ollama fallback)
│   ├── test_order.py                  # Tests for create_order skill
│   └── test_ai_management.py          # Tests for get_ai_model_status skill
└── pyproject.toml                     # Managed by uv; includes a2a-python dependency

# Agents registered in src/main.py using a2a-python SDK:
#   SDK handles Agent Card serving (GET /.well-known/agent.json) and
#   A2A endpoint (POST /a2a) with JSON-RPC dispatch automatically
```

### Backend (FastAPI + a2a-python SDK) — Billing-server (single agent, single process)
```
Billing-server/
├── src/
│   ├── main.py                        # FastAPI app entry, CORS, registers Usage Agent via a2a-python SDK
│   ├── agents/
│   │   └── usage/                     # Usage Agent
│   │       ├── agent.py               # Agent definition using a2a-python SDK (card + skill registration)
│   │       ├── models.py              # Pydantic models for query_bill
│   │       └── skills/
│   │           └── query_bill.py
│   ├── db.py                          # SQLite connection & table init
│   └── seed.py                        # Demo data seeding (billing data)
├── test/
│   └── test_usage.py                  # Tests for query_bill skill
└── pyproject.toml                     # Managed by uv; includes a2a-python dependency

# Agent registered in src/main.py using a2a-python SDK:
#   SDK handles Agent Card serving and A2A endpoint automatically
```

### Frontend (Vue 3) — per subsystem GUI
```
<Subsystem>-gui/
├── src/
│   ├── api/             # Axios API calls — one file per backend endpoint group
│   ├── components/      # PascalCase .vue files
│   ├── views/           # Page-level views
│   ├── stores/          # Pinia stores
│   └── main.ts          # App entry
├── vite.config.ts
└── package.json
```

### CC-client (Vue 3 GUI + WebRTC)
```
CC-client/
├── src/
│   ├── api/
│   │   └── signaling.ts           # WebSocket client — connect, send, receive signaling messages
│   ├── components/
│   │   ├── DialPad.vue            # Phone number input + numeric keypad (3×4) + Call/End buttons
│   │   ├── CallStatus.vue         # Current call state label + visual indicator dot
│   │   └── VideoStream.vue        # Local + remote <video> tiles; localStream (getUserMedia, muted) + remoteStream (RTCPeerConnection); hidden until connected
│   ├── composables/
│   │   └── useWebRTC.ts           # RTCPeerConnection lifecycle: offer, answer, ICE, state tracking; captures localStream via getUserMedia
│   ├── views/
│   │   └── DialerView.vue         # Single-page view: title header + VideoStream + DialPad + CallStatus
│   ├── stores/
│   │   └── callStore.ts           # Pinia store: callState, phoneNumber, localStream, remoteStream
│   ├── main.ts
│   └── App.vue
├── vite.config.ts
└── package.json
```

**Note:** CC-client makes **no REST HTTP calls** to CC-server — WebSocket signaling only (`signaling.ts`).

**WebRTC Notes (Demo Mode):**
- Uses browser-native `RTCPeerConnection` with **no STUN/TURN server** (`iceServers: []`)
- Signaling via WebSocket to CC-server at `ws://localhost:8001/ws/signal`
- CC-server relays SDP offer/answer and ICE candidates between CC-client and CC-gui
- Only works on localhost or same LAN — not suitable for production NAT traversal

---

## Port Allocation (never change without updating all configs)

| Module | Port |
|---|---|
| CC-server | 8001 |
| CC-client-gui | 5172 |
| CC-gui | 5173 |
| CRM-server | 8002 |
| CRM-gui | 5174 |
| Billing-server | 8003 |
| Billing-gui | 5175 |

**WebRTC Signaling:** `ws://localhost:8001/ws/signal` (served by CC-server, no dedicated port)

---

## A2A Skills Registry (current baseline)

### CC-server (Orchestrator + Communication Agent host)
Orchestrates the following flow internally:
1. Receive WebRTC signaling from CC-client via WebSocket (`/ws/signal`)
2. Relay SDP offer/answer and ICE candidates to CC-gui via WebSocket
3. On WebRTC call established: trigger A2A business flow with phone number from CC-client
4. Call `Profiling Agent` → get customer profile
5. Call `Usage Agent` → get bill summary
5.5. *(Optional)* Call `AI Management Agent` → check NBO model health; set `nbo_fallback=true, nbo_fallback_reason="model_inactive"` if `status == "inactive"`. If Recommendation Agent falls back due to Ollama unavailability, it sets `nbo_fallback=true, nbo_fallback_reason="ollama_unavailable"` in the response.
6. Call `Recommendation Agent` → get NBO recommendations (fallback mode if `nbo_fallback=true`)
7. On agent selection of offer: call `Profiling Agent` (`verify_identity`) → verify customer identity; abort if `verified == false`
8. Call `Order Agent` → confirm order
9. Call `Communication Agent` (self-hosted on CC-server) → send post-order notification to customer
10. Return aggregated result (including notification status) to CC-gui

**WebSocket Signaling Endpoint:** `ws://localhost:8001/ws/signal`
- Message types: `offer`, `answer`, `ice-candidate`, `call-start`, `call-end`

#### Communication Agent — `POST /communication/a2a` · Agent Card: `GET /communication/.well-known/agent.json`
| Skill | Input | Output | TMF API |
|---|---|---|---|
| `send_notification` | `{ "customer_id": str, "channel": "sms\|email\|push", "message": str }` | `{ "message_id", "status" ("sent"\|"failed"), "sent_at" }` | TMF681 |

### CRM-server Agents & Skills

#### Profiling Agent — `POST /profiling/a2a` · Agent Card: `GET /profiling/.well-known/agent.json`
| Skill | Input | Output | TMF API |
|---|---|---|---|
| `query_customer` | `{ "phone": str }` | `{ "customer_id", "name", "customer_category", "product_name" }` | TMF629 / TMF637 |
| `verify_identity` | `{ "customer_id": str, "verification_method": "otp\|biometric\|knowledge" }` | `{ "identity_id", "verified" (bool), "confidence_score", "verified_at" }` | TMF720 |

#### Recommendation Agent — `POST /recommendation/a2a` · Agent Card: `GET /recommendation/.well-known/agent.json`
| Skill | Input | Output | TMF API |
|---|---|---|---|
| `get_nbo` | `{ "customer_id": str }` | `{ "id", "recommendation_item": [ { "id", "priority", "offering_id", "name", "description", "price", "price_unit" } ] }` | TMF701 / TMF620 / TMF637 |

#### Order Agent — `POST /order/a2a` · Agent Card: `GET /order/.well-known/agent.json`
| Skill | Input | Output | TMF API |
|---|---|---|---|
| `create_order` | `{ "customer_id": str, "offer_id": str }` | `{ "order_id", "state", "order_date" }` | TMF622 |

#### AI Management Agent — `POST /ai-management/a2a` · Agent Card: `GET /ai-management/.well-known/agent.json`
| Skill | Input | Output | TMF API |
|---|---|---|---|
| `get_ai_model_status` | `{ "model_id": str }` | `{ "model_id", "model_name", "version", "status" ("active"\|"inactive"\|"training"), "accuracy_score", "last_updated" }` | TMF915 |

**CRM Field notes:**
- `customer_category` — TMF629 `Customer.customerCategory`
- `product_name` — TMF637 `Product.name` (currently subscribed plan)
- `id` (top-level of get_nbo output) — TMF701 `Recommendation.id`
- `recommendation_item[]` — TMF701 `Recommendation.recommendationItem[]`, ordered by `priority` ascending
- `recommendation_item[].id` — TMF701 `RecommendationItem.id`
- `recommendation_item[].priority` — TMF701 `RecommendationItem.priority` (integer, 1 = highest)
- `recommendation_item[].offering_id` — TMF620 `ProductOffering.id`
- `recommendation_item[].price_unit` — TMF620 price unit (e.g. `"EUR"`)
- `state` — TMF622 `ProductOrder.state`, initial value `"acknowledged"`
- `order_date` — TMF622 `ProductOrder.orderDate`, ISO 8601

### Billing-server Agents & Skills

#### Usage Agent — `POST /usage/a2a` · Agent Card: `GET /usage/.well-known/agent.json`
| Skill | Input | Output | TMF API |
|---|---|---|---|
| `query_bill` | `{ "customer_id": str }` | `{ "bucket_balance", "bucket_balance_unit", "due_date", "bill_amount", "bill_amount_unit", "plan_usage_pct" }` | TMF677 / TMF678 |

**Billing Field notes:**
- `bucket_balance` — TMF677 `UsageConsumption.bucket[usageType=balance].remainingValue.amount`
- `bucket_balance_unit` — TMF677 `bucket.remainingValue.units` (e.g. `"EUR"`)
- `due_date` — TMF678 `CustomerBill.paymentDueDate` (`YYYY-MM-DD`)
- `bill_amount` — TMF678 `CustomerBill.amountDue.value`
- `bill_amount_unit` — TMF678 `CustomerBill.amountDue.unit` (e.g. `"EUR"`)
- `plan_usage_pct` — TMF677 derived: data bucket usage percentage `0–100`

---

## Business Flow: End-to-End Spec

```
Trigger: CC-client (Vue 3 GUI) initiates WebRTC call via WebSocket signaling
         → CC-server relays SDP/ICE to CC-gui → P2P connection established
         → CC-server receives call-start event { phone: "138xxxxxxxx" } and begins A2A flow

Step 1 — CC-server → Profiling Agent (http://localhost:8002/profiling/a2a)
  A2A: tasks/send skill=query_customer input={ phone }
  Expect: customer_id, name, customer_category, product_name

Step 2 — CC-server → Usage Agent (http://localhost:8003/usage/a2a)
  A2A: tasks/send skill=query_bill input={ customer_id }
  Expect: bucket_balance, bucket_balance_unit, due_date, bill_amount, bill_amount_unit, plan_usage_pct

Step 3 — CC-server → Recommendation Agent (http://localhost:8002/recommendation/a2a)
  A2A: tasks/send skill=get_nbo input={ customer_id }
  Expect: TMF701 Recommendation { id, recommendation_item[] (≥1 item, ordered by priority) }
          each item: { id, priority, offering_id, name, description, price, price_unit }

Step 3.5 [OPTIONAL] — CC-server → AI Management Agent (http://localhost:8002/ai-management/a2a)
  A2A: tasks/send skill=get_ai_model_status input={ model_id }
  Expect: model_id, model_name, version, status, accuracy_score, last_updated
  If status == "inactive": set nbo_fallback=true; request fallback (price-sorted) from Recommendation Agent

Step 4 — CC-gui presents recommendations to agent
  Agent selects an offer → CC-gui POST /order/create { customer_id, offer_id }

Step 4.5 [NEW] — CC-server → Profiling Agent (http://localhost:8002/profiling/a2a)
  A2A: tasks/send skill=verify_identity input={ customer_id, verification_method }
  Expect: identity_id, verified (bool), confidence_score, verified_at
  If verified == false: abort order placement; return identity failure to CC-gui

Step 5 — CC-server → Order Agent (http://localhost:8002/order/a2a)
  A2A: tasks/send skill=create_order input={ customer_id, offer_id }
  Expect: order_id, state="acknowledged", order_date

Step 6 — CC-server → Communication Agent (http://localhost:8001/communication/a2a)
  A2A: tasks/send skill=send_notification input={ customer_id, channel, message }
  Expect: message_id, status ("sent"|"failed"), sent_at

Step 7 — CC-server returns full session summary to CC-gui
  Payload includes: customer, bill, nbo (+ nbo_fallback flag if set), order, notification
```

---

## Code Quality Rules

- All FastAPI route handlers and Skill functions must have **type annotations**
- All Pydantic models must have **field descriptions** (`Field(description="...")`)
- No hardcoded URLs — use environment variables or `config.py` constants
- A2A calls use `a2a-python` SDK (handles timeouts internally); non-A2A `httpx` calls (e.g., Ollama) must have an explicit **timeout**
- Vue components must use `<script setup lang="ts">` with TypeScript
- API functions in `src/api/` must return **typed responses** using TypeScript interfaces

---

## OpenSpec Spec Format

When writing `spec.md` files, use this format:

```markdown
# <Domain> Spec

## Requirements

- The system SHALL <requirement> (MUST = mandatory, SHOULD = recommended, MAY = optional)

## Scenarios

### Scenario: <name>
- Given: <precondition>
- When: <action>
- Then: <expected outcome>
```

---

## What NOT to do

- ❌ Do NOT invent arbitrary field names for Skill schemas — align with TMF Open API resource attributes
- ❌ Do NOT add direct database queries in FastAPI route handlers — use skill functions
- ❌ Do NOT create shared Python packages across subsystems
- ❌ Do NOT let CRM or Billing call each other
- ❌ Do NOT skip Agent Card definition when adding a new Skill
- ❌ Do NOT use `requests` library — use `a2a-python` SDK for A2A calls, `httpx.AsyncClient` for non-A2A calls
- ❌ Do NOT manually implement A2A protocol (JSON-RPC dispatch, Agent Card endpoints, envelope parsing) — import and use `a2a-python` SDK
- ❌ Do NOT use `pip install` directly — use `uv add` for dependencies, `uv run` for execution
- ❌ Do NOT hardcode `localhost` — use config constants
- ❌ Do NOT modify `openspec/specs/` directly — use `changes/` workflow
- ❌ Do NOT configure STUN/TURN servers in WebRTC — Demo uses direct connection only (`iceServers: []`)
- ❌ Do NOT make CC-client a Python script — it is a Vue 3 frontend GUI
