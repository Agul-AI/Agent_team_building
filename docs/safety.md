# Safety and Compliance

## Current Phase 1 guarantees

The spec validator enforces:

- stopping criteria for every workflow
- approval requirements for enabled critical tools
- approval requirements for enabled high-impact tools
- high-impact actions mirrored in human-review gates

## Future guardrails

- Tool-call authorization layer.
- Human approval queue.
- PII redaction.
- Domain-specific policy packs.
- Financial research-only mode by default.
- Audit logs for all tool calls and approvals.


## Phase 3 permission-layer guarantees

The manifest-only tool registry enforces:

- unknown tools are blocked
- disabled tools are blocked
- agent tool allowlists are enforced
- manifest permissions must be granted by the request
- critical/high-impact tools require human approval
- claimed approval requires a traceable approval id

No tool execution is implemented in Phase 3.
