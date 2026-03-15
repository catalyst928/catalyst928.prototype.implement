# Project Overview: A2A Protocol Demo

## Project Name
**A2A Inter-System Business Flow Demo**

## Purpose
Demonstrate end-to-end business process integration across multiple subsystems using the **A2A (Agent-to-Agent) Protocol**.
Core scenario: A call center (CC) receives an incoming customer call, then orchestrates CRM and Billing subsystems via A2A to complete a full business loop — customer lookup, bill inquiry, intelligent NBO recommendation, and order placement.

---

## Core Business Flow

```
[Incoming Customer Call]
    │
    ▼
CC-server (Call Center entry point)
    │  A2A: query customer info
    ▼
CRM-server (customer lookup)
    │  A2A: query bill info
    ▼
Billing-server (bill info response)
    │  A2A: request NBO recommendations
    ▼
CRM-server (NBO recommendations)
    │  A2A: place order
    ▼
CRM-server (order confirmation)
    │
    ▼
CC-server (aggregate results, return to agent dashboard)
```

---

## Project Structure

```
app/
├── Billing/
│   ├── Billing-gui/        # Vue 3 frontend — bill viewing interface
│   └── Billing-server/     # FastAPI service — hosts Usage Agent (query_bill)
├── CC/
│   ├── CC-client/          # Vue 3 frontend — simulates incoming call (WebRTC caller)
│   ├── CC-gui/             # Vue 3 frontend — agent dashboard (WebRTC receiver + main console)
│   └── CC-server/          # FastAPI service — call entry, flow orchestration, WebRTC signaling
└── CRM/
    ├── CRM-gui/            # Vue 3 frontend — customer 360 view
    └── CRM-server/         # FastAPI service — hosts Profiling Agent, Recommendation Agent, Order Agent
```

---

## Tech Stack

### Backend (All Server modules)
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **A2A Protocol**: Google A2A SDK (JSON-RPC 2.0 over HTTP)
- **Agent Card**: Each named agent exposes its own Agent Card at `GET /<agent-prefix>/.well-known/agent.json`
- **Data Store**: SQLite (demo use; each subsystem has its own independent database)
- **Async**: `asyncio` + `httpx` (for A2A inter-service calls)
- **Dependency Management**: `uv` + `pyproject.toml`

### Frontend (All GUI modules)
- **Framework**: Vue 3 (Composition API)
- **Build Tool**: Vite
- **UI Library**: Element Plus
- **HTTP Client**: Axios
- **State Management**: Pinia
- **Package Manager**: npm

### CC-client (Vue 3 GUI + WebRTC)
- **Framework**: Vue 3 (Composition API)
- **Build Tool**: Vite
- **WebRTC**: Browser-native WebRTC API (`RTCPeerConnection`)
- **Signaling**: WebSocket connection to CC-server (`ws://localhost:8001/ws/signal`)
- **Demo Mode**: Direct connection — no STUN/TURN server; suitable for localhost or same-LAN only
- **Package Manager**: npm

---

## Subsystem Responsibilities

### CC (Call Center — Orchestrator)
- **CC-server**: Receives incoming call events; acts as the sole A2A Orchestrator to coordinate the full business flow; aggregates results from all subsystems and returns them to the agent dashboard; also serves as WebRTC signaling relay via WebSocket
- **CC-client**: Vue 3 frontend GUI that simulates an incoming customer call; uses WebRTC direct connection (demo mode, no STUN/TURN) to establish a P2P call with CC-gui; triggers the CC-server business flow once the call is connected
- **CC-gui**: Agent operator dashboard; displays customer info, bill summary, NBO recommendation list, and order entry; also acts as WebRTC receiver to answer incoming calls

