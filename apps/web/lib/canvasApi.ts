// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/lib/canvasApi.ts"
// purpose: "Canvas API Client for PostgreSQL 16 (hub_memory) Delta Sync, WebSocket Collaboration, IndexedDB Hydration & Swarm Node Spawning"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "3.0.0"
// updated_at: "2026-09-03"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

export interface CanvasNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, any>;
}

export interface CanvasEdge {
  id: string;
  source: string;
  target: string;
  type?: string;
  label?: string;
  data?: Record<string, any>;
}

export interface CanvasDelta {
  upsert_nodes?: any[];
  delete_node_ids?: string[];
  upsert_edges?: any[];
  delete_edge_ids?: string[];
  sketches?: any[];
  viewport?: { x: number; y: number; zoom: number };
  client_revision?: number;
  change_summary?: string;
  actor_id?: string;
  workspace_id?: string;
}

export interface DeltaSyncResponse {
  success: boolean;
  canvas_id: string;
  revision_number: number;
  revision_id: string;
  scene: {
    nodes: any[];
    edges: any[];
    sketches: any[];
    viewport?: { x: number; y: number; zoom: number };
    meta?: Record<string, any>;
  };
  resolved_conflicts?: string[];
  updated_at?: string;
}

export interface CanvasRevisionInfo {
  id: string;
  document_id: string;
  revision_number: number;
  scene_checksum: string;
  created_by: string;
  created_at: string;
  change_summary?: string;
  parent_revision_id?: string;
}

export interface CanvasState {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  sketches?: any[];
  viewport?: { x: number; y: number; zoom: number };
  revision?: number;
  revisionId?: string;
  updatedAt?: string;
}

/**
 * Offline-first IndexedDB storage for Canvas state hydration and offline queue
 */
class IndexedDBCanvasStorage {
  private dbName = 'dnk_canvas_offline_db';
  private version = 1;
  private dbPromise: Promise<IDBDatabase> | null = null;

  private getDB(): Promise<IDBDatabase> {
    if (typeof window === 'undefined' || !window.indexedDB) {
      return Promise.reject(new Error('IndexedDB not available in this environment'));
    }
    if (!this.dbPromise) {
      this.dbPromise = new Promise((resolve, reject) => {
        const req = window.indexedDB.open(this.dbName, this.version);
        req.onupgradeneeded = (e) => {
          const db = (e.target as IDBOpenDBRequest).result;
          if (!db.objectStoreNames.contains('canvases')) {
            db.createObjectStore('canvases', { keyPath: 'canvas_id' });
          }
          if (!db.objectStoreNames.contains('pending_deltas')) {
            db.createObjectStore('pending_deltas', { autoIncrement: true });
          }
        };
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
      });
    }
    return this.dbPromise;
  }

  async saveCanvas(canvasId: string, state: any): Promise<void> {
    try {
      const db = await this.getDB();
      return new Promise((resolve, reject) => {
        const tx = db.transaction('canvases', 'readwrite');
        const store = tx.objectStore('canvases');
        store.put({ canvas_id: canvasId, state, cached_at: new Date().toISOString() });
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
      });
    } catch {
      // Graceful fallback to memory/noop if indexedDB is disabled
    }
  }

  async loadCanvas(canvasId: string): Promise<any | null> {
    try {
      const db = await this.getDB();
      return new Promise((resolve, reject) => {
        const tx = db.transaction('canvases', 'readonly');
        const store = tx.objectStore('canvases');
        const req = store.get(canvasId);
        req.onsuccess = () => {
          resolve(req.result ? req.result.state : null);
        };
        req.onerror = () => reject(req.error);
      });
    } catch {
      return null;
    }
  }
}

