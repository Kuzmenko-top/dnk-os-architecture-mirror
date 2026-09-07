// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/canvas/onboarding-scones.test.ts"
// purpose: "Comprehensive Unit and Integration Test Suite for SCONES Brand Memory, Business Templates, and Onboarding E2E Lifecycle"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["TaskDNA-PHASE-2-LAUNCHPAD-ONBOARDING-FINAL"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---

import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';

import { useSconesStore, DEFAULT_BRAND_DNA, BrandDNA } from '../../store/sconesStore';
import { BUSINESS_TEMPLATES } from './templates/businessTemplates';
import { useCanvasStore } from '../../store/canvasStore';
import { JSONCanvasDocument } from './json-canvas/types';

function isValidJSONCanvasDocument(doc: any): doc is JSONCanvasDocument {
  return doc && Array.isArray(doc.nodes) && Array.isArray(doc.edges);
}

describe('SCONES Brand Memory Vault Unit Tests (13 tests)', () => {
  beforeEach(() => {
    useSconesStore.setState({
      workspaceId: 'ws-alpha-001',
      currentBrand: { ...DEFAULT_BRAND_DNA },
      savedBrands: {
        'brand-reburn-default': { ...DEFAULT_BRAND_DNA }
      }
    });
  });

  it('1. should initialize with default Brand DNA and workspace', () => {
    const state = useSconesStore.getState();
    assert.equal(state.workspaceId, 'ws-alpha-001');
    assert.equal(state.currentBrand.brandName, 'ReBurn Energy');
    assert.equal(state.currentBrand.toneOfVoice, 'bold_energetic');
  });

  it('2. should isolate brands by workspaceId', () => {
    const store = useSconesStore.getState();
    store.setWorkspaceId('ws-beta-999');
    assert.equal(useSconesStore.getState().workspaceId, 'ws-beta-999');

    // List brands should filter by workspace
    const list = store.listBrands();
    assert.equal(list.length, 0);

    // Restore workspace
    store.setWorkspaceId('ws-alpha-001');
    assert.equal(store.listBrands().length >= 1, true);
  });

  it('3. should update basic brand identity fields', () => {
    const store = useSconesStore.getState();
    store.updateBrand({
      brandName: 'Apex Biohacking',
      tagline: 'Optimize Everything',
      industry: 'Human Performance',
      toneOfVoice: 'tech_futuristic',
    });

    const current = useSconesStore.getState().currentBrand;
    assert.equal(current.brandName, 'Apex Biohacking');
    assert.equal(current.tagline, 'Optimize Everything');
    assert.equal(current.industry, 'Human Performance');
    assert.equal(current.toneOfVoice, 'tech_futuristic');
  });

  it('4. should update brand color palette and typography', () => {
    const store = useSconesStore.getState();
    store.updateBrand({
      colors: {
        primary: '#3b82f6',
        secondary: '#1d4ed8',
        accent: '#f43f5e',
        background: '#030712',
        text: '#f9fafb',
      },
      typography: {
        headingFont: 'Space Grotesk',
        bodyFont: 'Inter',
      },
    });

    const current = useSconesStore.getState().currentBrand;
    assert.equal(current.colors.primary, '#3b82f6');
    assert.equal(current.colors.accent, '#f43f5e');
    assert.equal(current.typography.headingFont, 'Space Grotesk');
  });

  it('5. should update AI Studio parameters (FLUX.1, IC-Light, BiRefNet)', () => {
    const store = useSconesStore.getState();
    store.updateAIParams({
      fluxParams: {
        promptModifiers: ['hyperrealistic', '85mm f/1.4', 'anamorphic bokeh'],
        lighting: 'dramatic volumetric ray tracing',
        aspectRatio: '9:16',
      },
      icLightParams: {
        lightSource: 'overhead softbox diffuser',
        ambientColor: '#3b82f6',
        intensity: 0.95,
      },
      birefNetParams: {
        autoMatting: true,
        foregroundIsolation: true,
      },
    });

    const ai = useSconesStore.getState().currentBrand.aiParams;
    assert.equal(ai.fluxParams.aspectRatio, '9:16');
    assert.equal(ai.fluxParams.promptModifiers.includes('anamorphic bokeh'), true);
    assert.equal(ai.icLightParams.intensity, 0.95);
    assert.equal(ai.birefNetParams.autoMatting, true);
  });

  it('6. should save brand into SCONES vault and list it', () => {
    const store = useSconesStore.getState();
    store.updateBrand({ brandName: 'Apex Biohacking' });
    const id = store.saveBrandToVault();
    assert.ok(id);

    const brands = store.listBrands();
    const found = brands.find((b) => b.id === id);
    assert.ok(found);
    assert.equal(found.brandName, 'Apex Biohacking');
  });

  it('7. should load previously saved brand by ID', () => {
    const store = useSconesStore.getState();
    const ok = store.loadBrandFromVault('brand-reburn-default');
    assert.equal(ok, true);

    const current = useSconesStore.getState().currentBrand;
    assert.equal(current.id, 'brand-reburn-default');
    assert.equal(current.brandName, 'ReBurn Energy');
  });

  it('8. should return false when loading non-existent brand ID', () => {
    const store = useSconesStore.getState();
    const ok = store.loadBrandFromVault('brand-does-not-exist');
    assert.equal(ok, false);
  });

  it('9. should synthesize FLUX.1 Prompt Co-Pilot text with brand DNA', () => {
    const store = useSconesStore.getState();
    const prompt = store.generateFluxPrompt('Aluminum can product shot on dark granite');
    assert.ok(prompt.includes('Aluminum can product shot'));
    assert.ok(prompt.includes(store.currentBrand.colors.primary));
    assert.ok(prompt.includes('style:'));
  });

  it('10. should export SCONES memory vault to valid JSON', () => {
    const store = useSconesStore.getState();
    const json = store.exportSconesMemory();
    assert.ok(json.length > 50);

    const parsed = JSON.parse(json);
    assert.equal(parsed.version, '1.0.0');
    assert.ok(parsed.currentBrand);
    assert.ok(parsed.savedBrands);
  });

  it('11. should import SCONES memory vault from valid JSON', () => {
    const store = useSconesStore.getState();
    const samplePayload = JSON.stringify({
      version: '1.0.0',
      workspaceId: 'ws-imported-001',
      currentBrand: {
        ...DEFAULT_BRAND_DNA,
        id: 'brand-imported',
        brandName: 'Imported Brand Lab',
      },
      savedBrands: {
        'brand-imported': {
          ...DEFAULT_BRAND_DNA,
          id: 'brand-imported',
          brandName: 'Imported Brand Lab',
        },
      },
    });

    const success = store.importSconesMemory(samplePayload);
    assert.equal(success, true);
    assert.equal(useSconesStore.getState().currentBrand.brandName, 'Imported Brand Lab');
  });

  it('12. should reject invalid JSON during SCONES import', () => {
    const store = useSconesStore.getState();
    const success = store.importSconesMemory('{ malformed json');
    assert.equal(success, false);
  });

  it('13. should reset brand state to blank slate for new onboarding', () => {
    const store = useSconesStore.getState();
    store.resetBrand();

    const current = useSconesStore.getState().currentBrand;
    assert.equal(current.brandName, '');
    assert.equal(current.usp.length, 0);
    assert.equal(current.goals.length, 0);
  });
});

