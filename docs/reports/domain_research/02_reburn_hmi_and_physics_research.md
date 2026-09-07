# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/domain_research/02_reburn_hmi_and_physics_research.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

# 🌡️ ReBurn Smoker HMI & Physical Smoker Controller Research

---

- **Domain**: `02_ReBurn`
- **Target Modules**: `services/dnk_smoker_hmi`, `services/dnk_reburn_connector`
- **Status**: `Active`

## Executive Summary
This document registers the core physical parameters and controller loop behaviors for the ReBurn Smoker automated heating, smoke-induction, and telemetry system.

## Core Architectural Patterns
- **Modbus/TCP & PID Loop Integration**: Reads thermal values from K-type thermocouples, compares them against setpoint values, and calculates the duty cycle of the solid-state relay (SSR) driving the wood-chip heater elements.
- **Safety Interlocks**: Automatic cut-offs when temperature exceeds 300°C or fan tachometer falls below 500 RPM.