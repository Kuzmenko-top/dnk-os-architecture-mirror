// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/canvas/swarm-copilot-phase3.test.ts"
// purpose: "Comprehensive 17-Test Suite for Phase 3: Agent Co-Pilot, Streaming Generation, and Swarm Multi-Node Propagation."
// canonical_source: true
// alters_files: []
// triggers_tasks: ["TaskDNA-PHASE-3-TEST-SUITE"]
// status: "Active"
// version: "1.2.1"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// license: "DNK-INTERNAL"
// --- END DNK-MRH-HEADER ---

import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';

import { AgentCopilotService } from './copilot/agentCopilotService';
import { SwarmPropagationEngine } from './swarm/swarmPropagation';
import { useSconesStore, DEFAULT_BRAND_DNA, BrandDNA } from '../../store/sconesStore';
import { useCanvasStore } from '../../store/canvasStore';
import { Node, Edge } from '@xyflow/react';

describe('Phase 3: Agent Co-Pilot & Swarm Automation Test Suite', () => {
  beforeEach(() => {
    // Reset stores
    useSconesStore.setState({
      workspaceId: 'ws-alpha-001',
      currentBrand: { 
        ...DEFAULT_BRAND_DNA,
        brandName: 'Test Brand',
        colors: { 
          primary: '#FF0055', 
          secondary: '#AA0044',
          accent: '#00FF55', 
          background: '#121212',
          text: '#FFFFFF'
        },
        toneOfVoice: 'bold_energetic'
      },
    });

    useCanvasStore.setState({
      nodes: [],
      edges: [],
      history: [],
      historyIndex: -1,
    });
  });

  it('1. should execute CMO Agent Co-Pilot with SCONES Brand DNA context', async () => {
    const brand = useSconesStore.getState().currentBrand;
    let tokensCount = 0;

    const response = await AgentCopilotService.executeCoPilot({
      nodeId: 'node-strat-1',
      nodeType: 'StrategyMarkdownNode',
      agentId: 'dnk_marketing_cmo',
      brand,
      onStreamToken: (token, full) => {
        tokensCount++;
        assert.ok(token);
        assert.ok(full);
      },
    });

    assert.equal(response.success, true);
    assert.equal(response.agentId, 'dnk_marketing_cmo');
    const hypotheses = response.generatedData.hypotheses as string[];
    assert.ok(hypotheses.length > 0);
    assert.ok(tokensCount > 5);
  });

  it('2. should execute Video Creator Agent Co-Pilot for FLUX.1 & IC-Light 9:16 assets', async () => {
    const brand = useSconesStore.getState().currentBrand;

    const response = await AgentCopilotService.executeCoPilot({
      nodeId: 'node-design-1',
      nodeType: 'DesignGalleryNode',
      agentId: 'dnk_video_ai_creator',
      brand,
    });

    assert.equal(response.success, true);
    assert.equal(response.generatedData.aspectRatio, '9:16');
    const fluxPrompt = response.generatedData.fluxPrompt as string;
    assert.ok(fluxPrompt.includes(brand.brandName));
    assert.ok(response.generatedData.icLightSettings);
  });

  it('3. should execute Shopify AST & Fullstack API Agent Co-Pilot', async () => {
    const brand = useSconesStore.getState().currentBrand;

    const response = await AgentCopilotService.executeCoPilot({
      nodeId: 'node-code-1',
      nodeType: 'ApiDocsCodeNode',
      agentId: 'dnk_shopify',
      brand,
    });

    assert.equal(response.success, true);
    const liquidCode = response.generatedData.liquidCode as string;
    assert.ok(liquidCode.includes(brand.brandName));
    const apiEndpoint = response.generatedData.apiEndpoint as string;
    assert.ok(apiEndpoint.includes(brand.workspaceId));
  });

  it('4. should execute Gerych Builder Agent Co-Pilot for Sprint Kanban auto-decomposition', async () => {
    const brand = useSconesStore.getState().currentBrand;

    const response = await AgentCopilotService.executeCoPilot({
      nodeId: 'node-kanban-1',
      nodeType: 'SprintKanbanNode',
      agentId: 'gerych_builder',
      brand,
    });

    assert.equal(response.success, true);
    const tasks = response.generatedData.tasks as any[];
    assert.ok(tasks.length > 0);
  });

  it('5. should propagate Strategy updates down to Design, Code, and Kanban nodes via Swarm Engine', () => {
    const brand = useSconesStore.getState().currentBrand;

    const nodes: Node[] = [
      { id: 'strat-1', type: 'StrategyMarkdownNode', position: { x: 0, y: 0 }, data: { goal: 'Scale DTC sales 3x' } },
      { id: 'design-1', type: 'DesignGalleryNode', position: { x: 200, y: 0 }, data: { title: 'Design Assets' } },
      { id: 'code-1', type: 'ApiDocsCodeNode', position: { x: 400, y: 0 }, data: { code: 'initial' } },
      { id: 'kanban-1', type: 'SprintKanbanNode', position: { x: 600, y: 0 }, data: { title: 'Sprint' } },
    ];

    const edges: Edge[] = [
      { id: 'e1', source: 'strat-1', target: 'design-1', type: 'dataFlow' },
      { id: 'e2', source: 'strat-1', target: 'code-1', type: 'dataFlow' },
      { id: 'e3', source: 'strat-1', target: 'kanban-1', type: 'controlFlow' },
    ];

    const strategyPayload = { goal: 'Scale DTC sales 3x', focus: 'Organic TikTok & Shopify' };

    const result = SwarmPropagationEngine.propagate('strat-1', strategyPayload, nodes, edges, brand);

    assert.equal(result.propagatedCount, 3);

    const updatedDesign = result.nodes.find((n) => n.id === 'design-1');
    assert.equal(updatedDesign?.data.badge, 'Synced via Swarm ⚡');

    const updatedCode = result.nodes.find((n) => n.id === 'code-1');
    assert.ok((updatedCode?.data.code as string).includes(brand.brandName));

    const updatedKanban = result.nodes.find((n) => n.id === 'kanban-1');
    assert.ok(updatedKanban?.data.injectedTask);
  });

  it('6. should execute Fullstack Developer Co-Pilot specifically and generate API router endpoints', async () => {
    const brand = useSconesStore.getState().currentBrand;

    const response = await AgentCopilotService.executeCoPilot({
      nodeId: 'node-api-1',
      nodeType: 'ApiDocsCodeNode',
      agentId: 'dnk_dev_fullstack',
      brand,
    });

    assert.equal(response.success, true);
    assert.equal(response.agentId, 'dnk_dev_fullstack');
    const apiEndpoint = response.generatedData.apiEndpoint as string;
    assert.ok(apiEndpoint.includes('/api/v1/workspaces/'));
  });

  it('7. should fall back to default Gerych Builder agent when an unknown agent ID is provided', async () => {
    const brand = useSconesStore.getState().currentBrand;

    const response = await AgentCopilotService.executeCoPilot({
      nodeId: 'node-fallback-1',
      nodeType: 'SprintKanbanNode',
      agentId: 'non_existent_agent_id' as any,
      brand,
    });

    assert.equal(response.success, true);
    assert.equal(response.agentId, 'non_existent_agent_id' as any);
    const tasks = response.generatedData.tasks as any[];
    assert.ok(tasks.length > 0);
    assert.ok(tasks[0].title.includes('Test Brand'));
  });

  it('8. should verify token streaming emissions sequences', async () => {
    const brand = useSconesStore.getState().currentBrand;
    const tokens: string[] = [];

    await AgentCopilotService.executeCoPilot({
      nodeId: 'node-stream-1',
      nodeType: 'StrategyMarkdownNode',
      agentId: 'dnk_marketing_cmo',
      brand,
      onStreamToken: (token) => {
        tokens.push(token);
      },
    });

    assert.ok(tokens.length > 5);
    assert.ok(tokens[0].length > 0);
  });

  it('9. should handle empty or missing edge lists gracefully in propagation', () => {
    const brand = useSconesStore.getState().currentBrand;
    const nodes: Node[] = [
      { id: 'strat-1', type: 'StrategyMarkdownNode', position: { x: 0, y: 0 }, data: {} }
    ];

    const result = SwarmPropagationEngine.propagate('strat-1', { goal: 'test' }, nodes, [], brand);
    assert.equal(result.propagatedCount, 0);
    assert.equal(result.nodes.length, 1);
  });

  it('10. should handle multi-hop sequential propagation (Strategy -> Design -> Code)', () => {
    const brand = useSconesStore.getState().currentBrand;
    const nodes: Node[] = [
      { id: 'strat-1', type: 'StrategyMarkdownNode', position: { x: 0, y: 0 }, data: {} },
      { id: 'design-1', type: 'DesignGalleryNode', position: { x: 200, y: 0 }, data: {} },
      { id: 'code-1', type: 'ApiDocsCodeNode', position: { x: 400, y: 0 }, data: {} },
    ];

    const edges: Edge[] = [
      { id: 'e1', source: 'strat-1', target: 'design-1' },
      { id: 'e2', source: 'design-1', target: 'code-1' },
    ];

    const step1 = SwarmPropagationEngine.propagate('strat-1', { goal: 'Step 1' }, nodes, edges, brand);
    assert.equal(step1.propagatedCount, 1);

    const designNode = step1.nodes.find((n) => n.id === 'design-1');
    assert.equal(designNode?.data.badge, 'Synced via Swarm ⚡');

    const step2 = SwarmPropagationEngine.propagate('design-1', { designCompleted: true }, step1.nodes, edges, brand);
    assert.equal(step2.propagatedCount, 1);

    const codeNode = step2.nodes.find((n) => n.id === 'code-1');
    assert.ok(codeNode?.data.code);
  });

  it('11. should support multi-node simultaneous branching propagation', () => {
    const brand = useSconesStore.getState().currentBrand;
    const nodes: Node[] = [
      { id: 'source', type: 'StrategyMarkdownNode', position: { x: 0, y: 0 }, data: {} },
      { id: 'target-1', type: 'DesignGalleryNode', position: { x: 200, y: 0 }, data: {} },
      { id: 'target-2', type: 'ApiDocsCodeNode', position: { x: 400, y: 0 }, data: {} },
      { id: 'target-3', type: 'SprintKanbanNode', position: { x: 600, y: 0 }, data: {} },
    ];

    const edges: Edge[] = [
      { id: 'e1', source: 'source', target: 'target-1' },
      { id: 'e2', source: 'source', target: 'target-2' },
      { id: 'e3', source: 'source', target: 'target-3' },
    ];

    const result = SwarmPropagationEngine.propagate('source', { test: 'multi-branch' }, nodes, edges, brand);
    assert.equal(result.propagatedCount, 3);
  });

  it('12. should leave unconnected nodes unaffected during swarm propagation', () => {
    const brand = useSconesStore.getState().currentBrand;
    const nodes: Node[] = [
      { id: 'source', type: 'StrategyMarkdownNode', position: { x: 0, y: 0 }, data: {} },
      { id: 'target-connected', type: 'DesignGalleryNode', position: { x: 200, y: 0 }, data: {} },
      { id: 'target-unconnected', type: 'SprintKanbanNode', position: { x: 400, y: 0 }, data: { intact: true } },
    ];

    const edges: Edge[] = [
      { id: 'e1', source: 'source', target: 'target-connected' },
    ];

    const result = SwarmPropagationEngine.propagate('source', { action: 'prop' }, nodes, edges, brand);
    assert.equal(result.propagatedCount, 1);

    const unconnected = result.nodes.find((n) => n.id === 'target-unconnected');
    assert.equal(unconnected?.data.intact, true);
    assert.equal(unconnected?.data.injectedTask, undefined);
  });

  it('13. should verify canvasStore.propagateSwarm mutation triggers store changes and history updates', () => {
    const brand = useSconesStore.getState().currentBrand;
    
    const initialNodes = [
      { id: 'strat-1', type: 'StrategyMarkdownNode', position: { x: 0, y: 0 }, data: {} },
      { id: 'kanban-1', type: 'SprintKanbanNode', position: { x: 200, y: 0 }, data: {} },
    ];
    const initialEdges = [
      { id: 'e1', source: 'strat-1', target: 'kanban-1' }
    ];

    useCanvasStore.setState({
      nodes: initialNodes,
      edges: initialEdges,
      history: [
        { nodes: JSON.parse(JSON.stringify(initialNodes)), edges: JSON.parse(JSON.stringify(initialEdges)) }
      ],
      historyIndex: 0
    });

    const store = useCanvasStore.getState();
    const result = store.propagateSwarm('strat-1', { goal: 'Launch Campaign' }, brand);

    assert.equal(result.propagatedCount, 1);
    
    const updatedKanban = useCanvasStore.getState().nodes.find((n) => n.id === 'kanban-1');
    assert.ok(updatedKanban?.data.injectedTask);
    assert.ok(useCanvasStore.getState().history.length > 0);
  });

  it('14. should contextualize generated parameters using specific SCONES Brand DNA options', async () => {
    const customBrand: BrandDNA = {
      ...DEFAULT_BRAND_DNA,
      brandName: 'EcoSaaS',
      colors: { 
        primary: '#10B981', 
        secondary: '#065F46',
        accent: '#3B82F6', 
        background: '#0F172A',
        text: '#F8FAFC'
      },
      toneOfVoice: 'clean_minimal',
      workspaceId: 'workspace-ecosaas-001',
    };

    const response = await AgentCopilotService.executeCoPilot({
      nodeId: 'code-1',
      nodeType: 'ApiDocsCodeNode',
      agentId: 'dnk_shopify',
      brand: customBrand,
    });

    assert.equal(response.success, true);
    const liquidCode = response.generatedData.liquidCode as string;
    assert.ok(liquidCode.includes('EcoSaaS'));
    assert.ok(liquidCode.includes('#10B981'));
    const apiEndpoint = response.generatedData.apiEndpoint as string;
    assert.ok(apiEndpoint.includes('workspace-ecosaas-001'));
  });

  it('15. should verify undo/redo capabilities on swarm propagation changes', () => {
    const brand = useSconesStore.getState().currentBrand;
    
    const initialNodes = [
      { id: 'strat-1', type: 'StrategyMarkdownNode', position: { x: 0, y: 0 }, data: {} },
      { id: 'kanban-1', type: 'SprintKanbanNode', position: { x: 200, y: 0 }, data: {} },
    ];
    const initialEdges = [
      { id: 'e1', source: 'strat-1', target: 'kanban-1' }
    ];

    useCanvasStore.setState({
      nodes: initialNodes,
      edges: initialEdges,
      history: [
        { nodes: JSON.parse(JSON.stringify(initialNodes)), edges: JSON.parse(JSON.stringify(initialEdges)) }
      ],
      historyIndex: 0
    });

    const store = useCanvasStore.getState();
    
    store.propagateSwarm('strat-1', { goal: 'Undo test' }, brand);
    const kanbanWithTask = useCanvasStore.getState().nodes.find((n) => n.id === 'kanban-1');
    assert.ok(kanbanWithTask?.data.injectedTask);

    useCanvasStore.getState().undo();
    const kanbanRestored = useCanvasStore.getState().nodes.find((n) => n.id === 'kanban-1');
    assert.equal(kanbanRestored?.data.injectedTask, undefined);

    useCanvasStore.getState().redo();
    const kanbanRedone = useCanvasStore.getState().nodes.find((n) => n.id === 'kanban-1');
    assert.ok(kanbanRedone?.data.injectedTask);
  });

  it('16. should gracefully return original nodes on invalid/missing source propagation', () => {
    const brand = useSconesStore.getState().currentBrand;
    const nodes: Node[] = [
      { id: 'strat-1', type: 'StrategyMarkdownNode', position: { x: 0, y: 0 }, data: {} }
    ];

    const result = SwarmPropagationEngine.propagate('invalid-node-id', { data: 1 }, nodes, [], brand);
    assert.equal(result.propagatedCount, 0);
    assert.deepEqual(result.nodes, nodes);
  });

  it('17. Full E2E Integration: execute Co-Pilot -> mutate node -> propagate down to Kanban', async () => {
    const brand = useSconesStore.getState().currentBrand;
    
    useCanvasStore.setState({
      nodes: [
        { id: 'strat-e2e', type: 'StrategyMarkdownNode', position: { x: 0, y: 0 }, data: {} },
        { id: 'kanban-e2e', type: 'SprintKanbanNode', position: { x: 200, y: 0 }, data: {} },
      ],
      edges: [
        { id: 'e-e2e', source: 'strat-e2e', target: 'kanban-e2e' }
      ]
    });

    const response = await AgentCopilotService.executeCoPilot({
      nodeId: 'strat-e2e',
      nodeType: 'StrategyMarkdownNode',
      agentId: 'dnk_marketing_cmo',
      brand,
    });

    assert.equal(response.success, true);
    const hypotheses = response.generatedData.hypotheses as string[];
    assert.ok(hypotheses.length > 0);

    const store = useCanvasStore.getState();
    store.updateNodeData('strat-e2e', response.generatedData);
    
    const mutatedStrat = useCanvasStore.getState().nodes.find((n) => n.id === 'strat-e2e');
    const stratHypotheses = mutatedStrat?.data.hypotheses as string[];
    assert.deepEqual(stratHypotheses, hypotheses);

    const propResult = store.propagateSwarm('strat-e2e', response.generatedData, brand);
    assert.equal(propResult.propagatedCount, 1);

    const finalKanban = useCanvasStore.getState().nodes.find((n) => n.id === 'kanban-e2e');
    assert.ok(finalKanban?.data.injectedTask);
    const injected = finalKanban.data.injectedTask as any;
    assert.ok(injected.title.includes('Execute strategy goal'));
  });
});
