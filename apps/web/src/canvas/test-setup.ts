/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/test-setup.ts"
 * purpose: "Centralized Headless Test Setup for Canvas Engine: JSDOM polyfills, requestAnimationFrame mock, and Konva animation loop suppression."
 * canonical_source: true
 * alters_files: []
 * triggers_tasks: []
 * status: "Active"
 * version: "1.0.0"
 * updated_at: "2026-09-02"
 * author: "DNK-e.com Maksym & Gerych"
 * license: "DNK-INTERNAL"
 * --- END DNK-MRH-HEADER ---
 */

import { JSDOM } from 'jsdom';
import Konva from 'konva';

export function setupCanvasTestEnvironment(): { cleanup: () => void } {
  // 1. Setup DOM environment
  const dom = new JSDOM('<!DOCTYPE html><html><body><div id="container"></div></body></html>', {
    url: 'http://localhost:3000',
    pretendToBeVisual: true,
  });

  const originalWindow = global.window;
  const originalDocument = global.document;
  const originalNavigator = global.navigator;

  (global as any).window = dom.window;
  (global as any).document = dom.window.document;
  (global as any).navigator = dom.window.navigator;

  // 2. Polyfill requestAnimationFrame / cancelAnimationFrame for headless timers
  let rafId = 0;
  (global as any).requestAnimationFrame = (callback: FrameRequestCallback): number => {
    rafId += 1;
    setTimeout(() => callback(Date.now()), 16);
    return rafId;
  };

  (global as any).cancelAnimationFrame = (_id: number): void => {
    // noop
  };

  // 3. Suppress Konva internal animation loop to prevent Node.js test hang-ups
  if ((Konva as any).Animation) {
    (Konva.Animation as any)._animationLoop = () => {};
  }

  // 4. Return cleanup hook
  return {
    cleanup: () => {
      (global as any).window = originalWindow;
      (global as any).document = originalDocument;
      (global as any).navigator = originalNavigator;
    },
  };
}
