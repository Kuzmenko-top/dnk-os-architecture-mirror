// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/canvas/templates/businessTemplates.ts"
// purpose: "Pre-configured High-Velocity Business Templates converting into standard JSON Canvas 1.0 and @xyflow/react states"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["TaskDNA-PHASE-2-LAUNCHPAD-ONBOARDING-FINAL"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---

import { JSONCanvasDocument } from '../json-canvas/types';
import { Node, Edge } from '@xyflow/react';
import { reactFlowToJSONCanvas } from '../json-canvas/converter';
import { BrandDNA } from '../../../store/sconesStore';

export interface BusinessTemplate {
  id: string;
  title: string;
  description: string;
  category: 'ecommerce' | 'video' | 'saas' | 'branding';
  badge: string;
  estimatedTime: string;
  iconName: string;
  createGraph: (brand: BrandDNA) => { nodes: Node[]; edges: Edge[] };
  createJSONCanvas: (brand: BrandDNA) => JSONCanvasDocument;
}

export const BUSINESS_TEMPLATES: BusinessTemplate[] = [
  {
    id: 'tpl-ecom-dtc',
    title: 'E-Com швидкий старт (Shopify DTC)',
    description: 'Готовий ланцюг запуску магазину: брендбук ➔ Hero банери ➔ Dawn Liquid AST ➔ чекаут-воронка',
    category: 'ecommerce',
    badge: 'Shopify OS 2.0',
    estimatedTime: '15 хв',
    iconName: 'ShoppingBag',
    createGraph: (brand: BrandDNA) => {
      const n1: Node = {
        id: 'node-strategy-1',
        type: 'StrategyMarkdownNode',
        position: { x: 50, y: 150 },
        data: {
          title: `DTC Strategy: ${brand.brandName || 'Store'}`,
          industry: brand.industry,
          goals: brand.goals,
          toneOfVoice: brand.toneOfVoice,
        },
      };
      const n2: Node = {
        id: 'node-design-1',
        type: 'DesignGalleryNode',
        position: { x: 440, y: 150 },
        data: {
          title: 'Brand Visual Assets',
          colors: brand.colors,
          aiParams: brand.aiParams,
        },
      };
      const n3: Node = {
        id: 'node-code-1',
        type: 'ApiDocsCodeNode',
        position: { x: 830, y: 150 },
        data: {
          title: 'Shopify Liquid Hero Section',
          code: `{% schema %}\n{\n  "name": "DNK Hero ${brand.brandName}",\n  "settings": [\n    {"type": "color", "id": "bg_color", "default": "${brand.colors.primary}"}\n  ]\n}\n{% endschema %}`,
        },
      };
      const n4: Node = {
        id: 'node-kanban-1',
        type: 'SprintKanbanNode',
        position: { x: 440, y: 480 },
        data: {
          title: 'DTC Launch Sprint',
          columns: ['Backlog', 'In Review', 'Live on Shopify'],
        },
      };

      const edges: Edge[] = [
        {
          id: 'edge-strat-design',
          source: n1.id,
          target: n2.id,
          type: 'dataFlow',
          animated: true,
        },
        {
          id: 'edge-design-code',
          source: n2.id,
          target: n3.id,
          type: 'dataFlow',
          animated: true,
        },
        {
          id: 'edge-design-kanban',
          source: n2.id,
          target: n4.id,
          type: 'controlFlow',
        },
      ];

      return { nodes: [n1, n2, n3, n4], edges };
    },
    createJSONCanvas: (brand: BrandDNA) => {
      const graph = BUSINESS_TEMPLATES[0].createGraph(brand);
      return reactFlowToJSONCanvas(graph.nodes, graph.edges);
    },
  },
  {
    id: 'tpl-ugc-video',
    title: 'UGC Відео-воронка (Remotion 9:16)',
    description: 'Пайплайн вірусного контенту: аналіз хуків ➔ сценарій ➔ розкадровка ➔ авто-рендер відео',
    category: 'video',
    badge: 'Viral TikTok/Reels',
    estimatedTime: '10 хв',
    iconName: 'Video',
    createGraph: (brand: BrandDNA) => {
      const n1: Node = {
        id: 'node-research-1',
        type: 'MarketResearchNode',
        position: { x: 50, y: 150 },
        data: {
          title: 'Viral Hooks Research',
          competitors: brand.competitors,
          usp: brand.usp,
        },
      };
      const n2: Node = {
        id: 'node-mindmap-1',
        type: 'ConceptMindmapNode',
        position: { x: 440, y: 150 },
        data: {
          title: '3-Act Video Script Architecture',
          rootConcept: '3-Second Problem Hook',
        },
      };
      const n3: Node = {
        id: 'node-design-video',
        type: 'DesignGalleryNode',
        position: { x: 830, y: 150 },
        data: {
          title: 'Remotion Storyboard Assets (9:16)',
          aspectRatio: '9:16',
          colors: brand.colors,
        },
      };
      const n4: Node = {
        id: 'node-kanban-video',
        type: 'SprintKanbanNode',
        position: { x: 440, y: 480 },
        data: {
          title: 'Video Production Queue',
          columns: ['Scripting', 'Rendering', 'Distributed'],
        },
      };

      const edges: Edge[] = [
        { id: 'edge-v1', source: n1.id, target: n2.id, type: 'dataFlow', animated: true },
        { id: 'edge-v2', source: n2.id, target: n3.id, type: 'dataFlow', animated: true },
        { id: 'edge-v3', source: n3.id, target: n4.id, type: 'controlFlow' },
      ];

      return { nodes: [n1, n2, n3, n4], edges };
    },
    createJSONCanvas: (brand: BrandDNA) => {
      const graph = BUSINESS_TEMPLATES[1].createGraph(brand);
      return reactFlowToJSONCanvas(graph.nodes, graph.edges);
    },
  },
  {
    id: 'tpl-saas-growth',
    title: 'SaaS Growth Engine (B2B Stack)',
    description: 'Архітектура продукту: ICP позиціонування ➔ конкуренти ➔ FastAPI REST специфікації ➔ задачі релізу',
    category: 'saas',
    badge: 'Fullstack & API',
    estimatedTime: '20 хв',
    iconName: 'Server',
    createGraph: (brand: BrandDNA) => {
      const n1: Node = {
        id: 'node-strat-saas',
        type: 'StrategyMarkdownNode',
        position: { x: 50, y: 150 },
        data: {
          title: 'B2B Positioning & ICP',
          targetAudience: brand.targetAudience,
          goals: brand.goals,
        },
      };
      const n2: Node = {
        id: 'node-res-saas',
        type: 'MarketResearchNode',
        position: { x: 440, y: 150 },
        data: {
          title: 'Market & Competitive Matrix',
          competitors: brand.competitors,
        },
      };
      const n3: Node = {
        id: 'node-api-saas',
        type: 'ApiDocsCodeNode',
        position: { x: 830, y: 150 },
        data: {
          title: 'FastAPI Router & Schema',
          code: `@router.post('/v1/workspaces')\nasync def create_workspace(body: WorkspaceCreate):\n    return await service.provision(body)`,
        },
      };

      const edges: Edge[] = [
        { id: 'edge-s1', source: n1.id, target: n2.id, type: 'dataFlow', animated: true },
        { id: 'edge-s2', source: n2.id, target: n3.id, type: 'dataFlow', animated: true },
      ];

      return { nodes: [n1, n2, n3], edges };
    },
    createJSONCanvas: (brand: BrandDNA) => {
      const graph = BUSINESS_TEMPLATES[2].createGraph(brand);
      return reactFlowToJSONCanvas(graph.nodes, graph.edges);
    },
  },
  {
    id: 'tpl-brand-identity',
    title: 'Brand Identity Launch (Креатив 360°)',
    description: 'Створення бренду з нуля: архетипи ➔ FLUX.1 палітра ➔ Tone of Voice маніфест ➔ експорт брендбуку',
    category: 'branding',
    badge: 'SCONES Brain',
    estimatedTime: '12 хв',
    iconName: 'Sparkles',
    createGraph: (brand: BrandDNA) => {
      const n1: Node = {
        id: 'node-mindmap-brand',
        type: 'ConceptMindmapNode',
        position: { x: 50, y: 150 },
        data: {
          title: `${brand.brandName || 'Brand'} Identity Core`,
          rootConcept: 'Core Brand Archetype',
        },
      };
      const n2: Node = {
        id: 'node-design-brand',
        type: 'DesignGalleryNode',
        position: { x: 440, y: 150 },
        data: {
          title: 'Visual Palette & FLUX.1 Render Tokens',
          colors: brand.colors,
          typography: brand.typography,
        },
      };
      const n3: Node = {
        id: 'node-strat-brand',
        type: 'StrategyMarkdownNode',
        position: { x: 830, y: 150 },
        data: {
          title: 'Brand Manifesto & Voice Guidelines',
          toneOfVoice: brand.toneOfVoice,
          usp: brand.usp,
        },
      };

      const edges: Edge[] = [
        { id: 'edge-b1', source: n1.id, target: n2.id, type: 'dataFlow', animated: true },
        { id: 'edge-b2', source: n2.id, target: n3.id, type: 'dataFlow', animated: true },
      ];

      return { nodes: [n1, n2, n3], edges };
    },
    createJSONCanvas: (brand: BrandDNA) => {
      const graph = BUSINESS_TEMPLATES[3].createGraph(brand);
      return reactFlowToJSONCanvas(graph.nodes, graph.edges);
    },
  },
];
