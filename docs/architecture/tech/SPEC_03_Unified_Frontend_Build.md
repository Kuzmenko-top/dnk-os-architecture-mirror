# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/SPEC_03_Unified_Frontend_Build.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

# Unified Frontend Build Specification

## Overview
This document describes the setup of the unified frontend for DNK OS, integrating Open-Design Canvas, Hermes Execution Chat, and Swarm & Telemetry Map into a single web interface.

## Structure
The frontend is located at visual_shell/web_ui/ and is built using Next.js 14 with React.

### Key Components
1. Open-Design Canvas Zone: Implemented using ReactFlow/xyflow for node-based canvas to create task trees and display relationships.
Test line

## Overview
This document describes the setup of the unified frontend for DNK OS, integrating Open-Design Canvas, Hermes Execution Chat, and Swarm & Telemetry Map into a single web interface.
## Structure
The frontend is located at visual_shell/web_ui/ and is built using Next.js 14 with React.

### Key Components
1. Open-Design Canvas Zone: Implemented using ReactFlow/xyflow for node-based canvas to create task trees and display relationships.
2. Hermes Execution Chat Zone: Live terminal for execution and dialogue with Gerych.
3. Swarm & Telemetry Map Zone: Indicator of active subagents in the swarm and token/$ costs.

## Technical Details
- Framework: Next.js 14 (App Router)
- Language: JavaScript (with React 18)
- Styling: CSS Modules (can be extended to TailwindCSS)
Test
## Technical Details
- Framework: Next.js 14 (App Router)
- Language: JavaScript (with React 18)
- Styling: CSS Modules (can be extended to TailwindCSS)
Test line with parentheses
- State Management: React Context or Zustand (to be implemented)
- State Management: React Context or Zustand (to be implemented)
Test Integration
Test/line
Test: (something)
- Integration: FastMcp WebSocket/API binding to connect to the kernel.py server (port 8000/3001)

## Files Created
- package.json: Defines dependencies and scripts.
- pages/index.js: Basic homepage placeholder.
- public/: Directory for static assets (to be added).
- styles/: Directory for CSS styles (to be added).

## Setup Steps
1. Initialized npm project with npm init -y.
2. Installed core dependencies: next@latest, react@18, react-dom@18.
3. Created the basic page structure under pages/.
4. Configured npm scripts for development, build, and start.

## Next Steps
- Implement the three zones using appropriate libraries (ReactFlow for canvas, xterm.js for terminal, etc.).