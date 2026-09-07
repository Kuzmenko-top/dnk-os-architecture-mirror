# --- DNK-MRH-HEADER ---
# mrh_id: "scripts_demo_shopify_ast"
# purpose: "Standalone Interactive Demo & Studio Server for Shopify OS 2.0 AST, Mega-Registry, Infinite Canvas DAG, and ZIP Exporter."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import sys
import os
import json
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

# Ensure project root is in sys.path
HUB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HUB_ROOT not in sys.path:
    sys.path.insert(0, HUB_ROOT)

from services.dnk_shopify_builder.mechanical_transpiler import mechanical_transpiler
from services.dnk_shopify_builder.liquid_compiler import liquid_compiler
from services.dnk_shopify_builder.template_state_engine import TemplateStateEngine
from services.dnk_shopify_builder.theme_adapter import theme_adapter
from services.dnk_shopify_builder.store_synthesizer import store_synthesizer
from services.dnk_shopify_builder.theme_exporter import theme_exporter

app = FastAPI(
    title="DNK OS — Shopify Agentic Studio & AST Demo",
    description="Interactive laboratory for OS 2.0 AST transpilation, Visual Canvas DAG, Store Synthesis, and Theme ZIP Export.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TranspileNodeRequest(BaseModel):
    html_content: str = Field(..., description="Raw HTML/Tailwind from canvas")
    section_name: str = Field(default="custom_section", description="Target section name")
    theme_tokens: Optional[Dict[str, str]] = Field(default=None, description="Theme design tokens")


class TemplateMutateRequest(BaseModel):
    template: Dict[str, Any] = Field(..., description="Shopify OS 2.0 JSON template")
    action: str = Field(..., description="Mutation action: add_section, remove_section, move_section, add_block, set_settings")
    params: Dict[str, Any] = Field(default_factory=dict, description="Action-specific parameters")


class SynthesizeStoreRequest(BaseModel):
    store_name: str = Field(default="Apex Cybernetics", description="Brand or store name")
    niche: str = Field(default="tech_apparel", description="Niche preset")
    theme_tokens: Optional[Dict[str, str]] = Field(default=None, description="Open design tokens")


class AdaptBlockRequest(BaseModel):
    section_name: str = Field(..., description="Legacy section file name to adapt into Tinker block")
    target_block_name: Optional[str] = Field(default=None, description="Optional custom target block name")


class StoreExportZipRequest(BaseModel):
    store_name: str = Field(default="Apex Cybernetics", description="Store or brand name")
    niche: str = Field(default="tech_apparel", description="Niche: tech_apparel, health_supplements, luxury_jewelry, general_ecom")
    theme_tokens: Optional[Dict[str, str]] = Field(default=None, description="Custom theme tokens")
    custom_templates: Optional[Dict[str, Any]] = Field(default=None, description="Optional customized JSON templates dict")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "dnk_shopify_ast_studio", "version": "2.0.0"}


