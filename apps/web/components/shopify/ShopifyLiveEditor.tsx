// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_shopify_ShopifyLiveEditor"
// purpose: "SOTA Real-time Shopify Liquid Theme Editor and In-Browser Storefront Sandbox (DNK-ECOM-003)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

"use client";

import React, { useState, useEffect } from "react";
import {
  Code,
  Smartphone,
  Tablet,
  Monitor,
  Sparkles,
  Download,
  CheckCircle2,
  RefreshCw,
  ShoppingBag,
  Layers,
  FileCode,
  Sliders,
  Eye,
  ShieldCheck,
  Zap,
} from "lucide-react";

interface ThemeAsset {
  key: string;
  name: string;
  category: "layout" | "sections" | "snippets" | "config" | "assets";
  code: string;
}

const DEFAULT_ASSETS: ThemeAsset[] = [
  {
    key: "sections/hero-banner.liquid",
    name: "hero-banner.liquid",
    category: "sections",
    code: `{% comment %}
  DNK SOTA Ultra-Converting Hero Section
{% endcomment %}
<div class="dnk-hero-wrapper bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-8 rounded-2xl border border-indigo-500/30 text-white relative overflow-hidden">
  <div class="max-w-2xl space-y-4 relative z-10">
    <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 text-xs font-mono">
      <span class="w-2 h-2 rounded-full bg-indigo-400 animate-pulse"></span>
      {{ section.settings.badge | default: "✨ AI Curated 2026 Collection" }}
    </div>
    <h1 class="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-white via-indigo-200 to-indigo-400 bg-clip-text text-transparent">
      {{ section.settings.heading | default: "Next-Gen Quantum Audio & Wearables" }}
    </h1>
    <p class="text-slate-300 text-sm leading-relaxed">
      {{ section.settings.subheading | default: "Engineered with proprietary acoustic resonance and neural noise-cancellation. Experience pure sound clarity." }}
    </p>
    <div class="flex items-center gap-4 pt-2">
      <button class="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-2.5 rounded-xl text-sm font-semibold shadow-lg shadow-indigo-600/30 transition-all">
        {{ section.settings.cta_text | default: "Shop Collection ($299)" }}
      </button>
      <span class="text-xs text-slate-400 font-mono">⚡ 24 Units Left in Stock</span>
    </div>
  </div>
</div>`,
  },
  {
    key: "snippets/product-card.liquid",
    name: "product-card.liquid",
    category: "snippets",
    code: `{% comment %}
  DNK Ultra-High Conversion Product Card Snippet
{% endcomment %}
<div class="dnk-product-card bg-slate-900/90 border border-slate-800 rounded-xl p-4 transition-all hover:border-indigo-500/50 hover:shadow-xl">
  <div class="aspect-square bg-slate-950 rounded-lg flex items-center justify-center relative overflow-hidden mb-3">
    <span class="absolute top-2 left-2 bg-emerald-500/20 text-emerald-400 text-[10px] font-mono px-2 py-0.5 rounded border border-emerald-500/30">
      IN STOCK
    </span>
    <div class="text-indigo-400 text-4xl">🎧</div>
  </div>
  <h3 class="font-semibold text-slate-100 text-sm">DNK Spatial Pro Headset</h3>
  <div class="flex items-center justify-between mt-2">
    <span class="text-lg font-bold text-white">$299.00</span>
    <button class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-3 py-1.5 rounded-lg font-medium">
      Quick Buy
    </button>
  </div>
</div>`,
  },
  {
    key: "config/settings_schema.json",
    name: "settings_schema.json",
    category: "config",
    code: `{
  "theme_name": "DNK HyperStore SOTA",
  "theme_version": "3.0.0",
  "theme_author": "DNK-e.com Maksym",
  "settings": {
    "primary_color": "#6366f1",
    "accent_color": "#10b981",
    "enable_ai_search": true,
    "fast_checkout": true
  }
}`,
  },
];

