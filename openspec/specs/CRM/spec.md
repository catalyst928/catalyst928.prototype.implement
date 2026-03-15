# CRM Spec

## Overview

The CRM subsystem is a single FastAPI process (port 8002) hosting four named A2A agents, each with its own Agent Card and route prefix. All agents are consumed exclusively by CC-server. CRM-gui provides a read-only Customer 360 view connected only to CRM-server.

| Agent | Route Prefix | Skill | TMF API |
|---|---|---|---|
| **Profiling Agent** | `/profiling` | `query_customer`, `verify_identity` | TMF629, TMF637, TMF720 |
| **Recommendation Agent** | `/recommendation` | `get_nbo` | TMF701, TMF620, TMF637 |
| **Order Agent** | `/order` | `create_order` | TMF622 |
| **AI Management Agent** | `/ai-management` | `get_ai_model_status` | TMF915 |

**TMForum API coverage:** TMF629 – Customer Management · TMF701 – Recommendation API · TMF620 – Product Catalog Management · TMF637 – Product Inventory Management · TMF622 – Product Order Management · TMF720 – Digital Identity Management · TMF915 – AI Management

---

## TMForum Field Mapping

### Skill: `query_customer` — TMF629 Customer Management

| Skill Field | TMF629 Resource | TMF629 Field |
|---|---|---|
| `phone` (input) | `Customer.contactMedium[]` | `contactMedium[type=phone].characteristic.phoneNumber` |
| `customer_id` | `Customer` | `Customer.id` |
| `name` | `Customer` | `Customer.name` |
| `customer_category` | `Customer` | `Customer.customerCategory` |
| `product_name` | `Product` (TMF637) | `Product.name` (currently subscribed product) |

### Skill: `get_nbo` — TMF701 Recommendation API (+ TMF620 + TMF637)

| Skill Field | TMF Resource | TMF Field |
|---|---|---|
| `customer_id` (input) | TMF701 `Recommendation` | `Recommendation.relatedParty[role=customer].id` |
| `id` (output) | TMF701 `Recommendation` | `Recommendation.id` |
| `recommendation_item[]` | TMF701 `Recommendation` | `Recommendation.recommendationItem[]` |
| `recommendation_item[].id` | TMF701 `RecommendationItem` | `RecommendationItem.id` |
| `recommendation_item[].priority` | TMF701 `RecommendationItem` | `RecommendationItem.priority` (integer, 1 = highest) |
| `recommendation_item[].offering_id` | TMF620 `ProductOffering` | `ProductOffering.id` (via `RecommendationItem.productOffering.id`) |
| `recommendation_item[].name` | TMF620 `ProductOffering` | `ProductOffering.name` |
| `recommendation_item[].description` | TMF620 `ProductOffering` | `ProductOffering.description` |
| `recommendation_item[].price` | TMF620 `ProductOfferingPrice` | `ProductOffering.productOfferingPrice[0].price.value` |
| `recommendation_item[].price_unit` | TMF620 `ProductOfferingPrice` | `ProductOffering.productOfferingPrice[0].price.unit` |

> TMF637 Product Inventory is used internally to filter out offerings the customer already subscribes to; it does not appear in the skill output.

### Skill: `create_order` — TMF622 Product Order Management

| Skill Field | TMF622 Resource | TMF622 Field |
|---|---|---|
| `customer_id` (input) | `ProductOrder` | `ProductOrder.relatedParty[role=customer].id` |
| `offer_id` (input) | `ProductOrderItem` | `ProductOrder.productOrderItem[0].productOffering.id` |
| `order_id` | `ProductOrder` | `ProductOrder.id` |
| `state` | `ProductOrder` | `ProductOrder.state` (enum: `acknowledged` → `inProgress` → `completed`) |
| `order_date` | `ProductOrder` | `ProductOrder.orderDate` (ISO 8601) |

### Skill: `verify_identity` — TMF720 Digital Identity Management