describe('Launchpad Business Templates Unit Tests (4 tests)', () => {
  const mockBrand: BrandDNA = {
    ...DEFAULT_BRAND_DNA,
    brandName: 'NeoNutrition',
    colors: {
      primary: '#06b6d4',
      secondary: '#0891b2',
      accent: '#f97316',
      background: '#0f172a',
      text: '#ffffff',
    },
  };

  it('14. should generate valid graph for E-Com DTC template', () => {
    const tpl = BUSINESS_TEMPLATES.find((t) => t.id === 'tpl-ecom-dtc');
    assert.ok(tpl);
    const graph = tpl.createGraph(mockBrand);

    assert.equal(graph.nodes.length, 4);
    assert.equal(graph.edges.length, 3);
    assert.ok(graph.nodes.some((n) => n.type === 'StrategyMarkdownNode'));
    assert.ok(graph.nodes.some((n) => n.type === 'ApiDocsCodeNode'));
  });

  it('15. should generate valid graph for UGC Video template with 9:16 aspect ratio', () => {
    const tpl = BUSINESS_TEMPLATES.find((t) => t.id === 'tpl-ugc-video');
    assert.ok(tpl);
    const graph = tpl.createGraph(mockBrand);

    assert.equal(graph.nodes.length, 4);
    const designNode = graph.nodes.find((n) => n.type === 'DesignGalleryNode');
    assert.ok(designNode);
    assert.equal((designNode.data as any).aspectRatio, '9:16');
  });

  it('16. should generate valid graph for SaaS Growth Engine with FastAPI code', () => {
    const tpl = BUSINESS_TEMPLATES.find((t) => t.id === 'tpl-saas-growth');
    assert.ok(tpl);
    const graph = tpl.createGraph(mockBrand);

    assert.equal(graph.nodes.length, 3);
    const apiNode = graph.nodes.find((n) => n.type === 'ApiDocsCodeNode');
    assert.ok(apiNode);
    assert.ok((apiNode.data as any).code.includes('@router.post'));
  });

  it('17. should generate valid graph for Brand Identity Launch with Mindmap', () => {
    const tpl = BUSINESS_TEMPLATES.find((t) => t.id === 'tpl-brand-identity');
    assert.ok(tpl);
    const graph = tpl.createGraph(mockBrand);

    assert.equal(graph.nodes.length, 3);
    assert.ok(graph.nodes.some((n) => n.type === 'ConceptMindmapNode'));
  });
});

