# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/RUNBOOK_01_Vertex_AI_Integration.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

# 🛡️ VERTEX AI & GEMINI 3.X INTEGRATION RUNBOOK

## 🎯 Account & GCP Environment Governance

| Parameter | Canonical Value |
| :--- | :--- |
| **GCP Active Account** | `reburn.craft@gmail.com` |
| **GCP Active Project ID** | `project-51b6f23c-017b-4263-a5a` |
| **Vertex AI Region** | `us-central1` |
| **Vertex Endpoint Template** | `https://aiplatform.googleapis.com/v1/projects/${GOOGLE_CLOUD_PROJECT}/locations/us-central1/publishers/google` |
| **Auth Transport** | `Authorization: Bearer ya29...` (via `gcloud auth application-default print-access-token`) |

---

## 🛠️ Key Architectural Patches & Safeguards

### 1. OAuth2 Bearer Authorization Header
- **File**: `core/hermes_agent/agent/gemini_native_adapter.py`
- **Logic**: When the API key starts with `ya29.` (OAuth ADC token), send `Authorization: Bearer ya29...` header instead of `x-goog-api-key`.
- **Purpose**: Prevents `HTTP 400 (INVALID_ARGUMENT): API key not valid` error on Google Cloud.

### 2. Dual Provider Routing (`gemini` & `vertex`) to `GeminiNativeClient`
- **Files**:
  - `core/hermes_agent/agent/agent_runtime_helpers.py` (Line ~1231)
  - `core/hermes_agent/agent/auxiliary_client.py` (Lines ~1433, ~1470)
- **Logic**: Check `if provider in ("gemini", "vertex"):` to route both providers to `GeminiNativeClient`.
- **Purpose**: Prevents Hermes OpenAI transport from appending `/chat/completions` to Vertex AI URLs, which causes `HTTP 404 Not Found`.

### 3. Dynamic Base URL Resolution
- **File**: `core/hermes_agent/plugins/model-providers/gemini/__init__.py`
- **Logic**: `GeminiProfile.__getattribute__` intercepts `base_url` for `vertex` and constructs the full path with `locations/us-central1` and `GOOGLE_CLOUD_PROJECT`.
- **Purpose**: Fixes `locations/global` 404 errors by guaranteeing `us-central1` endpoint resolution.

### 4. Forced Project Locking in Launcher
- **File**: `scripts/system/gerych.sh`
- **Logic**: Forces `export GOOGLE_CLOUD_PROJECT="project-51b6f23c-017b-4263-a5a"`.
- **Purpose**: Prevents shell environments from inheriting dead/deleted GCP project IDs (`project-ed0b67a3-bf27-4ac1-a4f`).

---

## 🚑 Quick Diagnostic Checklist for Future Troubleshooting

| Symptom | Root Cause | Solution |
| :--- | :--- | :--- |
| **`HTTP 400: API key not valid`** | Request sent to AI Studio (`generativelanguage.googleapis.com`) with OAuth token, or `x-goog-api-key` header used. | Verify `gemini_native_adapter.py` sends `Authorization: Bearer ya29...` and `base_url` is Vertex AI. |
| **`HTTP 404: Not Found`** | URL missing `/locations/us-central1/publishers/google` OR OpenAI transport appended `/chat/completions`. | Verify `agent_runtime_helpers.py` has `provider in ("gemini", "vertex")` and region is `us-central1`. |
| **`HTTP 403: Billing Disabled`** | Token injected under wrong/deleted project ID. | Run `gcloud config set project project-51b6f23c-017b-4263-a5a` and restart `./scripts/gerych.sh`. |

---

## ⚡ Verified Working Command Execution Test

```bash
uv run python -c "
import os
token = os.popen('gcloud auth application-default print-access-token').read().strip()
from agent.gemini_native_adapter import GeminiNativeClient

client = GeminiNativeClient(
    api_key=token,
    base_url='https://aiplatform.googleapis.com/v1/projects/project-51b6f23c-017b-4263-a5a/locations/us-central1/publishers/google'
)

resp = client._create_chat_completion(
    model='gemini-3.5-flash',
    messages=[{'role': 'user', 'content': 'Hello'}]
)
print(resp.choices[0].message.content)
"
```