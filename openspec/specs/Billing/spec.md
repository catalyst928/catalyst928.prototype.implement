# Billing Spec

## Overview

The Billing subsystem is a single FastAPI process (port 8003) hosting one named agent: **Usage Agent**. It exposes one A2A Skill consumed exclusively by CC-server. Billing-gui provides a read-only bill details view connected only to Billing-server.

| Agent | Route Prefix | Skill | TMF API |
|---|---|---|---|
| **Usage Agent** | `/usage` | `query_bill` | TMF677, TMF678 |

**TMForum API coverage:** TMF677 – Usage Consumption Management · TMF678 – Customer Bill Management (reference only)

---

## TMForum Field Mapping

### Skill: `query_bill` — TMF677 Usage Consumption Management

| Skill Field | TMF API | TMF Resource / Field |
|---|---|---|
| `customer_id` (input) | TMF677 | `UsageConsumption.relatedParty[role=customer].id` |
| `bucket_balance` | TMF677 | `UsageConsumption.bucket[usageType=balance].remainingValue.amount` |
| `bucket_balance_unit` | TMF677 | `UsageConsumption.bucket[usageType=balance].remainingValue.units` |
| `plan_usage_pct` | TMF677 | Derived: `bucket[usageType=data].usageValue / bucket[usageType=data].validFor.totalValue × 100` |
| `due_date` | TMF678 | `CustomerBill.paymentDueDate` (ISO 8601 date) |
| `bill_amount` | TMF678 | `CustomerBill.amountDue.value` |
| `bill_amount_unit` | TMF678 | `CustomerBill.amountDue.unit` |

> **Note:** `due_date`, `bill_amount`, and `bill_amount_unit` are sourced from TMF678 Customer Bill Management semantics. TMF677 covers usage buckets and consumption data; the full billing lifecycle belongs to TMF678. In this demo both are served from the same `query_bill` skill for simplicity.

---

## Requirements

### General
- The system SHALL run as a single FastAPI process on port 8003
- The Usage Agent SHALL be registered using the `a2a-python` SDK, which handles Agent Card serving (`GET /usage/.well-known/agent.json`) and A2A endpoint (`POST /usage/a2a`) with JSON-RPC 2.0 dispatch automatically
- Do NOT manually implement JSON-RPC dispatch, Agent Card endpoints, or A2A request routing — import and use `a2a-python` SDK
- The system SHALL return standard JSON-RPC error objects on all error conditions (via `a2a-python` SDK error utilities)
- The system SHALL enable CORS on all endpoints to allow local GUI access
- The system SHALL NOT call CC-server or CRM-server directly
- Dependencies SHALL be managed via `uv` + `pyproject.toml` (including `a2a-python` as a dependency)

### Usage Agent (`/usage`) — Skill: `query_bill`
- The system SHALL return the current bill summary for a given `customer_id`
- The response SHALL include:
  - `bucket_balance` — remaining account balance (TMF677 `bucket.remainingValue.amount`)
  - `bucket_balance_unit` — currency unit (TMF677 `bucket.remainingValue.units`, e.g. `"EUR"`)
  - `due_date` — bill payment due date in `YYYY-MM-DD` format (TMF678 `CustomerBill.paymentDueDate`)
  - `bill_amount` — total bill amount for current period (TMF678 `CustomerBill.amountDue.value`)
  - `bill_amount_unit` — currency unit (TMF678 `CustomerBill.amountDue.unit`, e.g. `"EUR"`)
  - `plan_usage_pct` — plan data usage percentage, integer `0–100` (TMF677 derived)
- `due_date` SHALL be an ISO 8601 date string (`YYYY-MM-DD`)
- `plan_usage_pct` SHALL be a number between `0` and `100`
- The system SHALL return error code `-32001` with message `"Customer not found"` if no bill record exists for the given `customer_id`
- Bill data SHALL be stored in SQLite, initialized by `seed.py` at startup

### Billing-gui
- The GUI SHALL connect only to Billing-server (port 8003)
- The GUI SHALL display monthly bill details and consumption breakdown
- The GUI SHALL NOT initiate A2A calls or connect to CC-server or CRM-server

