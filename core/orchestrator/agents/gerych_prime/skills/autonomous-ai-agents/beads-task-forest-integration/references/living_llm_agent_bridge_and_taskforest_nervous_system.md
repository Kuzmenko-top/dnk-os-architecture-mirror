# Living LLM Agent Bridge & TaskForest Nervous System Protocol

## 🎯 Architecture Overview
In DNK OS, TaskForest serves as the central shared cognitive nervous system (Shared Cognitive DAG). Rather than relying on simple regex or rigid conversational heuristics, human interaction passes through a Living LLM Bridge (`GerychAgentBridge`) powered by Vertex AI / Gemini Flash, imbued with the persona defined in `SOUL.md`.

```
Human / Founder (Natural Language Chat)
               │
               ▼
┌──────────────────────────────────────────────┐
│  /api/v3/node_tasks/chat_intake              │
│  (ConversationalTaskExtractor)               │
└──────────────────────┬───────────────────────┘
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
[LLM Available]                [Offline / Fallback]
GerychAgentBridge              Deterministic Heuristic Extractor
(Vertex AI REST API)           (Regex & Keyword Rule Base)
       │                               │
       └───────────────┬───────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│        Dual-Channel Response Synthesizer     │
├──────────────────────────────────────────────┤
│ 1. `reply`: Human dialogue (Ukrainian,       │
│    persona-grounded, empathetic, concise)    │
│ 2. `nodes`/`edges`: Structured DAG updates   │
│    (empty on inquiry; populated on task)     │
└──────────────────────────────────────────────┘
```

---

## 🛠️ Key Implementation Patterns

### 1. Dual-Channel Response Contract
The LLM prompt instructs the model to return a structured JSON with two distinct channels:
```json
{
  "reply": "Текст живої відповіді Максиму українською мовою з особистістю Герича",
  "intent": "inquiry" | "task_creation",
  "nodes": [
    {
      "id": "task-slug-or-id",
      "title": "Коротка назва задачі",
      "description": "Детальний опис",
      "assigned_agent": "dnk_shopify" | "gerych_builder" | "dnk_dev_fullstack",
      "priority": "P0" | "P1" | "P2"
    }
  ],
  "edges": [
    {
      "source_id": "parent-id",
      "target_id": "child-id",
      "relation": "depends_on"
    }
  ]
}
```

### 2. Intent Disambiguation (Inquiry vs Task Creation)
- **Inquiry (`intent: "inquiry"`)**: When the user asks questions, greets the agent, or requests system status (e.g. `"Що за ноди у нас є?"`, `"Як справи?"`), the system returns `nodes: []`. **No task nodes are minted into the database**.
- **Task Creation (`intent: "task_creation"`)**: When the user expresses actionable intent (`"Створи задачу для dnk_shopify..."`), the model extracts structured TaskDNA specifications, and the persistence manager inserts the nodes into the active DAG.

### 3. Graceful Fallback Protocol
Always encapsulate LLM calls in a try/except block that falls back to the deterministic regex/keyword parser:
```python
try:
    llm_result = await bridge.think(prompt, current_graph_summary)
    if llm_result:
        return process_llm_result(llm_result)
except Exception as e:
    logger.warning(f"GerychAgentBridge fallback triggered: {e}")

# Fallback: Deterministic regex parser
return fallback_heuristic_parser(prompt)
```
This guarantees that integration test suites (`pytest`), offline environments, or transient API timeouts never break HTTP 200 contract execution.

### 4. Non-Brittle Test Assertion Patterns
When testing conversational endpoints backed by live or mocked LLMs:
- **Avoid single-string strict assertions**: Natural language responses can legitimately use synonyms (e.g. `"нод"`, `"вузлів"`, `"задач"`, `"граф"`).
- **Use flexible membership assertions**:
  ```python
  assert any(term in data["reply"] for term in ["вузлів", "нод", "задач", "граф"])
  ```
