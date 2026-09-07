/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/storage/storage.test.ts"
 * purpose: "Unit tests for Canvas Storage Service with fast-json-patch, OPFS, differential snapshots, and ring buffer invariants."
 * canonical_source: true
 * alters_files: []
 * triggers_tasks: []
 * status: "Active"
 * version: "1.1.0"
 * updated_at: "2026-09-02"
 * author: "DNK-e.com Maksym & Gerych"
 * --- END DNK-MRH-HEADER ---
 */

import 'fake-indexeddb/auto';
import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import {
  CanvasStorageService,
  JsonPatchEngine,
  calculateChecksum,
  generateUUID,
} from './storage.service';
import {
  validateCanvasState,
  validateTransaction,
  validateDraftRecord,
  validateCanvasAsset,
} from './schema';
import type { CanvasState, CanvasAsset } from './types/canvas';

function createSampleState(id = 'draft-test-01', name = 'Test Canvas'): CanvasState {
  return {
    id,
    name,
    version: 1,
    dimensions: { width: 1920, height: 1080 },
    viewport: { x: 0, y: 0, zoom: 1 },
    activeLayerId: 'layer-1',
    selectedNodeIds: ['node-rect-01'],
    metadata: {},
    layers: [
      {
        id: 'layer-1',
        name: 'Background Layer',
        visible: true,
        locked: false,
        opacity: 1,
        zIndex: 0,
        nodes: [
          {
            id: 'node-rect-01',
            type: 'shape',
            name: 'Hero Card',
            x: 100,
            y: 150,
            width: 400,
            height: 250,
            rotation: 0,
            opacity: 1,
            props: { fill: '#4F46E5', stroke: '#312E81', strokeWidth: 2, cornerRadius: 12 },
            customData: {},
          },
        ],
      },
    ],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };
}

