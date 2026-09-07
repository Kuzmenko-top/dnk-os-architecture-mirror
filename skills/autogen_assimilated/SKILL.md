---
name: "autogen_assimilated"
description: "SOTA indices and recipes for AutoGen conversational agent networks, group chats, and sandboxed code execution."
---

# 🤖 AutoGen Orchestration & Execution Assimilation Index

Meta-index tracking conversational agent networks, group chats, and sandboxed code-execution feedback loops.

## 📁 Core Specifications

1. **[Research & Evidence Trail](./references/RN-021_autogen-research.md)**
   - Analysis of `microsoft/autogen` for agent-to-agent communication and code execution.

2. **[Architecture Patterns](./references/DNK-ARCH-021_autogen-patterns.md)**
   - Conversable agent abstraction, paired loops, and group chat topologies.

3. **[Component State Contracts](./references/DNK-COMP-021_autogen-contracts.md)**
   - Python interfaces (`DNKConversableAgentPort`, `DNKCodeExecutorPort`, `DNKGroupChatPort`).

## 📁 Structure

- `scripts/` — ініціалізація та запуск Conversational Agents.
- `examples/` — приклади paired chat (Assistant + UserProxy) та GroupChat.
- `references/` — конфігурації промптів та списки підтримуваних мов програмування.
- `resources/` — системні схеми та діаграми.

Основна документація:
- [RN-021](../../docs/reports/rd_assimilation/langchain/RN-021_autogen-research.md)
- [DNK-ARCH-021](../../docs/tech/specs/DNK-ARCH-021_autogen-patterns.md)
- [DNK-COMP-021](../../docs/tech/specs/DNK-COMP-021_autogen-contracts.md)

## 🛠️ Executable Recipes

### Recipe A: Bootstrapping a Paired Code Execution Loop
- Initialize an AssistantAgent and UserProxyAgent with code execution enabled:
  ```python
  from core.contracts.autogen_contracts import DNKConversableAgentPort, DNKCodeExecutorPort
  # Implementation handles LLM code generation and local sandbox execution
  ```
