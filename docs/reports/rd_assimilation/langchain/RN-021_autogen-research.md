# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/rd_assimilation/langchain/RN-021_autogen-research.md"
# purpose: "SOTA Research and Pattern Extraction for microsoft/autogen"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# --- END DNK-MRH-HEADER ---

# 🧬 SOTA Research: AutoGen Conversational Multi-Agent Framework Assimilation (RN-021)

In-depth technical research and architectural analysis of `microsoft/autogen` (35,000+ stars, MIT license) for assimilation into DNK OS conversational networks and sandboxed code execution pipelines.

---

## 📋 Research Metadata
- **Donor Repository:** `microsoft/autogen` (v0.2/v0.4 architecture)
- **Task ID:** `DNK-ASSIM-021`
- **Domain:** `langchain`
- **License:** MIT License
- **Key Modules Analyzed:**
  - `autogen.agentchat.conversable_agent` — `ConversableAgent` core communication abstraction
  - `autogen.agentchat.assistant_agent` — `AssistantAgent` (LLM-driven problem solver)
  - `autogen.agentchat.user_proxy_agent` — `UserProxyAgent` (Human-in-the-loop & code executor)
  - `autogen.agentchat.groupchat` — `GroupChat` and `GroupChatManager` (Multi-agent orchestration)
  - `autogen.coding` — `CodeExecutor`, `LocalCommandLineCodeExecutor`, `DockerCommandLineCodeExecutor`
  - `autogen.agentchat.contrib.retrieve_user_proxy_agent` — Retrieval-augmented agentic QA

---

## 🏗️ Key Patterns Extracted

### 1. Conversational Agent Abstraction (`ConversableAgent`)
AutoGen unifies all agent interactions through a bidirectional conversation protocol:
- **Message Exchange Interface:** Agents interact by receiving and sending messages (`send`, `receive`, `initiate_chat`).
- **Reply Dispatch Pipeline (`register_reply`):** An extensible chain of reply generators evaluated in order of priority:
  1. `generate_tool_calls_reply`: Dispatches tool/function execution if tool calls are present.
  2. `generate_code_execution_reply`: Extracts and runs code blocks if execution is configured.
  3. `generate_oai_reply`: Queries LLM backend if previous handlers do not generate a terminal reply.
  4. `check_termination_and_human_reply`: Handles termination condition checks (`is_termination_msg`) and human intervention prompts.

```python
# 🧬 [DONOR START: microsoft/autogen]
from autogen import ConversableAgent

assistant = ConversableAgent(
    name="Coder",
    system_message="You are an expert Python developer. Write clean, self-contained code blocks.",
    llm_config={"config_list": [{"model": "gpt-4o", "api_key": "..."}]},
    human_input_mode="NEVER"
)
# 🧬 [DONOR END: microsoft/autogen]
```

### 2. Closed-Loop Code Execution (`UserProxyAgent` + `CodeExecutor`)
AutoGen provides automatic detection, extraction, and sandboxed execution of code blocks (Python, Bash, PowerShell) within chat messages:
- **Regex Code Block Extractor:** Parses markdown blocks matching ` ```<language>\n<code>\n``` `.
- **Docker / Local Sandbox Execution:** Runs code in ephemeral containers or isolated local scratch directories with timeout limits and stdout/stderr capturing.
- **Self-Healing Execution Loop:** When code execution fails with a runtime error, stderr is automatically sent back as the next conversation turn to the Assistant agent for auto-debugging.

```python
# 🧬 [DONOR START: microsoft/autogen]
from autogen import UserProxyAgent

user_proxy = UserProxyAgent(
    name="Executor",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: "TERMINATE" in x.get("content", ""),
    code_execution_config={"work_dir": "coding", "use_docker": False}
)
# 🧬 [DONOR END: microsoft/autogen]
```

### 3. Group Chat & Dynamic Speaker Selection (`GroupChat`)
Multi-agent topologies are managed via `GroupChat` rooms coordinated by `GroupChatManager`:
- **Speaker Selection Modes:**
  - `auto`: Uses an LLM prompt to dynamically choose the next speaker based on chat history and agent role descriptions.
  - `round_robin`: Cycles sequentially through the agent registry.
  - `random`: Uniformly samples the next speaker.
  - `manual`: Asks the user to pick the next speaker.
  - `graph_transition_matrix`: Constrains valid speaker transitions via an explicit adjacency list / state graph.
- **Broadcast Protocol:** Every message uttered by the active speaker is appended to the global message history and broadcast to all participants.

### 4. Native Tool & Function Registration
Functions are registered on both sides of the agent boundary:
- **LLM Schema Registration (`register_for_llm`):** Injects OpenAPI/Pydantic function calling schemas into the Assistant LLM config.
- **Execution Binding (`register_for_execution`):** Maps function names to physical Python callables on the UserProxy / Worker agent.

### 5. Conversation Memory & Summarization
- **Chat History Management:** In-memory message list with automated truncation and role filtering.
- **Chat Reflection & Summary:** `summary_method` (e.g. `last_msg`, `reflection_with_llm`) extracts structured conclusions upon `initiate_chat` completion.

---

## 🛡️ License & Clean-Room Compliance
- **License:** MIT License.
- **Compliance:** All contracts and patterns assimilated into `DNK_HUB` use pure abstract interface definitions (`abc.ABC`) without direct third-party proprietary dependencies.
