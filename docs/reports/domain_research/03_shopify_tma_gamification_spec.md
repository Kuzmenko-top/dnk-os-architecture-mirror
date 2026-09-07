# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/domain_research/03_shopify_tma_gamification_spec.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "projects/03_DNK_Shopify/tech/docs/TMA_GAMIFICATION_SPEC.md"
purpose: "Technical Specification for the Gamified Course Telegram Mini App"
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-07-27"
--- END DNK-MRH-HEADER --- -->

# 🎮 Technical Specification: Gamified Course Telegram Mini App (TMA)

## 1. 🎯 Overview & Architecture

**Goal:** Create a Telegram Mini App (TMA) to serve as the student portal, mission tracker, and leaderboard for the "14-Day E-com Challenge" (DNK Shopify Launch).
**Integration:** The TMA will be deeply integrated into `dnk_telegram_bot` (backend) and use `hub_memory` (PostgreSQL) for state management.

### Tech Stack

- **Frontend (TMA):** React + Vite + `@twa-dev/sdk` (Telegram Web Apps SDK) + TailwindCSS (Glassmorphism UI).
- **Backend (API):** FastAPI (extends `services/dnk_telegram_bot`).
- **Database:** PostgreSQL (`hub_memory`).
- **Verification Engine:** Automated API checks (Shopify Admin API/Storefront API) to verify mission completion.

## 2. 🗄️ Database Schema Design (PostgreSQL)

New tables need to be created in the `hub_memory` database, properly scoped via RLS (Row-Level Security) to `03_DNK_Shopify` project.

### `course_users`

| Column | Type | Description |
| :--- | :--- | :--- |
| `tg_user_id` | `BIGINT` | Primary Key. Telegram User ID. |
| `shopify_store_url` | `VARCHAR` | The `.myshopify.com` domain of the student. |
| `shopify_access_token` | `VARCHAR` | (Optional) Delegated token for auto-verifications. |
| `current_day` | `INT` | Current active mission day (1-14). |
| `dnk_coins` | `INT` | Total score. |
| `joined_at` | `TIMESTAMP` | Cohort tracking. |

### `course_missions`

| Column | Type | Description |
| :--- | :--- | :--- |
| `mission_id` | `INT` | Primary Key (Day 1, Day 2...). |
| `title` | `VARCHAR` | Mission name. |
| `reward_coins` | `INT` | Points awarded. |
| `verification_type` | `VARCHAR` | e.g., `manual`, `api_domain_check`, `api_product_check`. |

### `course_progress`

| Column | Type | Description |
| :--- | :--- | :--- |
| `tg_user_id` | `BIGINT` | Foreign Key -> `course_users`. |
| `mission_id` | `INT` | Foreign Key -> `course_missions`. |
| `status` | `VARCHAR` | `locked`, `in_progress`, `completed`. |
| `completed_at` | `TIMESTAMP` | Timestamp of completion. |

## 3. 🖥️ User Interface (TMA Views)

### A. Dashboard (Home)

- **Header:** User Avatar, Name, Current DNK Coins, Rank (e.g., "Top 15%").
- **Progress Ring:** Circular progress bar showing 14-day completion status.
- **Current Mission Card:** Large card with today's task, video link, and "Verify Completion" button.

### B. Leaderboard (Global & Cohort)

- Live ranking of students based on DNK Coins.
- Gamified UI with top 3 highlighted (Gold, Silver, Bronze styling).
- Anonymous mode support (e.g., "Entrepreneur_491").

### C. Achievement Vault

- Grid of locked/unlocked badges (e.g., "Theme Installed", "First Sale", "Domain Connected").

## 4. ⚙️ Automation & Verification Engine

To minimize manual moderation, the FastAPI backend will feature a `MissionVerifier` class:

```python
class MissionVerifier:
    async def verify_day_2_domain(self, shopify_url: str) -> bool:
        # Pings the Shopify store to check if a custom domain is active and password page is configured/removed.
        pass

    async def verify_day_4_theme(self, shopify_url: str, token: str) -> bool:
        # Uses Shopify API to check if DKK-E / DNK Theme is installed and active.
        pass
```

## 5. 🔔 Push Notification Strategy (via dnk_telegram_bot)

- **Morning (09:00):** ☀️ "Day {X} unlocked! Today's mission: {Mission_Name}. Let's build!"
- **Evening (19:00):** 🌙 "Reminder: Don't break your streak. Verify your progress to earn {Y} DNK Coins."
- **Event-Driven:** 🏆 "You just reached Top 10 in the Leaderboard!"

## 6. 🚀 Implementation Roadmap (Next Steps)

1. **[TECH]** Initialize Vite + React project under `services/dnk_telegram_bot/tma_edu_app`.
2. **[TECH]** Write SQL migrations for `course_users`, `course_missions`, `course_progress`.
3. **[TECH]** Create FastAPI endpoints in `dnk_telegram_bot` for TMA communication (`/api/v1/edu/leaderboard`, `/api/v1/edu/verify`).
4. **[TECH]** Integrate `twa-dev/sdk` and map Telegram Web App context to user sessions.