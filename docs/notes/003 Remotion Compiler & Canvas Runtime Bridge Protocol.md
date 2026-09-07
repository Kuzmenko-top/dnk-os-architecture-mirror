---
title: "003 Remotion Compiler & Canvas Runtime Bridge Protocol"
aliases:
  - "Remotion Compiler Protocol"
  - "Canvas Video Stream Bridge"
  - "Компілятор Remotion та Canvas Міст"
tags:
  - dnk-hub
  - remotion
  - canvas
  - video-engine
  - architecture
  - adr
type: architecture
status: active
created: 2026-09-04
updated: 2026-09-04
author: "Maksym Kuzmenko & Gerych Prime"
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "obsidian/DNK_HUB/003 Remotion Compiler & Canvas Runtime Bridge Protocol.md"
purpose: "Canonical Architectural Specification and Developer Guide for Remotion Compiler, CanvasRuntimeBridge WebSocket Stream, and Remotion v5 Patterns."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-04"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

-->

# 🎬 003 Remotion Compiler & Canvas Runtime Bridge Protocol

> [!abstract] **Суть системи в одному реченні**
> Цей модуль бере візуальну розкадровку з Canvas-ноди (`VideoStoryboardNoteNode`), автоматично перетворює її на чистий програмний React-відеокод (**Remotion v5**) з фізикою пружин та покадровою математикою, одночасно транслюючи живий прогрес генерації прямо у WebSocket-стрім Канвасу.

---

## 👤 Частина 1: Для Максима (Людина / Розробник)

### 💡 Проста аналогія: Як це працює?
Уяви, що у тебе на безкінечному канвасі є блокнот зі сценарієм відеоролика (наприклад, для титанового смокера **ReBurn**):
1. **Сцена 1 (0–3 сек):** Макро-кадр диму + хук-текст *"Tired of boring cocktails?"*
2. **Сцена 2 (3–6 сек):** Сітка фільтра в slow-motion + опис фічі *"Zero soot. Pure flavor."*
3. **Сцена 3 (6–9 сек):** Відкриття подарункової коробки + заклик до дії *"Claim First Edition"*.

Раніше генерація відео була "чорним ящиком" — ти відправив запит і чекаєш у темряві, поки сервер щось збере. 

Тепер працює **Remotion Compiler**:
- Він бере дані з твоєї візуальної ноди і **миттєво компілює їх у повноцінний React-код**.
- Замість важкого ручного монтажу чи глючних шаблонів, відео будується як веб-сторінка: тексти анімуються за законами справжньої фізики (пружини, плавний відскок, розмиття), а відео та картинки нарізаються на ідеальні кадри.
- **Живий пульс (Canvas Bridge):** Як тільки компілятор починає роботу, твоя нода на екрані оживає! Вона надсилає через WebSocket сигнали:
  - 🟢 *"Почав компіляцію"* (з'являється спінер);
  - 🟡 *"Обробляю Сцену 1 (33%)"*, *"Сцену 2 (66%)"*, *"Сцену 3 (100%)"*;
  - 🟢 *"Готово!"* — повертається готова композиція, яку можна одразу програвати або рендерити в MP4.

### 🌟 Чому це фундаментально для DNK OS?
1. **Zero Black Box:** Користувач або агент бачить точний стан кожної ноди в реальному часі.
2. **Чистий код (Code-as-Video):** Будь-яке відео можна відкрити як звичайний `.tsx` файл, змінити один рядок у коді або додати будь-який CSS/Tailwind ефект.
3. **Автономність для Агентів:** Агент `dnk_video_ai_creator` може сам створити ноду, підключити до неї генерацію аудіо чи субтитрів і самостійно перевірити результат через тести.

---

## 🤖 Частина 2: Для Агентів Рою (Technical Specification & Invariants)

### 📂 Canonical Codebase Anchors
- **Compiler Core:** `services/dnk_video_ai_creator/remotion_compiler.py`
- **Composition AST Schema:** `services/dnk_video_ai_creator/src/video_composition_schema.py`
- **Runtime WebSocket Bridge:** `core/canvas_runtime_bridge.py`
- **SOTA Reference Patterns:** `skills/remotion_composition_patterns/SKILL.md`
- **Canvas Node Component:** `apps/web/components/canvas/nodes/VideoStoryboardNoteNode.tsx`
- **Verification Suite:** `tests/verification/test_remotion_compiler.py`

---

### 🧬 Architectural Invariants & Patterns

#### 1. Frame-as-a-Function-of-Time Math
Жодних станів `useState` чи `useEffect` для анімації у внутрішніх шарах Remotion. Час і положення є суто детермінованою функцією поточного номера кадру:
```tsx
const frame = useCurrentFrame();
const { fps } = useVideoConfig();

// Плавна поява (Clamp Interpolation)
const opacity = interpolate(frame, [0, 15], [0, 1], {
  extrapolateLeft: 'clamp',
  extrapolateRight: 'clamp'
});
```

#### 2. Spring Physics Invariant
Динамічне масштабування (`scale`) та позиціонування комбінуються за схемою пружини з параметрами жорсткості, демпфування та маси:
```tsx
const scale = spring({
  frame,
  fps,
  config: {
    damping: 12,
    stiffness: 180,
    mass: 0.8,
    overshootClamping: false
  }
});
```

#### 3. `<Sequence />` Relative Timeline Slicing
Кожна сцена Canvas розбивається на локальний часовий зріз. Всередині `<Sequence from={start_frame} durationInFrames={duration}>` таймлайн для внутрішніх елементів скидається до `frame = 0`, що гарантує відсутність накладання або зсуву таймінгів.

---

### 📡 WebSocket Event Stream Specification

Компілятор взаємодіє з візуальним оточенням через `CanvasRuntimeBridge.publish_node_executed`:

| Step / Етап | Status | Event Type | Payload Attributes | Опис для Canvas UI |
| :--- | :--- | :--- | :--- | :--- |
| `compile_start` | `started` | `node.started` | `total_frames`, `fps`, `scenes_count` | Нода вмикає пульсуючу рамку та лічильник сцен |
| `frame_render` | `rendering` | `node.progress` | `scene_id`, `scene_index`, `progress (0..100)` | Оновлення шкали прогресу над нодою |
| `completed` | `completed` | `node.completed` | `composition_id`, `progress: 100`, `meta` | Відображення прев'ю-бейджів та посилання на TSX |
| `compile_error` | `failed` | `node.failed` | `error: str`, `step` | Червоний аварійний статус та код помилки |

---

### 🛡️ Quality Gates & Verification Commands
Для верифікації модифікацій компілятора агент зобов'язаний виконати:
```bash
# 1. Спеціалізований тест компілятора та подій мосту
.venv/bin/pytest tests/verification/test_remotion_compiler.py -v

# 2. Повний наскрізний шлюз якості DNK OS
bash scripts/verify_all.sh
```

---

## 🔗 Пов'язані матеріали та вузли знань
- [[000 DNK HUB Index|🌌 000 DNK HUB: Головний покажчик бази знань (MOC)]]
- [[002 DNK OS - Master System Architecture & Implementation Blueprint|🌌 002 DNK OS: Генеральна архітектура]]
- [[dnk_video_ai_creator|🎬 Спеціалізований агент: dnk_video_ai_creator]]
- [[gerych_builder|🛠️ Спеціалізований агент: gerych_builder]]
- [[Canvas Architecture|🎨 Infinite Node-Based Canvas Core]]

---
*Документ створено автоматично та синхронізовано з когнітивною пам'яттю Герича.*
