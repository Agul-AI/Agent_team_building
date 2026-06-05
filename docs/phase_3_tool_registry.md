# Phase 3: Tool Registry and Permission Layer

Phase 3 adds a manifest-only tool layer. It can register tool manifests and make
authorization decisions, but it **does not execute tools**.

## Scope

Implemented:

- `ToolManifest`: normalized runtime-facing view of a declared team-spec tool.
- `ToolCallRequest`: proposed tool-call request with purpose, agent id, permissions, and optional human approval id.
- `AuthorizationDecision`: structured outcome for a proposed tool call.
- `ToolRegistry`: manifest registry with agent allowlist enforcement.
- Registry construction from `TeamSpec` tool declarations.
- Permission checks for required tool permissions.
- Approval checks for critical/high-impact tools.
- Disabled tool blocking.
- Unknown tool blocking.

Not implemented:

- Actual tool execution.
- Tool adapters for web, code, databases, APIs, brokerages, booking, or email.
- Human approval queue UI/API.
- Sandbox execution.
- Rate-limit enforcement.
- Secret resolution.
- Tool-call audit persistence.

## Authorization outcomes

| Status | Meaning |
|---|---|
| `allowed` | The call is authorized in manifest-only mode. Nothing is executed. |
| `requires_human_approval` | The tool is enabled and allowed for the agent, but needs explicit approval. |
| `blocked` | The tool is unknown, disabled, not allowed for the agent, or missing permissions. |

## Rules

1. Unknown tools are blocked.
2. Disabled tools are blocked even if approval is supplied.
3. Agents can only request tools listed in their `allowed_tools`.
4. Tool manifest permissions must be present in the request permissions.
5. Critical and high-impact enabled tools require human approval.
6. Claimed approval must include an `approval_id` for traceability.

## Example

```python
from team_factory.specs.loader import load_team_spec
from team_factory.tools import ToolCallRequest, ToolRegistry

spec = load_team_spec("team_specs/travel_planning_team.yaml")
registry = ToolRegistry.from_team_spec(spec)
request = ToolCallRequest(
    tool_id="web_search",
    agent_id="destination_researcher",
    purpose="Research museum opening hours.",
)
decision = registry.authorize(request)
print(decision.status)
```

## Future Phase 3+ extensions

- Add tool-call audit events.
- Add approval queue primitives.
- Add sandbox policy objects.
- Add actual low-risk built-in calculator execution only after manifest-only behavior is stable.
- Add CLI command to inspect team tool permissions.
