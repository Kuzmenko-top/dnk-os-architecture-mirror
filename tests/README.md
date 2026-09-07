# --- DNK-MRH-HEADER ---
# mrh_id: "tests/README.md"
# purpose: "Canonical Architecture and Governance Guide for DNK OS Test Suite & Quality Assurance"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

# 🧪 DNK OS TEST SUITE & QUALITY ASSURANCE
## РЕГЛАМЕНТ АВТОМАТИЗОВАНОГО ТЕСТУВАННЯ СИСТЕМИ

Ця директорія містить повний верифікаційний комплекс тестів (Pytest / E2E).

### 🏛️ Правила Тестування:
- 100% проходження тестів є обов'язковою умовою для завершення будь-якої задачі.
- Тести мають виконуватися швидко (< 5 секунд на весь тестовий комплекс).
- Повна ізоляція від хост-середовища (використання mock-об'єктів та пісочниць).
