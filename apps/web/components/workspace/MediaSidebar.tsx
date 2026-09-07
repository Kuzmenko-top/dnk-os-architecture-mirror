// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_workspace_MediaSidebar"
// purpose: "Visual Template Sidebar for media templates (Video, Shopify, Photo) supporting HTML5 drag-to-canvas spawning with metadata and clean CapCut look"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-03"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { 
  Film, 
  ShoppingBag, 
  Camera, 
  Sparkles, 
  Grid, 
  Search, 
  Plus, 
  Move,
  Clock,
  Play,
  Copy
} from 'lucide-react';

interface TemplateItem {
  id: string;
  title: string;
  description: string;
  type: 'video_script' | 'shopify_spec' | 'photo_studio';
  category: string;
  nodeType: string;
  defaultData: Record<string, any>;
}

const TEMPLATES: TemplateItem[] = [
  // Video Storyboard Templates
  {
    id: 'vid-temp-kinetic',
    title: 'Kinetic UGC Hook',
    description: 'High-energy 9:16 product reveal with aggressive zoom cuts, emerald text overlays, and sound design markers.',
    type: 'video_script',
    category: 'Video (9:16)',
    nodeType: 'VideoStoryboardNoteNode',
    defaultData: {
      title: 'Kinetic UGC Product Hook',
      aspectRatio: '9:16',
      motionStyle: 'Hyper-Kinetic Neon Shutter',
      duration: 15,
      scenes: [
        { id: 'sc1', timeRange: '0:00 - 0:03', visualPrompt: 'Macro extreme close-up of titanium burner head firing blue-to-emerald lightning flame.', voiceover: '"This is NOT your average cocktail smoker."' },
        { id: 'sc2', timeRange: '0:03 - 0:08', visualPrompt: 'Smooth dynamic circular pan of solid oak chips releasing dense white smoke inside custom bell cloche.', voiceover: '"Instant premium bar experience, right on your table."' },
        { id: 'sc3', timeRange: '0:08 - 0:15', visualPrompt: 'Hands lifting smoker cloche to reveal swirling smoke cloud over perfectly chilled glass with glowing product logo.', voiceover: '"Level up your bar game today. 1-click bundle link below."' }
      ]
    }
  },
  {
    id: 'vid-temp-unboxing',
    title: 'ASMR Unboxing Experience',
    description: 'Crisp close-up ASMR unpackaging focusing on textured black matte paper, magnetic clasp clicks, and wooden textures.',
    type: 'video_script',
    category: 'Video (9:16)',
    nodeType: 'VideoStoryboardNoteNode',
    defaultData: {
      title: 'ASMR Luxury Unboxing',
      aspectRatio: '9:16',
      motionStyle: 'Satisfying ASMR Matte Flow',
      duration: 20,
      scenes: [
        { id: 'sc1', timeRange: '0:00 - 0:05', visualPrompt: 'Close-up of fingertips gently running across embossed matte-black box cover. Sharp audio of magnetic lid snapping open.', voiceover: '(*Magnetic click and satisfaction sound effects*)' },
        { id: 'sc2', timeRange: '0:05 - 0:12', visualPrompt: 'Lifting each gold-anodized metal part from its laser-cut foam insert. Laying them out with metallic ping sound.', voiceover: '"Unboxing the perfect cocktail smoker pack."' },
        { id: 'sc3', timeRange: '0:12 - 0:20', visualPrompt: 'Sliding out solid cherry wood coaster and igniting the first torch smoke. Heavy wood crackle sound.', voiceover: '"Premium quality you can hear and taste."' }
      ]
    }
  },

  // Shopify OS 2.0 Spec Templates
  {
    id: 'shop-temp-bundle',
    title: 'Glowing Bundle Stack Section',
    description: 'Shopify Liquid section for 3-in-1 cocktail smoker bundles with real-time countdown timers and stock-level urgency bars.',
    type: 'shopify_spec',
    category: 'Shopify OS 2.0',
    nodeType: 'ShopifySpecNoteNode',
    defaultData: {
      title: 'Glowing Bundle Stack Spec',
      theme: 'Dawn 15.0',
      section: 'Featured Product Bundle',
      liquidDetails: {
        features: ['Dynamic price calculating on component select', 'Glowing neon add-to-cart callout', 'Urgency countdown standard schema'],
        transpileTarget: 'sections/featured-bundle-stack.liquid'
      }
    }
  },
  {
    id: 'shop-temp-interactive',
    title: 'Interactive Cloche Transpiler',
    description: 'Custom canvas-to-liquid interactive smoke cloche reveal section with instant checkout hooks.',
    type: 'shopify_spec',
    category: 'Shopify OS 2.0',
    nodeType: 'ShopifySpecNoteNode',
    defaultData: {
      title: 'Interactive Cloche Reveal Section',
      theme: 'Sense 12.0',
      section: 'Interactive Cloche Reveal',
      liquidDetails: {
        features: ['Haptic feedback triggers', 'Dynamic product properties selector', '1-Click fast-checkout API integration'],
        transpileTarget: 'sections/interactive-cloche.liquid'
      }
    }
  },

  // Photo Studio Templates
  {
    id: 'photo-temp-neon',
    title: 'Studio Dark Neon Product Portrait',
    description: 'Branding lifestyle photograph highlighting glowing smoke paths, high contrast shadows, and emerald lasers.',
    type: 'photo_studio',
    category: 'Photo Studio',
    nodeType: 'PhotoStudioNode',
    defaultData: {
      title: 'Studio Dark Neon Portrait',
      prompt: 'Macro luxury tabletop photography of titanium cocktail smoker, heavy swirling smoke illuminated by thin laser beams of emerald green and electric cyan, stark moody contrast, cinematic dark bar background, 8k resolution, photorealistic',
      aspectRatio: '1:1'
    }
  },
  {
    id: 'photo-temp-outdoor',
    title: 'Daylight Tabletop Bar Lifestyle',
    description: 'Warm golden-hour ambient outdoor setup, glass condensation, smoke details with rich shadows.',
    type: 'photo_studio',
    category: 'Photo Studio',
    nodeType: 'PhotoStudioNode',
    defaultData: {
      title: 'Golden Hour Bar Lifestyle',
      prompt: 'Branding lifestyle photography of an elegant cocktail smoke dome resting on a rustic oak table outdoors during warm golden hour sunset, condensation on crystal glasses, warm sunlight refraction, luxury aesthetic, soft bokeh background',
      aspectRatio: '16:9'
    }
  }
];