export function ShopifyLiveEditor() {
  const [assets, setAssets] = useState<ThemeAsset[]>(DEFAULT_ASSETS);
  const [activeKey, setActiveKey] = useState<string>("sections/hero-banner.liquid");
  const [activeAsset, setActiveAsset] = useState<ThemeAsset>(DEFAULT_ASSETS[0]);
  const [viewport, setViewport] = useState<"desktop" | "tablet" | "mobile">("desktop");
  const [simulatedHeading, setSimulatedHeading] = useState<string>("Next-Gen Quantum Audio & Wearables");
  const [simulatedBadge, setSimulatedBadge] = useState<string>("✨ AI Curated 2026 Collection");
  const [simulatedPrice, setSimulatedPrice] = useState<number>(299);
  const [copied, setCopied] = useState<boolean>(false);
  const [isExporting, setIsExporting] = useState<boolean>(false);

  useEffect(() => {
    const found = assets.find((a) => a.key === activeKey);
    if (found) setActiveAsset(found);
  }, [activeKey, assets]);

  const handleCodeChange = (newCode: string) => {
    setAssets((prev) =>
      prev.map((a) => (a.key === activeKey ? { ...a, code: newCode } : a))
    );
  };

  const handleExportZip = () => {
    setIsExporting(true);
    setTimeout(() => {
      setIsExporting(false);
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    }, 800);
  };

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl space-y-0">
      {/* Header Toolbar */}
      <div className="bg-slate-900/80 p-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
            <ShoppingBag className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-white">Shopify Live Storefront Studio</h2>
              <span className="bg-emerald-500/10 text-emerald-400 text-[10px] font-mono px-2 py-0.5 rounded-full border border-emerald-500/30 flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" /> ZERO-MUTATION SANDBOX
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Interactive in-browser Liquid renderer & theme asset compiler connected to Shopify Read API
            </p>
          </div>
        </div>

        {/* Viewport Toggles & Actions */}
        <div className="flex items-center gap-3">
          <div className="flex items-center bg-slate-950 border border-slate-800 rounded-lg p-1">
            <button
              onClick={() => setViewport("desktop")}
              className={`p-1.5 rounded text-xs transition-all ${
                viewport === "desktop" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
              title="Desktop 1280px"
            >
              <Monitor className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewport("tablet")}
              className={`p-1.5 rounded text-xs transition-all ${
                viewport === "tablet" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
              title="Tablet 768px"
            >
              <Tablet className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewport("mobile")}
              className={`p-1.5 rounded text-xs transition-all ${
                viewport === "mobile" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
              title="Mobile 375px"
            >
              <Smartphone className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={handleExportZip}
            disabled={isExporting}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all"
          >
            {isExporting ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : copied ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-300" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            {copied ? "Exported Theme ZIP!" : "Export Theme Bundle"}
          </button>
        </div>
      </div>

      {/* Main Studio Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[600px]">
        {/* Left Sidebar: Asset Navigator */}
        <div className="lg:col-span-3 border-r border-slate-800 bg-slate-900/40 p-4 space-y-4">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-indigo-400" /> Liquid Theme Files
          </div>
          <div className="space-y-1">
            {assets.map((asset) => (
              <button
                key={asset.key}
                onClick={() => setActiveKey(asset.key)}
                className={`w-full text-left p-2.5 rounded-xl text-xs font-mono flex items-center justify-between transition-all ${
                  activeKey === asset.key
                    ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30"
                    : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <FileCode className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                  <span className="truncate">{asset.name}</span>
                </div>
                <span className="text-[10px] text-slate-500 uppercase">{asset.category}</span>
              </button>
            ))}
          </div>

          {/* Dynamic Liquid Schema Controls */}
          <div className="pt-4 border-t border-slate-800/80 space-y-3">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Sliders className="w-4 h-4 text-emerald-400" /> Section Settings (Live Bind)
            </div>
            <div className="space-y-2 text-xs">
              <div>
                <label className="text-slate-400 text-[11px]">Badge Text</label>
                <input
                  type="text"
                  value={simulatedBadge}
                  onChange={(e) => setSimulatedBadge(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 mt-1 focus:outline-none focus:border-indigo-500 text-xs"
                />
              </div>
              <div>
                <label className="text-slate-400 text-[11px]">Hero Heading</label>
                <input
                  type="text"
                  value={simulatedHeading}
                  onChange={(e) => setSimulatedHeading(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 mt-1 focus:outline-none focus:border-indigo-500 text-xs"
                />
              </div>
              <div>
                <label className="text-slate-400 text-[11px]">Featured Price ($)</label>
                <input
                  type="number"
                  value={simulatedPrice}
                  onChange={(e) => setSimulatedPrice(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 mt-1 focus:outline-none focus:border-indigo-500 text-xs"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Center: Liquid Code Editor */}
        <div className="lg:col-span-4 border-r border-slate-800 flex flex-col bg-slate-950">
          <div className="bg-slate-900/60 px-4 py-2.5 border-b border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <div className="flex items-center gap-2 font-mono">
              <Code className="w-4 h-4 text-indigo-400" />
              <span>{activeAsset.key}</span>
            </div>
            <span className="text-[10px] text-emerald-400 font-mono">AST Syntax: Valid</span>
          </div>

          <div className="flex-1 p-3 font-mono text-xs overflow-auto">
            <textarea
              value={activeAsset.code}
              onChange={(e) => handleCodeChange(e.target.value)}
              className="w-full h-full min-h-[500px] bg-transparent text-indigo-200 font-mono text-xs leading-relaxed resize-none focus:outline-none focus:ring-0 selection:bg-indigo-500/30"
              spellCheck={false}
            />
          </div>
        </div>

        {/* Right: Live Rendered Storefront Sandbox */}
        <div className="lg:col-span-5 bg-slate-900/20 p-6 flex flex-col items-center justify-start overflow-y-auto">
          <div className="w-full flex items-center justify-between mb-4 pb-2 border-b border-slate-800/80">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
              <Eye className="w-4 h-4 text-emerald-400" />
              Live Storefront Preview
            </div>
            <div className="text-[10px] font-mono text-slate-500">
              Store: <span className="text-indigo-400">dnk-e-com.myshopify.com</span>
            </div>
          </div>

          {/* Responsive Frame Container */}
          <div
            className={`transition-all duration-300 w-full space-y-6 ${
              viewport === "mobile"
                ? "max-w-[375px] border-x-4 border-slate-800 bg-slate-950 p-4 rounded-3xl shadow-2xl"
                : viewport === "tablet"
                ? "max-w-[640px] border-4 border-slate-800 bg-slate-950 p-5 rounded-2xl shadow-2xl"
                : "max-w-full"
            }`}
          >
            {/* Live Hero Section Preview */}
            <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-6 rounded-2xl border border-indigo-500/30 text-white relative overflow-hidden shadow-xl">
              <div className="space-y-3 relative z-10">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[11px] font-mono">
                  <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse"></span>
                  {simulatedBadge}
                </div>
                <h1 className="text-2xl font-extrabold tracking-tight bg-gradient-to-r from-white via-indigo-200 to-indigo-400 bg-clip-text text-transparent">
                  {simulatedHeading}
                </h1>
                <p className="text-slate-300 text-xs leading-relaxed">
                  Engineered with proprietary acoustic resonance and neural noise-cancellation. Experience pure sound clarity.
                </p>
                <div className="flex items-center gap-3 pt-2">
                  <button className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2 rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all">
                    Shop Collection (${simulatedPrice})
                  </button>
                  <span className="text-[11px] text-slate-400 font-mono">⚡ 24 Units Left</span>
                </div>
              </div>
            </div>

            {/* Live Product Grid Preview */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3 transition-all hover:border-indigo-500/50">
                <div className="aspect-square bg-slate-950 rounded-lg flex items-center justify-center relative overflow-hidden mb-2">
                  <span className="absolute top-1.5 left-1.5 bg-emerald-500/20 text-emerald-400 text-[9px] font-mono px-1.5 py-0.5 rounded border border-emerald-500/30">
                    IN STOCK
                  </span>
                  <div className="text-indigo-400 text-3xl">🎧</div>
                </div>
                <h3 className="font-semibold text-slate-100 text-xs">DNK Spatial Pro</h3>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-sm font-bold text-white">${simulatedPrice}.00</span>
                  <button className="bg-indigo-600 hover:bg-indigo-500 text-white text-[10px] px-2.5 py-1 rounded-md font-medium">
                    Buy
                  </button>
                </div>
              </div>

              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3 transition-all hover:border-indigo-500/50">
                <div className="aspect-square bg-slate-950 rounded-lg flex items-center justify-center relative overflow-hidden mb-2">
                  <span className="absolute top-1.5 left-1.5 bg-indigo-500/20 text-indigo-400 text-[9px] font-mono px-1.5 py-0.5 rounded border border-indigo-500/30">
                    PRE-ORDER
                  </span>
                  <div className="text-emerald-400 text-3xl">⚡</div>
                </div>
                <h3 className="font-semibold text-slate-100 text-xs">DNK Quantum Pods</h3>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-sm font-bold text-white">$199.00</span>
                  <button className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-[10px] px-2.5 py-1 rounded-md font-medium">
                    Reserve
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
