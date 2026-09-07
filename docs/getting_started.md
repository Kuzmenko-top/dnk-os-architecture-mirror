# --- DNK-MRH-HEADER ---
# mrh_id: "docs/getting_started.md"
# purpose: "Complete Getting Started & Operational Deployment Guide for DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🚀 Getting Started with DNK OS

Welcome to **DNK OS** — the next-generation autonomous AI orchestration and visual development platform.

---

## 1. Quickstart & Installation

### Prerequisites
- Python 3.12+ with virtual environment (`.venv`)
- Node.js 20+ and pnpm / npm
- Git with pre-commit hooks configured

### Environment Setup
```bash
# Clone the repository
git clone https://github.com/your-org/dnk-hub.git
cd dnk-hub

# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install frontend dependencies
npm install
```

---

## 2. Configuration & Secrets

Copy `.env.example` to `.env` (never commit `.env` to git):
```bash
cp .env.example .env
```

Ensure the following environment variables are set:
```bash
export WORKSPACE_ID="ws-alpha-001"
export VERTEX_API_KEY="[REDACTED]"
export GH_TOKEN="[REDACTED]"
```

---

## 3. Launching Services

### Local Development Server
```bash
# Start FastAPI backend server
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

# Start Web UI / Visual Canvas (in separate shell)
npm run dev --prefix apps/web
```

---

## 4. Production Launch Verification

Before releasing or promoting to production, execute the automated pre-launch verification suites:

### 1. Security Audit
Run the automated security scanner:
```bash
bash scripts/security/security_audit.sh
```

### 2. High-Load Stress Testing
Verify performance under load:
```bash
bash scripts/load_test/load_test.sh
```

### 3. Master Quality Gate
Certify 100% green tests:
```bash
bash scripts/verify_all.sh
```

---

## 5. Next Steps
- Review the [API Reference](api/api_reference.md) for REST and WebSocket specifications.
- Check the [Production Launch Checklist](launch/launch_checklist.md).
- Inspect the [Compliance Report](compliance/compliance_report.md).
