## ADDED Requirements

### Requirement: Product order creation
The Order Agent SHALL expose a `create_order` skill at `POST /order/a2a` that accepts `customer_id` and `offer_id` and creates a product order in SQLite. The response SHALL include `order_id` (TMF622 ProductOrder.id), `state` (initial value `"acknowledged"`), and `order_date` (ISO 8601).

#### Scenario: Successful order creation
- **WHEN** CC-server sends `tasks/send` to Order Agent with `skill=create_order` and `input={ "customer_id": "cust_001", "offer_id": "po_001" }`
- **THEN** CRM-server persists the order to SQLite and returns `{ "order_id": "...", "state": "acknowledged", "order_date": "..." }`

#### Scenario: Order with invalid customer
- **WHEN** CC-server sends `tasks/send` to Order Agent with `skill=create_order` and a `customer_id` that does not exist
- **THEN** CRM-server returns JSON-RPC error with code `-32001` and message `"Customer not found"`

#### Scenario: Order with invalid offering
- **WHEN** CC-server sends `tasks/send` to Order Agent with `skill=create_order` and an `offer_id` that does not exist in the catalog
- **THEN** CRM-server returns JSON-RPC error with code `-32001` and message `"ProductOffering not found"`

### Requirement: Order Agent Card
The Order Agent SHALL serve an Agent Card at `GET /order/.well-known/agent.json` describing the `create_order` skill, registered via the `a2a-python` SDK.

#### Scenario: Agent Card is accessible
- **WHEN** a client sends `GET /order/.well-known/agent.json`
- **THEN** the response SHALL be a valid Agent Card JSON with `skills` listing `create_order`