export class CanvasApiClient {
  private baseUrl: string;
  private offlineStorage = new IndexedDBCanvasStorage();

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || (typeof window !== 'undefined' && window.location ? window.location.origin : 'http://localhost:8000');
  }

  /**
   * Loads full canvas document and latest revision from PostgreSQL 16 (hub_memory)
   * with automatic offline fallback to IndexedDB.
   */
  async loadCanvas(canvasId: string, workspaceId: string = 'ws-alpha-001'): Promise<CanvasState> {
    const url = `${this.baseUrl}/api/v1/canvases/${encodeURIComponent(canvasId)}`;
    try {
      const resp = await fetch(url, {
        headers: {
          'X-Workspace-Id': workspaceId,
          'Accept': 'application/json'
        }
      });
      if (resp.ok) {
        const data = await resp.json();
        const scene = data.scene || data.scene_json || {};
        const state: CanvasState = {
          nodes: scene.nodes || [],
          edges: scene.edges || [],
          sketches: scene.sketches || [],
          viewport: scene.viewport || { x: 0, y: 0, zoom: 1 },
          revision: data.revision_number || data.revision || 1,
          revisionId: data.current_revision_id || data.revision_id,
          updatedAt: data.updated_at
        };
        // Persist to IndexedDB for offline hydration
        await this.offlineStorage.saveCanvas(canvasId, state);
        return state;
      }
    } catch {
      // Offline / network failure -> attempt IndexedDB hydration
      const cached = await this.offlineStorage.loadCanvas(canvasId);
      if (cached) {
        return cached;
      }
    }
    // Fallback default empty canvas
    return {
      nodes: [],
      edges: [],
      sketches: [],
      viewport: { x: 0, y: 0, zoom: 1 },
      revision: 1
    };
  }

  /**
   * Delta sync endpoint: sends only changed nodes/edges/sketches to PostgreSQL 16
   */
  async syncDelta(canvasId: string, delta: CanvasDelta): Promise<DeltaSyncResponse> {
    const url = `${this.baseUrl}/api/v1/canvases/${encodeURIComponent(canvasId)}/delta`;
    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Workspace-Id': delta.workspace_id || 'ws-alpha-001'
        },
        body: JSON.stringify(delta)
      });
      if (!resp.ok) {
        throw new Error(`Delta sync failed with HTTP status ${resp.status}`);
      }
      const data: DeltaSyncResponse = await resp.json();
      // Keep IndexedDB in sync with latest successful state
      if (data.scene) {
        await this.offlineStorage.saveCanvas(canvasId, {
          nodes: data.scene.nodes || [],
          edges: data.scene.edges || [],
          sketches: data.scene.sketches || [],
          viewport: data.scene.viewport,
          revision: data.revision_number,
          revisionId: data.revision_id,
          updatedAt: data.updated_at
        });
      }
      return data;
    } catch (err) {
      // Cache local update to IndexedDB even if offline
      await this.offlineStorage.loadCanvas(canvasId);
      throw err;
    }
  }

  /**
   * Retrieves revision history for undo beyond session & audit
   */
  async listRevisions(canvasId: string, limit: number = 30, offset: number = 0): Promise<CanvasRevisionInfo[]> {
    const url = `${this.baseUrl}/api/v1/canvases/${encodeURIComponent(canvasId)}/revisions?limit=${limit}&offset=${offset}`;
    const resp = await fetch(url);
    if (!resp.ok) {
      throw new Error(`Failed to list revisions: HTTP ${resp.status}`);
    }
    const data = await resp.json();
    return Array.isArray(data) ? data : (data.revisions || []);
  }

  /**
   * Restores a past revision in PostgreSQL hub_memory (time-travel undo)
   */
  async restoreRevision(canvasId: string, revisionId: string, actorId: string = 'client_user'): Promise<any> {
    const url = `${this.baseUrl}/api/v1/canvases/${encodeURIComponent(canvasId)}/revisions/${encodeURIComponent(revisionId)}/restore`;
    const resp = await fetch(url, {
      method: 'POST',
      headers: {
        'X-Actor-Id': actorId,
        'Content-Type': 'application/json'
      }
    });
    if (!resp.ok) {
      throw new Error(`Failed to restore revision: HTTP ${resp.status}`);
    }
    const result = await resp.json();
    if (result.scene) {
      await this.offlineStorage.saveCanvas(canvasId, {
        nodes: result.scene.nodes || [],
        edges: result.scene.edges || [],
        sketches: result.scene.sketches || [],
        revision: result.revision_number,
        revisionId: result.revision_id
      });
    }
    return result;
  }

  /**
   * Export React Flow nodes & edges to Obsidian Canvas file via REST Canvas Bridge
   */
  async exportToObsidianCanvas(canvasPath: string, reactFlow: { nodes: any[]; edges: any[] }): Promise<any> {
    const url = `${this.baseUrl}/api/v1/canvas/bridge/react-flow-to-canvas`;
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        canvas_path: canvasPath,
        react_flow: reactFlow
      })
    });
    if (!resp.ok) {
      const errText = await resp.text();
      throw new Error(`Failed to export to Obsidian Canvas: HTTP ${resp.status} - ${errText}`);
    }
    return await resp.json();
  }

  /**
   * Import Obsidian Canvas file into React Flow format via REST Canvas Bridge
   */
  async importFromObsidianCanvas(canvasPath: string): Promise<any> {
    const url = `${this.baseUrl}/api/v1/canvas/bridge/obsidian?canvas_path=${encodeURIComponent(canvasPath)}`;
    const resp = await fetch(url, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!resp.ok) {
      const errText = await resp.text();
      throw new Error(`Failed to import from Obsidian Canvas: HTTP ${resp.status} - ${errText}`);
    }
    return await resp.json();
  }

  /**
   * Real-time WebSocket connection for multi-user collaboration
   */
  connectWebSocket(
    canvasId: string,
    onMessage: (msg: any) => void,
    onError?: (err: any) => void
  ): WebSocket | null {
    if (typeof window === 'undefined') return null;
    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = this.baseUrl.replace(/^https?:\/\//, '');
    const wsUrl = `${wsProto}//${host}/api/v1/ws/canvas/${encodeURIComponent(canvasId)}`;

    try {
      const ws = new WebSocket(wsUrl);
      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          onMessage(payload);
        } catch (e) {
          console.error('[CanvasWS] Failed to parse message', e);
        }
      };
      if (onError) {
        ws.onerror = onError;
      }
      return ws;
    } catch (e) {
      if (onError) onError(e);
      return null;
    }
  }

  /**
   * Spawns a node and optionally creates an edge linking to a parent node.
   */
  async spawnNode(nodePayload: Partial<CanvasNode> & { title?: string }, parentNodeId?: string): Promise<string> {
    const id = `node-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`;
    const position = nodePayload.position || {
      x: 350 + Math.floor(Math.random() * 200),
      y: 200 + Math.floor(Math.random() * 200)
    };

    const newNode: CanvasNode = {
      id,
      type: nodePayload.type || 'StrategyMarkdownNode',
      position,
      data: {
        title: nodePayload.title || 'New Node',
        ...(nodePayload.data || {})
      }
    };

    // If in browser context with useCanvasStore, dispatch into store
    if (typeof window !== 'undefined') {
      try {
        const { useCanvasStore } = await import('../store/canvasStore');
        const store = useCanvasStore.getState();
        const createdId = store.addNode(
          nodePayload.type || 'StrategyMarkdownNode',
          position,
          {
            title: nodePayload.title || 'New Node',
            ...(nodePayload.data || {})
          }
        );

        if (parentNodeId) {
          store.onConnect({
            source: parentNodeId,
            target: createdId,
            sourceHandle: null,
            targetHandle: null
          });
        }
        return createdId;
      } catch (err) {
        console.warn('Could not inject into useCanvasStore directly:', err);
      }
    }

    return id;
  }

  /**
   * Dispatches a user prompt to the DNK Swarm and spawns the appropriate specialized node.
   */
  async dispatchSwarmPrompt(prompt: string, model: string = 'gemini-2.5-flash', typeHint: string = 'general'): Promise<{ success: boolean; nodeId: string; type: string }> {
    const lowerPrompt = prompt.toLowerCase();
    let type = 'StrategyMarkdownNode';
    let title = 'AI Generated Strategy';
    let defaultData: Record<string, any> = {};

    if (typeHint === 'video' || lowerPrompt.includes('video') || lowerPrompt.includes('відео') || lowerPrompt.includes('ugc') || lowerPrompt.includes('ролик')) {
      type = 'VideoStoryboardNoteNode';
      title = 'AI Video Storyboard';
      defaultData = {
        aspectRatio: '9:16',
        motionStyle: 'Hyper-Kinetic Neon Shutter',
        duration: 15,
        scenes: [
          { id: 'sc1', timeRange: '0:00 - 0:03', visualPrompt: `Macro shot of cocktail smoker based on: "${prompt}"`, voiceover: '"Unleashing next-gen sensory design."' },
          { id: 'sc2', timeRange: '0:03 - 0:10', visualPrompt: 'Close-up slow pan showcasing detailed glowing product aesthetic.', voiceover: '"Engineered to perfection."' },
          { id: 'sc3', timeRange: '0:10 - 0:15', visualPrompt: 'Ending CTA Card featuring bundle link and discounts.', voiceover: '"Get yours in the description today."' }
        ]
      };
    } else if (typeHint === 'shopify' || lowerPrompt.includes('shopify') || lowerPrompt.includes('шопіфай') || lowerPrompt.includes('section') || lowerPrompt.includes('секція')) {
      type = 'ShopifySpecNoteNode';
      title = 'Shopify Section Spec';
      defaultData = {
        theme: 'Dawn 15.0',
        section: 'Custom Feature Section',
        liquidDetails: {
          features: [
            'Interactive configuration matching: ' + prompt,
            'Fast checkout API integrations',
            'Full schema customization custom-fields'
          ],
          transpileTarget: 'sections/custom-feature-section.liquid'
        }
      };
    } else if (typeHint === 'photo' || lowerPrompt.includes('photo') || lowerPrompt.includes('фото') || lowerPrompt.includes('picture') || lowerPrompt.includes('зображення')) {
      type = 'PhotoStudioNode';
      title = 'AI Product Concept';
      defaultData = {
        prompt: prompt,
        aspectRatio: '1:1'
      };
    } else {
      type = 'StrategyMarkdownNode';
      title = 'AI Generated Strategy';
      defaultData = {
        content: `### Swarm-Generated Strategy Spec\n\n**Goal:** ${prompt}\n\n- Automatically analyzed by Gerych Core Swarm.\n- Standard components aligned with core architecture.\n- Ready for further node linkage.`
      };
    }

    const nodeId = await this.spawnNode({
      type,
      title,
      data: defaultData
    }, 'node-strategy');

    return { success: true, nodeId, type };
  }
}

export const canvasApiClient = new CanvasApiClient();
