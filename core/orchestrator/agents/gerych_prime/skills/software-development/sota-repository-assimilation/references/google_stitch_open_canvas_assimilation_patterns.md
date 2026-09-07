# Google Stitch & Open Canvas AI Assimilation Patterns

## Overview
Key technical patterns and contracts extracted from reverse-engineering Google Stitch (`stitch.withgoogle.com`), `@google/stitch-sdk` (Apache 2.0), and `DESIGN.md` spec for integration into DNK OS Open Canvas Engine.

## Core Architectural Pillars

### 1. Model Context Protocol (MCP) Bridge
- **MCP Endpoint**: `https://stitch.googleapis.com/mcp`
- **Authentication**: `STITCH_API_KEY` or OAuth (`STITCH_ACCESS_TOKEN` + `GOOGLE_CLOUD_PROJECT`).
- **Core MCP JSON-RPC Tools**:
  - `list_projects`: Enumerates active canvas projects.
  - `create_project`: Initializes a new multi-viewport canvas.
  - `generate_screen`: Generates responsive HTML/CSS/Tailwind UI DOM frames given a text prompt and `DESIGN.md` tokens.
  - `get_screen`: Retrieves DOM source, CSS, screenshots, and interaction targets.
  - `update_screen`: Performs differential JSON-Patch mutations on existing screen nodes.
  - `extract_design_system_from_url`: Extracts computed CSS styles from a live site and outputs normative `DESIGN.md` YAML front matter.

### 2. Screen DAG & Interactive State Machine
- **Nodes (`ScreenNode`)**:
  - `id`: Unique screen identifier (`scr-12345`).
  - `title`, `device_type` (`mobile` | `tablet` | `desktop`), `position_x`, `position_y`, `width`, `height`.
  - `html_content`, `css_content` (Tailwind CSS v4 ready).
  - `interactions`: List of `InteractionTarget` (CSS selector + event + target screen ID).
- **Edges (`ScreenEdge`)**:
  - `source_screen_id` -> `target_screen_id` triggered by element interaction (`#btn-checkout`).
  - Interactive "Play" Mode: State-machine execution engine for live prototype walkthrough.

### 3. DESIGN.md Normative Token Contract
- **Front Matter (YAML)**:
  - `colors`: `primary`, `secondary`, `tertiary`, `neutral`, `background`.
  - `typography`, `spacing`, `rounded`, `components`.
- **Automated Validation & Export**:
  - WCAG AA/AAA (4.5:1 ratio) contrast linter (`npx @google/design.md lint DESIGN.md`).
  - Native export to Tailwind v3/v4 theme config and W3C DTCG JSON.

### 4. Hexagonal Python Adapter Pattern (`DNKStitchAdapter`)
```python
class DNKStitchAdapter:
    async def list_projects() -> List[Dict[str, Any]]
    async def generate_screen(project_id, prompt, device_type, parent_screen_id) -> ScreenNode
    async def extract_design_system_from_url(url) -> DesignSystemTokenSpec
```
- Integrated into `core/adapters/dnk_stitch_adapter.py`.
- Unit tests verified in `tests/test_dnk_stitch_adapter.py`.
