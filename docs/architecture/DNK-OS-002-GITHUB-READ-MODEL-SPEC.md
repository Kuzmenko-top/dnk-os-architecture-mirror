# --- DNK-MRH-HEADER ---
# mrh_id: "docs_architecture_DNK-OS-002-GITHUB-READ-MODEL-SPEC"
# purpose: "Read Model Architecture Specification for DNK-OS-002 GitHub Adapter"
# author: "DNK-e.com Maksym"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# --- END DNK-MRH-HEADER ---

# DNK-OS-002 Read Model Architecture Specification

## Overview
The Server-Side GitHub Read-Only Adapter provides a secure, bounded interface for fetching pull request status, commit SHA metadata, and check run statuses without exposing GitHub credentials to client browsers.

```text
┌────────────────────────┐         ┌─────────────────────────┐         ┌────────────────────────┐
│   Next.js Client       │  HTTP   │   FastAPI Backend       │  HTTPS  │   GitHub REST API      │
│   (TaskDNA Dashboard)  │ ──────> │   (apps/api)            │ ──────> │   (api.github.com)     │
│   X-Workspace-ID / JWT │ <────── │   github_adapter.py     │ <────── │   Read-Only Auth       │
└────────────────────────┘         └─────────────────────────┘         └────────────────────────┘
```

## Contract Fields
- `data`: Normalized model payload (`NormalizedPullRequest`, `NormalizedBranch`, etc.)
- `data_source`: `"live"` | `"cache"` | `"fixture"`
- `stale`: `true` | `false`
- `fetched_at`: ISO 8601 timestamp
- `expires_at`: ISO 8601 timestamp
- `error_code`: `None` | `"timeout"` | `"rate_limit"` | `"upstream_5xx"` | `"unauthorized"` | `"not_found"` | `"forbidden_repo"`
