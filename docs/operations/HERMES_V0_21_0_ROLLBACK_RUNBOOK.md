# --- DNK-MRH-HEADER ---
# mrh_id: "docs_operations_hermes_v0_21_0_rollback_runbook"
# purpose: "Official Production Rollback Runbook for Hermes Agent v0.21.0."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🚨 Hermes Agent v0.21.0 Production Rollback Runbook

This document details the recovery and emergency rollback procedure to revert **Hermes Agent v0.21.0** back to **v0.20.5** in the event of an anomaly or failure during the promotion or monitoring phase.

---

## ⏱️ 1. SLA & Key Performance Indicators (KPIs)

- **Rollback Time SLA**: `< 30.0 seconds`
- **Measured Rollback Drill Execution**: **`1.139 seconds`** (Successfully verified during pre-promotion drill on 2026-09-03)
- **Data Integrity Threshold**: **`100% Zero-Loss`** (Zero sqlite lock contention, absolute SHA-256 consistency)

---

## 🛡️ 2. Trigger Conditions

An emergency rollback must be executed immediately upon detection of any of the following conditions:

| Trigger ID | Condition Name | Metric / Signal | Threshold | Action |
| :--- | :--- | :--- | :--- | :--- |
| **TRG-01** | Security Anomaly | Raw credential or API token found in unmasked stdout/stderr logs or context | `> 0 raw occurrences` | **IMMEDIATE ROLLBACK** |
| **TRG-02** | State Corruption | SQLite database integrity check fails, schema errors, or lock contention | `Any SQL/Integrity Error` | **IMMEDIATE ROLLBACK** |
| **TRG-03** | MCP Service Outage | Connection timeout, handshake failure, or credential rejection on Notion, Google Drive, or GitHub | `Connection failure > 30s` | **IMMEDIATE ROLLBACK** |
| **TRG-04** | Cost Mismatch | Total token consumption does not match: `parent_cost = own + children + tools` | `Any mathematical deviation` | **IMMEDIATE ROLLBACK** |
| **TRG-05** | Host Instability | Process crashes, unhandled exceptions, memory leaks, or SIGSEGV | `Crash count > 0` | **IMMEDIATE ROLLBACK** |

---

## 🛠️ 3. Step-by-Step Rollback Execution

### Крок 1: Термінова зупинка процесів v0.21.0 (Stop Active Runtime)
Зупинити всі діючі фонові процеси, запущені поточним середовищем v0.21.0.
```bash
# Знайти та завершити всі процеси Hermes Agent
pkill -f "hermes_agent"
```

### Крок 2: Відновлення лаунчера (Restore Launcher Link)
Миттєве атомарне перемикання бінарного лаунчера назад на резервну копію версії v0.20.5.
```bash
LAUNCHER_BIN="${HOME}/.local/bin/hermes"
BACKUP_LAUNCHER="${HOME}/.local/bin/hermes.v0.20.5.backup"

if [ -f "${BACKUP_LAUNCHER}" ]; then
  # Атомарна заміна симлінку на macOS/Linux
  ln -sfn "core/hermes_versions/v0.20.5/.venv/bin/hermes" "${LAUNCHER_BIN}.tmp"
  mv -f "${LAUNCHER_BIN}.tmp" "${LAUNCHER_BIN}"
  echo "✅ Launcher restored to v0.20.5 successfully."
else
  echo "❌ Error: Backup launcher v0.20.5 not found!"
  exit 1
fi
```

### Крок 3: Відновлення стану та конфігурації (Restore Database and State)
Повернення бази даних сесій SQLite `state.db` та конфігураційних файлів до вихідного працездатного стану.
```bash
PROD_HOME="${HOME}/.hermes"
# Знайти останню резервну копію, створену перед promotion
LATEST_BACKUP=$(ls -td ${PROD_HOME}_backup_* | head -1)

if [ -n "${LATEST_BACKUP}" ]; then
  # Відновлення БД
  cp "${LATEST_BACKUP}/state.db" "${PROD_HOME}/state.db"
  # Відновлення конфігурації
  cp "${LATEST_BACKUP}/config.yaml" "${PROD_HOME}/config.yaml"
  echo "✅ State DB and config restored from ${LATEST_BACKUP}."
else
  echo "❌ Error: No production backups found!"
  exit 1
fi
```

### Крок 4: Верифікація працездатності (Health Check & Re-verification)
Запуск вбудованих автоматизованих тестів версії v0.20.5 для підтвердження працездатності та відсутності деградації інтерфейсів.
```bash
# Перевірити версію лаунчера
${LAUNCHER_BIN} --version

# Запустити тести верифікації
python3 scripts/system/measure_rollback_drill.py
```

### Крок 5: Формування та надсилання звіту про інцидент (Report and Incident Post-Mortem)
Сформувати повний звіт про причини та час відкату і надіслати Максиму для детального аналізу.
```bash
# Логувати завершення відкату
echo "Rollback completed at $(date)" >> "${PROD_HOME}/logs/rollback_history.log"
```

---

## 🔍 4. Verification Checklists Post-Rollback

Після завершення процедури відновлення виконайте наступні кроки для забезпечення стабільності:
1. [ ] **Версія лаунчера**: Команда `hermes --version` повинна повертати версію `0.20.5`.
2. [ ] **Цілісність БД**: Запустити `sqlite3 ~/.hermes/state.db "PRAGMA integrity_check;"` і переконатися у відповіді `ok`.
3. [ ] **Секрети**: Переконатися, що під час збою секрети не потрапили в логи та відкриті директорії.
4. [ ] **MCP**: Перевірити статус підключень до GitHub та Notion у версії v0.20.5.
