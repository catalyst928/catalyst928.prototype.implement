## 1. Project Setup

- [x] 1.1 Create `app/CRM/CRM-server/` directory structure with `main.py`, `pyproject.toml`, and `src/` package following AGENTS.md convention: `src/config.py`, `src/db.py`, `src/seed.py`, `src/agents/base.py`, and agent subdirectories `src/agents/{profiling,recommendation,order,ai_management}/` each with `agent.py`, `models.py`, and `skills/` subdirectory
- [x] 1.2 Initialize `pyproject.toml` with dependencies (`fastapi`, `uvicorn`, `a2a-python`, `httpx`, `aiosqlite`, `pydantic`) using `uv`
- [x] 1.3 Implement `src/config.py` with env vars: `OLLAMA_BASE_URL` (default `http://localhost:11434`), `OLLAMA_MODEL` (default `qwen2.5:7b`), `DB_PATH`, and `CRM_SERVER_PORT` (default 8002)

## 2. Base Agent Executor

- [x] 2.1 Implement `src/agents/base.py` with `BaseAgentExecutor(AgentExecutor)` providing: `_extract_input(ctx)` (parse DataPart.data from message parts), `_emit_result(output, ctx, eq)` (emit TaskArtifactUpdateEvent + TaskStatusUpdateEvent completed), `_emit_error(message, ctx, eq)` (emit TaskStatusUpdateEvent failed with message string)

## 3. Database Layer

- [x] 3.1 Implement `src/db.py` with `init_db()` function: create `customers`, `product_offerings`, `orders`, `identities`, and `ai_models` tables (DDL from spec data model); call `seed_data()` from `seed.py`
- [x] 3.2 Implement `src/seed.py` with `seed_data(db)`: 3 customers (A: cust_001/13800000001/gold/Plan-50G, B: cust_002/13800000002/silver/Plan-100G, C: cust_003/13800000003/bronze/Plan-200G), 3+ product offerings with EUR prices, identity verification records for ALL 3 customers (at least one verified=true and one verified=false), and 1 AI model record (qwen2.5_7b/active)
- [x] 3.3 Add query functions in `src/db.py`: `get_customer_by_phone()`, `get_customer_by_id()`, `get_product_offerings()`, `get_product_offering_by_id()`, `create_order()`, `get_identity_by_customer()`, `get_ai_model_by_id()`

## 4. Profiling Agent

- [x] 4.1 Define Pydantic models in `src/agents/profiling/models.py`: `QueryCustomerInput`, `QueryCustomerOutput`, `VerifyIdentityInput`, `VerifyIdentityOutput` with `Field(description=...)` on all fields
- [x] 4.2 Implement `src/agents/profiling/skills/query_customer.py`: async function that takes validated input, calls `db.get_customer_by_phone()`, returns `QueryCustomerOutput` or raises `ValueError("Customer not found")`
- [x] 4.3 Implement `src/agents/profiling/skills/verify_identity.py`: async function that validates customer exists via `db.get_customer_by_id()`, looks up identity record, returns `VerifyIdentityOutput` or raises `ValueError("Customer not found")`
- [x] 4.4 Implement `src/agents/profiling/agent.py`: `PROFILING_AGENT_CARD` (AgentCard with `query_customer` and `verify_identity` skills) and `ProfilingAgentExecutor(BaseAgentExecutor)` with inline if/elif dispatch on `data["skill"]`, calling skill functions and using `_emit_result()`/`_emit_error()`

## 5. Recommendation Agent

