// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_app_patent_shield_page"
// purpose: "Patent Shield Dashboard Next.js page route"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-PATENT-001"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { PatentShieldDashboard } from '../../components/patent-shield/PatentShieldDashboard';

export default function PatentShieldPage() {
  return (
    <main className="min-h-screen bg-slate-950 p-6 flex flex-col justify-start items-center">
      <PatentShieldDashboard />
    </main>
  );
}