| Skill Field | TMF720 Resource | TMF720 Field |
|---|---|---|
| `customer_id` (input) | `DigitalIdentity` | `DigitalIdentity.relatedParty[role=customer].id` |
| `verification_method` (input) | `DigitalIdentity` | `DigitalIdentity.identityType` (enum: `otp`, `biometric`, `knowledge`) |
| `identity_id` | `DigitalIdentity` | `DigitalIdentity.id` |
| `verified` | `DigitalIdentity` | `DigitalIdentity.status` mapped to boolean (`active` → `true`, else `false`) |
| `confidence_score` | `DigitalIdentity` | `DigitalIdentity.characteristic[name=confidence].value` (0.0–1.0) |
| `verified_at` | `DigitalIdentity` | `DigitalIdentity.validFor.startDateTime` (ISO 8601) |

### Skill: `get_ai_model_status` — TMF915 AI Management

| Skill Field | TMF915 Resource | TMF915 Field |
|---|---|---|
| `model_id` (input) | `AIModel` | `AIModel.id` |
| `model_id` (output) | `AIModel` | `AIModel.id` |
| `model_name` | `AIModel` | `AIModel.name` |
| `version` | `AIModel` | `AIModel.version` |
| `status` | `AIModel` | `AIModel.lifecycleStatus` (enum: `active`, `inactive`, `training`) |
| `accuracy_score` | `AIModel` | `AIModel.characteristic[name=accuracy].value` (0.0–1.0) |
| `last_updated` | `AIModel` | `AIModel.lastUpdate` (ISO 8601) |

---

## Requirements

### General
- The system SHALL run as a single FastAPI process on port 8002
- Each agent router SHALL be mounted at its respective prefix (`/profiling`, `/recommendation`, `/order`)
- Each agent SHALL expose its own Agent Card at `GET /<prefix>/.well-known/agent.json`
- Each agent SHALL accept A2A requests at `POST /<prefix>/a2a` using JSON-RPC 2.0 format
- All agents SHALL return standard JSON-RPC error objects on all error conditions
- The system SHALL enable CORS on all endpoints to allow local GUI access
- The system SHALL NOT call CC-server or Billing-server directly

### Profiling Agent (`/profiling`) — Skills: `query_customer`, `verify_identity`

#### Skill: `query_customer`
- The system SHALL look up a customer record by phone number
- The system SHALL return `customer_id` (TMF629 `Customer.id`), `name` (TMF629 `Customer.name`), `customer_category` (TMF629 `Customer.customerCategory`), and `product_name` (TMF637 `Product.name`) on success
- The system SHALL return error code `-32001` with message `"Customer not found"` if no match exists
- The system SHALL store customer data in SQLite, initialized by `seed.py` at startup

#### Skill: `verify_identity`
- The system SHALL verify a customer's digital identity given a `customer_id` and `verification_method`
- The system SHALL return `identity_id` (TMF720 `DigitalIdentity.id`), `verified` (boolean), `confidence_score` (0.0–1.0), and `verified_at` (ISO 8601) on success
- The `verified` field SHALL be `true` only when the identity check passes (simulated in demo via seeded verification status per customer)
- The system SHALL return error code `-32001` if `customer_id` does not exist
- Supported `verification_method` values: `otp`, `biometric`, `knowledge`
- The system SHALL store identity verification records in SQLite and initialize seed data via `seed.py`

### Recommendation Agent (`/recommendation`) — Skill: `get_nbo`

> **Implementation note:** This agent uses an **LLM (Ollama) async call** to generate personalized NBO recommendations. The LLM ranks and selects from the seeded `ProductOffering` pool based on the customer's profile. All Ollama calls MUST be made with `httpx.AsyncClient` (no blocking I/O).

- The system SHALL return a TMF701 `Recommendation` object for a given `customer_id`
- The response SHALL include a top-level `id` (TMF701 `Recommendation.id`) and a `recommendation_item[]` array
- Each item SHALL include `id` (TMF701 `RecommendationItem.id`), `priority` (integer, 1 = highest priority), `offering_id` (TMF620 `ProductOffering.id`), `name`, `description`, `price`, and `price_unit`
- Items SHALL be ordered by `priority` ascending (priority 1 first)
- The system SHALL return at least one item for any valid `customer_id`
- The system SHALL return error code `-32001` if the `customer_id` does not exist

