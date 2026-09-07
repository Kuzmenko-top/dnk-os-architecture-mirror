# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tasks/05_Flowers/Flower_DNK_MEMORY_HUB_001.md"
# purpose: "Task Intake Card for Gerych: Audit & Deploy TencentDB Agent Memory Hub for Swarm Optimization."
# canonical_source: true
# alters_files: ["docker-compose.memory.yml", "core/memory/"]
# triggers_tasks: ["DNK-MEMORY-HUB-001"]
# status: "Ready"
# version: "1.0.0"
# updated_at: "2026-08-26"
# author: "Antigravity (Mentor/Architect)"
# --- END DNK-MRH-HEADER ---

# 🌸 Flower Task Intake Card: DNK-MEMORY-HUB-001

## 🎯 Мета завдання
Розгорнути та інтегрувати **TencentDB Agent Memory Hub** (CodeGraph + LLM-Wiki + Memory Proxy) у DNK OS Swarm для усунення 60-секундних пошукових затримок, забезпечення спільної пам'яті субагентів та прискорення роботи Герича у 5+ разів.

---

## 📋 План виконання для Герича (Chief Orchestrator)

### Етап 1: Аудит та підготовка конфігурації
- [ ] Клонувати або проінспектувати сервіси `TencentDB-Agent-Memory` (`deploy/global-images`).
- [ ] Перевірити сумісність портів (`8124`, `8125`, `8126`, `8127`) із існуючими контейнерами DNK OS (`postgres:5432/5433`, `redis:6379`, `api:8000`).
- [ ] Створити `DNK OS/docker-compose.memory.yml` для безшовного запуску в один клік.

### Етап 2: Інтеграція CodeGraph для репозиторію
- [ ] Підключити CodeGraph модуль до кодової бази `DNK_HUB` та `DNK_HUB`.
- [ ] Запустити тестове індексування AST символів (`taskdna.py`, `CabinetShell.tsx`, `api_client.ts`).
- [ ] Перевірити час пошуку символів через API (цільовий час < 50ms).

### Етап 3: Підключення Hermes / Subagent Proxy
- [ ] Налаштувати `Memory Proxy` (порт `8126`) як прозорий посередник для викликів інструментів.
- [ ] Перевірити роботу субагентів `dnk_koder` та `dnk-dev-01` зі спільним Memory Hub.

### Етап 4: Фінальна верифікація та звіт
- [ ] Виконати тестову сесію аудиту репозиторію за новим протоколом.
- [ ] Підтвердити зменшення часу пошуку з 60с до < 1с.
- [ ] Зберегти технічний звіт у `docs/reports/LAST_EXECUTION_REPORT.md`.

---

## 🛡️ Критерії готовності (Done Definition)
1. Контейнери пам'яті (`dnk-memory-core`, `dnk-memory-knowledge`, `dnk-memory-proxy`) активні та healthy.
2. CodeGraph індексує репозиторій DNK OS.
3. Веб-панель доступна на `http://localhost:8125`.
4. Unit/Integration тести успішно проходять (`pytest`).
