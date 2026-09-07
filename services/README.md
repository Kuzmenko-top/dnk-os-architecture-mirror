# --- DNK-MRH-HEADER ---
# mrh_id: "services/README.md"
# purpose: "Canonical Architecture and Governance Guide for DNK OS Microservices & Sandboxes"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

# 🐳 DNK OS MICROSERVICES & SANDBOXES GOVERNANCE
## РЕГЛАМЕНТ СТВОРЕННЯ ТА РОБОТИ З МІКРОСЕРВІСАМИ

Кожен мікросервіс у цій директорії є ізольованим докеризованим компонентом системи.

### 🏛️ Обов'язковий 4-Елементний Каркас Сервісу:
Кожен підкаталог `services/<service_name>/` зобов'язаний містити:
1. `README.md` — Опис сервісу, REST/WebSocket ендпоінти, порти та змінні середовища.
2. `Dockerfile` — Сувора Zero-Host Docker ізоляція (усі важкі залежності лише всередині контейнера).
3. `src/` — Чистий вихідний код сервісу (Python FastAPI / Node.js).
4. `tests/` — Обов'язковий набір unit-тестів сервісу.

### 🛡️ Непорушні Правила:
- **Zero Host Pollution**: Заборонено встановлювати залежності на хост-машину.
- **Порти**: FastAPI сервіси використовують `8000-8005`, Next.js — `3000-3005`.
- **Безпека**: Файлові операції здійснюються виключно через `DNKIsolatedFileSystem`.
