---
mrh_id: DNK-OVERVIEW-001
title: DNK Repositories & Roles
author: Maxim
license: MIT
version: 1.0.0
---

# DNK-OVERVIEW-001: DNK Repositories & Roles

## 1. DNK_HUB — R&D Laboratory

- **Purpose**: Long-term research, experiments, knowledge base, prototype services.
- **Location**: `/Users/<username>/Kuzmenko/MY_LIFE_WORK/DNK_HUB/`
- **Rules**:
  - Git tracks DNK_HUB content for R&D only.
  - The `DNK_HUB/` directory inside DNK_HUB is **ignored by DNK_HUB git**:
    - DNK_HUB does NOT track MVP code.
    - DNK OS is treated as a separate, nested repository.

## 2. DNK OS → GitHub: Kuzmenko-top/DNK_OS_MVP

- **Purpose**: Core DNK OS MVP product (first minimal version to deploy and use).
- **Location**: `/Users/<username>/Kuzmenko/MY_LIFE_WORK/DNK_HUB/`
- **Remote**: `https://github.com/Kuzmenko-top/DNK_OS_MVP`
- **Contains**:
  - Application code (backend, frontend, agents).
  - Task Forest (`docs/tasks/`).
  - Architecture specs (`docs/tech/specs/`).
  - User docs (`docs/user/`).

## 3. Assimilation Audit Repo → dnk-os-mvp-assimilation

- **Purpose**: Mentor audit buffer for assimilation and architecture artifacts.
- **Remote**: `https://github.com/Kuzmenko-top/dnk-os-mvp-assimilation`
- **Contains**:
  - Only Markdown artifacts:
    - Research reports (RN-XXX).
    - Architecture specs (DNK-ARCH-XXX).
    - Component specs (DNK-COMP-XXX).
    - Security specs (DNK-SEC-XXX).
    - Assimilated SKILL indices.
- **No application code, no secrets, no logs.**

## 4. High-Level Workflow

1. Work & code in **DNK OS**.
2. Export assimilation docs to **dnk-os-mvp-assimilation** for mentor review.
3. Keep R&D experiments in **DNK_HUB**, but migrate validated parts into DNK OS according to new standards.