#### LLM Integration (Ollama)
- The system SHALL call Ollama at `http://localhost:11434/api/generate` (configurable via env var `OLLAMA_BASE_URL`)
- The system SHALL use model `qwen2.5:7b` by default (configurable via env var `OLLAMA_MODEL`)
- The Ollama call MUST be made asynchronously using `httpx.AsyncClient` with `timeout=30.0`
- The system SHALL construct a prompt containing:
  - The full `ProductOffering` catalog (id, name, description, price, price_unit) from SQLite
  - The customer's profile (`customer_id`, `customer_category`, `product_name` — current subscription)
  - An instruction to rank and return at most 3 offerings as a JSON array, ordered by suitability
- The system SHALL request `"stream": false` from Ollama and parse the `response` field as JSON
- The system SHALL extract a JSON array from the LLM response using a regex fallback if the response contains extra prose
- The system SHALL filter out any `offering_id` that matches the customer's currently subscribed product (TMF637 inventory exclusion)
- **Fallback:** If the Ollama call fails (connection error, timeout, or unparseable response), the system SHALL fall back to returning all eligible offerings ordered by price ascending, and SHALL log a warning
- The system SHALL NOT expose Ollama errors to the A2A caller; all errors surface as the fallback result or as a `-32001` error only when `customer_id` is invalid

#### Prompt Template
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

### Order Agent (`/order`) — Skill: `create_order`
- The system SHALL create a product order for a given `customer_id` and `offer_id`
- The system SHALL return `order_id` (TMF622 `ProductOrder.id`), `state` (TMF622 `ProductOrder.state`), and `order_date` (TMF622 `ProductOrder.orderDate`) on success
- The initial `state` SHALL be `"acknowledged"` per TMF622 ProductOrder state machine
- The system SHALL return error code `-32001` if `customer_id` or `offer_id` does not exist
- The system SHALL persist the order to SQLite

### AI Management Agent (`/ai-management`) — Skill: `get_ai_model_status`
- The system SHALL return the current status of the NBO AI model given a `model_id`
- The system SHALL return `model_id`, `model_name`, `version`, `status` (TMF915 `AIModel.lifecycleStatus`), `accuracy_score`, and `last_updated` on success
- The `status` field SHALL be one of: `active`, `inactive`, `training`
- The demo SHALL pre-seed one AI model record corresponding to the Ollama `qwen2.5:7b` model used by the Recommendation Agent
- The system SHALL return error code `-32001` if `model_id` does not exist
- The system SHALL store AI model records in SQLite and initialize seed data via `seed.py`

### CRM-gui
- The GUI SHALL connect only to CRM-server (port 8002)
- The GUI SHALL display a Customer 360 view: customer profile and order history
- The GUI SHALL NOT initiate A2A calls or connect to CC-server or Billing-server

### Ollama Configuration
- `OLLAMA_BASE_URL` (env, default: `http://localhost:11434`) — base URL of the Ollama service
- `OLLAMA_MODEL` (env, default: `qwen2.5:7b`) — model name passed in the generate request
- The system SHALL log the resolved `OLLAMA_BASE_URL` and `OLLAMA_MODEL` at startup
- The system SHALL NOT fail startup if Ollama is unreachable; the fallback path handles runtime unavailability

### Data & Seeding
- The system SHALL pre-seed 3 test customers (A, B, C) covering different `customer_category` and `product_name` values
- The system SHALL pre-seed an NBO recommendation pool of at least 3 `ProductOffering` options
- `ProductOffering` seed data SHALL include `id`, `name`, `description`, `price`, `price_unit` fields — these are passed verbatim in the Ollama prompt
- All seed data SHALL be loaded via `seed.py` on service startup

---

## Scenarios

