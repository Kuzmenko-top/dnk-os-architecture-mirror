# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/rd_assimilation/storefront_skills/RND_REPORT.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

# 📊 R&D Report: Shopify Storefront Vibe-Code & Island Design Architecture

## Секція 1: Executive & Commercial Summary
`storefront-skills` пропонує концепцію **Vibe-Code** та **Island Design** для генерації надшвидких, висококонверсійних e-commerce сторінок. Головна цінність — генерація чистого HTML + Tailwind CSS із інтерактивними React-острівцями, що усуває потребу у важких JS фреймворках на клієнті.

## Секція 2: Core Architectural Patterns & Code Blueprints
### 1. React-Islands with data-props
Генерація острівців інтерактивності (наприклад, кошик чи вибір кольору) на статичній HTML-сторінці:
```html
<div data-island="AddToCartButton" data-props='{"variantId": "123456"}'>
  <!-- Fallback static button -->
  <button class="bg-black text-white px-6 py-2">Add To Cart</button>
</div>
```

### 2. Multi-Flow Layout Spacing Contracts
Суворе дотримання spacing-сіток для збереження візуальної цілісності під час ШІ-генерації:
`py-12 md:py-16 lg:py-20` та `w-full max-w-7xl px-4 mx-auto`.

## Секція 3: DNK OS Mapping Matrix
- **Модуль у DNK OS:** `core/orchestrator/agents/herich_librarian/skills/shopify-storefront-ai-generation-ops/`
- **Інтеграція:** Застосовується при автоматичній побудові нових дизайнів e-commerce у `dnk_shopify`.

## Секція 4: Executable Skills & Verification
- **Згенеровані навички:** `shopify-storefront-ai-generation-ops`
- **Верифікація:** Тест `services/dnk_git_research/tests/test_ecommerce_skills.py` перевіряє генерацію Vibe-Code.