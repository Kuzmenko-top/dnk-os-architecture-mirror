/*
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/vitest.config.ts"
// purpose: "Vitest Configuration for Teleprompter Web Adapters and UI Component Tests."
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---
*/

import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  root: __dirname,
  test: {
    globals: true,
    environment: 'node',
    include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@dnk/video-audit-core': path.resolve(__dirname, '../../packages/video-audit-core/src/index.ts'),
      '@dnk/teleprompter-core': path.resolve(__dirname, '../../packages/teleprompter-core/src/index.ts'),
    },
  },
});
