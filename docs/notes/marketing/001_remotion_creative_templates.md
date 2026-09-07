---
title: "001 Remotion Video & Creative Marketing Templates Library"
date: "2026-09-07"
tags:
  - marketing
  - remotion
  - templates
  - video-ai
  - direct-response
  - prompts
status: "Active"
version: "1.0.0"
---
<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/marketing/001_remotion_creative_templates.md"
purpose: "Standardized production Remotion video creative templates, storyboard schemas, and conversion prompts for DNK OS."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-07"
author: "DNK Swarm (dnk_marketing_cmo & dnk_video_ai_creator)"
--- END DNK-MRH-HEADER -->

# 🎬 001 Remotion Video & Creative Marketing Templates Library

Цей документ стандартизує бібліотеку виробничих шаблонів та інженерних специфікацій генерації відео-креативів за допомогою програмного рушія **Remotion v5 AST** та сервісу `services/dnk_video_ai_creator/remotion_compiler.py`.

Всі шаблони спираються на архітектуру крос-просторового конвеєра, описаного в [[045_cross_workspace_marketing_banner_pipeline|045 Cross-Workspace Marketing Banner Pipeline]], і синхронізовані з інструментом `dnk_video_generate_composition`.

---

## 📐 1. Загальні Інженерні Специфікації

| Параметр | Вертикальний (Reels/Shorts) | Квадрат (Feed/Carousel) | Горизонтальний (Pitch/YouTube) |
|---|---|---|---|
| **Формат (`format_type`)** | `story_9_16` | `square_1_1` | `landscape_16_9` |
| **Роздільна здатність** | 1080 × 1920 px | 1080 × 1080 px | 1920 × 1080 px |
| **FPS (кадрова частота)** | 30 / 60 fps | 30 fps | 60 fps |
| **Цільова тривалість** | 15с (450 кадрів) / 30с (900 кадрів) | 10–15с (300–450 кадрів) | 30–60с (1800–3600 кадрів) |
| **Рендер-компілятор** | `remotion_compiler.py` | `remotion_compiler.py` | `remotion_compiler.py` |

---

## ⚡ 2. Шаблон 1: "Problem-Agitate-Solve (PAS) Hook" (15 секунд, 9:16)

### 🎯 Концепт
Призначений для прямої конверсії холодного трафіку на e-commerce лендінги та вітрини Shopify. Захоплює увагу за перші 1.5 секунди через контрастний динамічний текст та звуковий сплеск.

### ⏱️ Розбивка по кадрах (30 FPS, разом 450 кадрів)
1. **Scene 1: Hook (Кадри 0–90 / 0.0с–3.0с)**
   - *Візуальний ряд*: Швидкий зум на проблему, миготливий бейдж "🚨 ЗУПИНИСЯ", кінетична типографіка.
   - *Voice AI Промпт*: "Ви все ще витрачаєте дні на ручне налаштування рекламних банерів та описів товарів?"
   - *Remotion Transitions*: `spring({ damping: 12, stiffness: 100 })`, масштабування від 0.8 до 1.0.
2. **Scene 2: Agitate (Кадри 91–210 / 3.0с–7.0с)**
   - *Візуальний ряд*: Зниження кольорової температури, показ графіків падіння CTR, розмиття невдалих макетів.
   - *Voice AI Промпт*: "Конкуренти запускають по 50 креативів на день, поки ви узгоджуєте один єдиний макет."
   - *Remotion Transitions*: `interpolate(frame, [90, 150], [1, 0.4])` для оверлею.
3. **Scene 3: Solution & Demo (Кадри 211–360 / 7.0с–12.0с)**
   - *Візуальний ряд*: Спалах світла, безшовна поява DNK OS Visual Canvas, демонстрація автоматичної генерації 1-Click Launch.
   - *Voice AI Промпт*: "DNK OS автоматично синтезує готові відео, копірайт та Shopify Liquid сторінки за 15 секунд."
   - *Remotion Transitions*: Полігональний розліт, 3D картка продукту з відблиском.
4. **Scene 4: Strong CTA (Кадри 361–450 / 12.0с–15.0с)**
   - *Візуальний ряд*: Фірмова плашка бренду, велика пульсуюча кнопка "Спробувати зараз", знижка / промокод.
   - *Voice AI Промпт*: "Тисни на посилання в профілі та отримуй доступ до автономного рою прямо зараз!"
   - *Remotion Transitions*: Нескінченна пульсація кнопки (`Math.sin(frame / 5) * 1.05`).

