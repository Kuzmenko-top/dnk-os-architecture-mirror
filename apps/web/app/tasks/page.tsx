// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/app/tasks/page.tsx"
// purpose: "Interactive Node Based Task & Ideas DAG System for DNK OS"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect } from 'react';
import { NodeTaskGraphCanvas } from '@/components/node-tasks/NodeTaskGraphCanvas';

export default function TasksPage() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  return (
    <main className="w-full h-full min-h-screen bg-zinc-950 flex flex-col">
      <NodeTaskGraphCanvas />
    </main>
  );
}
