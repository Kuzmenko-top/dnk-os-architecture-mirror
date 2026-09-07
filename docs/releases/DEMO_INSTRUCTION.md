# --- DNK-MRH-HEADER ---
# mrh_id: "docs_releases_demo_instruction"
# purpose: "Step-by-step guideline for running MVP v1.0 demonstration to Maksym"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-12"
# --- END DNK-MRH-HEADER ---

# DNK OS MVP v1.0 — Demo for Maxim

## 1. Запуск

```bash
cd .
docker-compose -f docker-compose.prod.yml up -d
```

## 2. Показати модулі

### 2.1 Visual Shell
- http://localhost:3000/canvas/3b5d78a8-13b8-420b-b120-364bac824597  
- Canvas + Agent Flow + Artifact Panel.

### 2.2 Security Gate
- Спроба ризикової дії → HTTP 403.  
- Audit trail у Timeline DB.

### 2.3 Multi-Agent
- 5+ агентів, черги, self-healing.

### 2.4 RAG
- Запит з контекстом → RAG augmentation.

### 2.5 Analytics
- http://localhost:3000/analytics  
- Overview, Agent Performance, Bottlenecks, Timeline.

### 2.6 Plugin System
- Показати slack_plugin, notion_plugin.

### 2.7 Моніторинг
- Grafana: http://localhost:3001  
- Prometheus: http://localhost:9090  
- Loki: http://localhost:3100

## 3. Фінал

- Показати `docs/releases/MVP-v1.0.md`.  
- Оголосити: **DNK OS MVP v1.0 — Production Ready**.
