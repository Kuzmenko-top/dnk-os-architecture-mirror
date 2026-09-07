# --- DNK-MRH-HEADER ---
# mrh_id: "docs_releases_production_checklist"
# purpose: "Production Checklist guidelines and deployment validation gates"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-12"
# --- END DNK-MRH-HEADER ---

# DNK OS MVP v1.0 — Production Checklist

## Перед деплоєм

- [ ] Перевірити `.env` файли (DATABASE_URL, REDIS_URL, API_KEY).  
- [ ] Перевірити `docker-compose.prod.yml` (репліки, мережа).  
- [ ] Перевірити `monitoring/alerts.yml` (алерти).  
- [ ] Перевірити `scripts/backup.sh` (шлях до бекапів).

## Деплой

- [ ] `docker-compose -f docker-compose.prod.yml up -d`.  
- [ ] Перевірити логи: `docker-compose logs -f`.  
- [ ] Перевірити метрики: http://localhost:9090.  
- [ ] Перевірити дашборд: http://localhost:3001.

## Після деплою

- [ ] Запустити тестовий сценарій (Visual Shell + Agent Flow).  
- [ ] Перевірити Security Gate (блокування ризикових дій).  
- [ ] Перевірити бекапи: `./scripts/backup.sh`.  
- [ ] Перевірити алерти (симуляція високого навантаження).

## Моніторинг

- [ ] Grafana дашборд (CPU, RAM, запити, помилки).  
- [ ] Prometheus метрики (API, DB, RAG).  
- [ ] Loki логи (structured logging).

## Бекапи

- [ ] Щоденний бекап DB + Redis.  
- [ ] Періодичне відновлення з бекапу (тест).
