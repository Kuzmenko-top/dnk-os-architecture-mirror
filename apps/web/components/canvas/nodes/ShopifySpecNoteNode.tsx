// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_ShopifySpecNoteNode"
// purpose: "Shopify E-Com Specification Living Document Node for DNK OS Note-Based Canvas (Task 3) combining theme settings, section inventory, Liquid AST compiler, and embedded live store mockup"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-31"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { 
  ShoppingBag, 
  Eye, 
  Laptop, 
  Play, 
  CheckCircle2, 
  RefreshCw, 
  Flame, 
  Check,
  ChevronDown,
  ChevronUp,
  Tag,
  Store,
  Layers
} from 'lucide-react';

export interface ThemeSection {
  id: string;
  name: string;
  type: string;
  enabled: boolean;
  category: string;
}

export interface ShopifySpecNoteData {
  storeName?: string;
  storeDomain?: string;
  themeArchitecture?: string;
  sections?: ThemeSection[];
}

export default function ShopifySpecNoteNode({ data, selected }: NodeProps) {
  const nodeData = (data || {}) as ShopifySpecNoteData;

  const [storeName, setStoreName] = useState<string>(nodeData.storeName || 'ReBurn Smoker & E-Com');
  const [storeDomain, setStoreDomain] = useState<string>(nodeData.storeDomain || 'reburn-smoker.myshopify.com');
  const [themeArchitecture] = useState<string>(nodeData.themeArchitecture || 'Shopify OS 2.0 (Neon Edition)');
  const [viewport, setViewport] = useState<'desktop' | 'mobile'>('desktop');
  const [buildStatus, setBuildStatus] = useState<'idle' | 'building' | 'deploying' | 'success'>('idle');
  const [statusMessage, setStatusMessage] = useState<string>('Liquid AST & Sections Synced');
  const [isExpanded, setIsExpanded] = useState<boolean>(true);

  const [sections, setSections] = useState<ThemeSection[]>(
    Array.isArray(nodeData.sections) && nodeData.sections.length > 0
      ? nodeData.sections
      : [
          { id: 's1', name: 'Hero Video Banner (High-Impact 9:16)', type: 'hero_video', enabled: true, category: 'Hero' },
          { id: 's2', name: 'High-AOV Bundle Selector (3-in-1 $120+)', type: 'bundle_selector', enabled: true, category: 'Conversion' },
          { id: 's3', name: 'Dynamic Product Grid & Verified Reviews', type: 'collection_grid', enabled: true, category: 'Catalog' },
          { id: 's4', name: 'Sticky 1-Click Checkout Slide Bar', type: 'sticky_atc', enabled: true, category: 'Checkout' },
        ]
  );

  const toggleSection = (id: string) => {
    setSections((prev) =>
      prev.map((s) => (s.id === id ? { ...s, enabled: !s.enabled } : s))
    );
  };

  const handleCompileAndDeploy = () => {
    setBuildStatus('building');
    setStatusMessage('Compiling Theme AST & Liquid templates...');
    setTimeout(() => {
      setBuildStatus('deploying');
      setStatusMessage('Syncing assets with Shopify Admin API...');
      setTimeout(() => {
        setBuildStatus('success');
        setStatusMessage('Theme Published & Active on Live Store! ✨');
      }, 1000);
    }, 800);
  };

  return (
    <div className={`w-[460px] rounded-3xl bg-[#02090a]/95 backdrop-blur-2xl border border-[#1e2c31] p-5 text-white shadow-[0_16px_50px_rgba(0,0,0,0.9)] transition-all duration-200 ${
      selected ? 'border-[#36f4a4] ring-1 ring-[#36f4a4] shadow-[0_0_35px_rgba(54,244,164,0.25)]' : ''
    }`}>
      {/* 4-Way Semantic Handles */}
      <Handle type="target" position={Position.Top} className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />
      <Handle type="source" position={Position.Bottom} className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />
      <Handle type="target" position={Position.Left} id="left" className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />
      <Handle type="source" position={Position.Right} id="right" className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />

      {/* Header */}
      <div className="flex items-start justify-between border-b border-[#1e2c31] pb-3 mb-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-2xl bg-[#102620] border border-[#36f4a4]/40 flex items-center justify-center text-[#36f4a4] shadow-sm">
            <ShoppingBag className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={storeName}
                onChange={(e) => setStoreName(e.target.value)}
                className="font-bold text-sm text-white bg-transparent border-none focus:outline-none focus:ring-1 focus:ring-[#36f4a4] rounded px-1"
              />
              <span className="px-2 py-0.5 rounded-full text-[9px] font-mono bg-[#102620] text-[#36f4a4] border border-[#36f4a4]/30 font-bold">OS 2.0</span>
            </div>
            <input
              type="text"
              value={storeDomain}
              onChange={(e) => setStoreDomain(e.target.value)}
              className="text-[11px] text-[#a1a1aa] bg-transparent border-none focus:outline-none focus:ring-1 focus:ring-[#36f4a4] rounded px-1 font-mono w-full truncate"
            />
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 rounded-full hover:bg-[#061a1c] text-[#a1a1aa] hover:text-white transition-colors cursor-pointer"
          >
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {isExpanded && (
        <>
          {/* Active Sections Checklist */}
          <div className="mb-3">
            <div className="flex items-center justify-between text-[11px] font-mono text-[#a1a1aa] mb-2 px-1">
              <span>Section Spec Inventory ({sections.filter(s => s.enabled).length}/{sections.length})</span>
              <span className="text-[#36f4a4] font-semibold">Liquid AST</span>
            </div>
            <div className="space-y-1.5 max-h-[140px] overflow-y-auto pr-1">
              {sections.map((sec) => (
                <div
                  key={sec.id}
                  onClick={() => toggleSection(sec.id)}
                  className={`flex items-center justify-between p-2.5 rounded-2xl text-xs font-mono cursor-pointer transition-all border ${
                    sec.enabled
                      ? 'bg-[#061a1c] border-[#1e2c31] text-white hover:border-[#36f4a4]/50'
                      : 'bg-[#02090a] border-[#1e2c31]/50 text-[#71717a]'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <div className={`w-4 h-4 rounded-full flex items-center justify-center border ${sec.enabled ? 'bg-[#36f4a4] border-[#36f4a4] text-black' : 'border-[#1e2c31]'}`}>
                      {sec.enabled && <Check className="w-3 h-3 stroke-[3]" />}
                    </div>
                    <span className="font-sans text-[11px] font-medium">{sec.name}</span>
                  </div>
                  <span className="text-[9px] uppercase px-2 py-0.5 rounded-full bg-[#02090a] text-[#a1a1aa] border border-[#1e2c31]">
                    {sec.category}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Embedded Live Mockup Preview */}
          <div className="mb-3 p-3 rounded-2xl bg-[#061a1c] border border-[#1e2c31]">
            <div className="flex items-center justify-between text-[10px] font-mono text-[#a1a1aa] mb-2 border-b border-[#1e2c31] pb-1.5">
              <span className="flex items-center gap-1.5 text-[#36f4a4] font-semibold">
                <Eye className="w-3 h-3" /> Live Mockup Preview
              </span>
              <span className="text-[#71717a] font-mono">{viewport.toUpperCase()} • 100% SCALE</span>
            </div>

            <div className="w-full rounded-xl overflow-hidden border border-[#1e2c31] bg-[#02090a] p-3 text-center">
              <div className="h-12 rounded-lg bg-[#102620] border border-[#36f4a4]/30 flex flex-col items-center justify-center mb-2">
                <span className="text-[10px] font-bold text-[#36f4a4] font-mono">⚡ 3-in-1 BUNDLE PROMO</span>
                <span className="text-[8px] text-[#a1a1aa]">Save $45 + Free Worldwide Shipping</span>
              </div>
              <div className="flex items-center justify-center gap-1.5 text-[9px] font-mono text-[#a1a1aa]">
                <Flame className="w-3 h-3 text-[#36f4a4] animate-pulse" />
                <span>Liquid AST Synchronized</span>
              </div>
            </div>
          </div>

          {/* Action Trigger Button */}
          <button
            onClick={handleCompileAndDeploy}
            disabled={buildStatus === 'building' || buildStatus === 'deploying'}
            className="w-full py-2.5 px-4 rounded-full bg-[#36f4a4] hover:bg-[#2de097] text-black font-bold font-mono text-xs flex items-center justify-center gap-2 transition-all shadow-md shadow-[#36f4a4]/20 active:scale-98 cursor-pointer"
          >
            {buildStatus === 'building' || buildStatus === 'deploying' ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : buildStatus === 'success' ? (
              <CheckCircle2 className="w-4 h-4" />
            ) : (
              <Play className="w-4 h-4 fill-current" />
            )}
            <span>
              {buildStatus === 'building'
                ? 'Compiling AST...'
                : buildStatus === 'deploying'
                ? 'Deploying to Shopify...'
                : buildStatus === 'success'
                ? 'Theme Live & Ready'
                : 'Build & Deploy Theme'}
            </span>
          </button>
        </>
      )}

      {/* Footer */}
      <div className="mt-3 pt-2.5 border-t border-[#1e2c31] flex items-center justify-between text-[10px] font-mono text-[#a1a1aa]">
        <span className="truncate max-w-[280px] text-white">{statusMessage}</span>
        <span className="text-[#36f4a4] font-semibold">/api/shopify/build</span>
      </div>
    </div>
  );
}
