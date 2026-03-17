## ADDED Requirements

### Requirement: AI model status query
The AI Management Agent SHALL expose a `get_ai_model_status` skill at `POST /ai-management/a2a` that accepts a `model_id` and returns the model's current status from SQLite. The response SHALL include `model_id`, `model_name`, `version`, `status` (TMF915 lifecycleStatus: `active` | `inactive` | `training`), `accuracy_score` (0.0–1.0), and `last_updated` (ISO 8601).

#### Scenario: Active model status query
- **WHEN** CC-server sends `tasks/send` to AI Management Agent with `skill=get_ai_model_status` and `input={ "model_id": "qwen2.5_7b" }`
- **THEN** CRM-server returns `{ "model_id": "qwen2.5_7b", "model_name": "qwen2.5:7b", "version": "7b", "status": "active", "accuracy_score": 0.87, "last_updated": "..." }`

#### Scenario: Inactive model triggers fallback awareness
- **WHEN** CC-server sends `tasks/send` to AI Management Agent with `skill=get_ai_model_status` and the model has `status: "inactive"`
- **THEN** CRM-server returns the model record with `status: "inactive"`, enabling CC-server to set `nbo_fallback=true`

#### Scenario: Unknown model ID
- **WHEN** CC-server sends `tasks/send` to AI Management Agent with `skill=get_ai_model_status` and `input={ "model_id": "unknown_model" }`
- **THEN** CRM-server returns JSON-RPC error with code `-32001` and message `"AIModel not found"`

### Requirement: AI Management Agent Card
The AI Management Agent SHALL serve an Agent Card at `GET /ai-management/.well-known/agent.json` describing the `get_ai_model_status` skill, registered via the `a2a-python` SDK.

#### Scenario: Agent Card is accessible
- **WHEN** a client sends `GET /ai-management/.well-known/agent.json`
- **THEN** the response SHALL be a valid Agent Card JSON with `skills` listing `get_ai_model_status`

### Requirement: Seeded AI model data
The system SHALL pre-seed one AI model record corresponding to the Ollama `qwen2.5:7b` model in the `ai_models` table at startup.

#### Scenario: AI model data available on startup
- **WHEN** CRM-server starts
- **THEN** the `ai_models` table contains a record with `model_id: "qwen2.5_7b"`, `model_name: "qwen2.5:7b"`, `status: "active"`
