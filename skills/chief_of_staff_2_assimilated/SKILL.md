---
name: chief_of_staff_2_assimilated
description: "Assimilated SOTA patterns and architecture from jdpolasky/chief-of-staff-2 (Obsidian-first AI Chief of Staff, Chair Anatomy, Subtraction Rebuild, 13 Laws)."
version: "2.0.0"
category: "software-development"
assimilated_at: "2026-09-07"
track: "Track 1: Direct Template Assimilation (Permissive)"
license: "MIT"
target_worker: "gerych_researcher"
---

# 🌐 Chief of Staff v2 Assimilation Guide & Patterns

Meta-index and operational recipes assimilated from **[jdpolasky/chief-of-staff-2](https://github.com/jdpolasky/chief-of-staff-2)**.

## 📌 Repository Intel & Legal Boundary
- **Repository**: `jdpolasky/chief-of-staff-2`
- **License**: `MIT` (Permissive, commercial-safe)
- **Assigned Evolution Track**: `Track 1: Direct Template Assimilation`
- **Core Insight**: Plain markdown in an Obsidian vault is the permanent canon; AI harnesses are thin disposable adapters. Eliminate memory bloat via the "Subtraction Rebuild".

---

## 🏛️ Key Architectural Concepts

### 1. The 4-Part Chair Anatomy
Every functional domain ("Chair") is structured identically:
```
<Chair Name>/
├── <Chair Name> Skill.md     # Thin, stateless procedural instructions (executable by cheap models)
├── <Chair Name> Source.md    # Current state sheet (open loops, current decisions, next physical action)
├── Parts/ or Research/       # Reference assets, specs, and domain investigations
└── Archive/                  # Dated write-once transcripts (YYYY-MM-DD Title.md; never auto-loaded)
```

### 2. Inward-Facing "Physical Plant" Chair
Isolates maintenance of harness configuration, skill routing, cron jobs, and vault hygiene from user-facing domain work (Planner, Career, Health, Money).

### 3. The 13 Laws
1. **Portability is the prime law**: Canon in markdown; harness is disposable.
2. **Routine work via code; model makes judgments**.
3. **Additions earn their way in**: Rules added only after 2nd mistake; 1 rule in = 1 rule retired.
4. **Every fact has one home**: SSOT, no copy-pasting.
5. **Nothing scheduled dies quietly**: Every cron job carries a heartbeat.
6. **Done means saved, wired, and tested**: Backed by verified tool output.
7. **Delegate down**: Routine work to fast/cheap models; top tier for architecture.
8. **Match effort to question size**: Concise when small, deep when large.
9. **Museum, never delete**: Archive retired material once replacement is proven.
10. **Keep the system boring**: System serves the work, never becomes its own project.
11. **Snapshots over living files**: Dated write-once notes.
12. **Born lazy**: 1-line index, load full bodies strictly on-demand (LOD).
13. **Finish it or put it in user's hand**: Single paste-and-run deliverables.
- **Coda: Subtraction over surveillance**: If a broken item was unmissed, eliminate it.

---

## 🧪 Operational Recipes

### Recipe 1: Scaffolding a New Domain Chair
To add a new chair (e.g. `E-Commerce` or `Product Engine`), create the 4-part structure:
```bash
CHAIR="Ecommerce"
mkdir -p "docs/notes/C-Suite/${CHAIR}/Archive"
mkdir -p "docs/notes/C-Suite/${CHAIR}/Parts"
```

Create `<CHAIR> Skill.md`:
```markdown
---
title: ${CHAIR} Skill
type: skill
owner: ${CHAIR}
tags: [c-suite, skill, ${CHAIR_LOWER}]
---
# ${CHAIR} Skill
1. Read [[${CHAIR} Source]] to load current state and open loops.
2. Execute the requested domain action.
3. Update [[${CHAIR} Source]] with results and next physical action.
```

Create `<CHAIR> Source.md`:
```markdown
---
title: ${CHAIR} Source
type: source
owner: ${CHAIR}
tags: [c-suite, source, ${CHAIR_LOWER}]
---
# ${CHAIR} Source
## Current State
- Active objectives: ...
## Open Loops
- [ ] Task 1: ...
## Next Physical Action
- The single next physical step to perform.
```

### Recipe 2: Executing Morning Briefing Rhythm
```markdown
1. Inspect calendar and active inbox/alerts for today.
2. Read Source files across active chairs.
3. Deliver 3-part brief:
   - Today: schedule + priority tasks.
   - This Week: upcoming milestones and deadlines.
   - The Big Picture: 1 sentence connecting today to long-term mission.
4. Conclude with exactly ONE next physical action (no shame, no overwhelm).
```

### Recipe 3: Executing End-of-Session Closure
```markdown
1. Identify real wins (accurate, un-inflated).
2. Write state changes back to the owning Chair's Source.md.
3. Record next physical action.
4. Verbatim log chat transcript to Chair's Archive/ if requested.
5. Stop immediately (no trailing questions).
```

---

## ⚠️ Pitfalls & Invariants
1. **[ZERO_ABSOLUTE_PATHS]**: All paths in vault notes and skills must be relative (`./`, `../`) or use `[[wikilinks]]`.
2. **[BORN_LAZY]**: Never bulk-load all Archive files into model context. Load strictly on-demand.
3. **[SUBTRACTION_INVARIANT]**: When an automated check or rule causes more maintenance overhead than real leverage, delete it.
