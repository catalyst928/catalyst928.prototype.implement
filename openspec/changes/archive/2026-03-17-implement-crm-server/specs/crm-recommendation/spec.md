## ADDED Requirements

### Requirement: LLM-powered next-best-offer recommendations
The Recommendation Agent SHALL expose a `get_nbo` skill at `POST /recommendation/a2a` that accepts a `customer_id` and returns a TMF701 Recommendation object. The system SHALL call Ollama asynchronously via `httpx.AsyncClient` with `timeout=30.0` to generate personalized product recommendations based on the customer profile and product catalog.

#### Scenario: NBO with Ollama available
- **WHEN** CC-server sends `tasks/send` to Recommendation Agent with `skill=get_nbo` and `input={ "customer_id": "cust_001" }`, and Ollama is reachable
- **THEN** CRM-server calls `POST {OLLAMA_BASE_URL}/api/generate` with the prompt template containing the customer profile and offering catalog, parses the response, and returns a TMF701 Recommendation with `id` and `recommendation_item[]` ordered by priority ascending

#### Scenario: NBO with Ollama unavailable (fallback)
- **WHEN** CC-server sends `tasks/send` to Recommendation Agent with `skill=get_nbo` and `input={ "customer_id": "cust_001" }`, but Ollama is unreachable
- **THEN** CRM-server logs a warning and returns all eligible offerings ordered by price ascending as the recommendation, with no error surfaced to the caller

#### Scenario: NBO with hallucinated offering IDs from Ollama
- **WHEN** Ollama returns offering IDs that do not exist in the `product_offerings` table
- **THEN** CRM-server SHALL fall back to price-sorted offerings, ensuring `recommendation_item[]` always contains at least one item

#### Scenario: NBO for non-existent customer
- **WHEN** CC-server sends `tasks/send` to Recommendation Agent with `skill=get_nbo` and an invalid `customer_id`
- **THEN** CRM-server returns JSON-RPC error with code `-32001` and message `"Customer not found"`

### Requirement: TMF637 inventory exclusion
The system SHALL filter out any product offering that matches the customer's currently subscribed product (`product_name`) from the recommendation results, both in the LLM path and the fallback path.

#### Scenario: Current plan excluded from recommendations
- **WHEN** Customer A (subscribed to Plan-50G) requests NBO
- **THEN** the returned `recommendation_item[]` SHALL NOT contain the offering corresponding to Plan-50G

### Requirement: Recommendation Agent Card
The Recommendation Agent SHALL serve an Agent Card at `GET /recommendation/.well-known/agent.json` describing the `get_nbo` skill, registered via the `a2a-python` SDK.

#### Scenario: Agent Card is accessible
- **WHEN** a client sends `GET /recommendation/.well-known/agent.json`
- **THEN** the response SHALL be a valid Agent Card JSON with `skills` listing `get_nbo`

### Requirement: Ollama configuration via environment variables
The system SHALL read `OLLAMA_BASE_URL` (default: `http://localhost:11434`) and `OLLAMA_MODEL` (default: `qwen2.5:7b`) from environment variables. The system SHALL log resolved values at startup and SHALL NOT fail startup if Ollama is unreachable.

#### Scenario: Ollama config logged at startup
- **WHEN** CRM-server starts
- **THEN** the resolved `OLLAMA_BASE_URL` and `OLLAMA_MODEL` values are logged

### Requirement: Seeded product offering data
The system SHALL pre-seed at least three product offerings in the `product_offerings` table with `id`, `name`, `description`, `price` (EUR), and `price_unit` fields.

#### Scenario: Product offerings available on startup
- **WHEN** CRM-server starts
- **THEN** the `product_offerings` table contains at least three seeded records used for NBO prompt construction and fallback
