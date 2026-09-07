// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_app_canvas_page"
// purpose: "DNK OS Canvas Workspace Page Root (DNK-VISUAL-OS-001)"
// author: "DNK-e.com Maksym"
// status: "Active"
// version: "3.0.0"
// updated_at: "2026-08-31"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import dynamic from 'next/dynamic';

const DNKStudioWorkspace = dynamic(
  () => import('../../components/workspace/DNKStudioWorkspace'),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-screen w-full items-center justify-center bg-[#060913] text-indigo-400 font-mono text-xs">
        <div className="flex items-center gap-3">
          <span className="w-3 h-3 rounded-full bg-indigo-500 animate-ping" />
          <span>Завантаження робочого простору DNK Studio Workspace...</span>
        </div>
      </div>
    )
  }
);

export default function CanvasPage() {
  return (
    <main className="min-h-screen bg-[#060913]">
      <DNKStudioWorkspace />
    </main>
  );
}