@app.post("/api/shopify/transpile/canvas-node")
def transpile_canvas_node(req: TranspileNodeRequest):
    try:
        ast_result = mechanical_transpiler.transpile(
            html_content=req.html_content,
            section_name=req.section_name,
            theme_tokens=req.theme_tokens
        )
        liquid_code = ast_result.get("liquid", "")
        validation = liquid_compiler.validate(liquid_code)
        return {
            "ast": ast_result,
            "liquid": liquid_code,
            "validation": validation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/shopify/template/mutate")
def mutate_template(req: TemplateMutateRequest):
    try:
        mutated = TemplateStateEngine.mutate(
            template=req.template,
            action=req.action,
            **req.params
        )
        return {"success": True, "template": mutated}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/shopify/components/registry")
def get_components_registry():
    try:
        return theme_adapter.build_mega_registry()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/shopify/components/adapt-block")
def adapt_legacy_section_to_block(req: AdaptBlockRequest):
    try:
        res = theme_adapter.adapt_legacy_section_to_tinker_block(
            section_name=req.section_name,
            target_block_name=req.target_block_name
        )
        if not res.get("success", False):
            raise HTTPException(status_code=404, detail=res.get("error", "Adaptation failed"))
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/shopify/store/synthesize")
def synthesize_store(req: SynthesizeStoreRequest):
    try:
        return store_synthesizer.synthesize_store(
            store_name=req.store_name,
            niche=req.niche,
            theme_tokens=req.theme_tokens
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/shopify/store/export-manifest")
def export_store_manifest(req: StoreExportZipRequest):
    try:
        _, manifest = theme_exporter.export_store_zip(
            store_name=req.store_name,
            niche=req.niche,
            theme_tokens=req.theme_tokens,
            custom_templates=req.custom_templates
        )
        return manifest
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/shopify/store/export-zip")
def export_store_zip(req: StoreExportZipRequest):
    try:
        zip_bytes, manifest = theme_exporter.export_store_zip(
            store_name=req.store_name,
            niche=req.niche,
            theme_tokens=req.theme_tokens,
            custom_templates=req.custom_templates
        )
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=\"{manifest['archive_name']}\"",
                "X-Archive-Name": manifest["archive_name"],
                "X-Archive-Size-KB": str(manifest["size_kb"]),
                "X-Total-Files": str(manifest["files_summary"]["total_files"])
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", response_class=HTMLResponse)
def index_page():
    return HTMLResponse(content="""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DNK OS — Shopify Agentic Studio & Infinite Canvas</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #030712;
      --bg-card: #0f172a;
      --bg-input: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --cyan: #06b6d4;
      --violet: #8b5cf6;
      --rose: #f43f5e;
      --emerald: #10b981;
      --amber: #f59e0b;
      --font: 'Plus Jakarta Sans', sans-serif;
      --mono: 'JetBrains Mono', monospace;
      --radius: 12px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: var(--font);
      padding: 2rem;
      min-height: 100vh;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 2rem;
      border-bottom: 1px solid var(--border);
      padding-bottom: 1.5rem;
      flex-wrap: wrap;
      gap: 1rem;
    }
    .header h1 {
      font-size: 1.8rem;
      font-weight: 800;
      background: linear-gradient(135deg, var(--cyan), var(--violet), var(--rose));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .header p { color: var(--text-muted); font-size: 0.95rem; margin-top: 0.25rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(460px, 1fr)); gap: 1.5rem; }
    .card {
      background: var(--bg-card); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 1.5rem;
      transition: border-color 0.3s, box-shadow 0.3s;
    }
    .card:hover { border-color: var(--cyan); box-shadow: 0 0 30px rgba(6,182,212,0.12); }
    .card h2 {
      font-size: 1.25rem; font-weight: 600; margin-bottom: 1rem;
      display: flex; align-items: center; gap: 0.5rem; justify-content: space-between;
    }
    .badge {
      font-size: 0.7rem; padding: 3px 8px; border-radius: 100px;
      font-weight: 600; text-transform: uppercase;
    }
    .badge-rose { background: rgba(244,63,94,0.2); color: var(--rose); }
    .badge-cyan { background: rgba(6,182,212,0.2); color: var(--cyan); }
    .badge-violet { background: rgba(139,92,246,0.2); color: var(--violet); }
    .badge-emerald { background: rgba(16,185,129,0.2); color: var(--emerald); }
    .badge-amber { background: rgba(245,158,11,0.2); color: var(--amber); }

    input, select, textarea {
      width: 100%; background: var(--bg-input);
      border: 1px solid var(--border); border-radius: 8px;
      color: var(--text); font-family: var(--font); font-size: 0.9rem;
      padding: 0.75rem 1rem; outline: none; transition: border-color 0.3s;
    }
    textarea { font-family: var(--mono); font-size: 0.85rem; min-height: 140px; resize: vertical; }
    input:focus, select:focus, textarea:focus { border-color: var(--cyan); }

    .btn-group { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 1rem; }
    button {
      padding: 0.75rem 1.25rem;
      background: linear-gradient(135deg, var(--cyan), var(--violet));
      color: white; border: none; border-radius: 8px;
      font-family: var(--font); font-weight: 600; font-size: 0.9rem;
      cursor: pointer; transition: opacity 0.2s, transform 0.1s;
      display: inline-flex; align-items: center; gap: 0.5rem;
    }
    button.btn-emerald { background: linear-gradient(135deg, var(--emerald), var(--cyan)); }
    button.btn-amber { background: linear-gradient(135deg, var(--amber), var(--rose)); }
    button.btn-secondary { background: var(--bg-input); border: 1px solid var(--border); }
    button:hover { opacity: 0.9; }
    button:active { transform: scale(0.98); }

    .output {
      margin-top: 1rem; background: var(--bg-input);
      border: 1px solid var(--border); border-radius: 8px;
      padding: 1rem; font-family: var(--mono); font-size: 0.8rem;
      max-height: 360px; overflow: auto; white-space: pre-wrap;
      color: var(--emerald); line-height: 1.5;
    }
    .output.error { color: var(--rose); }
    .full-card { grid-column: 1 / -1; }

    .stats { display: flex; gap: 1rem; margin-top: 1rem; flex-wrap: wrap; }
    .stat {
      background: var(--bg); border: 1px solid var(--border);
      border-radius: 8px; padding: 0.75rem 1rem; flex: 1; min-width: 120px;
      text-align: center;
    }
    .stat-value { font-size: 1.6rem; font-weight: 700; color: var(--cyan); }
    .stat-label { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem; }

    /* Canvas DAG Flow Styles */
    .canvas-container {
      margin-top: 1.5rem;
      background: #020617;
      border: 1px solid #1e293b;
      border-radius: var(--radius);
      padding: 1.5rem;
      position: relative;
      overflow-x: auto;
    }
    .canvas-tabs { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
    .canvas-tab {
      padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer;
      background: var(--bg-input); border: 1px solid var(--border);
      font-size: 0.85rem; font-weight: 600; color: var(--text-muted);
    }
    .canvas-tab.active { background: var(--cyan); color: #000; border-color: var(--cyan); }
    
    .dag-flow {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1rem 0;
      min-width: 100%;
    }
    .dag-node {
      background: var(--bg-card);
      border: 1.5px solid var(--border);
      border-radius: 10px;
      padding: 1rem;
      min-width: 200px;
      max-width: 220px;
      position: relative;
      cursor: pointer;
      transition: all 0.2s;
    }
    .dag-node:hover {
      border-color: var(--cyan);
      transform: translateY(-3px);
      box-shadow: 0 8px 24px rgba(6,182,212,0.2);
    }
    .dag-node.selected {
      border-color: var(--violet);
      box-shadow: 0 0 20px rgba(139,92,246,0.4);
    }
    .dag-node-header {
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 0.5rem;
    }
    .dag-node-title { font-weight: 700; font-size: 0.9rem; color: var(--text); }
    .dag-node-type { font-size: 0.75rem; color: var(--cyan); font-family: var(--mono); }
    .dag-node-blocks {
      font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;
      background: rgba(255,255,255,0.03); padding: 4px 8px; border-radius: 4px;
    }
    .dag-arrow {
      color: var(--cyan);
      font-size: 1.4rem;
      font-weight: bold;
      user-select: none;
    }

    /* Node Inspector Modal / Drawer */
    #nodeInspector {
      margin-top: 1rem;
      background: var(--bg-input);
      border: 1px solid var(--violet);
      border-radius: 8px;
      padding: 1rem;
      display: none;
    }
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h1>🚀 DNK OS — Shopify Agentic Studio</h1>
      <p>Autonomous AI Store Synthesizer • Infinite Visual Canvas DAG • One-Click ZIP Exporter • 529 Components</p>
    </div>
    <div style="display:flex;gap:0.75rem;">
      <a href="/docs" target="_blank" style="text-decoration:none">
        <button class="btn-secondary">📖 API Swagger Docs</button>
      </a>
    </div>
  </div>

  <div class="grid">

    <!-- 1. AI Store Synthesizer & ZIP Exporter (FLAGSHIP) -->
    <div class="card full-card">
      <h2>
        <span>✨ Autonomous Store Synthesizer & Theme Packager</span>
        <span class="badge badge-cyan">AI STUDIO ENGINE</span>
      </h2>
      <p style="color:var(--text-muted);margin-bottom:1.25rem">
        Synthesizes complete high-conversion Shopify OS 2.0 templates and packages them with 500+ modular blocks into a ready-to-upload Theme ZIP.
      </p>
      
      <div style="display:grid;grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:1rem;">
        <div>
          <label style="color:var(--text-muted);font-size:0.85rem;display:block;margin-bottom:0.3rem">Store / Brand Name</label>
          <input id="storeName" value="Apex Cybernetics" />
        </div>
        <div>
          <label style="color:var(--text-muted);font-size:0.85rem;display:block;margin-bottom:0.3rem">Niche & Funnel Architecture</label>
          <select id="storeNiche" onchange="runStoreSynthesize()">
            <option value="tech_apparel">Tech Apparel (High-Performance Ergonomics)</option>
            <option value="health_supplements">Health & Nootropics (Longevity Bio-Protocol)</option>
            <option value="luxury_jewelry">Luxury Fine Jewelry (Architectural Craft)</option>
            <option value="general_ecom">General E-Commerce (Next-Gen Essentials)</option>
          </select>
        </div>
        <div>
          <label style="color:var(--text-muted);font-size:0.85rem;display:block;margin-bottom:0.3rem">Primary Accent Token</label>
          <input id="tokenAccent" value="#06b6d4" />
        </div>
        <div>
          <label style="color:var(--text-muted);font-size:0.85rem;display:block;margin-bottom:0.3rem">Canvas Dark Token</label>
          <input id="tokenBgDark" value="#030712" />
        </div>
      </div>

      <div class="btn-group">
        <button onclick="runStoreSynthesize()">⚡ 1. Synthesize Store Architecture</button>
        <button onclick="exportThemeZip()" class="btn-emerald">📦 2. Export Production Theme (.ZIP)</button>
        <button onclick="exportManifestOnly()" class="btn-secondary">📋 Inspect File Manifest</button>
      </div>

      <div class="stats" id="synthesizeStats" style="display:none"></div>

      <!-- Infinite Visual Canvas DAG -->
      <div class="canvas-container" id="canvasBox" style="display:none">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem">
          <div class="canvas-tabs">
            <div class="canvas-tab active" id="tabIndex" onclick="switchCanvasTab('index')">🏠 Homepage (index.json)</div>
            <div class="canvas-tab" id="tabProduct" onclick="switchCanvasTab('product')">🛍️ Product Page (product.json)</div>
          </div>
          <span style="font-size:0.8rem;color:var(--text-muted)">💡 Click any node to inspect / edit settings</span>
        </div>

        <div class="dag-flow" id="dagFlow"></div>

        <div id="nodeInspector">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem">
            <h3 id="inspectorTitle" style="color:var(--cyan);font-size:1rem">Node Inspector</h3>
            <span class="badge badge-violet" id="inspectorType">type</span>
          </div>
          <div id="inspectorContent" style="font-family:var(--mono);font-size:0.8rem;color:#cbd5e1"></div>
        </div>
      </div>

      <div class="output" id="synthesizeOut" style="display:none"></div>
    </div>

    <!-- 2. Mega-Registry Inspector -->
    <div class="card full-card">
      <h2>
        <span>📚 Mega-Component Registry</span>
        <span class="badge badge-emerald">529 COMPONENTS</span>
      </h2>
      <p style="color:var(--text-muted);margin-bottom:1rem">
        Unified component bank (99 modular blocks, 133 conversion sections, 297 snippets) indexed for AI RAG synthesis.
      </p>
      <button onclick="loadRegistry()" class="btn-emerald">🔍 Scan & Filter Registry</button>
      <div class="stats" id="registryStats" style="display:none"></div>
      <div class="output" id="registryOut" style="display:none"></div>
    </div>

    <!-- 3. Mechanical Transpiler -->
    <div class="card">
      <h2>
        <span>🔄 Mechanical Transpiler</span>
        <span class="badge badge-rose">CANVAS → LIQUID</span>
      </h2>
      <textarea id="transpileInput"><div class="hero p-8 bg-slate-950 text-white">
  <h1 class="text-4xl font-bold">Cyber Titanium Sneaker</h1>
  <p class="text-rose-400">Ultra-limited 2026 Drop</p>
  <div class="grid grid-cols-2 gap-4 mt-6">
    <div class="card p-4 border border-slate-800">
      <h3>Titanium Sole</h3><p>Indestructible grip</p>
    </div>
    <div class="card p-4 border border-slate-800">
      <h3>RGB Laces</h3><p>App controlled</p>
    </div>
  </div>
</div></textarea>
      <button onclick="runTranspile()">Transpile HTML → Liquid AST</button>
      <div class="output" id="transpileOut" style="display:none"></div>
    </div>

    <!-- 4. Template State Engine -->
    <div class="card">
      <h2>
        <span>🧬 Template State Engine</span>
        <span class="badge badge-violet">RFC 6902 MUTATIONS</span>
      </h2>
      <textarea id="mutateTemplate">{
  "sections": {
    "header": { "type": "header-group", "settings": {} },
    "hero": { "type": "image-banner", "settings": { "heading": "Welcome" } },
    "footer": { "type": "footer-group", "settings": {} }
  },
  "order": ["header", "hero", "footer"]
}</textarea>
      <button onclick="runMutate()">Apply Atomic Mutation (add_section)</button>
      <div class="output" id="mutateOut" style="display:none"></div>
    </div>

  </div>

  <script>
    let currentStoreData = null;
    let currentTab = 'index';

    async function apiCall(url, method='POST', body=null) {
      const opt = { method, headers: {'Content-Type':'application/json'} };
      if (body) opt.body = JSON.stringify(body);
      const res = await fetch(url, opt);
      if (!res.ok) {
        const err = await res.json().catch(() => ({detail: res.statusText}));
        throw new Error(err.detail || 'Request failed');
      }
      return res.json();
    }

    function showOutput(id, data, isError=false) {
      const el = document.getElementById(id);
      el.style.display = 'block';
      el.className = 'output' + (isError ? ' error' : '');
      el.textContent = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
    }

    async function runStoreSynthesize() {
      const name = document.getElementById('storeName').value;
      const niche = document.getElementById('storeNiche').value;
      const accent = document.getElementById('tokenAccent').value;
      const bgDark = document.getElementById('tokenBgDark').value;

      try {
        const data = await apiCall('/api/shopify/store/synthesize', 'POST', {
          store_name: name,
          niche: niche,
          theme_tokens: { accent, bgDark }
        });
        currentStoreData = data;
        
        // Render stats
        const stats = document.getElementById('synthesizeStats');
        stats.style.display = 'flex';
        stats.innerHTML = `
          <div class="stat"><div class="stat-value">${data.summary.index_sections_count}</div><div class="stat-label">Index Sections</div></div>
          <div class="stat"><div class="stat-value">${data.summary.product_sections_count}</div><div class="stat-label">Product Sections</div></div>
          <div class="stat"><div class="stat-value">${data.summary.total_blocks_used}</div><div class="stat-label">Blocks Configured</div></div>
          <div class="stat"><div class="stat-value">${data.niche}</div><div class="stat-label">Active Niche Preset</div></div>
        `;

        // Render Canvas DAG
        document.getElementById('canvasBox').style.display = 'block';
        renderCanvasDAG();

        showOutput('synthesizeOut', {
          status: "Synthesized successfully",
          store_name: data.store_name,
          niche: data.niche,
          summary: data.summary,
          templates_overview: {
            "index.json": data.templates["index.json"].order,
            "product.json": data.templates["product.json"].order
          }
        });
      } catch(e) {
        showOutput('synthesizeOut', {error: e.message}, true);
      }
    }

    function switchCanvasTab(tab) {
      currentTab = tab;
      document.getElementById('tabIndex').className = 'canvas-tab' + (tab === 'index' ? ' active' : '');
      document.getElementById('tabProduct').className = 'canvas-tab' + (tab === 'product' ? ' active' : '');
      renderCanvasDAG();
    }

    function renderCanvasDAG() {
      if (!currentStoreData) return;
      const container = document.getElementById('dagFlow');
      const tplKey = currentTab === 'index' ? 'index.json' : 'product.json';
      const template = currentStoreData.templates[tplKey];
      if (!template) return;

      let html = '';
      const order = template.order || [];

      order.forEach((secKey, index) => {
        const sec = template.sections[secKey] || {};
        const blockCount = sec.blocks ? Object.keys(sec.blocks).length : 0;
        const type = sec.type || 'section';
        
        html += `
          <div class="dag-node" onclick="inspectNode('${secKey}', '${tplKey}')" id="node_${secKey}">
            <div class="dag-node-header">
              <span class="badge badge-cyan">#${index+1}</span>
              <span class="badge ${blockCount > 0 ? 'badge-violet' : 'badge-emerald'}">${blockCount > 0 ? blockCount + ' BLOCKS' : 'STATIC'}</span>
            </div>
            <div class="dag-node-title">${secKey.replace(/_/g, ' ').toUpperCase()}</div>
            <div class="dag-node-type">${type}</div>
            ${blockCount > 0 ? `<div class="dag-node-blocks">📦 ${blockCount} modular blocks attached</div>` : ''}
          </div>
        `;
        if (index < order.length - 1) {
          html += `<div class="dag-arrow">➔</div>`;
        }
      });

      container.innerHTML = html;
    }

    function inspectNode(secKey, tplKey) {
      document.querySelectorAll('.dag-node').forEach(el => el.classList.remove('selected'));
      const activeEl = document.getElementById('node_' + secKey);
      if (activeEl) activeEl.classList.add('selected');

      const template = currentStoreData.templates[tplKey];
      const sec = template.sections[secKey];
      
      const inspector = document.getElementById('nodeInspector');
      inspector.style.display = 'block';
      document.getElementById('inspectorTitle').textContent = `Node: ${secKey} (${tplKey})`;
      document.getElementById('inspectorType').textContent = sec.type || 'section';
      document.getElementById('inspectorContent').textContent = JSON.stringify(sec, null, 2);
    }

    async function exportThemeZip() {
      const name = document.getElementById('storeName').value;
      const niche = document.getElementById('storeNiche').value;
      const accent = document.getElementById('tokenAccent').value;
      const bgDark = document.getElementById('tokenBgDark').value;

      try {
        const response = await fetch('/api/shopify/store/export-zip', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            store_name: name,
            niche: niche,
            theme_tokens: { accent, bgDark },
            custom_templates: currentStoreData ? currentStoreData.templates : null
          })
        });

        if (!response.ok) throw new Error('ZIP Export failed');

        const filename = response.headers.get('X-Archive-Name') || `${name.toLowerCase().replace(/\\s+/g, '_')}_theme.zip`;
        const blob = await response.blob();
        
        // Trigger browser file download
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        
        showOutput('synthesizeOut', `✅ SUCCESS! Downloaded production-ready Shopify Theme ZIP archive: ${filename} (${(blob.size / (1024*1024)).toFixed(2)} MB)`);
      } catch(e) {
        showOutput('synthesizeOut', {error: e.message}, true);
      }
    }

    async function exportManifestOnly() {
      const name = document.getElementById('storeName').value;
      const niche = document.getElementById('storeNiche').value;
      try {
        const manifest = await apiCall('/api/shopify/store/export-manifest', 'POST', {
          store_name: name,
          niche: niche,
          custom_templates: currentStoreData ? currentStoreData.templates : null
        });
        showOutput('synthesizeOut', manifest);
      } catch(e) {
        showOutput('synthesizeOut', {error: e.message}, true);
      }
    }

    async function loadRegistry() {
      try {
        const data = await apiCall('/api/shopify/components/registry', 'GET');
        showOutput('registryOut', data);
        const stats = document.getElementById('registryStats');
        stats.style.display = 'flex';
        stats.innerHTML = `
          <div class="stat"><div class="stat-value">${data.stats.total_blocks}</div><div class="stat-label">Blocks</div></div>
          <div class="stat"><div class="stat-value">${data.stats.total_sections}</div><div class="stat-label">Sections</div></div>
          <div class="stat"><div class="stat-value">${data.stats.total_snippets}</div><div class="stat-label">Snippets</div></div>
          <div class="stat"><div class="stat-value">${data.stats.total_components}</div><div class="stat-label">Total Components</div></div>
        `;
      } catch(e) { showOutput('registryOut', {error: e.message}, true); }
    }

    async function runTranspile() {
      const html = document.getElementById('transpileInput').value;
      try {
        const data = await apiCall('/api/shopify/transpile/canvas-node', 'POST', {
          html_content: html,
          section_name: 'cyber_sneaker_hero',
          theme_tokens: { accent: '#06b6d4', bgDark: '#030712' }
        });
        showOutput('transpileOut', data);
      } catch(e) { showOutput('transpileOut', {error: e.message}, true); }
    }

    async function runMutate() {
      const template = JSON.parse(document.getElementById('mutateTemplate').value);
      try {
        const data = await apiCall('/api/shopify/template/mutate', 'POST', {
          template,
          action: 'add_section',
          params: {
            section_type: 'bundle-offer',
            after_ordinal: 2,
            settings: { title: 'VIP Bundle & Save 25%' }
          }
        });
        showOutput('mutateOut', data);
        if (data.template) {
          document.getElementById('mutateTemplate').value = JSON.stringify(data.template, null, 2);
        }
      } catch(e) { showOutput('mutateOut', {error: e.message}, true); }
    }

    // Auto-run on initial load for instant visual feedback
    window.addEventListener('DOMContentLoaded', () => {
      runStoreSynthesize();
    });
  </script>
</body>
</html>
""")


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 DNK OS — Shopify Agentic Studio & AST Demo Server")
    print("=" * 60)
    print("   Open in browser:  http://localhost:8888")
    print("   Swagger UI:       http://localhost:8888/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8888)
