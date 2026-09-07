# --- DNK-MRH-HEADER ---
# mrh_id: "docs/beta/BETA_USER_ONBOARDING.md"
# purpose: "Beta User Onboarding Protocol, Google Form Specification & Feedback Loop"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# --- END DNK-MRH-HEADER ---

# 👥 DNK OS Canvas MVP — Beta User Onboarding Protocol

This document defines the onboarding framework, survey specifications, and feedback collection workflows for the first cohort of beta testers for the **DNK OS Canvas Studio MVP**.

---

## 🎯 Program Overview & Timeline

- **Cohort Size**: 5 – 10 Selected Users (Founders, E-commerce Operators, Full-Stack Engineers).
- **Target Launch Date**: `2026-09-07 (Monday)`
- **Evaluation Period**: 1 Week (`2026-09-07` to `2026-09-14`)
- **Key Objective**: Validate core user workflows (E-com quick start, AI Co-Pilot streaming, Swarm Propagation, Canvas export).

---

## 📝 Beta Intake Form (Google Form Specification)

The Google Form is structured to qualify incoming participants and capture their initial requirements:

### Section 1: Participant Identity
1. **Full Name** *(Short Text, Required)*
2. **Work Email** *(Email format, Required)*
3. **Primary Role** *(Single Choice, Required)*
   - Founder / CEO
   - E-Commerce Store Owner / Operator
   - Full-Stack / Frontend Developer
   - UI/UX Designer
   - Other *(Short Text)*
4. **Current E-Commerce Platform / Stack** *(Checkboxes)*
   - Shopify
   - WooCommerce
   - Custom Next.js / Headless
   - None / Planning new brand

### Section 2: Experience & Objectives
5. **AI Experience Level** *(Linear Scale 1–5)*
   - `1 = Novice (rarely use AI tools)` to `5 = Power User (daily prompt engineering/APIs)`
6. **Primary Goal with DNK OS** *(Paragraph, Required)*
   - *Example prompt*: "What specific problem are you hoping the visual canvas and AI swarm will solve for your workflow?"
7. **Which features are most critical to you?** *(Multiple Selection)*
   - ⚡ **AI Co-Pilot** (Streaming assistance on Strategy & Design nodes)
   - 🐝 **Swarm Propagation** (Connecting Strategy → Design → Code → Tasks)
   - 💾 **Export / Import** (Obsidian `.canvas` & JSON state backup)
   - ⏪ **Undo / Redo** (Frictionless timeline editing)
   - 🛍️ **Shopify Liquid Transpilation** (Auto-generating production theme code)

### Section 3: Onboarding Logistics
8. **How did you hear about DNK OS?** *(Single Choice)*
   - Twitter / X
   - Telegram / Community chat
   - Personal invite from Maksym
   - LinkedIn / Technical blog
9. **Would you like a 30-minute 1:1 guided onboarding call?** *(Single Choice, Required)*
   - Yes, absolutely (Schedule Calendly link)
   - No, I prefer self-guided exploration via `USER_GUIDE.md`

---

## 🗺️ 7-Day Beta Tester Journey

```
Day 1 (Sep 7): Welcome & Deployment
  ├── Receive invitation & Docker Quick Start guide
  └── Successful local launch: http://localhost:3000

Day 2-3 (Sep 8-9): First Project Exploration
  ├── Run "E-Com швидкий старт" wizard
  └── Trigger AI Co-Pilot on Strategy node

Day 4-5 (Sep 10-11): Swarm Propagation & Export
  ├── Flow changes to Design and Code nodes
  └── Export production-ready .canvas and theme files

Day 6-7 (Sep 12-14): Retrospective & Feedback
  ├── Submit 5-minute exit survey
  └── Optional 15-minute feedback debrief with Maxim
```

---

## 💬 Exit Feedback Survey (Day 7)

At the conclusion of the test period, users complete a lightweight review:
1. **System Usability Scale (SUS)**: Rating from 1 to 10 on ease of use.
2. **Time to First Value (TTFV)**: Did you achieve a tangible result in under 15 minutes?
3. **Friction Points**: Where did the workflow stall or feel unintuitive?
4. **Feature Requests**: What is the #1 feature missing before you would use this weekly?
5. **Net Promoter Score (NPS)**: How likely are you to recommend DNK OS to a peer? (0–10)

---

## 📬 Support & Communication Channels
- **Dedicated Telegram Channel**: Private support group for instant bug reports and questions.
- **Direct Lead Contact**: Maksym Kuzmenko (`DNK-e.com`).
- **Issue Tracking**: Bugs escalated directly to Gerych Swarm for rapid patch turnaround.