### 🛠️ Готовий JSON-маніфест для `dnk_video_generate_composition`
```json
{
  "title": "PAS_Ecom_Automated_Launch_15s",
  "format_type": "story_9_16",
  "duration_seconds": 15,
  "props": {
    "template_id": "pas_direct_response_v1",
    "theme": "dark_cyber_neon",
    "colors": {
      "primary": "#3B82F6",
      "accent": "#10B981",
      "background": "#0B0F19",
      "text": "#F8FAFC"
    },
    "typography": {
      "hook_font": "Inter, sans-serif",
      "weight": 900,
      "text_transform": "uppercase"
    },
    "badge_text": "🚨 АВТОНОМНИЙ РІЙ DNK OS",
    "headline": "ГЕНЕРАЦІЯ КРЕАТИВІВ ЗА 15 СЕКУНД",
    "pain_bullet": "Забудьте про ручний монтаж та втрачений час",
    "solution_bullet": "14 ШІ-агентів створюють контент автономно",
    "cta_label": "Отримати доступ",
    "product_price": "$0 (Beta)",
    "music_track": "high_energy_tech_pulse.mp3"
  }
}
```

---

## 💎 3. Шаблон 2: "Feature-Advantage-Benefit (FAB) Innovation Showcase" (30 секунд, 9:16)

### 🎯 Концепт
Фокусується на технічній перевазі та презентації складних технологій (PersonaLive, Diffusion Studio, SCONES Memory) для фаундерів, CMO та digital-агенцій.

### ⏱️ Розбивка по кадрах (30 FPS, разом 900 кадрів)
1. **Кадри 0–150 (0–5с): The Breakthrough (Feature)**
   - Демонстрація PersonaLive — цифрова людина синтезує мову у реальному часі без затримок.
   - Промпт: "Це не відеомонтажер. Це повністю автономний аватар, що говорить у прямому ефірі."
2. **Кадри 151–450 (5–15с): Architectural Power (Advantage)**
   - Зум у бекенд-пайплайн: Fast-Fourier Motion, SCONES Vector Lakehouse, sub-50ms latency.
   - Промпт: "Завдяки інноваційній пам'яті SCONES та квантовій диспетчеризації завдань, точність досягає 99.8%."
3. **Кадри 451–750 (15–25с): Tangible ROI (Benefit)**
   - Порівняльна таблиця вартості виробництва контенту ($500 традиційно vs $0.05 у DNK OS).
   - Промпт: "Скорочуйте витрати на медіавиробництво на 90% та масштабуйте рекламні кампанії у 10 разів."
4. **Кадри 751–900 (25–30с): Conversion Closer**
   - QR-код для переходу, логотип DNK OS, фіксація партнерського статусу.
   - Промпт: "Підключайте свій бізнес до платформи майбутнього вже сьогодні."

---

## 🎨 4. Шаблон 3: "Cross-Workspace Interactive Banner" (1:1 / 16:9)

Шаблон для мультиканальної генерації рекламних банерів та інтерактивних обкладинок.
- Спирається на `core/rag/marketing_banner.py`.
- Автоматично формує SVG/Canvas макет із закругленими картками, градієнтними обводками та чіткими лейблами цін/знижок.

```json
{
  "title": "Cross_Workspace_Product_Banner_1x1",
  "format_type": "square_1_1",
  "duration_seconds": 10,
  "props": {
    "template_id": "clean_glassmorphism_banner",
    "glass_blur": "16px",
    "gradient_angle": 135,
    "highlight_badge": "SOTA 2026",
    "product_title": "DNK Unified Studio",
    "subtitle": "Canvas Engine + Shopify OS 2.0 Integration",
    "price_tag": "Повний стек автоматизації",
    "cta": "Дізнатися більше"
  }
}
```

---

## 🤖 5. Промпт-гайдлайн для генерації Voice AI (`dnk_video_ai_creator`)
- **Темп мовлення**: 1.1x для молодіжного/динамічного сегменту, 0.95x для B2B презентацій.
- **Емоційний окрас**: Впевнений, харизматичний, технологічний (без штучного пафосу та галюцинацій).
- **Фокус на цінності**: Перші 3 слова повинні містити дієслово або цифру ("Скоротіть на 90%...", "14 агентів замість команди...").
