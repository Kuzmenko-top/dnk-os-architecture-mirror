<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/tech/sota_assimilation/capcut/research/RN-CAPCUT-OPENSOURCE-ALTERNATIVES.md"
purpose: "Research Note: Comparative Analysis of CapCut AI Design vs Penpot, Doop, and ComfyUI for DNK OS."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-02"
author: "DNK-e.com Maksym & Gerych"
--- END DNK-MRH-HEADER --- -->

# Research Note: CapCut vs Open-Source Canvas Engines (Penpot / Doop / ComfyUI)

## 1. Executive Summary
This document establishes the comparative baseline between CapCut's proprietary AI Design web canvas and key open-source alternatives:
1. **Penpot**: Open-source vector and design tool built on ClojureScript / SVG / WebAssembly.
2. **Doop / Excalidraw / Fabric.js / Konva**: Lightweight 2D canvas engines.
3. **ComfyUI**: Node-based graph execution engine for diffusion models (SDXL, Flux, Seedream).

## 2. Architectural Comparison Matrix

| Dimension | CapCut AI Design | Penpot | ComfyUI | DNK OS Canvas Target |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Renderer** | WebGL / Canvas2D + ByteDance Engine | SVG / Canvas2D / Rust Wasm | Canvas2D (LiteGraph) / DOM | WebGL2 / WebGPU + DOM overlay |
| **State Architecture** | Centralized Signals / State Store | ClojureScript Atoms / CRDT | Graph Execution DAG | Zustand + Immer + Event Sourcing |
| **AI Integration** | Direct Layer inpainting / Generative API | Plugin-based (REST) | Native Node Execution | Swarm Agentic AST Mutations |
| **Layer Representation** | Hierarchical Node Tree | SVG Tree + Group hierarchy | Execution Flow / Tensor Graph | Multi-type Scene Graph DTO |
| **Extensibility** | Closed Web App | Open Extensible API | Python custom nodes | Native Swarm Protocol (TaskDNA) |