### Data & Seeding
- The system SHALL pre-seed bill records for all 3 test customers (A, B, C) covering different balance and usage states
- All seed data SHALL be loaded via `seed.py` on service startup

---

## Data Model

### SQLite Database (Billing-server)

#### `bills` table
| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT PRIMARY KEY | Bill record ID |
| `customer_id` | TEXT UNIQUE | FK reference to customer |
| `bucket_balance` | REAL | Remaining account balance (TMF677 `bucket[usageType=balance].remainingValue.amount`) |
| `bucket_balance_unit` | TEXT | Currency unit (e.g. `EUR`) |
| `due_date` | TEXT | Payment due date (`YYYY-MM-DD`, TMF678 `CustomerBill.paymentDueDate`) |
| `bill_amount` | REAL | Total bill amount due (TMF678 `CustomerBill.amountDue.value`) |
| `bill_amount_unit` | TEXT | Currency unit (e.g. `EUR`) |
| `plan_usage_pct` | INTEGER | Data usage percentage `0–100` (TMF677 derived) |

> **Note:** `plan_usage_pct` is stored directly in the `bills` table for simplicity. In a production TMF677 implementation this would be derived from usage bucket data.

---

## Scenarios

### Scenario: Query bill for existing customer
- Given: Customer A is seeded with a bill record
- When: CC-server sends `tasks/send` to **Usage Agent** (`POST /usage/a2a`) with `skill=query_bill`, `input={ "customer_id": "cust_A" }`
- Then: Billing-server returns:
  ```json
  {
    "bucket_balance": 35.50,
    "bucket_balance_unit": "EUR",
    "due_date": "2026-04-05",
    "bill_amount": 99.00,
    "bill_amount_unit": "EUR",
    "plan_usage_pct": 72
  }
  ```

### Scenario: Query bill for non-existent customer
- Given: No bill record exists for `customer_id` `"cust_999"`
- When: CC-server sends `tasks/send` to **Usage Agent** with `skill=query_bill`, `input={ "customer_id": "cust_999" }`
- Then: Billing-server returns JSON-RPC error `{ "code": -32001, "message": "Customer not found" }`

### Scenario: Billing-gui loads bill details
- Given: Billing-server is running and seeded
- When: A user opens Billing-gui and selects a customer
- Then: The GUI displays `bucket_balance`, `due_date`, `plan_usage_pct`, `bill_amount`, and `bill_amount_unit` fetched from Billing-server

---

## A2A Skill Schemas

### `query_bill`
```json
{
  "inputSchema": {
    "type": "object",
    "properties": {
      "customer_id": { "type": "string", "description": "TMF677 UsageConsumption.relatedParty[role=customer].id" }
    },
    "required": ["customer_id"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "bucket_balance":      { "type": "number", "description": "TMF677 UsageConsumption.bucket[usageType=balance].remainingValue.amount" },
      "bucket_balance_unit": { "type": "string", "description": "TMF677 bucket.remainingValue.units (e.g. EUR)" },
      "due_date":            { "type": "string", "format": "date",      "description": "TMF678 CustomerBill.paymentDueDate (YYYY-MM-DD)" },
      "bill_amount":         { "type": "number", "description": "TMF678 CustomerBill.amountDue.value" },
      "bill_amount_unit":    { "type": "string", "description": "TMF678 CustomerBill.amountDue.unit (e.g. EUR)" },
      "plan_usage_pct":      { "type": "number", "minimum": 0, "maximum": 100, "description": "TMF677 derived: data bucket usage percentage" }
    },
    "required": ["bucket_balance", "bucket_balance_unit", "due_date", "bill_amount", "bill_amount_unit", "plan_usage_pct"]
  }
}
```

---

## Port & Service Reference

| Module | Port | Agent Endpoints |
|---|---|---|
| Billing-server | 8003 | `/usage/a2a` |
| Billing-gui | 5175 | — |

| Agent | Agent Card | A2A Endpoint |
|---|---|---|
| Usage Agent | `GET /usage/.well-known/agent.json` | `POST /usage/a2a` |
