# --- DNK-MRH-HEADER ---
# mrh_id: "CHANGELOG.md"
# purpose: "Canonical Changelog for DNK OS MVP Release Milestones."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-13"
# author: "DNK-e.com Maksym"
# license: "MIT"
# --- END DNK-MRH-HEADER ---

# CHANGELOG

## [1.0.0] — 2026-08-12

### Added

- **Timeline DB** — PostgreSQL-first база для аудиту всіх виконань.
- **Security Gate** — Policy + Decorator для контролю ризикових дій.
- **Visual Shell** — Робочий кабінет (Canvas + Agent Flow + Artifact Panel).
- **Self-Improvement Loop** — Аналіз виконань → генерація покращень.
- **Multi-Agent Collaboration** — Координація 5+ агентів з чергами.
- **Knowledge Base + RAG** — Векторна база (pgvector) + RAG.
- **Deployment Pipeline** — Docker + CI/CD, моніторинг, алерти.
- **Advanced Analytics Dashboard** — Аналітика успішності, вузьких місць.
- **Plugin System** — Розширюваність через плагіни.
- **Production Hardening** — Моніторинг, безпека, бекапи, масштабування.

### Tests

- 108+ тестів PASS.

### Security

- Rate Limiting, CORS, API Key.
- XOR-Base64 шифрування.
- Security Gate для всіх ризикових дій.

### Deployment

- Docker Compose (API, Web, DB, Redis).
- Моніторинг (Prometheus + Grafana + Loki).
- Бекапи (Postgres + Redis).
