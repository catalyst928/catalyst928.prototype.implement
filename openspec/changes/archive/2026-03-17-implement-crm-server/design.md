## Context

CC-server (port 8001) is fully implemented and dispatches A2A calls to CRM-server endpoints (`/profiling/a2a`, `/recommendation/a2a`, `/order/a2a`, `/ai-management/a2a`). CRM-server does not yet exist. The authoritative spec at `openspec/specs/CRM/spec.md` defines four agents, five skills, five SQLite tables, and an Ollama LLM integration. CC-server's implementation establishes the `a2a-python` SDK patterns (AgentCard, AgentExecutor, A2AStarletteApplication) that CRM-server will follow.

## Goals / Non-Goals

**Goals:**
- Deliver a fully functional CRM-server on port 8002 that satisfies all A2A skill contracts CC-server depends on
- Follow identical `a2a-python` SDK patterns established by CC-server (AgentCard → AgentExecutor → A2AStarletteApplication → mount)
- Provide LLM-powered NBO recommendations with a reliable fallback path
- Pre-seed all required demo data via `seed.py` at startup

**Non-Goals:**
- CRM-gui implementation (separate change)
- Modifying CC-server code
- Production-grade security, authentication, or identity verification
- Ollama model training or fine-tuning
- Horizontal scalability or multi-instance deployment

## Decisions

### 1. Single FastAPI process, four mounted A2A agents

**Decision:** Host all four agents (Profiling, Recommendation, Order, AI Management) in one FastAPI process, each mounted under its route prefix via `A2AStarletteApplication`.

**Rationale:** Matches CC-server's pattern. The spec mandates a single process on port 8002. Four separate services would add unnecessary operational complexity for a demo.

**Alternative considered:** One FastAPI process per agent — rejected due to port conflicts and added coordination overhead.

### 2. `aiosqlite` for async SQLite access

**Decision:** Use `aiosqlite` for all database operations.

**Rationale:** Architecture rules forbid synchronous I/O. `aiosqlite` wraps `sqlite3` in an async interface compatible with FastAPI's event loop. No ORM needed for this scope — raw SQL with parameterized queries is simpler and sufficient for five tables.

**Alternative considered:** SQLAlchemy async — rejected as over-engineered for a demo with five simple tables and no migrations.

### 3. Shared database module with startup initialization

**Decision:** `src/db.py` owns the SQLite connection, DDL (`init_db()`), and query functions. `src/seed.py` contains demo data insertion, called from `init_db()`. Both are invoked via FastAPI `lifespan` in `main.py`.

**Rationale:** Avoids duplicate connection management. The lifespan pattern ensures the DB is ready before any request is handled. Separating `seed.py` matches AGENTS.md directory convention and cleanly separates schema from data.

**Alternative considered:** Single `db.py` with embedded seed data — rejected to follow AGENTS.md convention and keep schema/data concerns separate (~150 + ~80 lines vs ~250 in one file).

### 4. Ollama integration via `httpx.AsyncClient` with JSON parsing + regex fallback

**Decision:** Call `POST {OLLAMA_BASE_URL}/api/generate` with `stream: false`, parse the `response` field as JSON. If JSON parsing fails, use regex to extract a JSON array from prose. If the Ollama call fails entirely or returns no valid offering IDs, fall back to price-sorted offerings.

**Rationale:** Spec mandates `httpx.AsyncClient` with `timeout=30.0`. The regex fallback handles LLM responses wrapped in prose. The price-sorted fallback ensures `recommendation_item[]` always has at least one item regardless of Ollama availability.

**Alternative considered:** Structured output via Ollama's format parameter — not reliably supported across all models; regex fallback is more robust.

### 5. Agent module structure

**Decision:** Follow AGENTS.md convention with `src/agents/<name>/skills/<skill>.py`:
```
app/CRM/CRM-server/
├── main.py                              # FastAPI app entry, CORS, lifespan, agent mounting
├── pyproject.toml
├── src/
│   ├── config.py                        # Env vars: OLLAMA_BASE_URL, OLLAMA_MODEL, DB path
│   ├── db.py                            # SQLite DDL, query functions
│   ├── seed.py                          # Demo data insertion (called from db.init_db)
│   ├── agents/
│   │   ├── base.py                      # BaseAgentExecutor: _extract_input, _emit_result, _emit_error
│   │   ├── profiling/
│   │   │   ├── agent.py                 # AgentCard, ProfilingAgentExecutor (dispatches by skill)
│   │   │   ├── models.py               # Input/Output Pydantic models
│   │   │   └── skills/
│   │   │       ├── query_customer.py    # Business logic: DB lookup by phone
│   │   │       └── verify_identity.py   # Business logic: identity verification
│   │   ├── recommendation/
│   │   │   ├── agent.py                 # AgentCard, RecommendationAgentExecutor
│   │   │   ├── models.py               # Input/Output Pydantic models
│   │   │   └── skills/
│   │   │       └── get_nbo.py           # Business logic: Ollama call + fallback
│   │   ├── order/
│   │   │   ├── agent.py                 # AgentCard, OrderAgentExecutor
│   │   │   ├── models.py               # Input/Output Pydantic models
│   │   │   └── skills/
│   │   │       └── create_order.py      # Business logic: order persistence
│   │   └── ai_management/
│   │       ├── agent.py                 # AgentCard, AIManagementAgentExecutor
│   │       ├── models.py               # Input/Output Pydantic models
│   │       └── skills/
│   │           └── get_ai_model_status.py  # Business logic: model status lookup
└── test/
```

