# --- DNK-MRH-HEADER ---
# mrh_id: "core/README.md"
# purpose: "Canonical Architecture and Governance Guide for DNK OS Core Kernel"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

# ⚙️ DNK OS CORE KERNEL
## РЕГЛАМЕНТ РОЗРОБКИ ЯДРА СИСТЕМИ

Ця директорія містить фундаментальні механізми маршрутизації, синтезу патернів та безпеки.

### 🏛️ Модулі Ядра:
- `kernel.py` — Головне ядро FastMCP та обробки подій.
- `omni_router.py` — Розумна маршрутизація запитів та інструментів.
- `canvas_engine.py` — 5-атомний рушій обробки графу полотна.
- `pattern_synthesizer.py` — Генератор та валідатор агентних патернів.
- `tests/` — Обов'язковий набір тестів ядра (100% проходження).
