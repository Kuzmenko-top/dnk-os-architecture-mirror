# --- DNK-MRH-HEADER ---
# mrh_id: "docs/deployment/DOCKER_SETUP.md"
# purpose: "Comprehensive Docker containerization and Docker Compose orchestration guide for DNK OS (Backend, Frontend, PostgreSQL+pgvector, Redis)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🐳 DNK OS Docker Containerization & Deployment Guide

## 📌 1. Архітектура та Огляд Стеку

Контейнеризація DNK OS побудована на базі ізольованих мікросервісів з підтримкою високої доступності, локальної розробки та безшовного production-розгортання:

| Компонент | Технологічний стек | Контейнерний образ / Dockerfile | Порт за замовчуванням | Призначення |
| :--- | :--- | :--- | :--- | :--- |
| **Backend** | FastAPI, Python 3.12, Uvicorn | `Dockerfile.backend` | `8000` | REST API, WebSocket, оркестрація агентів |
| **Frontend** | Next.js 14, React 18, Node.js 20 | `Dockerfile.frontend` | `3000` | Visual Canvas, Workspace UI, Dashboard |
| **PostgreSQL + pgvector** | PostgreSQL 16 + pgvector | `pgvector/pgvector:pg16` | `5432` / `5433` | Реляційні дані, сесії та векторні ембеддинги |
| **Redis** | Redis 7 Alpine (AOF) | `redis:7-alpine` | `6379` | Кешування, черги задач, pub/sub події |
| **Gateway (Prod)** | Nginx 1.25 Alpine | `nginx:1.25-alpine` | `80`, `443` | Reverse proxy, SSL-термінація, rate limit |

---

## 🚀 2. Швидкий старт (Локальне розгортання)

### 2.1. Запуск стеку в фоновому режимі

```bash
docker-compose up -d
```

Команда автоматично збере образи бекенду та фронтенду, запустить PostgreSQL із розширенням `pgvector`, Redis та налаштує внутрішню мікросервісну мережу `dnk_network`.

### 2.2. Перевірка статусу контейнерів

```bash
docker-compose ps
```

Очікуваний статус сервісів `dnk_backend`, `dnk_frontend`, `dnk_postgres`, `dnk_redis` — `Up (healthy)`.

### 2.3. Запуск тестів всередині контейнера Backend

```bash
docker-compose exec backend pytest tests/
```

Команда виконує перевірку кодової бази та інтеграційних модулів безпосередньо у робочому оточенні контейнера.

### 2.4. Перегляд логів сервісів

```bash
# Останні 50 рядків логів усіх сервісів
docker-compose logs --tail=50

# Стрімінг логів конкретного сервісу
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

## 🏭 3. Production Розгортання (`docker-compose.prod.yml`)

Для розгортання в production-середовищі з реплікацією, лімітами ресурсів та Nginx Gateway:

```bash
# Збірка та запуск production стеку
docker-compose -f docker-compose.prod.yml up -d --build

# Перевірка здоров'я
docker-compose -f docker-compose.prod.yml ps
```

Особливості Production конфігурації:
- **Zero-root execution**: Контейнери запускаються від непривілейованих користувачів (`dnkuser:10001`, `nextjs:10001`).
- **Resource Constraints**: Чітко визначені CPU та RAM ліміти і резервації для запобігання OOM.
- **Nginx Ingress**: Маршрутизація `/api` -> `backend:8000`, `/` -> `frontend:3000` з gzip-компресією.
- **Persistent Data**: Виділені томи `pgdata_prod` та `redisdata_prod`.

---

## ⚙️ 4. Змінні оточення (Environment Variables)

### Backend (`Dockerfile.backend` / Compose)
| Змінна | Значення за замовчуванням | Опис |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `development` / `production` | Режим роботи застосунку |
| `DATABASE_URL` | `postgresql://dnk:dnk_password@postgres:5432/dnk_os` | Рядок підключення до PostgreSQL |
| `VECTOR_DB_URL` | `postgresql://dnk:dnk_password@pgvector:5432/dnk_os_vectors` | Підключення до pgvector бази |
| `REDIS_URL` | `redis://redis:6379/0` | Рядок підключення до Redis |
| `SECURITY_RATE_LIMIT` | `100000` (dev) / `10000` (prod) | Ліміт запитів API |
| `PYTHONPATH` | `/app:/app/services` | Шляхи імпорту модулів |

### Frontend (`Dockerfile.frontend` / Compose)
| Змінна | Значення за замовчуванням | Опис |
| :--- | :--- | :--- |
| `NODE_ENV` | `production` / `development` | Режим середовища Node.js |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` (dev) / `/api` (prod) | Базовий URL для запитів клієнта |
| `PORT` | `3000` | Внутрішній порт HTTP-сервера |
| `HOSTNAME` | `0.0.0.0` | IP інтерфейс прослуховування |

---

## 🛠️ 5. Корисні команди та діагностика

```bash
# Зупинка локального стеку
docker-compose down

# Зупинка з очищенням томів даних
docker-compose down -v

# Підключення до терміналу контейнера backend
docker-compose exec backend /bin/bash

# Перевірка доступності розширення pgvector в БД
docker-compose exec postgres psql -U dnk -d dnk_os -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Перевірка зв'язку з Redis
docker-compose exec redis redis-cli ping
```

---

## 🛡️ 6. Відповідність стандартам DNK OS
- **MRH-стандарт**: Усі конфігурації Docker та Compose містять `DNK-STD-0075` метадані.
- **Two-Tier Hygiene**: Контейнери збираються безпосередньо з уніфікованого кореня репозиторію.
- **Redacted Security**: Жодні реальні секрети чи приватні ключі не захардкоджені в образах.
