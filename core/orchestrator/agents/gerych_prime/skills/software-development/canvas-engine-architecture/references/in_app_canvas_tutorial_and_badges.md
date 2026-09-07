# In-App Canvas Interactive Tutorial, Audio Synthesis & Achievement Badges

## Overview
This reference specifies the design and implementation pattern for embedding interactive, step-by-step tutorial overlays into spatial canvas applications without external heavy dependencies.

---

## 1. 5-Step Guided Tutorial Architecture
A guided experience overlays interactive focus rings over existing UI components rather than redirecting the user to passive video or documentation:
1. **Targeting UI Elements:** Identify action buttons using stable semantic identifiers or relative container references (e.g., `data-tutorial-step="new-canvas"`, `aria-label`).
2. **Glow & Spotlight Overlay:** CSS box-shadow rings (`0 0 0 4px rgba(99, 102, 241, 0.4)`) and pulsed animation indicate interactive targets without blocking pointer events on non-target elements if exploration is permitted.
3. **5 Standard Canvas Tutorial Steps:**
   - Step 1: Create Canvas (`New Canvas` action button)
   - Step 2: Name & Meta (`Canvas Title` input field)
   - Step 3: Template Selection (`Template Selector` dropdown)
   - Step 4: AI Node Generation (`Generate Nodes` action trigger)
   - Step 5: Spatial Result Exploration (`Canvas Viewport` pan & zoom)

---

## 2. Zero-Dependency Sound Synthesis (Web Audio API)
Avoid bundling audio assets (MP3/WAV) for UI sounds. Use the native browser `AudioContext`:

```typescript
export function playSynthesizedChime() {
  if (typeof window === "undefined") return;
  const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
  if (!AudioCtx) return;

  const ctx = new AudioCtx();
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();

  osc.type = "sine";
  osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
  osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.15); // A5

  gain.gain.setValueAtTime(0.12, ctx.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);

  osc.connect(gain);
  gain.connect(ctx.destination);

  osc.start();
  osc.stop(ctx.currentTime + 0.25);
}
```

- **Mute Invariant:** Sound effects must always be toggleable and muted by default or respect browser autoplay policies (`AudioContext` suspended until user interaction).

---

## 3. Pure CSS / SVG Confetti Particle System
Rather than importing `canvas-confetti` (adds bundle weight):
- Render 20-30 lightweight absolute `span` or `div` particles with deterministic random offsets (`--x-offset`, `--rot`, `--delay`).
- Animate via CSS `@keyframes` with `translateY` and `rotate`.
- Respect `prefers-reduced-motion`: disable particle animations when reduced motion is requested.

---

## 4. Gamification & Achievement Badges
Four canonical onboarding milestones:
1. `First Canvas` (🎯) - Initialized the first project.
2. `Quick Learner` (⚡) - Completed the guided tutorial in < 3 minutes.
3. `Onboarding Complete` (🏆) - Finished all onboarding steps.
4. `Creative Mind` (🎨) - Customized node styles or generated AI artboards.

**Social Sharing Invariant:**
- Prefer `navigator.share` for native mobile/desktop OS sheet.
- Fallback to `navigator.clipboard.writeText` with toast confirmation ("Посилання скопійовано!").

---

## 5. Analytics & State Persistence
- **LocalStorage Keys:**
  - `tutorial_completed`: boolean flag to prevent repeated auto-triggering.
  - `tutorial_current_step`: index for resuming interrupted sessions.
  - `unlocked_badges`: serialized array of unlocked badge IDs.
- **Telemetry Events:**
  - `tutorial_started` { timestamp, entry_point }
  - `tutorial_step_completed` { step_index, step_id, duration_ms }
  - `tutorial_completed` { total_duration_ms, badge_count }
  - `tutorial_abandoned` { last_step_index, reason }

---

## 6. WCAG 2.1 AA Accessibility Checklist
- **Progress Bar:** Element must provide `role="progressbar"`, `aria-label="Прогрес навчання"`, `aria-valuenow`, `aria-valuemin="0"`, `aria-valuemax="100"`.
- **Keyboard Navigation:** Full support for `Tab` focus cycling, `Enter`/`Space` activation, and `Escape` to dismiss overlays.
- **Focus Trap / Restoration:** Return focus to trigger button upon closing tutorial modals.
