// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_hub_MediaAssetsVaultSection"
// purpose: "Cloud Media Assets Vault matching CapCut /my-edit & Excalidraw #5 specification"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "2.1.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { 
  Cloud, 
  UploadCloud, 
  Film, 
  Music, 
  Image as ImageIcon, 
  FileCode, 
  Download, 
  ExternalLink,
  Plus,
  CheckCircle2,
  HardDrive,
  FolderOpen
} from 'lucide-react';

const INITIAL_ASSETS = [
  {
    id: 'asset_01',
    name: 'reburn_smoker_broll_4k.mp4',
    type: 'video',
    size: '124 MB',
    duration: '0:45',
    resolution: '3840x2160 (4K)',
    icon: Film,
    iconColor: 'text-pink-400',
    tag: 'B-Roll 4K'
  },
  {
    id: 'asset_02',
    name: 'smoke_slowmo_embers.mp4',
    type: 'video',
    size: '64 MB',
    duration: '0:20',
    resolution: '1920x1080 (HD)',
    icon: Film,
    iconColor: 'text-purple-400',
    tag: 'Effects'
  },
  {
    id: 'asset_03',
    name: 'voiceover_ukrainian_reburn_v2.mp3',
    type: 'audio',
    size: '3.2 MB',
    duration: '0:30',
    resolution: '320 kbps',
    icon: Music,
    iconColor: 'text-emerald-400',
    tag: 'AI Voiceover'
  },
  {
    id: 'asset_04',
    name: 'reburn_brand_logo_gold.svg',
    type: 'image',
    size: '420 KB',
    duration: 'Vector',
    resolution: 'Scalable SVG',
    icon: ImageIcon,
    iconColor: 'text-amber-400',
    tag: 'Brand Asset'
  },
  {
    id: 'asset_05',
    name: 'shopify_product_shot_smoker.png',
    type: 'image',
    size: '5.1 MB',
    duration: 'Still',
    resolution: '4000x3000',
    icon: ImageIcon,
    iconColor: 'text-cyan-400',
    tag: 'E-Com Shot'
  },
  {
    id: 'asset_06',
    name: 'dark_ambient_synth_beat.mp3',
    type: 'audio',
    size: '8.4 MB',
    duration: '2:15',
    resolution: '48 kHz Stereo',
    icon: Music,
    iconColor: 'text-indigo-400',
    tag: 'Soundtrack'
  }
];

export default function MediaAssetsVaultSection() {
  const [filterType, setFilterType] = useState('all');
  const [assets] = useState(INITIAL_ASSETS);
  const [isDragging, setIsDragging] = useState(false);

  const categories = [
    { id: 'all', label: 'Всі завантажені файли (6)' },
    { id: 'video', label: '🎬 Відеофутажі (2)' },
    { id: 'audio', label: '🎵 Аудіо та Озвучка (2)' },
    { id: 'image', label: '🖼️ Зображення та Лого (2)' }
  ];

  const filtered = filterType === 'all'
    ? assets
    : assets.filter(a => a.type === filterType);

  return (
    <section className="mb-9" id="media">
      {/* Section Header (Matching Excalidraw #5) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h2 className="font-bold text-lg text-white tracking-wide flex items-center gap-2 font-sans">
            <Cloud className="w-5 h-5 text-purple-400" />
            <span>Робочий кабінет мого акаунту та всі завантажені файли</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5 font-sans">
            Усі ваші завантажені відеофутажі, звукові доріжки, бренд-елементи та медіа-бібліотека
          </p>
        </div>

        {/* Upload Button */}
        <label className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/40 text-xs font-semibold text-purple-300 transition-all cursor-pointer shadow-sm">
          <UploadCloud className="w-4 h-4 text-purple-400" />
          <span>Завантажити файли</span>
          <input type="file" className="hidden" multiple />
        </label>
      </div>

      {/* Drag & Drop Zone (CapCut style) */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => { e.preventDefault(); setIsDragging(false); }}
        className={`mb-4 p-5 rounded-2xl border-2 border-dashed transition-all flex items-center justify-center gap-4 ${
          isDragging
            ? 'border-purple-400 bg-purple-950/40 scale-[1.01]'
            : 'border-white/10 bg-[#141722]/60 hover:border-purple-500/30'
        }`}
      >
        <div className="p-3 rounded-2xl bg-purple-600/15 text-purple-400 border border-purple-500/20">
          <UploadCloud className="w-6 h-6" />
        </div>
        <div>
          <h3 className="font-bold text-xs text-slate-200">
            Перетягніть футажі, фото або звуки сюди для миттєвого збереження в SCONES Vault
          </h3>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Підтримуються MP4, MOV, WAV, MP3, PNG, SVG (до 4K UHD без обмежень)
          </p>
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 mb-4 scrollbar-none">
        {categories.map(c => (
          <button
            key={c.id}
            onClick={() => setFilterType(c.id)}
            className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all cursor-pointer ${
              filterType === c.id
                ? 'bg-purple-600/25 text-purple-200 border border-purple-500/50 shadow-sm'
                : 'bg-[#141722]/80 text-slate-400 border border-white/5 hover:text-slate-200 hover:bg-[#1a1e2c]'
            }`}
          >
            {c.label}
          </button>
        ))}
      </div>

      {/* Assets Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
        {filtered.map((asset) => {
          const Icon = asset.icon;
          return (
            <div
              key={asset.id}
              className="p-3.5 rounded-2xl bg-[#141722]/85 border border-white/8 hover:border-purple-500/40 transition-all flex items-center justify-between group hover:shadow-xl hover:-translate-y-0.5"
            >
              <div className="flex items-center gap-3 truncate">
                <div className={`p-2.5 rounded-xl bg-slate-950 border border-white/5 ${asset.iconColor} shrink-0 shadow-inner`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div className="truncate">
                  <h4 className="font-semibold text-xs text-slate-200 truncate group-hover:text-purple-300 transition-colors">
                    {asset.name}
                  </h4>
                  <div className="flex items-center gap-2 text-[10px] text-slate-500 font-mono mt-0.5">
                    <span>{asset.size}</span>
                    <span>•</span>
                    <span>{asset.duration}</span>
                    <span>•</span>
                    <span className="text-purple-400">{asset.tag}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-1 shrink-0 ml-2">
                <button
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
                  title="Використати в проєкті"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
