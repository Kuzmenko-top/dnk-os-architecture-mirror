# ⚙️ Programmatic Swarm Model & Reasoning Effort Protocol

## 1. Hermes CLI System Configuration
To set default model and reasoning effort globally in Hermes CLI:
```bash
hermes config set model.default gemini-3.8-flash
hermes config set model.reasoning_effort high
hermes config set delegation.model gemini-3.8-flash
hermes config set delegation.reasoning_effort high
```

## 2. Multi-Agent Config Synchronization
All swarm agents in `core/orchestrator/agents/*/config.yaml` maintain individual configuration settings.
When updating the active model and reasoning effort across all swarm agents programmatically:

```python
import glob, yaml

files = glob.glob("core/orchestrator/agents/*/config.yaml")
for f in files:
    with open(f, "r") as fp:
        data = yaml.safe_load(fp) or {}
    data["model"] = "gemini-3.8-flash"
    if "delegation" in data:
        data["delegation"]["model"] = "gemini-3.8-flash"
        data["delegation"]["reasoning_effort"] = "high"
    with open(f, "w") as fp:
        yaml.dump(data, fp, sort_keys=False)
```

## 3. SOUL.md & Visual Shell UI Consistency
- **System SOUL**: In `core/orchestrator/agents/*/SOUL.md`, update system identity metadata blocks (`gemini-3.8-flash (Vertex AI)`).
- **Visual Shell**: In `apps/web/src/components/home/DnkModelGcpQuickBar.tsx`, sync available model choices and badges (`Reasoning High`).