### CRM (Customer Relationship Management)
CRM-server is a single FastAPI process (port 8002) hosting four named agents, each with its own Agent Card and A2A route prefix:
- **Profiling Agent** (`/profiling`) — `query_customer`, `verify_identity`: look up customer profile by phone number and verify digital identity before order placement *(TMF629 – Customer Management, TMF637 – Product Inventory Management, TMF720 – Digital Identity Management)*
- **Recommendation Agent** (`/recommendation`) — `get_nbo`: generate a prioritized NBO recommendation list *(TMF701 – Recommendation API; TMF620 – Product Catalog Management; TMF637 – Product Inventory Management)*
- **Order Agent** (`/order`) — `create_order`: place a product order and return the order ID *(TMF622 – Product Order Management)*
- **AI Management Agent** (`/ai-management`) — `get_ai_model_status`: query the health and status of the NBO AI model *(TMF915 – AI Management)*
- **CRM-gui**: Customer 360 view — displays customer information and order history

### Billing
Billing-server is a single FastAPI process (port 8003) hosting one named agent:
- **Usage Agent** (`/usage`) — `query_bill`: query the customer's current bill, account balance, and plan usage consumption *(TMF677 – Usage Consumption Management)*
- **Billing-gui**: Bill details interface — displays monthly bill and consumption breakdown

---

## A2A Protocol Conventions

### Agent Card Specification
Each named agent exposes its own Agent Card at `GET /<agent-prefix>/.well-known/agent.json`, containing:
- `name`: Agent name (e.g. `"Profiling Agent"`, `"Recommendation Agent"`)
- `description`: Functional description
- `skills`: List of supported skills (with `inputSchema` / `outputSchema`)
- `url`: Agent base URL (e.g. `http://localhost:8002/profiling`)

**Agent endpoints per server:**

| Server | Agent | Agent Card | A2A Endpoint |
|---|---|---|---|
| CRM-server (8002) | Profiling Agent | `GET /profiling/.well-known/agent.json` | `POST /profiling/a2a` |
| CRM-server (8002) | Recommendation Agent | `GET /recommendation/.well-known/agent.json` | `POST /recommendation/a2a` |
| CRM-server (8002) | Order Agent | `GET /order/.well-known/agent.json` | `POST /order/a2a` |
| CRM-server (8002) | AI Management Agent | `GET /ai-management/.well-known/agent.json` | `POST /ai-management/a2a` |
| CC-server (8001) | Communication Agent | `GET /communication/.well-known/agent.json` | `POST /communication/a2a` |
| Billing-server (8003) | Usage Agent | `GET /usage/.well-known/agent.json` | `POST /usage/a2a` |

### Message Format
- Base protocol: **JSON-RPC 2.0 over HTTP POST**
- Content-Type: `application/json`
- Request path: `/<agent-prefix>/a2a`
- Standard request body:
```json
{
  "jsonrpc": "2.0",
  "method": "tasks/send",
  "params": {
    "skill": "<skill_name>",
    "input": { ... }
  },
  "id": "<uuid>"
}
```

### Port Allocation (Demo defaults)
| Service | Port |
|---|---|
| CC-server | 8001 |
| CC-client-gui | 5172 |
| CC-gui | 5173 |
| CRM-server | 8002 |
| CRM-gui | 5174 |
| Billing-server | 8003 |
| Billing-gui | 5175 |

> WebRTC signaling channel: `ws://localhost:8001/ws/signal` (served by CC-server, no dedicated port)

---

## TMForum OpenAPI Alignment

A2A Skill interfaces are designed to align with **TM Forum Open API** data models and resource schemas. Each skill maps to a canonical TMF API, ensuring the demo reflects industry-standard telecom BSS/OSS integration patterns.

