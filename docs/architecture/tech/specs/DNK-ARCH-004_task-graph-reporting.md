# 🏛️ Architecture Specification: Task Graph & Reporting (DNK-ARCH-004)
## Title: Task Node Placement Rules & Execution Cycle Auto-Reporting
## Status: Active | Version: 1.0.0 | Author: Maxim | License: MIT

This specification defines the rules for locating tasks within the 5-tier plant scale taxonomy and the structure of completed execution cycle reports under DNK OS.

### 1. Rules for Task Node Placement (Task Forest Taxonomy)
Subtasks are organized strictly hierarchically to mirror natural growth. The agent determines the placement of each new node based on the following classification:
- **`plant_scale: field`**: Root of the project or overall workspace goal (such as `DNK_HUB`).
- **`plant_scale: sector`**: Domain / area of development (such as `Core`, `UI`, `Ecom`).
- **`plant_scale: tree`**: Epic task requiring substantial implementation, lasting from 1 week to several months.
- **`plant_scale: bush`**: Feature-level task requiring 1 to 3 days.
- **`plant_scale: flower`**: Micro-step requiring 1 to 4 hours of focused work.

Each child node's `parent_id` MUST map strictly to its correct next-higher taxonomic tier (e.g., Flower maps to Bush, Bush maps to Tree).

### 2. Execution Cycle Auto-Reporting
When 100% of child tasks (`Task Flower` / `Feature Bush`) under an Epic or Feature are marked `completed`, the system auto-generates an official cycle report:
- **File Path**: `docs/reports/execution_cycles/CYC_{cycle_id}_{name}_REPORT.md`
- **Mandatory Sections**:
  - **Completed Nodes**: Structured list of all closed tasks.
  - **Modified Files**: List of all source code files edited during this cycle.
  - **Execution Rationale**: Short, clear explanation of the architectural approach and decisions.
  - **Lessons Learned**: Cognitive notes to preserve in memory to prevent future regression.
