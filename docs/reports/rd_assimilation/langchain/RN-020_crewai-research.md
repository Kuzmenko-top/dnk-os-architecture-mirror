# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/rd_assimilation/langchain/RN-020_crewai-research.md"
# purpose: "SOTA Research and Pattern Extraction for crewAIInc/crewAI"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-16"
# --- END DNK-MRH-HEADER ---

# 🧬 SOTA Research: crewAI Framework Assimilation (RN-020)

In-depth technical research and architectural analysis of `crewAIInc/crewAI` (10,000+ stars, MIT license) for assimilation into DNK OS multi-agent swarm orchestration (`DNK-DOMAIN-SWARM`).

## 📋 Research Metadata
- **Donor Repository:** `crewAIInc/crewAI`
- **Task ID:** `DNK-ASSIM-020`
- **Domain:** `langchain`
- **License:** MIT
- **Key Modules Analyzed:**
  - `crewai.agent` — `Agent` class (role, goal, backstory, allow_delegation, tools)
  - `crewai.task` — `Task` class (description, expected_output, agent, async_execution, context)
  - `crewai.crew` — `Crew` class (agents, tasks, process, manager_llm, manager_agent)
  - `crewai.process` — `Process` enum (sequential, hierarchical)
  - `crewai.memory` — `ShortTermMemory`, `LongTermMemory`, `EntityMemory`
  - `crewai.tools` — `@tool` decorator & `BaseTool` integration

---

## 🏗️ Key Patterns Extracted

### 1. Role-Based Persona Pipelining
crewAI enforces structured persona prompting by separating an agent's persona into 3 fundamental dimensions:
- **`role`:** Defines the agent's job title and domain scope (e.g. `"Lead R&D Researcher"`).
- **`goal`:** Concise statement of what the agent aims to achieve.
- **`backstory`:** Background story that primes the LLM system prompt with domain expertise and tone.

```python
# 🧬 [DONOR START: crewAIInc/crewAI]
from crewai import Agent

researcher = Agent(
    role="Senior Market Analyst",
    goal="Discover disruptive e-commerce trends in 2026",
    backstory="You are a veteran analyst with 15 years experience at Gartner.",
    verbose=True,
    allow_delegation=True,
    memory=True
)
# 🧬 [DONOR END: crewAIInc/crewAI]
```

### 2. Crew Orchestration Modes
The `Crew` container coordinates agents and tasks through explicit execution processes:
- **Sequential Process (`Process.sequential`):** Tasks execute in strict linear order ($T_1 
ightarrow T_2 
ightarrow T_3$). The output of $T_1$ automatically feeds into the context of $T_2$.
- **Hierarchical Process (`Process.hierarchical`):** A manager agent (either auto-generated via `manager_llm` or custom `manager_agent`) dynamically plans tasks, delegates subtasks to team agents based on their roles, reviews output, and requests revisions.

### 3. Task Delegation & Handoff Protocols
When `allow_delegation=True`, crewAI injects two internal tools into the agent's toolset:
- `Delegate work to coworker`: Allows an agent to offload a specific subtask to a peer agent.
- `Ask question to coworker`: Allows an agent to query a peer agent for clarification without transferring full task ownership.

```python
# 🧬 [DONOR START: crewAIInc/crewAI]
from crewai import Task, Crew, Process

task1 = Task(
    description="Analyze competitor pricing strategies",
    expected_output="A structured markdown report with bullet points",
    agent=researcher
)

crew = Crew(
    agents=[researcher],
    tasks=[task1],
    process=Process.sequential,
    verbose=True
)
result = crew.kickoff()
# 🧬 [DONOR END: crewAIInc/crewAI]
```

### 4. Sequential Task Context Passing
Task results flow sequentially across the pipeline. A downstream task can explicitly declare upstream dependencies using the `context` parameter:
```python
task2 = Task(
    description="Synthesize executive summary from market research",
    expected_output="Executive summary paragraph",
    agent=writer,
    context=[task1]  # Output of task1 is injected into task2 prompt
)
```

### 5. Multi-Layer Memory Architecture
crewAI combines 3 memory layers backed by vector stores (ChromaDB / Mem0) and SQLite:
- **Short-Term Memory:** RAG-backed memory storing recent task outputs during current crew execution.
- **Long-Term Memory:** Persistent store across multiple crew executions tracking historical agent performance and task outcomes.
- **Entity Memory:** Knowledge graph / entity extraction storing relationships between key domain entities (products, users, systems).

### 6. Tool Integration & Function Calling
Tools are defined using Pydantic or the `@tool` decorator. Tools can be assigned globally to an `Agent` or scoped locally to a specific `Task`.

---

## 🛡️ License & Clean-Room Compliance
- **License:** MIT License.
- **Compliance:** All contracts and patterns assimilated into `DNK_HUB` use pure abstract interface definitions (`abc.ABC`) without direct third-party proprietary dependencies.
