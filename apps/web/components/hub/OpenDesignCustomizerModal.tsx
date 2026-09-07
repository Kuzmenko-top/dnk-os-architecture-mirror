// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_hub_OpenDesignCustomizerModal"
// purpose: "Interactive Customization Modal for DNK OS First Screen leveraging 100+ Open Design design systems and tokens"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { 
  Palette, 
  X, 
  Check, 
  Sparkles, 
  Sliders, 
  Eye, 
  Layout, 
  ShieldCheck, 
  Layers,
  Wand2,
  FolderKanban,
  Cloud,
  LayoutTemplate
} from 'lucide-react';
import { useOpenDesignTheme, OPEN_DESIGN_PRESETS } from '../../context/OpenDesignThemeContext';

interface OpenDesignCustomizerModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const BRAND_ACCENT_COLORS = [
  { name: 'DNK Purple', value: '#a855f7', label: 'Фіолетовий' },
  { name: 'ReBurn Gold', value: '#f59e0b', label: 'Золотий' },
  { name: 'Cyber Cyan', value: '#06b6d4', label: 'Лазурний' },
  { name: 'Emerald Sync', value: '#10b981', label: 'Смарагдовий' },
  { name: 'Viral Rose', value: '#f43f5e', label: 'Рожевий' },
];

export default function OpenDesignCustomizerModal({
  isOpen,
  onClose
}: OpenDesignCustomizerModalProps) {
  const {
    currentPreset,
    setPresetById,
    accentColor,
    setAccentColor,
    glassOpacity,
    setGlassOpacity,
    showLaunchpad,
    setShowLaunchpad,
    showProjects,
    setShowProjects,
    showMediaVault,
    setShowMediaVault,
    showTemplates,
    setShowTemplates
  } = useOpenDesignTheme();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
      <div className="w-full max-w-2xl bg-[#12151f] border border-white/10 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-5 border-b border-white/10 flex items-center justify-between bg-white/5">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-purple-600/20 text-purple-400 border border-purple-500/30">
              <Palette className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-base text-white tracking-wide">
                Налаштування першого робочого екрану
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Керування темами, акцентами та блоками на базі Open Design
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
          {/* 1. Design System Presets from Open Design */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <span>1. Дизайн-Система (Open Design Presets)</span>
              </span>
              <span className="text-[10px] font-mono text-purple-400 bg-purple-950/80 px-2 py-0.5 rounded-full border border-purple-800/40">
                100+ в ядрі
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {OPEN_DESIGN_PRESETS.map((preset) => {
                const isSelected = currentPreset.id === preset.id;
                return (
                  <button
                    key={preset.id}
                    onClick={() => setPresetById(preset.id)}
                    className={`p-3.5 rounded-2xl border text-left transition-all relative cursor-pointer ${
                      isSelected
                        ? 'bg-purple-600/15 border-purple-500 shadow-lg shadow-purple-600/20'
                        : 'bg-white/5 border-white/8 hover:border-white/20 hover:bg-white/10'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-bold text-xs text-white">
                        {preset.name}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-950/80 text-slate-300 border border-white/10">
                        {preset.badge}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 leading-snug">
                      {preset.description}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 2. Brand Primary Accent Color */}
          <div>
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono block mb-3">
              2. Фірмовий колір підсвічування (Brand Highlight)
            </span>
            <div className="flex flex-wrap gap-2.5">
              {BRAND_ACCENT_COLORS.map((col) => {
                const isSelected = accentColor === col.value;
                return (
                  <button
                    key={col.value}
                    onClick={() => setAccentColor(col.value)}
                    className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-xs font-semibold transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-white/15 border-white text-white shadow-md'
                        : 'bg-white/5 border-white/10 text-slate-400 hover:text-white hover:bg-white/10'
                    }`}
                  >
                    <span 
                      className="w-3.5 h-3.5 rounded-full shadow-sm"
                      style={{ backgroundColor: col.value }}
                    />
                    <span>{col.label}</span>
                    {isSelected && <Check className="w-3.5 h-3.5 ml-0.5 text-white" />}
                  </button>
                );
              })}
            </div>
          </div>

          {/* 3. Section Toggles on First Screen */}
          <div>
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono block mb-3">
              3. Відображення блоків на першому екрані
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              <label className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/8 hover:bg-white/10 transition-colors cursor-pointer">
                <div className="flex items-center gap-2 text-xs font-medium text-slate-200">
                  <Wand2 className="w-4 h-4 text-pink-400" />
                  <span>Блок "Що створюємо сьогодні?"</span>
                </div>
                <input
                  type="checkbox"
                  checked={showLaunchpad}
                  onChange={(e) => setShowLaunchpad(e.target.checked)}
                  className="rounded bg-slate-800 border-slate-700 text-purple-600 focus:ring-purple-500 w-4 h-4 cursor-pointer"
                />
              </label>

              <label className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/8 hover:bg-white/10 transition-colors cursor-pointer">
                <div className="flex items-center gap-2 text-xs font-medium text-slate-200">
                  <FolderKanban className="w-4 h-4 text-purple-400" />
                  <span>Блок "Кабінет проєктів та папок"</span>
                </div>
                <input
                  type="checkbox"
                  checked={showProjects}
                  onChange={(e) => setShowProjects(e.target.checked)}
                  className="rounded bg-slate-800 border-slate-700 text-purple-600 focus:ring-purple-500 w-4 h-4 cursor-pointer"
                />
              </label>

              <label className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/8 hover:bg-white/10 transition-colors cursor-pointer">
                <div className="flex items-center gap-2 text-xs font-medium text-slate-200">
                  <Cloud className="w-4 h-4 text-cyan-400" />
                  <span>Блок "Хмарні медіаактиви"</span>
                </div>
                <input
                  type="checkbox"
                  checked={showMediaVault}
                  onChange={(e) => setShowMediaVault(e.target.checked)}
                  className="rounded bg-slate-800 border-slate-700 text-purple-600 focus:ring-purple-500 w-4 h-4 cursor-pointer"
                />
              </label>

              <label className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/8 hover:bg-white/10 transition-colors cursor-pointer">
                <div className="flex items-center gap-2 text-xs font-medium text-slate-200">
                  <LayoutTemplate className="w-4 h-4 text-emerald-400" />
                  <span>Блок "Бібліотека шаблонів"</span>
                </div>
                <input
                  type="checkbox"
                  checked={showTemplates}
                  onChange={(e) => setShowTemplates(e.target.checked)}
                  className="rounded bg-slate-800 border-slate-700 text-purple-600 focus:ring-purple-500 w-4 h-4 cursor-pointer"
                />
              </label>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-white/10 bg-white/5 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-mono">
            <ShieldCheck className="w-4 h-4" />
            <span>Open Design Tokens Synced</span>
          </div>
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs shadow-lg shadow-purple-600/30 transition-all cursor-pointer"
          >
            Зберегти налаштування
          </button>
        </div>
      </div>
    </div>
  );
}
