# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/discourse_discourse.md"
# purpose: "SOTA Ingested Knowledge Card for discourse/discourse."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-18"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🧬 SOTA Knowledge Card: discourse/discourse

## 📊 Overview Metadata
- **Repository**: discourse/discourse
- **License**: GPL-2.0
- **Evolution Track**: **Reverse Engineering Synthesis** (100% Clean-Room MIT implementation)

---

## 🏛️ Extracted Architecture & Stack
- **Primary Stack**: Ruby on Rails 7+ / PostgreSQL 15+ / Redis 7+ / Sidekiq / Ember.js (Fastboot) / REST & FastMCP Bridge
- **Architecture Principle**: Event-driven Monolith with Real-Time MessageBus & Hierarchical Permission Guardian

### Key Extracted Features:
- **Guardian Security & Authorization Matrix**: Context-aware granular policy gatekeeping (`can_see_topic?`, `can_create_post?`, `can_moderate?`, `can_edit_tag?`).
- **Trust Levels (0-4) Lifecycle**: Automated progression and permission scaling for community safety (TL0 Newuser, TL1 Basic, TL2 Member, TL3 Regular, TL4 Leader).
- **MessageBus WebSocket Architecture**: High-throughput real-time push with Redis pub/sub backplane and `last_message_id` sequence tracking.
- **Topic & Post Directed Acyclic Graph (DAG)**: Linear/threaded discourse model with full-text search (`pg_trgm`) and reply linkage (`reply_to_post_number`).
- **Zero-Downtime Migration & Plugin Hooks**: Extensible lifecycle hooks for micro-services and LLM agents.

---

## 🛡️ License & Legal Directives
RESTRICTIVE LICENSE (GPL-2.0). Direct copying of code or files is 100% prohibited.
Clean-Room Design specifications:
1. Study the extracted schemas and API parameters.
2. Design a clean, independent module from scratch under MIT license.
3. Use only public specifications and sovereignly written algorithms.

---

## 📋 Extracted Technical Schemas
```json
{
  "TopicSchema": {
    "id": "int",
    "title": "str",
    "category_id": "int",
    "user_id": "str",
    "posts_count": "int",
    "archetype": "regular|private_message|banner",
    "status": "active|closed|archived"
  },
  "PostSchema": {
    "id": "int",
    "topic_id": "int",
    "post_number": "int",
    "raw_content": "str",
    "cooked_html": "str",
    "reply_to_post_number": "Optional[int]",
    "like_count": "int"
  },
  "TrustLevelSchema": {
    "user_id": "str",
    "level": "0_newuser|1_basic|2_member|3_regular|4_leader",
    "is_locked": "bool",
    "daily_rate_limits": "dict"
  },
  "MessageBusPacket": {
    "channel": "str",
    "message_id": "int",
    "payload": "dict",
    "target_user_ids": "Optional[List[str]]"
  }
}
```

---

*Ingested and verified by DNK OS DNA Assimilation Engine.*
