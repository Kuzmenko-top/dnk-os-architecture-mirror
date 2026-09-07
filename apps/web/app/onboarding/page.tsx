// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/app/onboarding/page.tsx"
// purpose: "Dedicated Standalone Interactive User Onboarding Page for DNK OS with Integrated Canvas Demo"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.1.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import OnboardingWizard from '../../components/onboarding/OnboardingWizard';
import InteractiveCanvasDemo from '../../components/tutorial/InteractiveCanvasDemo';
import { Sparkles, Layers, ArrowLeft } from 'lucide-react';

export default function OnboardingPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'wizard' | 'tutorial'>('wizard');
  const [tutorialCompleted, setTutorialCompleted] = useState<boolean>(false);

  useEffect(() => {
    try {
      if (typeof window !== 'undefined') {
        const isDone = localStorage.getItem('tutorial_completed') === 'true';
        setTutorialCompleted(isDone);
      }
    } catch {
      // Ignore localStorage errors
    }
  }, []);

  const handleComplete = () => {
    router.push('/');
  };

  const handleTutorialComplete = () => {
    setTutorialCompleted(true);
    try {
      localStorage.setItem('tutorial_completed', 'true');
    } catch {}
  };

  return (
    <main className="min-h-screen bg-[#04060a] text-white flex flex-col items-center justify-center p-3 sm:p-6">
      {/* Top Navigation Bar with View Switcher */}
      <header className="w-full max-w-4xl mx-auto flex items-center justify-between pb-4 mb-4 border-b border-white/10">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleComplete}
            aria-label="Повернутися на головну"
            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <span className="text-sm font-semibold tracking-wide">DNK OS Onboarding Hub</span>
        </div>

        {/* View Mode Switcher: Wizard vs Interactive Demo */}
        <nav aria-label="Onboarding Views" className="flex items-center bg-white/5 p-1 rounded-xl border border-white/10">
          <button
            type="button"
            onClick={() => setActiveTab('wizard')}
            aria-pressed={activeTab === 'wizard'}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
              activeTab === 'wizard'
                ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Майстер налаштування</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('tutorial')}
            aria-pressed={activeTab === 'tutorial'}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
              activeTab === 'tutorial'
                ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Interactive Canvas Demo</span>
            {tutorialCompleted && (
              <span className="w-2 h-2 rounded-full bg-emerald-400" title="Виконано" />
            )}
          </button>
        </nav>
      </header>

      {/* Main Content Area */}
      <section className="w-full max-w-4xl mx-auto flex items-center justify-center">
        {activeTab === 'wizard' ? (
          <OnboardingWizard
            standalone={true}
            onComplete={handleComplete}
            onClose={handleComplete}
          />
        ) : (
          <InteractiveCanvasDemo
            onComplete={handleTutorialComplete}
            onExit={() => setActiveTab('wizard')}
          />
        )}
      </section>
    </main>
  );
}
