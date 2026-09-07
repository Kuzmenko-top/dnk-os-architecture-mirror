// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/launchpad/LaunchpadView.tsx"
// purpose: "DNK OS Studio Launchpad (Root Dashboard): Business Templates, Saved Projects, SCONES Memory Vault, and Instant Canvas Launch"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["TaskDNA-PHASE-2-LAUNCHPAD-ONBOARDING-FINAL"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Rocket, 
  ShoppingBag, 
  Video, 
  Server, 
  Sparkles, 
  Plus, 
  ArrowRight, 
  Layers, 
  Brain, 
  Clock, 
  ChevronRight,
  ShieldCheck,
  FolderKanban
} from 'lucide-react';
import { BUSINESS_TEMPLATES, BusinessTemplate } from '../../src/canvas/templates/businessTemplates';
import { useSconesStore } from '../../store/sconesStore';
import { useCanvasStore } from '../../store/canvasStore';

interface LaunchpadViewProps {
  onStartOnboarding: () => void;
}

export default function LaunchpadView({ onStartOnboarding }: LaunchpadViewProps) {
  const router = useRouter();
  const { currentBrand, workspaceId, listBrands, loadBrandFromVault } = useSconesStore();
  const { resetToDefault, onConnect } = useCanvasStore();
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const brands = listBrands();

  const handleLaunchTemplate = (template: BusinessTemplate) => {
    resetToDefault();
    const graph = template.createGraph(currentBrand);
    
    // Populate canvas store with template nodes & edges
    const store = useCanvasStore.getState();
    graph.nodes.forEach((n) => {
      store.addNode(n.type || 'StrategyMarkdownNode', n.position, n.data);
    });
    
    // Connect edges
    graph.edges.forEach((e) => {
      store.onConnect({
        source: e.source,
        target: e.target,
        sourceHandle: 'right',
        targetHandle: 'left',
      });
    });

    router.push('/canvas');
  };

  const getTemplateIcon = (name: string) => {
    switch (name) {
      case 'ShoppingBag': return <ShoppingBag className="w-5 h-5 text-emerald-400" />;
      case 'Video': return <Video className="w-5 h-5 text-purple-400" />;
      case 'Server': return <Server className="w-5 h-5 text-cyan-400" />;
      default: return <Sparkles className="w-5 h-5 text-amber-400" />;
    }
  };

  const filteredTemplates = selectedCategory === 'all' 
    ? BUSINESS_TEMPLATES 
    : BUSINESS_TEMPLATES.filter(t => t.category === selectedCategory);

  return (
    <div className="min-h-screen bg-[#07090e] text-slate-100 font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Header Navigation */}
      <header className="border-b border-[#1c2230] bg-[#0c1018]/80 backdrop-blur-xl sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
              <Rocket className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-base tracking-tight text-white flex items-center gap-2">
                DNK OS Launchpad
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  v4.3
                </span>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Workspace & SCONES Brain Badge */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#121722] border border-[#232a3b] text-xs">
              <Brain className="w-4 h-4 text-emerald-400" />
              <span className="text-slate-400 font-mono">{workspaceId}</span>
              <span className="text-slate-600">|</span>
              <span className="text-white font-medium">{currentBrand.brandName || 'Untitled Brand'}</span>
            </div>

            <button
              onClick={onStartOnboarding}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-semibold shadow-lg shadow-indigo-500/20 flex items-center gap-2 transition-all cursor-pointer"
            >
              <Sparkles className="w-4 h-4" />
              AI Onboarding Wizard
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 py-10 space-y-12">
        {/* Hero Section */}
        <div className="relative rounded-3xl bg-gradient-to-r from-[#111624] via-[#0d121d] to-[#151026] border border-[#242b3d] p-8 overflow-hidden shadow-2xl">
          <div className="relative z-10 max-w-2xl space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-mono">
              <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
              SCONES Memory + Spatial Canvas Architecture
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white leading-tight">
              Створюйте автономні системи на <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">просторовому полотні</span>
            </h1>
            <p className="text-slate-400 text-sm leading-relaxed">
              Оберіть швидкий бізнес-шаблон або запустіть діалогового Co-Pilot агента для формування Brand DNA та автоматичної побудови TaskDNA-графу в реальному часі.
            </p>
            <div className="pt-2 flex items-center gap-3">
              <button
                onClick={() => router.push('/canvas')}
                className="px-5 py-2.5 rounded-xl bg-white text-slate-950 font-bold text-xs hover:bg-slate-200 transition-all flex items-center gap-2 shadow-lg cursor-pointer"
              >
                Відкрити порожнє полотно
                <ArrowRight className="w-4 h-4" />
              </button>
              <button
                onClick={onStartOnboarding}
                className="px-5 py-2.5 rounded-xl bg-[#1b2130] hover:bg-[#252d42] border border-[#2b354c] text-white font-medium text-xs transition-all flex items-center gap-2 cursor-pointer"
              >
                Пройти AI-бриф
              </button>
            </div>
          </div>
        </div>

        {/* Section: Business Templates */}
        <section className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <FolderKanban className="w-5 h-5 text-indigo-400" />
                Готові бізнес-шаблони запуску
              </h2>
              <p className="text-slate-400 text-xs mt-1">
                Генерують повноцінний TaskDNA-граф з 4 живими нодами та зв'язками у форматі JSON Canvas 1.0
              </p>
            </div>

            {/* Category Filter Tabs */}
            <div className="flex items-center gap-1 p-1 bg-[#121622] rounded-xl border border-[#212738] text-xs">
              {['all', 'ecommerce', 'video', 'saas', 'branding'].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer ${
                    selectedCategory === cat 
                      ? 'bg-indigo-600 text-white shadow' 
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {cat.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {filteredTemplates.map((tpl) => (
              <div
                key={tpl.id}
                className="group relative rounded-2xl bg-[#0f141f] border border-[#1e2536] hover:border-indigo-500/50 p-5 flex flex-col justify-between transition-all duration-300 hover:shadow-2xl hover:shadow-indigo-500/10 hover:-translate-y-1"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="w-10 h-10 rounded-xl bg-[#161c2b] border border-[#283248] flex items-center justify-center">
                      {getTemplateIcon(tpl.iconName)}
                    </div>
                    <span className="px-2.5 py-1 rounded-full text-[10px] font-mono bg-[#1a2030] text-indigo-300 border border-indigo-500/20">
                      {tpl.badge}
                    </span>
                  </div>

                  <h3 className="font-bold text-sm text-white group-hover:text-indigo-300 transition-colors">
                    {tpl.title}
                  </h3>

                  <p className="text-slate-400 text-xs leading-relaxed line-clamp-3">
                    {tpl.description}
                  </p>
                </div>

                <div className="pt-6 border-t border-[#1a2130] mt-4 flex items-center justify-between">
                  <span className="text-[11px] font-mono text-slate-500 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    {tpl.estimatedTime}
                  </span>
                  <button
                    onClick={() => handleLaunchTemplate(tpl)}
                    className="px-3 py-1.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer"
                  >
                    Запустити
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Section: SCONES Brand Vault */}
        <section className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Brain className="w-5 h-5 text-emerald-400" />
                SCONES Brand Memory Vault
              </h2>
              <p className="text-slate-400 text-xs mt-1">
                Збережені профілі брендів, налаштування FLUX.1 та IC-Light генерації
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {brands.map((b) => (
              <div
                key={b.id}
                onClick={() => loadBrandFromVault(b.id)}
                className={`cursor-pointer rounded-2xl bg-[#0f141f] border p-5 space-y-4 transition-all ${
                  b.id === currentBrand.id
                    ? 'border-emerald-500/60 ring-2 ring-emerald-500/20 shadow-lg shadow-emerald-500/10'
                    : 'border-[#1e2536] hover:border-slate-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-sm">{b.brandName}</span>
                  {b.id === currentBrand.id && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      Активний
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 italic">"{b.tagline}"</p>
                
                {/* Palette preview */}
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] font-mono text-slate-500 mr-1">Палітра:</span>
                  {[b.colors.primary, b.colors.secondary, b.colors.accent].map((col, idx) => (
                    <div
                      key={idx}
                      className="w-4 h-4 rounded-full border border-[#2b354c]"
                      style={{ backgroundColor: col }}
                      title={col}
                    />
                  ))}
                </div>

                <div className="text-[11px] text-slate-400 flex items-center justify-between pt-2 border-t border-[#1a2130]">
                  <span>ToV: <strong className="text-slate-200">{b.toneOfVoice}</strong></span>
                  <span className="font-mono text-slate-500">{b.industry}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
