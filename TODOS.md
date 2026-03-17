# TODOS

## Refactor CC-server directory to match AGENTS.md convention

**What:** Restructure `app/CC/CC-server/src/` from flat `src/<agent>/` to `src/agents/<name>/skills/<skill>.py` per AGENTS.md.

**Why:** CRM-server (and future Billing-server) follows AGENTS.md convention with `src/agents/` parent and `skills/` subdirectories. CC-server was built before the convention was finalized and uses a flat layout, creating inconsistency across subsystems.

**Pros:** All three subsystem servers share the same directory structure. Easier to navigate and onboard.

**Cons:** Touches shipped, working code. Risk of import path regressions. No functional change.

**Context:** CC-server has `src/communication/agent.py` + `src/communication/models.py`. The AGENTS.md convention is `src/agents/communication/agent.py` + `src/agents/communication/models.py` + `src/agents/communication/skills/send_notification.py`. Best done when Billing-server ships, to align all three at once.

**Depends on / blocked by:** None. Can be done anytime after CRM-server ships.

---

## Update CRM spec error handling language

**What:** Replace references to "JSON-RPC error code -32001" in `openspec/specs/CRM/spec.md` scenarios with `TaskState.failed` + message string convention.

**Why:** The a2a-python SDK reserves `-32001` for protocol-level `TaskNotFoundError`. CRM domain errors (customer not found, model not found, etc.) are signaled via `TaskState.failed` with a descriptive message string, which CC-server's client already parses correctly. The spec's current language implies raw JSON-RPC error codes that won't actually appear on the wire.

**Pros:** Spec matches implementation reality. Prevents confusion for future implementers or AI agents implementing from spec.

**Cons:** Editorial work only, no functional impact. Spec is "close enough" for current use.

**Context:** Discovered during /plan-eng-review of implement-crm-server change (2026-03-17). CC-server's `src/a2a_client/client.py` catches `TaskState.failed` and wraps it as `A2AError(code=-32000)`. The spec should document this pattern.

**Depends on / blocked by:** None. Can be done before or after CRM-server implementation.
