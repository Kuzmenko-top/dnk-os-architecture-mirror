// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_hub_MagicToolsLaunchpad"
// purpose: "Launchpad 'Що можна створювати в даному додатку?' matching CapCut /my-edit & Excalidraw specification"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "2.1.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { 
  Film, 
  ShoppingBag, 
  Sparkles, 
  Wand2, 
  Scissors, 
  Image as ImageIcon, 
  Dna, 
  ArrowRight,
  Layers,
  Video,
  Smartphone,
  Monitor
} from 'lucide-react';

interface MagicToolsLaunchpadProps {
  onSelectAction: (actionId: string) => void;
}

export default function MagicToolsLaunchpad({ onSelectAction }: MagicToolsLaunchpadProps) {
  const tools = [
    {
      id: 'create_video_blank',
      title: 'Створити відео',
      desc: 'Чистий таймлайн: 9:16 Reels, 16:9 YouTube або 1:1 Square',
      icon: Film,
      badge: '9:16 / 16:9',
      gradient: 'from-purple-600/20 via-indigo-600/10 to-transparent',
      borderColor: 'border-purple-500/40 hover:border-purple-400',
      iconColor: 'text-purple-400',
      actionUrl: '/canvas/new-video'
    },
    {
      id: 'script_to_video',
      title: 'Текст у відео (AI Script)',
      desc: 'Автоматична генерація озвучки, субтитрів та підбір футажів',
      icon: Wand2,
      badge: 'Gemini AI',
      gradient: 'from-pink-600/20 via-purple-600/10 to-transparent',
      borderColor: 'border-pink-500/40 hover:border-pink-400',
      iconColor: 'text-pink-400',
      actionUrl: '/canvas/script-to-video'
    },
    {
      id: 'autocut_broll',
      title: 'Розумний Автомонтаж',
      desc: 'Видалення пауз, синхронізація з бітом та нарізка b-roll',
      icon: Scissors,
      badge: 'AutoCut',
      gradient: 'from-cyan-600/20 via-blue-600/10 to-transparent',
      borderColor: 'border-cyan-500/40 hover:border-cyan-400',
      iconColor: 'text-cyan-400',
      actionUrl: '/canvas/autocut'
    },
    {
      id: 'shopify_product_ads',
      title: 'Shopify Товарні Промо',
      desc: 'Імпорт товарів з магазину, генерація 3D карток та Liquid AST',
      icon: ShoppingBag,
      badge: 'Shopify v2',
      gradient: 'from-emerald-600/20 via-teal-600/10 to-transparent',
      borderColor: 'border-emerald-500/40 hover:border-emerald-400',
      iconColor: 'text-emerald-400',
      actionUrl: '/canvas/shopify'
    },
    {
      id: 'image_generator',
      title: 'Генерація зображень',
      desc: 'Створення фото продуктів, банерів та фонів для соцмереж',
      icon: ImageIcon,
      badge: 'Diffusion',
      gradient: 'from-amber-600/20 via-orange-600/10 to-transparent',
      borderColor: 'border-amber-500/40 hover:border-amber-400',
      iconColor: 'text-amber-400',
      actionUrl: '/canvas/image-gen'
    },
    {
      id: 'taskdna_swarm',
      title: 'TaskDNA Swarm Flow',
      desc: 'Повний оркестрований пайплайн на 14 автономних агентів',
      icon: Dna,
      badge: 'Orchestrator',
      gradient: 'from-indigo-600/20 via-purple-600/10 to-transparent',
      borderColor: 'border-indigo-500/40 hover:border-indigo-400',
      iconColor: 'text-indigo-400',
      actionUrl: '/os'
    }
  ];

  return (
    <section className="mb-9">
      {/* Section Title (Matching Excalidraw #2 & #20) */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="font-bold text-lg text-white tracking-wide flex items-center gap-2 font-sans">
            <Sparkles className="w-5 h-5 text-purple-400 animate-pulse" />
            <span>Що можна створювати в даному додатку?</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Оберіть формат або інструмент для швидкого запуску роботи над медіаматеріалами
          </p>
        </div>
      </div>

      {/* Grid of Creation Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        {tools.map((tool) => {
          const Icon = tool.icon;
          return (
            <button
              key={tool.id}
              onClick={() => onSelectAction(tool.id)}
              className={`p-4 rounded-2xl bg-gradient-to-b ${tool.gradient} bg-[#141722]/80 backdrop-blur-xl border ${tool.borderColor} text-left transition-all group hover:scale-[1.03] hover:shadow-2xl cursor-pointer flex flex-col justify-between h-44`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className={`p-2 rounded-xl bg-slate-950/80 border border-white/5 ${tool.iconColor} shadow-inner`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="text-[9px] font-mono px-2 py-0.5 rounded-full bg-slate-950/80 text-slate-300 border border-white/10 font-semibold">
                    {tool.badge}
                  </span>
                </div>
                <h3 className="font-bold text-xs text-white group-hover:text-purple-300 transition-colors leading-tight">
                  {tool.title}
                </h3>
                <p className="text-[10px] text-slate-400 mt-1 leading-snug line-clamp-2 font-sans">
                  {tool.desc}
                </p>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-white/5 text-[9px] text-slate-500 font-mono group-hover:text-purple-300">
                <span>Створити</span>
                <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform text-purple-400" />
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}
