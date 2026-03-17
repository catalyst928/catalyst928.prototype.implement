## ADDED Requirements

### Requirement: Customer lookup by phone number
The Profiling Agent SHALL expose a `query_customer` skill at `POST /profiling/a2a` that accepts a phone number and returns the matching customer profile from SQLite. The response SHALL include `customer_id` (TMF629 Customer.id), `name` (TMF629 Customer.name), `customer_category` (TMF629 Customer.customerCategory), and `product_name` (TMF637 Product.name).

#### Scenario: Successful customer lookup
- **WHEN** CC-server sends `tasks/send` to Profiling Agent with `skill=query_customer` and `input={ "phone": "13800000001" }`
- **THEN** CRM-server returns `{ "customer_id": "cust_001", "name": "...", "customer_category": "gold", "product_name": "Plan-50G" }`

#### Scenario: Customer not found
- **WHEN** CC-server sends `tasks/send` to Profiling Agent with `skill=query_customer` and `input={ "phone": "00000000000" }`
- **THEN** CRM-server returns JSON-RPC error with code `-32001` and message `"Customer not found"`

### Requirement: Identity verification
The Profiling Agent SHALL expose a `verify_identity` skill at `POST /profiling/a2a` that accepts a `customer_id` and `verification_method` (enum: `otp`, `biometric`, `knowledge`) and returns identity verification results. The response SHALL include `identity_id` (TMF720 DigitalIdentity.id), `verified` (boolean), `confidence_score` (0.0–1.0), and `verified_at` (ISO 8601).

#### Scenario: Identity verification succeeds
- **WHEN** CC-server sends `tasks/send` to Profiling Agent with `skill=verify_identity` and `input={ "customer_id": "cust_001", "verification_method": "otp" }` for a customer with passing verification status
- **THEN** CRM-server returns `{ "identity_id": "...", "verified": true, "confidence_score": 0.95, "verified_at": "..." }`

#### Scenario: Identity verification fails
- **WHEN** CC-server sends `tasks/send` to Profiling Agent with `skill=verify_identity` for a customer with a simulated fraud flag
- **THEN** CRM-server returns `{ "identity_id": "...", "verified": false, "confidence_score": 0.20, "verified_at": "..." }`

#### Scenario: Identity verification for non-existent customer
- **WHEN** CC-server sends `tasks/send` to Profiling Agent with `skill=verify_identity` and an invalid `customer_id`
- **THEN** CRM-server returns JSON-RPC error with code `-32001` and message `"Customer not found"`

### Requirement: Profiling Agent Card
The Profiling Agent SHALL serve an Agent Card at `GET /profiling/.well-known/agent.json` describing both `query_customer` and `verify_identity` skills, registered via the `a2a-python` SDK.

#### Scenario: Agent Card is accessible
- **WHEN** a client sends `GET /profiling/.well-known/agent.json`
- **THEN** the response SHALL be a valid Agent Card JSON with `skills` listing `query_customer` and `verify_identity`

### Requirement: Seeded customer and identity data
The system SHALL pre-seed three test customers (A: phone 13800000001/gold/Plan-50G, B: phone 13800000002/silver/Plan-100G, C: phone 13800000003/bronze/Plan-200G) and corresponding identity verification records in SQLite at startup.

#### Scenario: Seed data available on startup
- **WHEN** CRM-server starts
- **THEN** the `customers` and `identities` tables contain the three pre-seeded records with correct TMF field values
