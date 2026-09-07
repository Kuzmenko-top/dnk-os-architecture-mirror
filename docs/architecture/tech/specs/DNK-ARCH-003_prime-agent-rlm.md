# 🏛️ Architecture Specification: Prime Agent RLM & Harness (DNK-ARCH-003)
## Title: Recursive Language Model (RLM), Continual Harness & Smart Context Compaction
## Status: Active | Version: 1.0.0 | Author: Maxim | License: MIT

This specification implements the canonical RLM and Harness communication, experience accumulation, and context compaction protocol for DNK OS sandboxed agent sessions.

### 1. Ядро RLM (Recursive Language Model)
The RLM architecture handles subagent invocations and shell execution as first-class, sandboxed program loops:
- **Persistent IPython Kernel**: Subagents use a long-lived IPython kernel to perform Python, filesystem, and bash operations within a persistent state, avoiding raw CLI execution latency.
- **Asynchronous Non-Blocking Delegation (`rlm.run`)**: Spawning subagents is non-blocking. Invoking `await rlm("task", name="reviewer")` returns an `RLMSpawnHandle` containing session boundaries immediately, running the child asynchronously.
- **Control-Channel ZeroMQ Communication**: To prevent deadlocks on IPython shell channels, agent-to-host commands and subagent coordination messages flow strictly over the **Control channel** of the Jupyter ZeroMQ protocol.

### 2. Continual Harness (`harness_state.json`)
System state, facts, and short-term rules are saved dynamically in a localized `harness_state.json` file rather than altering immutable system prompts:
- **Harness Keys**:
  - `prompt`: Local instruction adjustments.
  - `memory`: Discovered developer facts, environment variables, and preferences.
  - `skill`: Registered Python function boundaries and argument signatures.
  - `subagent`: Registry of active child workers.
- **Refinement Loop (`/refine`)**: Sessions automatically evaluate trajectory outcomes, write minimal delta patches to `harness_state.json`, and retain versioned snapshot states for rollsback.

### 3. Smart Context Compaction
When context tokens approach limits, old messages are programmatically summarized or dropped under strict integrity criteria:
- **Cut Point Rules**: Context slices must align strictly to user, assistant, or bash execution message boundaries. Slicing must **never split a tool call from its raw tool results**.
- **Cumulative File Tracking**: Each compaction generates a `CompactionEntry` that preserves a cumulative history of all files read (`<read-files>`) or modified (`<modified-files>`) throughout the entire session.

### 4. Critical Traps & Mitigations
- **ZeroMQ Deadlocks**: Synchronous waits on IPython shell threads hang the interpreter. Always delegate communication through Control-channel handlers.
- **Context Loss during Compaction**: Discarding tool results breaks the model's trajectory memory. Always keep tool results glued to their preceding invocations.