describe('Integration & E2E Tests (3 tests)', () => {
  const brand: BrandDNA = {
    ...DEFAULT_BRAND_DNA,
    brandName: 'ReBurn Omega',
  };

  it('18. Integration: should serialize all business templates into standard JSON Canvas 1.0 format', () => {
    for (const tpl of BUSINESS_TEMPLATES) {
      const jsonCanvas = tpl.createJSONCanvas(brand);
      assert.equal(isValidJSONCanvasDocument(jsonCanvas), true);
      assert.ok(jsonCanvas.nodes.length >= 3);
      assert.ok(jsonCanvas.edges.length >= 2);
    }
  });

  it('19. Integration: should load business template directly into Canvas Zustand store', () => {
    const canvasStore = useCanvasStore.getState();
    canvasStore.resetToDefault();

    const tpl = BUSINESS_TEMPLATES[0]; // E-com DTC
    const graph = tpl.createGraph(brand);

    graph.nodes.forEach((n) => {
      canvasStore.addNode(n.type || 'StrategyMarkdownNode', n.position, n.data);
    });

    const nodes = useCanvasStore.getState().nodes;
    assert.equal(nodes.length, 4);
  });

  it('20. E2E: simulates Full Onboarding Wizard Flow ➔ SCONES Vault ➔ Reactive Canvas Graph', () => {
    // Step 1: Onboarding user sets up new Brand
    const scones = useSconesStore.getState();
    scones.resetBrand();
    scones.updateBrand({
      brandName: 'CyberFit Bio',
      tagline: 'High-tech supplements',
      industry: 'Sports Nutrition',
      toneOfVoice: 'bold_energetic',
      colors: {
        primary: '#22c55e',
        secondary: '#15803d',
        accent: '#eab308',
        background: '#050811',
        text: '#ffffff',
      },
      goals: ['Reach 100k MRR on Shopify', 'Scale Remotion ad creatives'],
    });

    const brandId = scones.saveBrandToVault();
    assert.ok(brandId);

    // Step 2: Synthesis into Canvas Store with Flowgram.ai Data-Flow
    const canvas = useCanvasStore.getState();
    canvas.resetToDefault();

    const currentBrand = scones.currentBrand;

    // Node 1: Strategy
    const stratId = canvas.addNode('StrategyMarkdownNode', { x: 50, y: 100 }, {
      title: `${currentBrand.brandName} Strategy`,
      goals: currentBrand.goals,
      outputData: {
        brandName: currentBrand.brandName,
        industry: currentBrand.industry,
      },
    });

    // Node 2: Design
    const designId = canvas.addNode('DesignGalleryNode', { x: 450, y: 100 }, {
      title: 'Visual Assets',
      colors: currentBrand.colors,
      inputData: {},
      outputData: {
        primaryColor: currentBrand.colors.primary,
      },
    });

    // Node 3: Code
    const codeId = canvas.addNode('ApiDocsCodeNode', { x: 850, y: 100 }, {
      title: 'Shopify Liquid Component',
      inputData: {},
    });

    // Step 3: Connect nodes & test reactive data propagation
    canvas.onConnect({
      source: stratId,
      target: designId,
      sourceHandle: 'right',
      targetHandle: 'left',
    });

    canvas.onConnect({
      source: designId,
      target: codeId,
      sourceHandle: 'right',
      targetHandle: 'left',
    });

    // Trigger update on Strategy Node and assert propagation across the graph
    canvas.updateNodeData(stratId, {
      outputData: {
        brandName: 'CyberFit Bio',
        theme: 'dark-cyber',
      },
    });
    canvas.propagateDataFlow(stratId, {
      brandName: 'CyberFit Bio',
      theme: 'dark-cyber',
    });

    const updatedDesign = useCanvasStore.getState().nodes.find((n) => n.id === designId);
    assert.equal((updatedDesign?.data?.upstreamData as any)?.[stratId]?.brandName, 'CyberFit Bio');
    assert.equal((updatedDesign?.data?.upstreamData as any)?.[stratId]?.theme, 'dark-cyber');

    // Export canvas to JSON Canvas 1.0 and verify lossless structure
    const exportedCanvas = canvas.exportJSONCanvas();
    assert.equal(isValidJSONCanvasDocument(exportedCanvas), true);
    assert.equal(exportedCanvas.nodes.length, 3);
    assert.equal(exportedCanvas.edges.length, 2);
  });
});