### Scenario: Query existing customer by phone
- Given: Customer A is seeded with phone `"13800000001"`
- When: CC-server sends `tasks/send` to **Profiling Agent** (`POST /profiling/a2a`) with `skill=query_customer`, `input={ "phone": "13800000001" }`
- Then: CRM-server returns `{ "customer_id": "...", "name": "...", "customer_category": "gold", "product_name": "Plan-50G" }`

### Scenario: Query non-existent customer
- Given: No customer exists with phone `"00000000000"`
- When: CC-server sends `tasks/send` to **Profiling Agent** with `skill=query_customer`, `input={ "phone": "00000000000" }`
- Then: CRM-server returns JSON-RPC error `{ "code": -32001, "message": "Customer not found" }`

### Scenario: Get NBO recommendations (LLM path — Ollama available)
- Given: Customer A exists, Ollama is reachable and returns a valid JSON array
- When: CC-server sends `tasks/send` to **Recommendation Agent** (`POST /recommendation/a2a`) with `skill=get_nbo`, `input={ "customer_id": "..." }`
- Then: CRM-server sends an async `POST http://localhost:11434/api/generate` with the customer profile + offering catalog prompt, parses the LLM response into an ordered offering list, and returns a TMF701 `Recommendation`:
  ```json
  {
    "id": "rec_001",
    "recommendation_item": [
      { "id": "ri_001", "priority": 1, "offering_id": "po_002", "name": "Plan-200G", "description": "...", "price": 199.0, "price_unit": "EUR" },
      { "id": "ri_002", "priority": 2, "offering_id": "po_003", "name": "Plan-500G", "description": "...", "price": 299.0, "price_unit": "EUR" }
    ]
  }
  ```

### Scenario: Get NBO recommendations (fallback path — Ollama unavailable)
- Given: Customer A exists, but Ollama is unreachable (connection refused or timeout)
- When: CC-server sends `tasks/send` to **Recommendation Agent** with `skill=get_nbo`, `input={ "customer_id": "..." }`
- Then: CRM-server logs a warning, falls back to returning all eligible offerings ordered by price ascending, and returns a valid TMF701 `Recommendation` (no error surfaced to caller)

### Scenario: Place an order
- Given: Customer A exists and offer `"po_001"` is in the ProductOffering pool
- When: CC-server sends `tasks/send` to **Order Agent** (`POST /order/a2a`) with `skill=create_order`, `input={ "customer_id": "...", "offer_id": "po_001" }`
- Then: CRM-server returns `{ "order_id": "...", "state": "acknowledged", "order_date": "2026-03-14T10:00:00Z" }`

### Scenario: Place order with invalid offer
- Given: Customer A exists but `"po_999"` does not exist in the catalog
- When: CC-server sends `tasks/send` to **Order Agent** with `skill=create_order`, `input={ "customer_id": "...", "offer_id": "po_999" }`
- Then: CRM-server returns JSON-RPC error `{ "code": -32001, "message": "ProductOffering not found" }`

### Scenario: Verify customer identity — success
- Given: Customer A is seeded with a passing verification status for method `otp`
- When: CC-server sends `tasks/send` to **Profiling Agent** (`POST /profiling/a2a`) with `skill=verify_identity`, `input={ "customer_id": "...", "verification_method": "otp" }`
- Then: CRM-server returns `{ "identity_id": "...", "verified": true, "confidence_score": 0.95, "verified_at": "2026-03-14T10:00:00Z" }`

### Scenario: Verify customer identity — failure
- Given: Customer A is seeded with a failing verification status (simulated fraud flag)
- When: CC-server sends `tasks/send` to **Profiling Agent** (`POST /profiling/a2a`) with `skill=verify_identity`, `input={ "customer_id": "...", "verification_method": "otp" }`
- Then: CRM-server returns `{ "identity_id": "...", "verified": false, "confidence_score": 0.20, "verified_at": "2026-03-14T10:00:00Z" }`