- [x] 5.1 Define Pydantic models in `src/agents/recommendation/models.py`: `GetNboInput`, `RecommendationItem`, `GetNboOutput` with TMF701 field descriptions
- [x] 5.2 Implement `src/agents/recommendation/skills/get_nbo.py`: async function containing Ollama call via shared `httpx.AsyncClient` (passed as parameter), prompt template from spec verbatim, JSON response parsing with regex fallback for prose-wrapped responses, TMF637 inventory exclusion (filter current plan), fallback to price-sorted offerings on Ollama failure or all-invalid IDs, warning log on fallback
- [x] 5.3 Implement `src/agents/recommendation/agent.py`: `RECOMMENDATION_AGENT_CARD` and `RecommendationAgentExecutor(BaseAgentExecutor)` with `get_nbo` skill, passing `app.state.ollama_client` to the skill function

## 6. Order Agent

- [x] 6.1 Define Pydantic models in `src/agents/order/models.py`: `CreateOrderInput`, `CreateOrderOutput` with TMF622 field descriptions
- [x] 6.2 Implement `src/agents/order/skills/create_order.py`: async function that validates customer and offering exist via db, persists order with state `"acknowledged"` and ISO 8601 `order_date`, returns `CreateOrderOutput` or raises `ValueError`
- [x] 6.3 Implement `src/agents/order/agent.py`: `ORDER_AGENT_CARD` and `OrderAgentExecutor(BaseAgentExecutor)` with `create_order` skill

## 7. AI Management Agent

- [x] 7.1 Define Pydantic models in `src/agents/ai_management/models.py`: `GetAiModelStatusInput`, `GetAiModelStatusOutput` with TMF915 field descriptions
- [x] 7.2 Implement `src/agents/ai_management/skills/get_ai_model_status.py`: async function that looks up model by ID, returns `GetAiModelStatusOutput` or raises `ValueError("AIModel not found")`
- [x] 7.3 Implement `src/agents/ai_management/agent.py`: `AI_MANAGEMENT_AGENT_CARD` and `AIManagementAgentExecutor(BaseAgentExecutor)` with `get_ai_model_status` skill

## 8. Application Assembly

- [x] 8.1 Implement `main.py`: create FastAPI app, add CORS middleware, initialize DB via lifespan, create shared `httpx.AsyncClient(timeout=30.0)` in lifespan stored on `app.state.ollama_client`, log config (including OLLAMA_BASE_URL and OLLAMA_MODEL) at startup
- [x] 8.2 Mount all four A2A agents under their route prefixes (`/profiling`, `/recommendation`, `/order`, `/ai-management`) using `A2AStarletteApplication`
- [x] 8.3 Add `/health` endpoint returning `{ "status": "ok", "service": "crm-server" }`

## 9. Testing

- [x] 9.1 Create `test/` directory with pytest configuration and shared fixtures (test DB setup, seeded data, app client)
- [x] 9.2 Test Profiling Agent (`test/test_profiling.py`): customer lookup success, customer lookup failure (phone not found), identity verification success (verified=true), identity verification failure (verified=false), identity verification for non-existent customer, unknown skill name returns error
- [x] 9.3 Test Recommendation Agent (`test/test_recommendation.py`): NBO with mocked Ollama valid response, NBO with Ollama prose-wrapped JSON (regex extraction), NBO with Ollama unparseable response (triggers fallback), NBO with Ollama connection error (triggers fallback), NBO with all-invalid Ollama IDs (triggers fallback), NBO customer not found, TMF637 inventory exclusion (current plan filtered), prompt template verification (contains customer profile and offerings), unknown skill name returns error
- [x] 9.4 Test Order Agent (`test/test_order.py`): order creation success (state=acknowledged), invalid customer, invalid offering, unknown skill name returns error
- [x] 9.5 Test AI Management Agent (`test/test_ai_management.py`): model status query (active), model status query (inactive), unknown model, unknown skill name returns error
- [x] 9.6 Test Agent Cards (`test/test_agent_cards.py`): verify all four Agent Cards are served correctly at their `.well-known/agent.json` endpoints with correct skill listings
- [x] 9.7 Test Database (`test/test_db.py`): init_db creates all 5 tables, seed data present after startup (3 customers, 3+ offerings, identity records, 1 AI model)
