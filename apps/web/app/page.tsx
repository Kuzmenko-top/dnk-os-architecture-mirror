// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/app/page.tsx"
// purpose: "DNK OS Root Launchpad: Project Catalog, Business Templates, SCONES Vault, and Onboarding Wizard Modal"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["TaskDNA-PHASE-2-LAUNCHPAD-ONBOARDING-FINAL"]
// status: "Active"
// version: "3.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { Sparkles } from 'lucide-react';
import LaunchpadView from '../components/launchpad/LaunchpadView';

const OnboardingWizard = dynamic(
  () => import('../components/onboarding/OnboardingWizard'),
  { ssr: false }
);

export default function RootPage() {
  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);

  return (
    <main className="min-h-screen bg-[#07090e] relative">
      {/* Onboarding Quick Access CTA Banner */}
      <div className="bg-gradient-to-r from-cyan-950/60 via-indigo-950/50 to-purple-950/60 border-b border-white/10 px-4 py-2.5 flex items-center justify-between text-xs text-gray-300">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-cyan-400 animate-pulse" />
          <span>Новий користувач? Опануйте DNK OS за 5 хвилин з інтерактивним туром.</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsOnboardingOpen(true)}
            type="button"
            className="px-3 py-1 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/30 font-medium transition-colors"
          >
            Пройти Onboarding
          </button>
          <Link
            href="/onboarding"
            className="text-gray-400 hover:text-white transition-colors underline"
          >
            Відкрити сторінку туру
          </Link>
        </div>
      </div>

      <LaunchpadView onStartOnboarding={() => setIsOnboardingOpen(true)} />
      <OnboardingWizard
        isOpen={isOnboardingOpen}
        onClose={() => setIsOnboardingOpen(false)}
      />
    </main>
  );
}