- **Ensure Agent Persona Signature**: If the prompt calls for a signed response, normalize the output to ensure the agent identity (`🤖 Герич:`) is present for both tests and frontend chat rendering.

### 5. Real-World Temporal Grounding (Local Timezone Injection)
LLMs have no internal system clock. To answer temporal questions ("котра година?", "яка дата?") accurately:
```python
def get_kyiv_time_str() -> str:
    tz_kyiv = timezone(timedelta(hours=3))
    now = datetime.now(tz_kyiv)
    days = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"]
    months = ["січня", "лютого", "березня", "квітня", "травня", "червня", "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"]
    return f"{days[now.weekday()]}, {now.day} {months[now.month - 1]} {now.year} року, {now.strftime('%H:%M')} (Київ, UTC+3)"
```
Inject this string into the prompt payload before dispatching to Vertex AI.

### 6. OAuth Bearer Token Synchronization for Docker Backends
When FastAPI executes inside a Docker container while Google Cloud SDK (`gcloud`) resides on the host:
- Google OAuth bearer tokens expire every 60 minutes (`ya29...`).
- When expired, LLM calls fail with `HTTP 401: Unauthorized` and trigger silent fallback to heuristics.
- Fix: A host watchdog daemon (`scripts/system/gcp_token_daemon.py`) runs in the background and writes updated tokens to `.vertex_token` in the repo root every 30-35 minutes.
- The root `.vertex_token` is mounted into the container at `/app/.vertex_token` (permissions `600`), ensuring 24/7 hot access.

### 7. Heuristic Fallback Imperative Guardrails
To prevent casual queries ("напиши дату", "напиши привіт") from matching imperative task keywords (`^напиши\b`) in offline mode:
- Explicitly check for temporal inquiry keywords (`re.search(r"\b(?:час|година|дата|дату|день)\b")` before testing task creation regexes.
- Return a helpful conversational response containing `get_kyiv_time_str()` and set `created_nodes: []`.

### 8. Multi-Turn History & Selection Context Injection
Conversational task intake is not stateless. User commands like "Ну давай, реалізовувай" rely completely on prior conversational context:
- In client store (`nodeTasksStore.ts`), maintain and pass the recent 6–10 turns in `chat_history: [{sender: 'user'|'agent', text: '...'}]` together with `selected_node_id`.
- In the bridge (`GerychAgentBridge.call_living_gerych`), format the dialog history into the prompt under `### ІСТОРІЯ ПОТОЧНОГО ДІАЛОГУ:`.
- This ensures follow-up directives carry forward what was previously discussed (e.g., UX improvements, specific node refactorings, blocker analysis).

### 9. Zero-Sycophancy & Tone Governance Protocol
Overly deferential prompts cause LLMs to produce obsequious fluff ("мій дорогий друже і творець", "дуже дякую за довіру", "я до ваших послуг") that wastes screen real estate and irritates users:
- **System Prompt Invariant**: Explicitly ban groveling terms and sycophantic greetings.
- **Architectural Persona**: Mandate concise, confident 2–4 sentence responses focused directly on graph topology, blocker mitigation, and concrete task assignments.

### 10. Autonomous "Action-First" Synthesis on Founder Mandate
When the user gives approval or an open directive ("реалізовуй", "роби так, як бачиш", "зроби зручніше для користувача"):
- **Strictly Prohibited**: Asking passive clarifying questions like "який напрямок зараз пріоритетний?".
- **Action-First Pattern**:
  1. Classify intent as `task_creation`.
  2. Synthesize 2–4 concrete, actionable engineering tasks (UI/UX refinements, API adjustments, testing gates).
  3. Map tasks to specialized domain swarm agents (`gerych_builder`, `dnk_dev_fullstack`, `gerych_auditor`).
  4. Generate and persist DAG nodes and dependency edges immediately.
  5. Provide a crisp 1–2 sentence confirmation of what work was scheduled.
