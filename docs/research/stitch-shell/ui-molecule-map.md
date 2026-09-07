# --- DNK-MRH-HEADER ---
# mrh_id: "ui-molecule-map.md"
# purpose: "Карта молекулярних областей та сітка інтерфейсу Stitch."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# author: "Maxim"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

# UI Molecule Map: Canvas Grid Layout

Візуальне розташування молекул Stitch на екрані користувача:

```
┌─────────────────────────────────────────────────────────────┐
│ [DNK_OS_MVP]             [- 100% + Reset]    [Export] [Share]│ ◄ StitchTopHeader
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌──────────────┐                                ┌───────┐   │
│ │ glm-5.2      │                                │   S   │   │
│ │ Thoughts     │                                │   H   │   │
│ │ & Console    │      (Infinite Canvas Grid)    │   D   │   │ ◄ StitchRightToolbar
│ │              │                                │   M   │   │
│ │ [Logs]       │                                │   F   │   │
│ └──────────────┘                                └───────┘   │
│ ◄ StitchLeftAgentPanel                                      │
│                                                             │
│                        ┌───────────────────┐                │
│                        │ [Pill 1] [Pill 2] │                │
│                        ├───────────────────┤                │
│                        │ [Prompt Input...] │                │
│                        └───────────────────┘                │
│                         ◄ StitchPromptDock                  │
└─────────────────────────────────────────────────────────────┘
```