### Scenario: Verify identity for non-existent customer
- Given: No customer exists with the given `customer_id`
- When: CC-server sends `tasks/send` to **Profiling Agent** (`POST /profiling/a2a`) with `skill=verify_identity`
- Then: CRM-server returns JSON-RPC error `{ "code": -32001, "message": "Customer not found" }`

### Scenario: Get AI model status — model active
- Given: The NBO model is seeded with `status: "active"`
- When: CC-server sends `tasks/send` to **AI Management Agent** (`POST /ai-management/a2a`) with `skill=get_ai_model_status`, `input={ "model_id": "qwen2.5_7b" }`
- Then: CRM-server returns:
  ```json
  { "model_id": "qwen2.5_7b", "model_name": "qwen2.5:7b", "version": "7b", "status": "active", "accuracy_score": 0.87, "last_updated": "2026-03-01T00:00:00Z" }
  ```

### Scenario: Get AI model status — model inactive (triggers fallback)
- Given: The NBO model is seeded with `status: "inactive"`
- When: CC-server sends `tasks/send` to **AI Management Agent** with `skill=get_ai_model_status`, `input={ "model_id": "qwen2.5_7b" }`
- Then: CRM-server returns `{ ..., "status": "inactive", ... }` → CC-server sets `nbo_fallback=true` and requests price-sorted fallback from Recommendation Agent

### Scenario: Get AI model status — unknown model
- Given: No model exists with id `"unknown_model"`
- When: CC-server sends `tasks/send` to **AI Management Agent** with `skill=get_ai_model_status`, `input={ "model_id": "unknown_model" }`
- Then: CRM-server returns JSON-RPC error `{ "code": -32001, "message": "AIModel not found" }`

---

## A2A Skill Schemas

### Profiling Agent — `query_customer`
```json
{
  "inputSchema": {
    "type": "object",
    "properties": {
      "phone": { "type": "string", "description": "Customer phone number (TMF629 contactMedium.characteristic.phoneNumber)" }
    },
    "required": ["phone"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "customer_id":       { "type": "string", "description": "TMF629 Customer.id" },
      "name":              { "type": "string", "description": "TMF629 Customer.name" },
      "customer_category": { "type": "string", "description": "TMF629 Customer.customerCategory (e.g. gold, silver, bronze)" },
      "product_name":      { "type": "string", "description": "TMF637 Product.name — currently subscribed product/plan" }
    },
    "required": ["customer_id", "name", "customer_category", "product_name"]
  }
}
```

### Profiling Agent — `verify_identity`
```json
{
  "inputSchema": {
    "type": "object",
    "properties": {
      "customer_id":          { "type": "string", "description": "TMF720 DigitalIdentity.relatedParty[role=customer].id" },
      "verification_method":  { "type": "string", "description": "Verification method: otp | biometric | knowledge (TMF720 DigitalIdentity.identityType)", "enum": ["otp", "biometric", "knowledge"] }
    },
    "required": ["customer_id", "verification_method"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "identity_id":      { "type": "string",  "description": "TMF720 DigitalIdentity.id" },
      "verified":         { "type": "boolean", "description": "true if identity check passes (TMF720 DigitalIdentity.status == active)" },
      "confidence_score": { "type": "number",  "description": "Confidence score 0.0–1.0 (TMF720 DigitalIdentity.characteristic[name=confidence].value)", "minimum": 0.0, "maximum": 1.0 },
      "verified_at":      { "type": "string",  "description": "TMF720 DigitalIdentity.validFor.startDateTime (ISO 8601)", "format": "date-time" }
    },
    "required": ["identity_id", "verified", "confidence_score", "verified_at"]
  }
}
```

