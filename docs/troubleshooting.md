# --- DNK-MRH-HEADER ---
# mrh_id: "docs/troubleshooting.md"
# purpose: "Canonical Troubleshooting, Diagnostics, Health Checks & Disaster Recovery Guide for DNK OS MVP."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "3.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# DNK OS Troubleshooting Guide

Comprehensive guide for diagnosing issues, debugging container workloads, executing health checks, and running recovery procedures across the **DNK OS Multi-Agent Core** infrastructure.

---

## 📑 Table of Contents
1. [Common Issues](#1-common-issues)
   - [Issue 1: Docker Desktop не запускається](#issue-1-docker-desktop-не-запускається)
   - [Issue 2: Контейнер не стартує](#issue-2-контейнер-не-стартує)
   - [Issue 3: API не відповідає (502 / Connection Refused)](#issue-3-api-не-відповідає)
   - [Issue 4: Frontend не вантажиться](#issue-4-frontend-не-вантажиться)
   - [Issue 5: Database Connection Failed](#issue-5-database-connection-failed)
   - [Issue 6: Redis Connection Failed](#issue-6-redis-connection-failed)
   - [Issue 7: Nginx не проксує запити](#issue-7-nginx-не-проксує-запити)
2. [Debug Commands](#2-debug-commands)
3. [Health Checks](#3-health-checks)
4. [Recovery Procedures](#4-recovery-procedures)

---

## 1. Common Issues

### Issue 1: Docker Desktop не запускається
**Symptoms:**
- Docker daemon не відповідає
- `docker info` повертає помилку зв'язку
- Контейнери не стартують

**Solution:**
```bash
# Перезапустити Docker Desktop
# macOS: Quit Docker Desktop з трею та відкрити знову

# Очистити кеш та тимчасові томи Docker
docker system prune -af --volumes
docker builder prune -af

# Перевірити статус демона
docker info
```

---

### Issue 2: Контейнер не стартує
**Symptoms:**
- `docker compose ps` показує статус `Exit 1` або `Restarting`
- Логи контейнера свідчать про критичну помилку ініціалізації

**Solution:**
```bash
# Переглянути логи проблемного контейнера
docker compose logs <container-name>

# Перезапустити окремий контейнер
docker compose restart <container-name>

# Перезібрати образ та перезапустити контейнер
docker compose up --build -d <container-name>
```

---

### Issue 3: API не відповідає
**Symptoms:**
- `curl http://localhost:80/health` повертає `502 Bad Gateway` або зависає
- Upstream сервіси недоступні на балансувальнику

**Solution:**
```bash
# Перевірити статус API кластера
docker compose ps dnk-api-1 dnk-api-2 dnk-api-3

# Перевірити системні логи одного з API воркерів
docker compose logs dnk-api-1

# Перезапустити пул API воркерів
docker compose restart dnk-api-1 dnk-api-2 dnk-api-3

# Перевірити здоров'я після рестарту
curl http://localhost:80/health | jq .
```

---

### Issue 4: Frontend не вантажиться
**Symptoms:**
- `curl http://localhost:3000` повертає помилку з'єднання
- 502 Bad Gateway або 404 Not Found у браузері

**Solution:**
```bash
# Перевірити статус сервісу frontend
docker compose ps dnk-frontend-1

# Перевірити логи Next.js
docker compose logs dnk-frontend-1

# Перезапустити frontend контейнер
docker compose restart dnk-frontend-1

# Перевірити доступність сторінки
curl http://localhost:3000 | grep "DNK OS"
```

---

### Issue 5: Database connection failed
**Symptoms:**
- У логах API фіксується "Connection refused to postgres:5432"
- Ендпоінт `/health` показує `database: unhealthy`

**Solution:**
```bash
# Перевірити статус контейнера PostgreSQL
docker compose ps dnk-postgres-1

# Перевірити логи бази даних
docker compose logs dnk-postgres-1

# Перезапустити PostgreSQL
docker compose restart dnk-postgres-1

# Перевірити інтерактивне підключення до БД
docker compose exec dnk-postgres-1 psql -U postgres -c "SELECT 1;"
```

---

### Issue 6: Redis connection failed
**Symptoms:**
- Ендпоінт `/health` сигналізує `redis: unhealthy`
- API повертає помилки кешування та збої блокувань

**Solution:**
```bash
# Перевірити статус контейнера Redis
docker compose ps dnk-redis-1

# Перевірити логи Redis
docker compose logs dnk-redis-1

# Перезапустити Redis
docker compose restart dnk-redis-1

# Виконати команду PING
docker compose exec dnk-redis-1 redis-cli ping
```

---

### Issue 7: Nginx не проксує запити
**Symptoms:**
- Помилка `502 Bad Gateway` на всіх вхідних маршрутах
- У логах Nginx зафіксовано "upstream prematurely closed connection while reading response header"

**Solution:**
```bash
# Перевірити статус Nginx
docker compose ps dnk-nginx-1

# Перевірити логи зворотного проксі
docker compose logs dnk-nginx-1

# Перезапустити Nginx
docker compose restart dnk-nginx-1

# Перевірити синтаксис конфігурації
docker compose exec dnk-nginx-1 nginx -t
```

---

## 2. Debug Commands

### 🔍 Container Status
```bash
# Огляд запущених контейнерів
docker compose ps

# Огляд усіх контейнерів, включаючи зупинені
docker compose ps -a

# Моніторинг утилізації ресурсів (CPU/MEM/NET I/O)
docker stats
```

### 📋 Logs
```bash
# Загальний потік логів усіх сервісів
docker compose logs

# Логи конкретного API сервісу
docker compose logs dnk-api-1

# Логи у режимі реального часу (follow)
docker compose logs -f dnk-api-1
```

### 🩺 Health Checks
```bash
# Перевірка загального API Health
curl http://localhost:80/health | jq .

# Перевірка доступності Frontend
curl http://localhost:3000 | grep "DNK OS"

# Перевірка працездатності PostgreSQL
docker compose exec dnk-postgres-1 psql -U postgres -c "SELECT 1;"

# Перевірка зв'язку з Redis
docker compose exec dnk-redis-1 redis-cli ping

# Перевірка кореневого статусу API через Nginx
curl http://localhost:80/ | jq .
```

### 🌐 Network Debug
```bash
# Перелік мереж Docker
docker network ls

# Детальна інспекція мережевого мосту
docker network inspect dnk_os_mvp_default

# Перевірка прокидання портів контейнера
docker compose port dnk-api-1 8000
```

### 💾 Disk Space & Optimization
```bash
# Перевірка використання дискового простору Docker
docker system df

# Повне очищення невикористовуваних образів, контейнерів та томів
docker system prune -af --volumes
docker builder prune -af
```

---

## 3. Health Checks

### Full System Health
```bash
# Комплексний статус усіх підсистем
curl http://localhost:80/health | jq .

# Очікуваний JSON-результат:
# {
#   "status": "healthy",
#   "services": {
#     "api": {"status": "healthy", "service": "dnk-api"},
#     "database": {"status": "healthy", "latency_ms": 5, "connection": "active"},
#     "redis": {"status": "healthy", "latency_ms": 2, "connection": "active"},
#     "memory": {"status": "healthy", "usage_percent": 27.8, "available_mb": 2827},
#     "cpu": {"status": "healthy", "usage_percent": 1.3, "cores": 8},
#     "disk": {"status": "healthy", "usage_percent": 16.2, "free_gb": 24.89}
#   }
# }
```

### Individual Service Health
```bash
# API Root
curl http://localhost:80/ | jq .

# Frontend SSR Check
curl http://localhost:3000 | grep "DNK OS"

# PostgreSQL Primary
docker compose exec dnk-postgres-1 psql -U postgres -c "SELECT 1;"

# Redis In-Memory Cache
docker compose exec dnk-redis-1 redis-cli ping

# pgvector Vector Engine
docker compose exec dnk-pgvector-1 psql -U postgres -c "SELECT 1;"
```

### Container Health
```bash
# Перевірити статус контейнерів
docker compose ps

# Отримати точний статус healthcheck для окремого контейнера
docker inspect --format='{{.State.Health.Status}}' dnk-api-1
```

---

## 4. Recovery Procedures

### 🔄 Full Stack Restart
```bash
# Зупинити всі сервіси
docker compose down

# Перезібрати та запустити у фоновому режимі
docker compose up --build -d

# Перевірити статус контейнерів
docker compose ps

# Верифікувати здоров'я API
curl http://localhost:80/health | jq .
```

### 🗄️ Database Recovery
```bash
# Зупинити сервіси баз даних
docker compose stop dnk-postgres-1 dnk-pgvector-1

# Запустити сервіси баз даних
docker compose start dnk-postgres-1 dnk-pgvector-1

# Перевірити з'єднання
docker compose exec dnk-postgres-1 psql -U postgres -c "SELECT 1;"
```

### ⚡ Cache Recovery
```bash
# Зупинити сервіс Redis
docker compose stop dnk-redis-1

# Запустити сервіс Redis
docker compose start dnk-redis-1

# Перевірити готовність
docker compose exec dnk-redis-1 redis-cli ping
```

### 🚀 API Cluster Recovery
```bash
# Зупинити API кластер
docker compose stop dnk-api-1 dnk-api-2 dnk-api-3

# Запустити API кластер
docker compose start dnk-api-1 dnk-api-2 dnk-api-3

# Верифікувати здоров'я
curl http://localhost:80/health | jq .
```

### 🖥️ Frontend Recovery
```bash
# Зупинити сервіс frontend
docker compose stop dnk-frontend-1

# Запустити сервіс frontend
docker compose start dnk-frontend-1

# Перевірити доступність
curl http://localhost:3000 | grep "DNK OS"
```

### 🛡️ Nginx Recovery
```bash
# Зупинити Nginx
docker compose stop dnk-nginx-1

# Запустити Nginx
docker compose start dnk-nginx-1

# Перевірити конфігурацію
docker compose exec dnk-nginx-1 nginx -t

# Перевірити маршрутизацію
curl http://localhost:80/ | jq .
```

### 🚨 Emergency Full Reset
```bash
# Повна зупинка та видалення контейнерів, мереж і томів
docker compose down -v

# Глибоке очищення Docker середовища
docker system prune -af --volumes
docker builder prune -af

# Повне розгортання з нуля
docker compose up --build -d

# Фінальна перевірка статусу та здоров'я
docker compose ps
curl http://localhost:80/health | jq .
```