describe('Canvas Storage Engine & Services', () => {
  let storage: CanvasStorageService;

  beforeEach(async () => {
    storage = new CanvasStorageService({
      dbName: `test_canvas_db_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
      dbVersion: 1,
      maxRingBufferSize: 100,
      autoSaveIntervalMs: 100,
    });
    await storage.init();
  });

  afterEach(async () => {
    await storage.close();
  });

  describe('1. Zod Runtime Schemas & Validation', () => {
    it('should validate a complete and valid CanvasState structure', () => {
      const state = createSampleState();
      const validated = validateCanvasState(state);
      assert.equal(validated.id, state.id);
      assert.equal(validated.layers.length, 1);
      assert.equal(validated.layers[0].nodes[0].name, 'Hero Card');
    });

    it('should fail validation when required fields are missing', () => {
      const invalid = { id: 'invalid-state' };
      assert.throws(() => validateCanvasState(invalid as any));
    });

    it('should validate Transaction schema properly', () => {
      const tx = {
        id: generateUUID(),
        draftId: 'draft-001',
        sequenceNumber: 1,
        timestamp: Date.now(),
        description: 'Update Hero Card position',
        forwardPatches: [{ op: 'replace' as const, path: '/layers/0/nodes/0/x', value: 200 }],
        inversePatches: [{ op: 'replace' as const, path: '/layers/0/nodes/0/x', value: 100 }],
      };
      const validated = validateTransaction(tx);
      assert.equal(validated.draftId, 'draft-001');
      assert.equal(validated.forwardPatches[0].path, '/layers/0/nodes/0/x');
    });
  });

  describe('2. Draft Management (Save, Retrieve, Differential Snapshots)', () => {
    it('should save and retrieve a full canvas draft', async () => {
      const original = createSampleState('draft-save-01', 'Landing Hero');
      const saved = await storage.saveDraft(original);

      assert.equal(saved.id, 'draft-save-01');
      assert.equal(saved.checksum.length, 8);
      assert.equal(saved.isDifferential, false);

      const retrieved = await storage.getDraft('draft-save-01');
      assert.ok(retrieved);
      assert.equal(retrieved?.id, 'draft-save-01');
      assert.equal(retrieved?.name, 'Landing Hero');
      assert.equal(retrieved?.state.layers[0].nodes[0].x, 100);
    });

    it('should list all drafts ordered by updatedAt descending', async () => {
      const draftA = createSampleState('draft-a', 'Draft A');
      const draftB = createSampleState('draft-b', 'Draft B');

      await storage.saveDraft(draftA);
      await new Promise((r) => setTimeout(r, 10));
      await storage.saveDraft(draftB);

      const list = await storage.listDrafts();
      assert.ok(list.length >= 2);
      assert.equal(list[0].id, 'draft-b');
    });

    it('should delete a draft and clear its associated session meta', async () => {
      const draft = createSampleState('draft-to-delete');
      await storage.saveDraft(draft);

      let retrieved = await storage.getDraft('draft-to-delete');
      assert.ok(retrieved);

      await storage.deleteDraft('draft-to-delete');
      retrieved = await storage.getDraft('draft-to-delete');
      assert.equal(retrieved, null);
    });

    it('should correctly save and reconstruct a differential draft snapshot', async () => {
      const baseState = createSampleState('base-draft', 'Base Design');
      await storage.saveDraft(baseState);

      const modifiedState: CanvasState = JSON.parse(JSON.stringify(baseState));
      modifiedState.id = 'diff-draft-01';
      modifiedState.name = 'Diff Design';
      modifiedState.layers[0].nodes[0].x = 550;
      modifiedState.layers[0].nodes[0].props = { fill: '#10B981' };

      const diffRecord = await storage.saveDraft(modifiedState, {
        isDifferential: true,
        baseDraftId: 'base-draft',
      });

      assert.equal(diffRecord.isDifferential, true);
      assert.equal(diffRecord.baseDraftId, 'base-draft');
      assert.ok(diffRecord.differentialSnapshot);
      assert.ok(diffRecord.differentialSnapshot?.forwardPatches.length! > 0);

      const retrievedDiff = await storage.getDraft('diff-draft-01');
      assert.ok(retrievedDiff);
      assert.equal(retrievedDiff?.state.layers[0].nodes[0].x, 550);
      assert.equal((retrievedDiff?.state.layers[0].nodes[0].props as any)?.fill, '#10B981');
    });
  });

  describe('3. Ring Buffer Invariant (Max 100 Transactions)', () => {
    it('should store transactions and enforce max capacity by evicting oldest transactions', async () => {
      const smallStorage = new CanvasStorageService({
        dbName: `test_ring_${Date.now()}`,
        maxRingBufferSize: 5,
        useMemoryOnly: true,
      });
      await smallStorage.init();

      const draftId = 'ring-draft-01';

      for (let i = 1; i <= 8; i++) {
        await smallStorage.saveTransaction(
          draftId,
          `Action #${i}`,
          [{ op: 'replace', path: '/viewport/zoom', value: i }],
          [{ op: 'replace', path: '/viewport/zoom', value: i - 1 }]
        );
      }

      const history = await smallStorage.getHistory(draftId);
      assert.equal(history.length, 5, 'History must strictly be clamped to max capacity 5');
      assert.equal(history[0].sequenceNumber, 4, 'Oldest transaction should have been evicted to seq 4');
      assert.equal(history[4].sequenceNumber, 8, 'Newest transaction should be seq 8');

      const stats = await smallStorage.getRingBufferStats(draftId);
      assert.equal(stats.currentCount, 5);
      assert.equal(stats.totalRecorded, 8);
      assert.equal(stats.oldestSequenceNumber, 4);
      assert.equal(stats.newestSequenceNumber, 8);

      await smallStorage.close();
    });

    it('should support pagination and sinceSeq filtering', async () => {
      const draftId = 'pagination-draft';
      for (let i = 1; i <= 10; i++) {
        await storage.saveTransaction(
          draftId,
          `Move step ${i}`,
          [{ op: 'replace', path: '/viewport/x', value: i * 10 }],
          [{ op: 'replace', path: '/viewport/x', value: (i - 1) * 10 }]
        );
      }

      const sinceFive = await storage.getHistory(draftId, { sinceSeq: 5 });
      assert.equal(sinceFive.length, 5);
      assert.equal(sinceFive[0].sequenceNumber, 6);

      const latestThree = await storage.getHistory(draftId, { limit: 3 });
      assert.equal(latestThree.length, 3);
      assert.equal(latestThree[2].sequenceNumber, 10);
    });
  });

  describe('4. Auto-Save Engine & Dirty Tracking', () => {
    it('should trigger auto-save when marked dirty and interval elapses', async () => {
      let currentState = createSampleState('autosave-draft', 'Autosave Design');
      storage.startAutoSave(() => currentState, 50);

      storage.markDirty(true);
      assert.equal(storage.isDirty(), true);

      currentState = {
        ...currentState,
        name: 'Autosave Design Updated',
      };

      await new Promise((r) => setTimeout(r, 120));

      const saved = await storage.getDraft('autosave-draft');
      assert.ok(saved);
      assert.equal(saved?.name, 'Autosave Design Updated');
      assert.equal(storage.isDirty(), false);

      storage.stopAutoSave();
    });

    it('should not perform redundant saves if state is clean', async () => {
      const state = createSampleState('clean-draft');
      await storage.saveDraft(state);

      storage.startAutoSave(() => state, 50);
      storage.markDirty(false);

      const triggerResult = await storage.triggerAutoSave();
      assert.equal(triggerResult, null);

      storage.stopAutoSave();
    });
  });

  describe('5. Crash Recovery Protocol (recoverFromCrash)', () => {
    it('should detect ungraceful exit and reconstruct state by replaying transaction log', async () => {
      const baseState = createSampleState('crash-draft-01', 'Crash Test');
      await storage.saveDraft(baseState);

      await storage.flagSessionStart('crash-draft-01');

      const crashStatusBefore = await storage.checkCrashStatus();
      assert.equal(crashStatusBefore.hasCrashed, true);

      await storage.saveTransaction(
        'crash-draft-01',
        'Move node X to 300',
        [{ op: 'replace', path: '/layers/0/nodes/0/x', value: 300 }],
        [{ op: 'replace', path: '/layers/0/nodes/0/x', value: 100 }]
      );
      await storage.saveTransaction(
        'crash-draft-01',
        'Change fill to yellow',
        [{ op: 'replace', path: '/layers/0/nodes/0/props/fill', value: '#EAB308' }],
        [{ op: 'replace', path: '/layers/0/nodes/0/props/fill', value: '#4F46E5' }]
      );

      const recovery = await storage.recoverFromCrash('crash-draft-01');

      assert.equal(recovery.recovered, true);
      assert.equal(recovery.replayedTransactionsCount, 2);
      assert.equal(recovery.state?.layers[0].nodes[0].x, 300);
      assert.equal((recovery.state?.layers[0].nodes[0].props as any)?.fill, '#EAB308');

      const crashStatusAfter = await storage.checkCrashStatus();
      assert.equal(crashStatusAfter.hasCrashed, false);
    });

    it('should handle crash recovery when no transactions exist gracefully', async () => {
      const baseState = createSampleState('empty-tx-draft');
      await storage.saveDraft(baseState);

      const recovery = await storage.recoverFromCrash('empty-tx-draft');
      assert.equal(recovery.recovered, true);
      assert.equal(recovery.replayedTransactionsCount, 0);
      assert.equal(recovery.state?.id, 'empty-tx-draft');
    });
  });

  describe('6. Asset Storage & OPFS Management', () => {
    it('should save, retrieve, list, and delete canvas assets', async () => {
      const asset: CanvasAsset = {
        id: 'asset-img-01',
        name: 'Hero Logo',
        mimeType: 'image/png',
        size: 1024,
        dataBase64: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };

      const saved = await storage.saveAsset(asset);
      assert.equal(saved.id, 'asset-img-01');

      const retrieved = await storage.getAsset('asset-img-01');
      assert.ok(retrieved);
      assert.equal(retrieved?.name, 'Hero Logo');

      const list = await storage.listAssets();
      assert.ok(list.length >= 1);

      await storage.deleteAsset('asset-img-01');
      const afterDelete = await storage.getAsset('asset-img-01');
      assert.equal(afterDelete, null);
    });

    it('should save and retrieve files using OPFS storage engine', async () => {
      const filename = 'test-file-buffer.bin';
      const testContent = 'DNK-OPFS-STORAGE-PAYLOAD-OK';
      await storage.saveToOPFS(filename, testContent);

      const buffer = await storage.getFromOPFS(filename);
      assert.ok(buffer);
      const text = new TextDecoder().decode(buffer);
      assert.equal(text, testContent);

      const list = await storage.listOPFSFiles();
      assert.ok(list.includes(filename));

      await storage.deleteFromOPFS(filename);
      const deleted = await storage.getFromOPFS(filename);
      assert.equal(deleted, null);
    });
  });

  describe('7. Checksum & RFC 6902 Patch Engine', () => {
    it('should compute deterministic checksums', () => {
      const dataA = { name: 'DNK Canvas', zoom: 1.5 };
      const dataB = { name: 'DNK Canvas', zoom: 1.5 };
      const dataC = { name: 'DNK Canvas', zoom: 2.0 };

      assert.equal(calculateChecksum(dataA), calculateChecksum(dataB));
      assert.notEqual(calculateChecksum(dataA), calculateChecksum(dataC));
    });

    it('should accurately generate forward and inverse patches and apply them', () => {
      const base = { title: 'Old Title', count: 10, items: ['a', 'b'] };
      const updated = { title: 'New Title', count: 20, items: ['a', 'b', 'c'] };

      const { forward, inverse } = JsonPatchEngine.generateDiff(base, updated);
      assert.ok(forward.length > 0);
      assert.ok(inverse.length > 0);

      const appliedForward = JsonPatchEngine.applyPatch(base, forward);
      assert.deepEqual(appliedForward, updated);

      const appliedInverse = JsonPatchEngine.applyPatch(appliedForward, inverse);
      assert.deepEqual(appliedInverse, base);
    });
  });
});