| A2A Skill | Subsystem | TMF API | TMF Resource |
|---|---|---|---|
| `query_customer` | CRM | **TMF629** – Customer Management | `Customer`, `Individual` |
| `get_nbo` | CRM | **TMF701** – Recommendation API | `Recommendation`, `RecommendationItem` |
| `get_nbo` (offering detail) | CRM | **TMF620** – Product Catalog Management | `ProductOffering` |
| `get_nbo` (inventory check) | CRM | **TMF637** – Product Inventory Management | `ProductInventory` |
| `create_order` | CRM | **TMF622** – Product Order Management | `ProductOrder`, `ProductOrderItem` |
| `create_order` (service provisioning) | CRM | **TMF641** – Service Order Management | `ServiceOrder` |
| `verify_identity` | CRM | **TMF720** – Digital Identity Management | `DigitalIdentity` |
| `get_ai_model_status` | CRM | **TMF915** – AI Management | `AIModel` |
| `send_notification` | CC | **TMF681** – Communication Management | `CommunicationMessage` |
| `query_bill` | Billing | **TMF677** – Usage Consumption Management | `UsageConsumption`, `ConsumptionSummary` |

### Alignment Principles

- **Field naming**: Skill input/output field names SHOULD match TMF resource attribute names where practical (e.g., `id`, `name`, `status`, `@type`)
- **Status values**: Order and resource status values SHALL follow TMF enumeration conventions (e.g., `ProductOrder.state`: `acknowledged` → `inProgress` → `completed`)
- **Date format**: All date/time fields SHALL use ISO 8601 (`YYYY-MM-DDThh:mm:ssZ`) consistent with TMF API conventions
- **Error codes**: JSON-RPC error messages SHOULD reference the relevant TMF error category where applicable
- **Demo scope**: Full TMF schema compliance is not required — only key fields relevant to the demo flow are implemented; schemas are TMF-inspired, not TMF-complete

### TMF API Reference Summary

| TMF API | Scope in this project |
|---|---|
| **TMF620** – Product Catalog Management | Offering detail source — `ProductOffering` attributes embedded in each `RecommendationItem` |
| **TMF622** – Product Order Management | Order placement and lifecycle tracking |
| **TMF629** – Customer Management | Customer identity, tier, and contact lookup |
| **TMF637** – Product Inventory Management | Customer's currently subscribed products/plans (informs NBO filtering) |
| **TMF641** – Service Order Management | Service-level fulfillment triggered by a product order |
| **TMF677** – Usage Consumption Management | Plan usage percentage and billing consumption data |
| **TMF681** – Communication Management | Post-order customer notification via preferred channel (SMS, email, push) |
| **TMF701** – Recommendation API | Primary model for `get_nbo` — `Recommendation` with prioritized `RecommendationItem` list |
| **TMF720** – Digital Identity Management | Customer identity verification gate before order placement |
| **TMF915** – AI Management | NBO AI model lifecycle and health status tracking |

---

## Architecture Patterns

- **Orchestrator Pattern**: CC-server is the sole orchestrator; it calls other Agents in sequence; CRM and Billing must never call each other directly
- **Agent Card Discovery**: Before any cross-system call, the caller must GET `/<agent-prefix>/.well-known/agent.json` to verify the target Agent's capabilities
- **Stateless Skills**: Each A2A Skill call is stateless; session state is maintained by CC-server
- **Error Propagation**: A2A call failures must return a standard JSON-RPC error object; CC-server is responsible for graceful degradation

---

## Code Standards

- **Python**: Follow PEP 8; use `pydantic` for request/response model validation; all A2A handlers must have type annotations
- **Vue**: Use `<script setup>` syntax throughout; component filenames in PascalCase; all API calls encapsulated in `src/api/`
- **Naming**: A2A Skill names use `snake_case`; REST routes use `kebab-case`
- **No Shared Code**: Each subsystem's code is fully independent; cross-subsystem imports are forbidden; shared types are defined only via A2A JSON Schema
- **CORS**: All servers enable CORS to allow local GUI cross-origin requests
- **TMForum Alignment**: Skill input/output field names and status enumerations SHOULD follow TMF Open API conventions; refer to the TMForum OpenAPI Alignment section for the mapping table

---

## Demo Data

- 3 pre-seeded test customers (Customer A / B / C) covering different plans and billing states
- Pre-seeded NBO recommendation pool (3 plan upgrade options)
- All data is initialized into SQLite via `seed.py` at service startup

---

## Getting Started

### One-Command Startup (Docker Compose)

