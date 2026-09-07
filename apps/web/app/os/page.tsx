// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_app_os_page"
// purpose: "DNK OS Studio Desktop Workspace Route mounting DNKStudioWorkspace"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-31"
// --- END DNK-MRH-HEADER ---

'use client';

import dynamic from 'next/dynamic';

const DNKStudioWorkspace = dynamic(
  () => import('../../components/workspace/DNKStudioWorkspace'),
  { ssr: false }
);

export default function StudioPage() {
  return <DNKStudioWorkspace />;
}
