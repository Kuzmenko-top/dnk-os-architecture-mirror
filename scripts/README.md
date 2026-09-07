# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/README.md"
# purpose: "Canonical Architecture and Governance Guide for DNK OS Automation Scripts"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

# 🛠️ DNK OS AUTOMATION SCRIPTS
## РЕГЛАМЕНТ ДЕТЕРМІНОВАНИХ СКРИПТІВ СИСТЕМИ

Ця директорія містить надійні виконувані скрипти автоматизації, бекапу та обслуговування.

### 🏛️ Правила Скриптів:
- Тільки відносні шляхи (ніяких хардкодних абсолютних шляхів).
- Повна ідемпотентність (повторний запуск не ламає систему).
- Наявність валідації вхідних параметрів та логування помилок.