### Recommendation Agent — `get_nbo`
```json
{
  "inputSchema": {
    "type": "object",
    "properties": {
      "customer_id": { "type": "string", "description": "TMF701 Recommendation.relatedParty[role=customer].id" }
    },
    "required": ["customer_id"]
  },
  "outputSchema": {
    "type": "object",
    "description": "TMF701 Recommendation",
    "properties": {
      "id": { "type": "string", "description": "TMF701 Recommendation.id" },
      "recommendation_item": {
        "type": "array",
        "description": "TMF701 Recommendation.recommendationItem[] — ordered by priority ascending",
        "items": {
          "type": "object",
          "properties": {
            "id":           { "type": "string",  "description": "TMF701 RecommendationItem.id" },
            "priority":     { "type": "integer", "description": "TMF701 RecommendationItem.priority (1 = highest)", "minimum": 1 },
            "offering_id":  { "type": "string",  "description": "TMF620 ProductOffering.id (RecommendationItem.productOffering.id)" },
            "name":         { "type": "string",  "description": "TMF620 ProductOffering.name" },
            "description":  { "type": "string",  "description": "TMF620 ProductOffering.description" },
            "price":        { "type": "number",  "description": "TMF620 ProductOffering.productOfferingPrice[0].price.value" },
            "price_unit":   { "type": "string",  "description": "TMF620 ProductOffering.productOfferingPrice[0].price.unit (e.g. EUR)" }
          },
          "required": ["id", "priority", "offering_id", "name", "price", "price_unit"]
        }
      }
    },
    "required": ["id", "recommendation_item"]
  }
}
```

### Order Agent — `create_order`
```json
{
  "inputSchema": {
    "type": "object",
    "properties": {
      "customer_id": { "type": "string", "description": "TMF622 ProductOrder.relatedParty[role=customer].id" },
      "offer_id":    { "type": "string", "description": "TMF622 ProductOrder.productOrderItem[0].productOffering.id" }
    },
    "required": ["customer_id", "offer_id"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "order_id":   { "type": "string",  "description": "TMF622 ProductOrder.id" },
      "state":      { "type": "string",  "description": "TMF622 ProductOrder.state", "enum": ["acknowledged", "inProgress", "completed", "failed", "cancelled"] },
      "order_date": { "type": "string",  "description": "TMF622 ProductOrder.orderDate (ISO 8601)", "format": "date-time" }
    },
    "required": ["order_id", "state", "order_date"]
  }
}
```

### AI Management Agent — `get_ai_model_status`
```json
{
  "inputSchema": {
    "type": "object",
    "properties": {
      "model_id": { "type": "string", "description": "TMF915 AIModel.id — identifier of the AI model to query" }
    },
    "required": ["model_id"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "model_id":       { "type": "string", "description": "TMF915 AIModel.id" },
      "model_name":     { "type": "string", "description": "TMF915 AIModel.name" },
      "version":        { "type": "string", "description": "TMF915 AIModel.version" },
      "status":         { "type": "string", "description": "TMF915 AIModel.lifecycleStatus", "enum": ["active", "inactive", "training"] },
      "accuracy_score": { "type": "number", "description": "TMF915 AIModel.characteristic[name=accuracy].value (0.0–1.0)", "minimum": 0.0, "maximum": 1.0 },
      "last_updated":   { "type": "string", "description": "TMF915 AIModel.lastUpdate (ISO 8601)", "format": "date-time" }
    },
    "required": ["model_id", "model_name", "version", "status", "accuracy_score", "last_updated"]
  }
}
```

---

## Port & Service Reference

| Module | Port | Agent Endpoints |
|---|---|---|
| CRM-server | 8002 | `/profiling/a2a`, `/recommendation/a2a`, `/order/a2a`, `/ai-management/a2a` |
| CRM-gui | 5174 | — |

| Agent | Agent Card | A2A Endpoint | Skills |
|---|---|---|---|
| Profiling Agent | `GET /profiling/.well-known/agent.json` | `POST /profiling/a2a` | `query_customer`, `verify_identity` |
| Recommendation Agent | `GET /recommendation/.well-known/agent.json` | `POST /recommendation/a2a` | `get_nbo` |
| Order Agent | `GET /order/.well-known/agent.json` | `POST /order/a2a` | `create_order` |
| AI Management Agent | `GET /ai-management/.well-known/agent.json` | `POST /ai-management/a2a` | `get_ai_model_status` |
