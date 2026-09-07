# Visual Canvas Control Panel & TaskDNA Synchronization Protocol

## Purpose & Overview
Integrates TaskDNA DAG execution graphs and live Swarm Agent telemetry directly with Obsidian JSON Canvas (`.canvas`) files. Enables a real-time, bidirectional Visual Control Panel (Пульт Керування) in Obsidian without requiring third-party plugins.

Key modules:
- **Core Engine**: `core/orchestrator/visual_canvas_control.py` (`VisualCanvasControlPanel`)
- **CLI Runner**: `scripts/system/visual_canvas_control_runner.py`
- **Verification Suite**: `tests/verification/test_visual_canvas_control.py`
- **SSOT Vault Note**: `docs/notes/058_Visual_Canvas_Control_Panel_Architecture.md`

---

## 1. Topological Columnar Layout & Phase Groups

To prevent overlapping nodes and provide intuitive Left-to-Right progression:
- **X-axis (Dependency Depth)**:
  $$X = \text{base\_x} + (\text{depth} \times 380\text{px})$$
  - `depth 0` (Backlog/Analysis): $X = 0$
  - `depth 1` (Implementation/Code): $X = 380$
  - `depth 2` (Audit/Verification): $X = 760$
- **Y-axis (Phase Level Stacking)**:
  $$Y = \text{base\_y} + (\text{level\_index} \times 240\text{px})$$
- **Obsidian Phase Groups (`type: "group"`)**:
  Encloses nodes of each execution stage into background bounding boxes (`width: 340`, `height: 480`), visually grouping tasks by phase.

---

## 2. Standard Obsidian Canvas Color Palette

Strict adherence to Obsidian Canvas v1.0 numerical color indices:

| Code | Color Name | Swarm Status / Stage | Meaning |
|---|---|---|---|
| `"3"` | Yellow / Amber | `backlog`, `pending`, `analysis` | Planned task awaiting execution |
| `"5"` | Blue / Cyan | `in_progress`, `development` | Active Swarm Agent working |
| `"4"` | Green / Emerald | `done`, `completed` | Verified with green test gate |
| `"6"` | Purple / Violet | `review`, `audit` | Adversarial audit / Review phase |
| `"1"` | Red / Crimson | `blocked`, `failed` | Test failure or security blocker |

---

## 3. Master HUD Summary Node

Anchored on the top-left margin ($X = -420, Y = 0, W = 360, H = 260$):
- **Live Progress Bar**: e.g., `[████░░░░░░] 33%`
- **Milestones Counter**: e.g., `**1** / **3** completed`
- **Active Agents**: Formatted list of engaged Swarm Workers (`🛠️ Gerych Builder`, `🛡️ Gerych Auditor`, etc.)
- **Master Quality Gate**: Live state badge (`READY`, `RUNNING`, `PASSED`)

---

## 4. CLI Runner Usage Recipes

```bash
# 1. Decompose goal and scaffold interactive .canvas control panel
python3 scripts/system/visual_canvas_control_runner.py \
  --goal "Build Canvas Engine and Shopify Checkout UI" \
  --output ./docs/notes/017_Swarm_TaskDNA_Control_Panel.canvas

# 2. Transition task status when an agent finishes an atomic slice
python3 scripts/system/visual_canvas_control_runner.py \
  --update-node slice_1_arch \
  --stage done \
  --notes "Architecture approved" \
  --canvas-path ./docs/notes/017_Swarm_TaskDNA_Control_Panel.canvas

# 3. Inspect real-time telemetry and HUD status
python3 scripts/system/visual_canvas_control_runner.py \
  --status \
  --canvas-path ./docs/notes/017_Swarm_TaskDNA_Control_Panel.canvas

# 4. Bidirectional synchronization with TaskForest
python3 scripts/system/visual_canvas_control_runner.py --sync-forest
```

---

## 5. Critical Pitfalls & Distilled Fixes

1. **Regex Worker Extraction Robustness**:
   - *Pitfall*: Matching worker names with restrictive patterns like `\*\*Worker\*\*:\s*`([a-z_]+)`` breaks when workers are rendered with human titles or emojis (e.g. `🛠️ Gerych Builder`).
   - *Fix*: Use `r"\*\*Worker\*\*:\s*([^\n]+)"` and strip markdown markers cleanly.

2. **Parent-Child Hierarchy Edge Generation**:
   - *Pitfall*: Tasks specifying `parent_id` but omitting `depends_on` lose visual dependency arrows.
   - *Fix*: In edge generation, inspect both `depends_on` lists AND `parent_id` links, generating directed edges from parent to child with label `subtask`.

3. **Atomic HUD Telemetry Recalculation**:
   - *Pitfall*: Updating a node's stage without rebuilding the HUD card causes visual desync between card status and summary progress.
   - *Fix*: `update_canvas_node_status()` MUST re-evaluate all node states and rewrite the `control_panel_hud` node text in the same atomic write.
