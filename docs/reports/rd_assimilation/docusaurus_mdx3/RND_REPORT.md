# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/rd_assimilation/docusaurus_mdx3/RND_REPORT.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

# 📊 R&D Report: Docusaurus Static Documentation & Swizzling Component Architecture

## Секція 1: Executive & Commercial Summary
Docusaurus надає SOTA архітектуру для швидкої побудови та версіонування баз знань та документації на основі React та MDX. Основна цінність — гнучка кастомізація через концепт Swizzling та уникнення дублювання контенту при багатомовній локалізації.

## Секція 2: Core Architectural Patterns & Code Blueprints
### 1. Swizzling Pattern (Wrapping vs Ejecting)
Дозволяє безпечно перевизначати окремі компоненти теми:
```bash
# Обертання компонента (краще для оновлень)
npm run swizzle @docusaurus/theme-classic Footer -- --wrap
```

### 2. Versioned Docs Strategy
Контент заморожується за допомогою знімків, створюючи ізольовані папки версій:
`/versioned_docs/version-1.0.0/`

## Секція 3: DNK OS Mapping Matrix
- **Модуль у DNK OS:** `services/dnk_literature_compiler` та `docs/` publishing pipeline
- **Інтеграція:** Публікація та генерація PDF-версій документації для користувачів та інженерів.

## Секція 4: Executable Skills & Verification
- **Згенеровані навички:** `docusaurus`
- **Верифікація:** Тестова збірка документації через `npm run build` у папці документації завершується без помилок.