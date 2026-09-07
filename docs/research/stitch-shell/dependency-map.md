# --- DNK-MRH-HEADER ---
# mrh_id: "dependency-map.md"
# purpose: "Карта внутрішніх та зовнішніх залежностей компонентів Stitch."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# author: "Maxim"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

# Dependency Map: Stitch Components

Цей файл описує дерево залежностей та зв'язків між Stitch компонентами.

```
StitchCanvasContainer
 ├── StitchTopHeader (Масштабування, Скидання, Експорт)
 │    └── design.commands (canvas.reset_view, canvas.export)
 ├── StitchLeftAgentPanel (Логи Агентів, Керування станами)
 │    └── design.types (QualityState)
 ├── StitchRightToolbar (Вибір інструментів)
 │    └── design.types (QualityState)
 └── StitchPromptDock (Введення промпту, Швидкі Pills)
      ├── design.commands (design.generate_liquid, design.generate_workspace, etc.)
      └── design.types (QualityState)
```

## Зовнішні залежності (External Packages)
1. **React 18**: Базовий фреймворк UI.
2. **Tailwind CSS**: Утиліти стилізації (класи backdrop-blur, absolute, flex, transition, animate-pulse).
3. **Vitest & @testing-library/react** (Dev): Інфраструктура тестування та інтеграційних сценаріїв.