interface MediaSidebarProps {
  onSpawnTemplate?: (nodeType: string, defaultData: Record<string, any>) => void;
}

export default function MediaSidebar({ onSpawnTemplate }: MediaSidebarProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const handleDragStart = (e: React.DragEvent, nodeType: string, defaultData: Record<string, any>) => {
    e.dataTransfer.setData('application/reactflow', nodeType);
    e.dataTransfer.setData('application/reactflow-data', JSON.stringify(defaultData));
    e.dataTransfer.effectAllowed = 'move';
  };

  const filteredTemplates = TEMPLATES.filter(tpl => {
    const matchesSearch = tpl.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          tpl.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = !selectedCategory || tpl.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const categories = Array.from(new Set(TEMPLATES.map(tpl => tpl.category)));

  return (
    <div className="w-80 border-r border-[#1e2c31] bg-[#02090a]/95 backdrop-blur-2xl flex flex-col h-full text-white overflow-hidden relative select-none">
      {/* Glow Accent Line */}
      <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-[#36f4a4]/30 to-transparent" />

      {/* Sidebar Header */}
      <div className="p-4 border-b border-[#1e2c31]">
        <div className="flex items-center gap-2 mb-3">
          <div className="p-1.5 rounded-lg bg-[#102620] border border-[#36f4a4]/30 text-[#36f4a4]">
            <Sparkles className="w-4 h-4 animate-pulse" />
          </div>
          <div>
            <h2 className="font-bold text-sm tracking-wider">MEDIA TEMPLATES</h2>
            <p className="text-[10px] text-[#71717a] font-mono">DRAG & DROP TO CANVAS</p>
          </div>
        </div>

        {/* Search Bar */}
        <div className="flex items-center gap-2 bg-[#061a1c] border border-[#1e2c31] rounded-xl px-3 py-2 focus-within:border-[#36f4a4]/40 transition-colors">
          <Search className="w-3.5 h-3.5 text-[#4c5c5c]" />
          <input
            type="text"
            placeholder="Search templates..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-transparent border-none text-xs text-white focus:outline-none focus:ring-0 placeholder-[#4c5c5c] w-full"
          />
        </div>
      </div>

      {/* Category Tabs */}
      <div className="px-4 py-2 border-b border-[#1e2c31] flex gap-1.5 overflow-x-auto scrollbar-none shrink-0">
        <button
          onClick={() => setSelectedCategory(null)}
          className={`px-2.5 py-1 rounded-lg text-[10px] font-mono whitespace-nowrap border transition-colors cursor-pointer ${
            !selectedCategory 
              ? 'bg-[#102620] border-[#36f4a4]/40 text-[#36f4a4]' 
              : 'bg-[#061a1c] border-transparent text-[#71717a] hover:text-white'
          }`}
        >
          All
        </button>
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-2.5 py-1 rounded-lg text-[10px] font-mono whitespace-nowrap border transition-colors cursor-pointer ${
              selectedCategory === cat 
                ? 'bg-[#102620] border-[#36f4a4]/40 text-[#36f4a4]' 
                : 'bg-[#061a1c] border-transparent text-[#71717a] hover:text-white'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Templates List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
        {filteredTemplates.map(tpl => {
          let typeIcon = <Film className="w-3.5 h-3.5 text-[#36f4a4]" />;
          let accentBorder = 'hover:border-[#36f4a4]/30';
          let tagBg = 'bg-[#102620] text-[#36f4a4] border-[#36f4a4]/20';
          
          if (tpl.type === 'shopify_spec') {
            typeIcon = <ShoppingBag className="w-3.5 h-3.5 text-[#22d3ee]" />;
            accentBorder = 'hover:border-[#22d3ee]/30';
            tagBg = 'bg-[#081e2b] text-[#22d3ee] border-[#22d3ee]/20';
          } else if (tpl.type === 'photo_studio') {
            typeIcon = <Camera className="w-3.5 h-3.5 text-[#c084fc]" />;
            accentBorder = 'hover:border-[#c084fc]/30';
            tagBg = 'bg-[#1e112c] text-[#c084fc] border-[#c084fc]/20';
          }

          return (
            <div
              key={tpl.id}
              draggable
              onDragStart={(e) => handleDragStart(e, tpl.nodeType, tpl.defaultData)}
              className={`p-3.5 rounded-2xl bg-[#061a1c] border border-[#1e2c31] ${accentBorder} cursor-grab active:cursor-grabbing transition-all group relative overflow-hidden`}
              title="Drag me onto the canvas!"
            >
              {/* Corner drag handle indicator */}
              <div className="absolute top-2.5 right-2.5 opacity-0 group-hover:opacity-100 text-[#71717a] transition-opacity duration-200 pointer-events-none">
                <Move className="w-3.5 h-3.5" />
              </div>

              {/* Title & Icon */}
              <div className="flex items-center gap-2 mb-1.5 pr-6">
                {typeIcon}
                <h3 className="font-bold text-xs truncate group-hover:text-white text-[#d4d4d8] transition-colors">{tpl.title}</h3>
              </div>

              {/* Description */}
              <p className="text-[11px] text-[#71717a] leading-relaxed mb-3 font-sans group-hover:text-[#a1a1aa] transition-colors">
                {tpl.description}
              </p>

              {/* Tag & Action Row */}
              <div className="flex items-center justify-between">
                <span className={`px-2 py-0.5 rounded-full text-[9px] font-mono font-bold border ${tagBg}`}>
                  {tpl.category}
                </span>

                <button
                  onClick={() => onSpawnTemplate?.(tpl.nodeType, tpl.defaultData)}
                  className="p-1 rounded bg-[#02090a]/50 border border-[#1e2c31] hover:border-[#36f4a4]/40 text-[#a1a1aa] hover:text-white opacity-0 group-hover:opacity-100 transition-all cursor-pointer"
                  title="Spawn directly here"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}

        {filteredTemplates.length === 0 && (
          <div className="text-center py-8">
            <p className="text-xs text-[#71717a] font-mono">No templates found</p>
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="p-3 bg-[#02090a]/50 border-t border-[#1e2c31] text-[10px] font-mono text-[#71717a] flex items-center justify-between">
        <span>STITCH TEMPLATES v1.2</span>
        <span className="flex items-center gap-1 text-[#36f4a4]">
          <Play className="w-2.5 h-2.5 fill-current" />
          <span>DRAG READY</span>
        </span>
      </div>
    </div>
  );
}
