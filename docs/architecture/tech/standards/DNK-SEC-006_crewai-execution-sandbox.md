# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/standards/DNK-SEC-006_crewai-execution-sandbox.md"
# purpose: "Security Standards and Sandbox Egress Controls for crewAI-style Orchestrations"
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

# 🛡️ Security Standards: crewAI Sandbox Execution (DNK-SEC-006)

This specification defines the security standards, resource limits, and sandbox boundaries for executing crewAI-style role-playing multi-agent workflows inside the DNK OS Core.

## 1. Sandbox Boundaries & Agent Limits

Because crewAI orchestrates multiple cooperative agents, the system introduces higher concurrency and communication volumes. Execution must adhere to these boundaries:
- **Maximum Concurrent Agents:** A single Crew can run at most `5` concurrent agents to prevent container resource exhaustion.
- **Maximum Task Depth:** The sequence of tasks in a single Crew cannot exceed `10` sequential steps.

## 2. Resource Constraints & Timeout Gates

- **Execution Timeout:** The total execution time of a `Crew.kickoff()` pipeline is capped at `300s` (5 minutes). Individual task executions are capped at `120s`.
- **Memory Caps:** Sandboxed containers running crewAI tasks must be locked to a maximum of `512MB` RAM.
- **API Call Restrictions:** A single crew execution is allowed a maximum of `50` LLM API requests. If this is exceeded, a `QuotaExceededError` is raised.

## 3. Comparison with LangGraph Sandbox (DNK-SEC-005)

- **State vs Context:** LangGraph (DNK-SEC-005) manages a complex global shared state, which requires transition-level validation. crewAI manages linear context handoffs, which requires strict output parsing validation at task handoff boundaries.
- **Egress:** Both frameworks enforce full network-drop constraints, routing strictly to whitelisted and cryptographically signed local MCP servers.

## 4. Key Recommendations

1. **Output Sanitation:** Tasks returning JSON or code blocks must run through a validation schema checker before context is passed to the next agent in the sequence.
2. **Task Start Gates:** Any crew task involving host filesystem mutations or tool executions must trigger a Maksym approval token.