The primary startup path uses Docker Compose. A `docker-compose.yml` SHALL exist at the repository root, defining all services with correct dependency ordering.

```
docker compose up
```

#### Services

| Service | Build Context | Exposed Port | Depends On |
|---------|--------------|--------------|------------|
| `ollama` | `ollama/ollama` (image) | 11434 | — |
| `model-init` | `ollama/ollama` (image) | — | `ollama` (healthy) |
| `cc-server` | `./app/CC/CC-server` | 8001 | `model-init` (completed) |
| `crm-server` | `./app/CRM/CRM-server` | 8002 | `model-init` (completed) |
| `billing-server` | `./app/Billing/Billing-server` | 8003 | `model-init` (completed) |
| `cc-client` | `./app/CC/CC-client` | 5172 | `cc-server` |
| `cc-gui` | `./app/CC/CC-gui` | 5173 | `cc-server` |
| `crm-gui` | `./app/CRM/CRM-gui` | 5174 | `crm-server` |
| `billing-gui` | `./app/Billing/Billing-gui` | 5175 | `billing-server` |

#### Service Specifications

**`ollama`**
- Image: `ollama/ollama`
- Volume: named volume `ollama_data` → `/root/.ollama` (model persistence across restarts)
- Health check: `ollama list` exits 0; interval 10s, retries 5

**`model-init`**
- Image: `ollama/ollama`
- Command: `ollama pull qwen2.5:7b`
- `restart: on-failure` — exits 0 on success; compose marks it `service_completed_successfully`
- Environment: `OLLAMA_HOST=http://ollama:11434`
- Depends on: `ollama` condition `service_healthy`

**Backend servers (`cc-server`, `crm-server`, `billing-server`)**
- Each built from a `Dockerfile` at its service directory root
- Depend on: `model-init` condition `service_completed_successfully`
- `crm-server` MUST set `OLLAMA_BASE_URL=http://ollama:11434` — the only env var that differs between Docker and manual startup; all other servers do not call Ollama directly

**Frontend services (`cc-client`, `cc-gui`, `crm-gui`, `billing-gui`)**
- Each built from a `Dockerfile` at its GUI directory root
- Run Vite dev server: `npm run dev -- --host 0.0.0.0 --port <port>`
- Each GUI's backend API base URL MUST be configurable via `VITE_API_BASE_URL` build-time env var, passed as a Docker build arg

#### Dockerfile Templates

**Backend (FastAPI + uv):**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install uv
COPY pyproject.toml .
RUN uv sync
COPY . .
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "<port>"]
```

**Frontend (Vue 3 + Vite):**
```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json .
RUN npm install
COPY . .
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
EXPOSE <port>
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "<port>"]
```

---

### Manual Startup (Fallback)

For environments where Docker is unavailable:

```bash
# 1. Start Ollama and pull model
ollama serve &
ollama pull qwen2.5:7b

# 2. Start backend servers (3 terminals)
cd app/CC/CC-server           && uv run uvicorn main:app --port 8001
cd app/CRM/CRM-server         && uv run uvicorn main:app --port 8002
cd app/Billing/Billing-server && uv run uvicorn main:app --port 8003

# 3. Start frontend GUIs (4 terminals)
cd app/CC/CC-client       && npm run dev
cd app/CC/CC-gui          && npm run dev
cd app/CRM/CRM-gui        && npm run dev
cd app/Billing/Billing-gui && npm run dev
```

> In manual mode, `crm-server` reads `OLLAMA_BASE_URL` from environment (default: `http://localhost:11434`). No override needed for localhost startup.

---

## Development Guidelines

1. **Define the Agent Card first**, then implement Skill logic — contract before code
2. **CC-server is the sole orchestration entry point** — all business flow changes go through CC-server only
3. **Each GUI connects only to its own subsystem server** — no direct cross-subsystem calls from the frontend
4. **Each Skill must have its own Pydantic Input/Output Schema**
5. **Use `httpx.AsyncClient` for all A2A calls** — synchronous `requests` is forbidden