**Rationale:** Follows AGENTS.md directory convention. `skills/<skill>.py` contains pure business logic (async functions that take validated input, return Pydantic output or raise). `agent.py` handles SDK concerns (AgentCard, executor dispatch, event queue). `base.py` eliminates boilerplate duplication across 4 executors.

**Alternative considered:** Flat `src/<agent>/` (CC-server's current pattern) — rejected to align with AGENTS.md; CC-server will be refactored later (see TODOS.md).

### 5a. BaseAgentExecutor for DRY

**Decision:** Create `src/agents/base.py` with `BaseAgentExecutor` providing:
- `_extract_input(ctx)` — parse `DataPart.data` from message parts (+ `data["skill"]` extraction)
- `_emit_result(output, ctx, eq)` — emit `TaskArtifactUpdateEvent` + `TaskStatusUpdateEvent(completed)`
- `_emit_error(message, ctx, eq)` — emit `TaskStatusUpdateEvent(failed)` with message string

All 4 agent executors inherit from `BaseAgentExecutor`.

**Rationale:** Without this, each executor duplicates ~30 lines of identical SDK glue code (input extraction, artifact emission, status updates). With 4 executors, that's ~90 lines of unnecessary duplication.

### 5b. Multi-skill dispatch pattern

**Decision:** Agents with multiple skills (Profiling) use inline `if/elif` on `data["skill"]` in `execute()`. The `a2a-python` SDK has no first-class skill routing — skill ID is embedded in the `DataPart` payload as `{"skill": "skill_name", ...}` (CC-server's client uses this convention).

```
                    ┌──────────────────────────┐
  JSON-RPC req ───► │  ProfilingAgentExecutor   │
  data["skill"] =   │                           │
  "query_customer"  │  if/elif dispatch         │
  ─ ─ ─ ─ ─ ─ ─ ►  │   ├─► query_customer()    │
  "verify_identity" │   └─► verify_identity()   │
                    └──────────────────────────┘
```

Unknown skill names emit `TaskState.failed` with message `"Unknown skill: {name}"`.

### 5c. Domain error signaling

**Decision:** Domain errors (customer not found, model not found, etc.) are signaled via `TaskState.failed` + descriptive message string, NOT raw JSON-RPC error codes.

**Rationale:** The a2a-python SDK reserves `-32001` for protocol-level `TaskNotFoundError`. CC-server's client already catches `TaskState.failed` and wraps it as `A2AError(message=...)`. Using `TaskState.failed` is the correct SDK-native pattern.

### 5d. Shared httpx.AsyncClient for Ollama

**Decision:** Create `httpx.AsyncClient(timeout=30.0)` in FastAPI `lifespan`, store on `app.state.ollama_client`, pass to the Recommendation Agent's `get_nbo` skill. Client is closed on shutdown.

**Rationale:** Follows httpx best practice of reusing connection-pooled clients. Prevents resource leaks under concurrent requests.

### 6. Ollama prompt template from spec, verbatim

**Decision:** Use the prompt template defined in `openspec/specs/CRM/spec.md` § Prompt Template exactly as written, with `{customer_id}`, `{customer_category}`, `{product_name}`, and `{offerings_json}` interpolated at runtime.

```
You are a telecom product recommendation engine.

Customer profile:
- customer_id: {customer_id}
- category: {customer_category}
- current plan: {product_name}

Available product offerings (excluding current plan):
{offerings_json}

Return ONLY a JSON array of up to 3 offering IDs ranked by suitability for this customer, most suitable first.
Example: ["po_002", "po_003", "po_001"]
Do not include any explanation.
```

**Rationale:** The spec defines the exact prompt. No deviation needed.

## Risks / Trade-offs

**[SQLite concurrency under parallel A2A calls]** → SQLite allows only one writer at a time. Mitigation: `aiosqlite` serializes writes automatically; demo workload is low-concurrency. Acceptable for a demo scenario.

**[Ollama response quality varies]** → LLM may return hallucinated offering IDs or malformed JSON. Mitigation: Regex fallback for JSON extraction + validation that returned IDs exist in the `product_offerings` table + full fallback to price-sorted offerings if all IDs are invalid.

**[Ollama unavailability at demo time]** → Connection refused or timeout. Mitigation: Spec-defined fallback path returns price-sorted offerings; service starts without Ollama and logs a warning at call time only.

**[No cross-subsystem Python imports]** → Confirmed: CRM-server imports only from its own `src/` package. Contracts with CC-server are purely via A2A JSON-RPC over HTTP.

## Open Questions

_(none — the spec is comprehensive and all decisions are straightforward)_
