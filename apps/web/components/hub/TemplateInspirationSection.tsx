// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_hub_TemplateInspirationSection"
// purpose: "Template Library & Inspiration Hub matching CapCut /my-edit & Excalidraw #10 specification"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "2.1.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { 
  LayoutTemplate, 
  Sparkles, 
  Flame, 
  ShoppingBag, 
  Film, 
  ArrowRight,
  Zap,
  Check
} from 'lucide-react';

interface TemplateInspirationSectionProps {
  onUseTemplate: (templateId: string) => void;
}

const TEMPLATES = [
  {
    id: 'tpl_reburn_viral_01',
    title: 'ReBurn Smoker — Viral 9:16 TikTok Ad',
    category: 'ecom_video',
    badge: 'Trending 🔥',
    desc: 'Динамічні неонові переходи, слоу-мо дим, звуковий дизайн та заклики до дії',
    gradient: 'from-pink-950/70 via-purple-950/40 to-[#12151e]',
    tags: ['9:16 Reels', 'E-Com', '30 sec'],
    uses: '2.4k'
  },
  {
    id: 'tpl_stripe_obsidian_02',
    title: 'Stripe / Obsidian Aurora — Shopify Theme',
    category: 'shopify_theme',
    badge: 'Luxury ✨',
    desc: 'Темний скляний лендінг із сяючими 3D картками обладнання та інтерактивним Liquid AST',
    gradient: 'from-emerald-950/70 via-teal-950/40 to-[#12151e]',
    tags: ['Shopify v2', 'Tailwind', 'Liquid'],
    uses: '1.8k'
  },
  {
    id: 'tpl_flash_sale_03',
    title: 'Flash Sale Countdown & Discount Badges',
    category: 'ecom_video',
    badge: 'High Convert ⚡',
    desc: 'Таймер зворотного відліку, анімовані промокоди та швидкий ритм монтажу',
    gradient: 'from-amber-950/70 via-orange-950/40 to-[#12151e]',
    tags: ['Conversion', 'Urgency', '15 sec'],
    uses: '4.1k'
  },
  {
    id: 'tpl_hardware_showcase_04',
    title: 'Hardware & Sequencer 4K Promo',
    category: 'showcase',
    badge: 'Pro 4K',
    desc: 'Елегантний огляд складного обладнання з виділенням технічних характеристик',
    gradient: 'from-cyan-950/70 via-blue-950/40 to-[#12151e]',
    tags: ['16:9 4K', 'Spec Grid', '60 sec'],
    uses: '950'
  }
];

export default function TemplateInspirationSection({ onUseTemplate }: TemplateInspirationSectionProps) {
  const [activeCategory, setActiveCategory] = useState('all');

  const categories = [
    { id: 'all', label: 'Всі шаблони (4)' },
    { id: 'ecom_video', label: '🔥 Топ Відео для E-Com' },
    { id: 'shopify_theme', label: '🛍️ Shopify Теми та Лендінги' },
    { id: 'showcase', label: '🎬 Промо Обладнання' }
  ];

  const filtered = activeCategory === 'all'
    ? TEMPLATES
    : TEMPLATES.filter(t => t.category === activeCategory);

  return (
    <section className="mb-9" id="templates">
      {/* Section Header (Matching Excalidraw #10) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h2 className="font-bold text-lg text-white tracking-wide flex items-center gap-2 font-sans">
            <LayoutTemplate className="w-5 h-5 text-purple-400" />
            <span>Бібліотека натхнення та вибору вже існуючих шаблонів</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5 font-sans">
            Використовуйте перевірені шаблони для швидкого створення відеороликів та Shopify-лендінгів
          </p>
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 mb-4 scrollbar-none">
        {categories.map(c => (
          <button
            key={c.id}
            onClick={() => setActiveCategory(c.id)}
            className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all cursor-pointer ${
              activeCategory === c.id
                ? 'bg-purple-600/25 text-purple-200 border border-purple-500/50 shadow-sm'
                : 'bg-[#141722]/80 text-slate-400 border border-white/5 hover:text-slate-200 hover:bg-[#1a1e2c]'
            }`}
          >
            {c.label}
          </button>
        ))}
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {filtered.map((tpl) => (
          <div
            key={tpl.id}
            className="rounded-2xl bg-[#141722]/90 border border-white/8 hover:border-purple-500/50 transition-all flex flex-col justify-between overflow-hidden group hover:shadow-2xl hover:-translate-y-0.5"
          >
            {/* Header Preview */}
            <div className={`h-36 bg-gradient-to-b ${tpl.gradient} p-3.5 flex flex-col justify-between`}>
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-950/80 text-purple-300 border border-purple-800/40 font-bold">
                  {tpl.badge}
                </span>
                <span className="text-[10px] text-slate-400 font-mono">
                  {tpl.uses} вик.
                </span>
              </div>
              <div className="flex flex-wrap gap-1">
                {tpl.tags.map((tag, idx) => (
                  <span key={idx} className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-950/60 text-slate-300">
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            {/* Content Body */}
            <div className="p-3.5 flex flex-col justify-between flex-1">
              <div>
                <h3 className="font-bold text-xs text-white group-hover:text-purple-300 transition-colors leading-tight">
                  {tpl.title}
                </h3>
                <p className="text-[11px] text-slate-400 mt-1 leading-snug line-clamp-2 font-sans">
                  {tpl.desc}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
                <span className="text-[10px] text-slate-500 font-mono">1-Click Remix</span>
                <button
                  onClick={() => onUseTemplate(tpl.id)}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-purple-600/20 hover:bg-purple-600 text-purple-300 hover:text-white border border-purple-500/40 text-xs font-semibold transition-all cursor-pointer"
                >
                  <span>Використати</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
