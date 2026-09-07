# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/rd_assimilation/meta_ads_analyzer/RND_REPORT.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

# 📊 R&D Report: Meta Ads Auction Diagnostics Engine

## Секція 1: Executive & Commercial Summary
`meta-ads-analyzer` фокусується на виявленні та діагностиці проблем рекламних кампаній Meta Ads (Facebook/Instagram). Він дозволяє уникнути передчасного ручного вимкнення адсетів (через розуміння Breakdown Effect) та вчасно сигналізує про вигорання креативів, що дозволяє економити до 30% рекламного бюджету.

## Секція 2: Core Architectural Patterns & Code Blueprints
### 1. Creative Fatigue Formula
Діагностика вигорання креативів на основі CTR та частоти показів:
$$\text{Fatigue} = \text{Frequency} > 3.5 \quad \text{and} \quad \text{CTR} < 1.0\%$$

### 2. Funnel Bottleneck Diagnostics Logic
```python
def diagnose_meta_funnel(cpm, ctr, cvr, target_cpa):
    issues = []
    if cpm > 30 and ctr < 1.0:
        issues.append("Visual Hook Fatigue / Audience Mismatch")
    if ctr > 2.0 and cvr < 1.5:
        issues.append("Landing Page / PDP Conversion Friction")
    return issues
```

## Секція 3: DNK OS Mapping Matrix
- **Модуль у DNK OS:** `services/dnk_shopify/src/meta_ads_analyzer.py`
- **Інтеграція:** Інтегровано у рекламний монітор, що надсилає сповіщення у Telegram-бот при виявленні фази "Learning Phase Limited".

## Секція 4: Executable Skills & Verification
- **Згенеровані навички:** `meta-ads-analyzer`
- **Верифікація:** `pytest services/dnk_git_research/tests/test_shopify_calculator.py` валідує розрахунки ROI та CPA.