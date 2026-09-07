# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/agents/gerych_prime/skills/software-development/sota-repository-assimilation/references/chief_of_staff_obsidian_chair_anatomy_and_subtraction_rebuild.md"
# purpose: "SOTA Reference: jdpolasky/chief-of-staff-2 Obsidian-First Chair Anatomy, Subtraction Rebuild, and 13 Operational Laws"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "Gerych Prime & Maxim"
# --- END DNK-MRH-HEADER ---

# 🧬 SOTA Reference: Chief of Staff v2 (jdpolasky/chief-of-staff-2)

## 📌 Context & Motivation
Many AI operating systems collapse under self-inflicted bloat:
1. Memory systems mutate into tiered indices, decay rules, and logs that require their own audit tools.
2. Hook proliferation triggers cascading latency and silent failures.
3. Founders spend their mornings fixing the assistant instead of doing high-leverage work (breaking Law 10: *The system may never become its own project*).

`chief-of-staff-2` provides the proven antidote: a complete "Subtraction Rebuild" based on plain markdown in Obsidian, disposable harnesses, strict 4-part chair anatomy, an inward-facing maintenance chair ("Physical Plant"), and 13 operational laws.

---

## 🏛️ 1. The 4-Part Chair Anatomy
Every role / domain worker ("Chair") in the personal AI C-suite follows this exact invariant structure:

```
[ Chair Folder ]/
├── <Chair> Skill.md     # Thin, stateless instructions. Followable by cheap/fast models.
├── <Chair> Source.md    # Active state sheet. Open loops, active decisions, next physical action.
├── Parts/ or Research/  # Domain reference assets, specifications, schemas, working documents.
└── Archive/             # Dated write-once transcripts (YYYY-MM-DD Title.md). Never indexed or auto-loaded.
```

### Invariant Rules for Chair Anatomy:
- **Skill**: Contains zero session state and zero history. Must fit in small context windows.
- **Source**: Single Source of Truth (SSOT) for current status. Read at session start, rewritten at session end.
- **Archive**: Write-once history. Never auto-loaded (respects Law 12: *Born Lazy*). Loaded strictly when specific historical recall is explicitly requested.

---

## 🏢 2. The Inward-Facing "Physical Plant" Chair
Most systems blend infrastructure management with user task execution, leading to context contamination and distraction.
Chief of Staff v2 isolates all internal upkeep into a dedicated inward-facing chair:

- **Outward-Facing Chairs**: Planner (Time), Career Coach (Strategy), Health (Energy), Money (Runway), Product/Builder (Engineering).
- **Inward-Facing Chair (`Physical Plant`)**:
  - Owns: Harness configuration, permissions, skill routing, cron heartbeat verification, vault directory structure.
  - Does NOT own: Domain content or user decisions.
  - Mandate: *"Finish the machinery well enough that the user stops having to think about it."*

---

## ⚖️ 3. The 13 Operational Laws
1. **Portability is the Prime Law**: The canon lives in human-readable markdown; any agent harness (Hermes, Claude Code, Cursor) is a thin, disposable adapter rebuildable in 1 hour.
2. **Routine Work via Code; Model Makes Judgments**: Never ask an LLM to derive what a 10-line Python or bash script can execute deterministically.
3. **Additions Earn Their Way In**: A mistake must happen twice before creating a new rule or hook. One rule added = one retired rule pruned.
4. **Every Fact Has One Home**: Never duplicate facts across files. Cross-link via wikilinks.
5. **Nothing Scheduled Dies Quietly**: Scheduled jobs must emit visible heartbeats or fail with alerts.
6. **Done Means Saved, Wired, and Tested**: Work is only complete when backed by real tool verification.
7. **Delegate Down**: Routine formatting and scans run on cheap/fast models; save frontier models for architecture and adversarial audits.
8. **Match Effort to Question Size**: Provide punchy answers for simple questions; reserve deep reasoning for architectural decisions.
9. **Museum, Never Delete**: Archive retired components rather than destructively deleting historical context.
10. **Keep the System Boring**: The system exists to serve the work; it must never become its own black hole.
11. **Snapshots Over Living Files**: Prefer dated write-once session notes over files undergoing continuous mutation.
12. **Born Lazy**: Maintain a 1-line index; load full text only when explicitly triggered (Level-of-Detail / LOD).
13. **Finish It or Put It in the User's Hand**: Never leave dangling half-steps; deliver single-action CLI recipes.
- **Coda: Subtraction Over Surveillance**: If an automated monitor or rule broke silently and nobody missed it, delete it.

---

## 🔄 4. Universal Session Rhythms

### Morning Briefing (`Morning.md`)
- Inspect schedule and active alerts.
- Read active Chair `Source.md` files.
- Produce 3 blocks:
  1. **Today**: Schedule + priority tasks.
  2. **This Week**: Deadlines and rhythm milestones.
  3. **The Big Picture**: 1 sentence connecting today's effort to the founder mission.
- End with **one next physical action** (zero guilt, zero overwhelm).

### Session Closure (`End.md`)
- Acknowledge verified wins.
- Sync state mutations back to the owning Chair's `Source.md`.
- Record the single next move.
- Halt execution cleanly without open-ended trailing questions.
