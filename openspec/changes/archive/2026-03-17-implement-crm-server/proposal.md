## Why

CC-server (the orchestrator) is implemented and ready to dispatch A2A calls to CRM-server, but the CRM subsystem has no running service yet. Without CRM-server, the end-to-end call-center business flow cannot execute — customer lookup, identity verification, product recommendations, and order placement all depend on it. CRM-server is the next critical path item.

## What Changes

- **New FastAPI application** at `app/CRM/CRM-server/` (port 8002) hosting four A2A agents via the `a2a-python` SDK
- **Profiling Agent** (`/profiling`) — `query_customer` (TMF629) and `verify_identity` (TMF720) skills
- **Recommendation Agent** (`/recommendation`) — `get_nbo` skill (TMF701) with LLM-powered recommendations via Ollama, plus price-sorted fallback
- **Order Agent** (`/order`) — `create_order` skill (TMF622) for product order placement
- **AI Management Agent** (`/ai-management`) — `get_ai_model_status` skill (TMF915) for Ollama model health checks
- **SQLite database** with `customers`, `product_offerings`, `orders`, `identities`, and `ai_models` tables
- **Seed script** (`seed.py`) to initialize the database with three test customers and product offerings

## Non-goals

- CRM-gui implementation (separate change)
- Modifications to CC-server orchestration logic (already coded against the A2A contract)
- Real authentication or production-grade identity verification
- Persistent Ollama model training or fine-tuning

## Capabilities

### New Capabilities

- `crm-profiling`: Customer lookup by phone and identity verification via Profiling Agent (TMF629/TMF720)
- `crm-recommendation`: LLM-powered next-best-offer recommendations via Recommendation Agent (TMF701/TMF620/TMF637)
- `crm-order`: Product order creation and state tracking via Order Agent (TMF622)
- `crm-ai-management`: AI model status monitoring via AI Management Agent (TMF915)

### Modified Capabilities

_(none — no existing spec requirements are changing)_

## Impact

- **Subsystem affected:** CRM (new service); CC-server orchestration is NOT modified
- **New code:** `app/CRM/CRM-server/` — FastAPI app, four agent modules, SQLite database layer, seed script
- **Dependencies:** `a2a-python`, `fastapi`, `uvicorn`, `httpx`, `aiosqlite`, `pydantic` (managed via `uv` + `pyproject.toml`)
- **External integration:** Ollama API for `get_nbo` LLM inference (model `qwen2.5:7b`)
- **TMForum alignment:** TMF620, TMF622, TMF629, TMF637, TMF701, TMF720, TMF915
- **Port:** 8002 (allocated, no conflict)
