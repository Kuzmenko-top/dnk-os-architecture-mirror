/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/storage/storage.service.ts"
 * purpose: "Production-grade IndexedDB & OPFS storage engine with fast-json-patch diffing, ring buffer, auto-save, and crash recovery."
 * canonical_source: true
 * alters_files: []
 * triggers_tasks: []
 * status: "Active"
 * version: "1.1.0"
 * updated_at: "2026-09-02"
 * author: "DNK-e.com Maksym & Gerych"
 * --- END DNK-MRH-HEADER ---
 */

import { compare, applyPatch as fastApplyPatch, Operation } from 'fast-json-patch';
import {
  CANVAS_DB_NAME,
  CANVAS_DB_VERSION,
  CANVAS_STORES,
  validateCanvasState,
  validateDraftRecord,
  validateTransaction,
  validateCanvasAsset,
  validateCanvasMeta,
} from './schema';
import type {
  CanvasState,
  CanvasAsset,
  CanvasMeta,
} from './types/canvas';
import type {
  CommandOperation,
  DifferentialSnapshot,
  Transaction,
  DraftRecord,
  RingBufferStats,
  CrashRecoveryResult,
} from './types/history';

export const MAX_RING_BUFFER_SIZE = 100;
export const DEFAULT_AUTOSAVE_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes
export const DEFAULT_META_ID = 'dnk_canvas_session_meta';
export const OPFS_ROOT_DIRECTORY = 'dnk_canvas_opfs';

// Deterministic UUID generator (zero external dep requirement)
export function generateUUID(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

// Fast string / object hash for checksum calculation (FNV-1a)
export function calculateChecksum(data: unknown): string {
  const json = typeof data === 'string' ? data : JSON.stringify(data);
  let hash = 0x811c9dc5;
  for (let i = 0; i < json.length; i++) {
    hash ^= json.charCodeAt(i);
    hash += (hash << 1) + (hash << 4) + (hash << 7) + (hash << 8) + (hash << 24);
  }
  return (hash >>> 0).toString(16).padStart(8, '0');
}

// JSON Patch (RFC 6902) Diffing and Patching Engine backed by fast-json-patch
export class JsonPatchEngine {
  public static generateDiff(base: any, target: any): { forward: CommandOperation[]; inverse: CommandOperation[] } {
    const baseClone = base ? JSON.parse(JSON.stringify(base)) : {};
    const targetClone = target ? JSON.parse(JSON.stringify(target)) : {};

    const forwardOps: Operation[] = compare(baseClone, targetClone);
    const inverseOps: Operation[] = compare(targetClone, baseClone);

    const forward: CommandOperation[] = forwardOps.map((op) => ({
      op: op.op as CommandOperation['op'],
      path: op.path,
      value: (op as any).value,
      from: (op as any).from,
    }));

    const inverse: CommandOperation[] = inverseOps.map((op) => ({
      op: op.op as CommandOperation['op'],
      path: op.path,
      value: (op as any).value,
      from: (op as any).from,
    }));

    return { forward, inverse };
  }

  public static applyPatch<T>(doc: T, patches: CommandOperation[]): T {
    const cloned = JSON.parse(JSON.stringify(doc));
    const fastOps: Operation[] = patches.map((p) => {
      const opObj: any = { op: p.op, path: p.path };
      if (p.value !== undefined) opObj.value = JSON.parse(JSON.stringify(p.value));
      if (p.from !== undefined) opObj.from = p.from;
      return opObj;
    });

    const result = fastApplyPatch(cloned, fastOps, true, false);
    return result.newDocument as T;
  }
}

// In-Memory Storage Fallback Adapter (for Node test runners and SSR)
class MemoryStorageAdapter {
  private stores: Record<string, Map<string, any>> = {
    [CANVAS_STORES.DRAFTS]: new Map(),
    [CANVAS_STORES.HISTORY]: new Map(),
    [CANVAS_STORES.ASSETS]: new Map(),
    [CANVAS_STORES.META]: new Map(),
  };

  private opfsMemoryStore = new Map<string, ArrayBuffer>();

  public async get<T>(store: string, key: string): Promise<T | undefined> {
    return this.stores[store]?.get(key);
  }

  public async set<T>(store: string, key: string, value: T): Promise<void> {
    if (!this.stores[store]) {
      this.stores[store] = new Map();
    }
    this.stores[store].set(key, JSON.parse(JSON.stringify(value)));
  }

  public async delete(store: string, key: string): Promise<void> {
    this.stores[store]?.delete(key);
  }

  public async getAll<T>(store: string): Promise<T[]> {
    const map = this.stores[store];
    if (!map) return [];
    return Array.from(map.values()).map((v) => JSON.parse(JSON.stringify(v)));
  }

  public async clear(store?: string): Promise<void> {
    if (store && this.stores[store]) {
      this.stores[store].clear();
    } else {
      for (const s of Object.values(CANVAS_STORES)) {
        this.stores[s]?.clear();
      }
    }
  }

  // Memory OPFS methods
  public async setOPFS(filename: string, buffer: ArrayBuffer): Promise<void> {
    this.opfsMemoryStore.set(filename, buffer.slice(0));
  }

  public async getOPFS(filename: string): Promise<ArrayBuffer | null> {
    const buf = this.opfsMemoryStore.get(filename);
    return buf ? buf.slice(0) : null;
  }

  public async deleteOPFS(filename: string): Promise<void> {
    this.opfsMemoryStore.delete(filename);
  }

  public async listOPFS(): Promise<string[]> {
    return Array.from(this.opfsMemoryStore.keys());
  }
}

export interface StorageOptions {
  dbName?: string;
  dbVersion?: number;
  autoSaveIntervalMs?: number;
  maxRingBufferSize?: number;
  useMemoryOnly?: boolean;
}

export class CanvasStorageService {
  private dbName: string;
  private dbVersion: number;
  private autoSaveIntervalMs: number;
  private maxRingBufferSize: number;
  private db: IDBDatabase | null = null;
  private memoryAdapter: MemoryStorageAdapter | null = null;
  private autoSaveTimer: ReturnType<typeof setInterval> | null = null;
  private getStateFn: (() => CanvasState) | null = null;
  private isDirtyState = false;
  private isInitialized = false;
  private boundBeforeUnload: ((e: any) => void) | null = null;

  constructor(options: StorageOptions = {}) {
    this.dbName = options.dbName || CANVAS_DB_NAME;
    this.dbVersion = options.dbVersion || CANVAS_DB_VERSION;
    this.autoSaveIntervalMs = options.autoSaveIntervalMs || DEFAULT_AUTOSAVE_INTERVAL_MS;
    this.maxRingBufferSize = options.maxRingBufferSize || MAX_RING_BUFFER_SIZE;

    const hasIndexedDB = typeof globalThis !== 'undefined' && 'indexedDB' in globalThis && globalThis.indexedDB !== null;
    if (options.useMemoryOnly || !hasIndexedDB) {
      this.memoryAdapter = new MemoryStorageAdapter();
    }
  }

  public async init(): Promise<void> {
    if (this.isInitialized) return;

    if (this.memoryAdapter) {
      this.isInitialized = true;
      await this.ensureMetaInitialized();
      return;
    }

    return new Promise((resolve) => {
      try {
        const req = globalThis.indexedDB.open(this.dbName, this.dbVersion);

        req.onupgradeneeded = () => {
          const db = req.result;
          if (!db.objectStoreNames.contains(CANVAS_STORES.DRAFTS)) {
            const draftStore = db.createObjectStore(CANVAS_STORES.DRAFTS, { keyPath: 'id' });
            draftStore.createIndex('updatedAt', 'updatedAt', { unique: false });
          }
          if (!db.objectStoreNames.contains(CANVAS_STORES.HISTORY)) {
            const historyStore = db.createObjectStore(CANVAS_STORES.HISTORY, { keyPath: 'id' });
            historyStore.createIndex('draftId', 'draftId', { unique: false });
            historyStore.createIndex('sequenceNumber', 'sequenceNumber', { unique: false });
            historyStore.createIndex('draft_seq', ['draftId', 'sequenceNumber'], { unique: true });
          }
          if (!db.objectStoreNames.contains(CANVAS_STORES.ASSETS)) {
            const assetStore = db.createObjectStore(CANVAS_STORES.ASSETS, { keyPath: 'id' });
            assetStore.createIndex('createdAt', 'createdAt', { unique: false });
          }
          if (!db.objectStoreNames.contains(CANVAS_STORES.META)) {
            db.createObjectStore(CANVAS_STORES.META, { keyPath: 'id' });
          }
        };

        req.onsuccess = async () => {
          this.db = req.result;
          this.isInitialized = true;
          await this.ensureMetaInitialized();
          resolve();
        };

        req.onerror = () => {
          this.memoryAdapter = new MemoryStorageAdapter();
          this.isInitialized = true;
          resolve();
        };
      } catch (err) {
        this.memoryAdapter = new MemoryStorageAdapter();
        this.isInitialized = true;
        resolve();
      }
    });
  }

  private async ensureMetaInitialized(): Promise<void> {
    const existing = await this.getMeta();
    if (!existing) {
      const initialMeta: CanvasMeta = {
        id: DEFAULT_META_ID,
        currentDraftId: null,
        lastSavedAt: Date.now(),
        isDirty: false,
        isCrashed: false,
        activeSessionId: generateUUID(),
        schemaVersion: 1,
      };
      await this.setMeta(initialMeta);
    }
  }

  // --- Low Level Store Operations ---
  private async getStoreItem<T>(storeName: string, key: string): Promise<T | undefined> {
    await this.init();
    if (this.memoryAdapter) {
      return this.memoryAdapter.get<T>(storeName, key);
    }
    return new Promise((resolve, reject) => {
      if (!this.db) return resolve(undefined);
      const tx = this.db.transaction(storeName, 'readonly');
      const store = tx.objectStore(storeName);
      const req = store.get(key);
      req.onsuccess = () => resolve(req.result as T);
      req.onerror = () => reject(req.error);
    });
  }

  private async setStoreItem<T>(storeName: string, value: T): Promise<void> {
    await this.init();
    if (this.memoryAdapter) {
      const item: any = value;
      return this.memoryAdapter.set<T>(storeName, item.id || DEFAULT_META_ID, value);
    }
    return new Promise((resolve, reject) => {
      if (!this.db) return resolve();
      const tx = this.db.transaction(storeName, 'readwrite');
      const store = tx.objectStore(storeName);
      const req = store.put(value);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  }

  private async deleteStoreItem(storeName: string, key: string): Promise<void> {
    await this.init();
    if (this.memoryAdapter) {
      return this.memoryAdapter.delete(storeName, key);
    }
    return new Promise((resolve, reject) => {
      if (!this.db) return resolve();
      const tx = this.db.transaction(storeName, 'readwrite');
      const store = tx.objectStore(storeName);
      const req = store.delete(key);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  }

  private async getAllStoreItems<T>(storeName: string): Promise<T[]> {
    await this.init();
    if (this.memoryAdapter) {
      return this.memoryAdapter.getAll<T>(storeName);
    }
    return new Promise((resolve, reject) => {
      if (!this.db) return resolve([]);
      const tx = this.db.transaction(storeName, 'readonly');
      const store = tx.objectStore(storeName);
      const req = store.getAll();
      req.onsuccess = () => resolve((req.result || []) as T[]);
      req.onerror = () => reject(req.error);
    });
  }

  // --- Draft Management ---
  public async saveDraft(
    state: CanvasState,
    options: { isDifferential?: boolean; baseDraftId?: string } = {}
  ): Promise<DraftRecord> {
    const validated = validateCanvasState(state);
    const now = Date.now();
    const checksum = calculateChecksum(validated);

    let differentialSnapshot: DifferentialSnapshot | undefined = undefined;

    if (options.isDifferential && options.baseDraftId) {
      const baseRecord = await this.getDraft(options.baseDraftId);
      if (baseRecord) {
        const { forward, inverse } = JsonPatchEngine.generateDiff(baseRecord.state, validated);
        differentialSnapshot = {
          baseSnapshotId: options.baseDraftId,
          targetSnapshotId: validated.id,
          forwardPatches: forward,
          inversePatches: inverse,
          timestamp: now,
          version: validated.version,
          checksum,
        };
      }
    }

    const draftRecord: DraftRecord = {
      id: validated.id,
      name: validated.name,
      state: validated,
      isDifferential: Boolean(options.isDifferential && differentialSnapshot),
      baseDraftId: differentialSnapshot ? options.baseDraftId : null,
      differentialSnapshot,
      checksum,
      createdAt: validated.createdAt || now,
      updatedAt: now,
    };

    const validatedRecord = validateDraftRecord(draftRecord);
    await this.setStoreItem(CANVAS_STORES.DRAFTS, validatedRecord);

    await this.updateMeta({
      currentDraftId: validated.id,
      lastSavedAt: now,
      isDirty: false,
    });

    this.isDirtyState = false;
    return validatedRecord;
  }

  public async getDraft(id: string): Promise<DraftRecord | null> {
    const record = await this.getStoreItem<DraftRecord>(CANVAS_STORES.DRAFTS, id);
    if (!record) return null;

    if (record.isDifferential && record.baseDraftId && record.differentialSnapshot) {
      const baseDraft = await this.getDraft(record.baseDraftId);
      if (baseDraft) {
        const reconstructedState = JsonPatchEngine.applyPatch(
          baseDraft.state,
          record.differentialSnapshot.forwardPatches
        );
        record.state = validateCanvasState(reconstructedState);
      }
    }

    return validateDraftRecord(record);
  }

  public async listDrafts(): Promise<DraftRecord[]> {
    const drafts = await this.getAllStoreItems<DraftRecord>(CANVAS_STORES.DRAFTS);
    return drafts.sort((a, b) => b.updatedAt - a.updatedAt);
  }

  public async deleteDraft(id: string): Promise<void> {
    await this.deleteStoreItem(CANVAS_STORES.DRAFTS, id);
    await this.clearHistory(id);

    const meta = await this.getMeta();
    if (meta && meta.currentDraftId === id) {
      await this.updateMeta({ currentDraftId: null, isDirty: false });
    }
  }

  // --- Ring Buffer History Operations (Max 100 Transactions) ---
  public async saveTransaction(
    draftId: string,
    descriptionOrTx: string | Transaction,
    forwardPatches?: CommandOperation[],
    inversePatches?: CommandOperation[],
    metadata?: Record<string, unknown>
  ): Promise<Transaction> {
    await this.init();
    const allHistory = await this.getHistory(draftId);
    const nextSeq = allHistory.length > 0 ? Math.max(...allHistory.map((t) => t.sequenceNumber)) + 1 : 1;

    let transaction: Transaction;
    if (typeof descriptionOrTx === 'object' && descriptionOrTx !== null) {
      transaction = {
        ...descriptionOrTx,
        draftId,
        sequenceNumber: descriptionOrTx.sequenceNumber || nextSeq,
        timestamp: descriptionOrTx.timestamp || Date.now(),
      };
    } else {
      transaction = {
        id: generateUUID(),
        draftId,
        sequenceNumber: nextSeq,
        timestamp: Date.now(),
        description: descriptionOrTx,
        forwardPatches: forwardPatches || [],
        inversePatches: inversePatches || [],
        metadata,
      };
    }

    const validatedTx = validateTransaction(transaction);
    await this.setStoreItem(CANVAS_STORES.HISTORY, validatedTx);

    // Enforce Ring Buffer limit (max 100 items per draft)
    const updatedHistory = [...allHistory, validatedTx].sort((a, b) => a.sequenceNumber - b.sequenceNumber);
    if (updatedHistory.length > this.maxRingBufferSize) {
      const overflowCount = updatedHistory.length - this.maxRingBufferSize;
      const toDelete = updatedHistory.slice(0, overflowCount);
      for (const oldTx of toDelete) {
        await this.deleteStoreItem(CANVAS_STORES.HISTORY, oldTx.id);
      }
    }

    this.markDirty(true);
    return validatedTx;
  }

  public async getHistory(draftId: string, options: { limit?: number; sinceSeq?: number } = {}): Promise<Transaction[]> {
    const all = await this.getAllStoreItems<Transaction>(CANVAS_STORES.HISTORY);
    let filtered = all.filter((t) => t.draftId === draftId);

    if (options.sinceSeq !== undefined) {
      filtered = filtered.filter((t) => t.sequenceNumber > options.sinceSeq!);
    }

    filtered.sort((a, b) => a.sequenceNumber - b.sequenceNumber);

    if (options.limit && options.limit > 0) {
      filtered = filtered.slice(-options.limit);
    }

    return filtered;
  }

  public async getRingBufferStats(draftId: string): Promise<RingBufferStats> {
    const history = await this.getHistory(draftId);
    const currentCount = history.length;
    const oldestSeq = currentCount > 0 ? history[0].sequenceNumber : 0;
    const newestSeq = currentCount > 0 ? history[currentCount - 1].sequenceNumber : 0;

    return {
      draftId,
      totalRecorded: newestSeq,
      currentCount,
      oldestSequenceNumber: oldestSeq,
      newestSequenceNumber: newestSeq,
      capacity: this.maxRingBufferSize,
    };
  }

  public async clearHistory(draftId: string): Promise<void> {
    const all = await this.getAllStoreItems<Transaction>(CANVAS_STORES.HISTORY);
    const toDelete = all.filter((t) => t.draftId === draftId);
    for (const tx of toDelete) {
      await this.deleteStoreItem(CANVAS_STORES.HISTORY, tx.id);
    }
  }

  // --- Asset Management ---
  public async saveAsset(asset: CanvasAsset): Promise<CanvasAsset> {
    const validated = validateCanvasAsset(asset);
    await this.setStoreItem(CANVAS_STORES.ASSETS, validated);
    return validated;
  }

  public async getAsset(id: string): Promise<CanvasAsset | null> {
    const asset = await this.getStoreItem<CanvasAsset>(CANVAS_STORES.ASSETS, id);
    return asset ? validateCanvasAsset(asset) : null;
  }

  public async listAssets(): Promise<CanvasAsset[]> {
    const assets = await this.getAllStoreItems<CanvasAsset>(CANVAS_STORES.ASSETS);
    return assets.sort((a, b) => b.createdAt - a.createdAt);
  }

  public async deleteAsset(id: string): Promise<void> {
    await this.deleteStoreItem(CANVAS_STORES.ASSETS, id);
  }

  // --- OPFS (Origin Private File System) Engine ---
  public async saveToOPFS(filename: string, data: ArrayBuffer | Blob | string): Promise<void> {
    await this.init();
    let buffer: ArrayBuffer;

    if (data instanceof ArrayBuffer) {
      buffer = data;
    } else if (typeof Blob !== 'undefined' && data instanceof Blob) {
      buffer = await data.arrayBuffer();
    } else if (typeof data === 'string') {
      buffer = new TextEncoder().encode(data).buffer as ArrayBuffer;
    } else {
      buffer = new ArrayBuffer(0);
    }

    if (
      typeof navigator !== 'undefined' &&
      navigator.storage &&
      typeof navigator.storage.getDirectory === 'function' &&
      !this.memoryAdapter
    ) {
      try {
        const root = await navigator.storage.getDirectory();
        const fileHandle = await root.getFileHandle(filename, { create: true });
        const accessHandle = await (fileHandle as any).createWritable();
        await accessHandle.write(buffer);
        await accessHandle.close();
        return;
      } catch (err) {
        // Fallback to memory adapter
      }
    }

    if (!this.memoryAdapter) {
      this.memoryAdapter = new MemoryStorageAdapter();
    }
    await this.memoryAdapter.setOPFS(filename, buffer);
  }

  public async getFromOPFS(filename: string): Promise<ArrayBuffer | null> {
    await this.init();

    if (
      typeof navigator !== 'undefined' &&
      navigator.storage &&
      typeof navigator.storage.getDirectory === 'function' &&
      !this.memoryAdapter
    ) {
      try {
        const root = await navigator.storage.getDirectory();
        const fileHandle = await root.getFileHandle(filename, { create: false });
        const file = await fileHandle.getFile();
        return await file.arrayBuffer();
      } catch (err) {
        return null;
      }
    }

    if (this.memoryAdapter) {
      return this.memoryAdapter.getOPFS(filename);
    }
    return null;
  }

  public async deleteFromOPFS(filename: string): Promise<void> {
    await this.init();

    if (
      typeof navigator !== 'undefined' &&
      navigator.storage &&
      typeof navigator.storage.getDirectory === 'function' &&
      !this.memoryAdapter
    ) {
      try {
        const root = await navigator.storage.getDirectory();
        await root.removeEntry(filename);
        return;
      } catch (err) {
        return;
      }
    }

    if (this.memoryAdapter) {
      await this.memoryAdapter.deleteOPFS(filename);
    }
  }

  public async listOPFSFiles(): Promise<string[]> {
    await this.init();

    if (
      typeof navigator !== 'undefined' &&
      navigator.storage &&
      typeof navigator.storage.getDirectory === 'function' &&
      !this.memoryAdapter
    ) {
      try {
        const root = await navigator.storage.getDirectory();
        const names: string[] = [];
        // @ts-ignore - async iterator for directory handle
        for await (const name of (root as any).keys()) {
          names.push(name);
        }
        return names;
      } catch (err) {
        return [];
      }
    }

    if (this.memoryAdapter) {
      return this.memoryAdapter.listOPFS();
    }
    return [];
  }

  // --- Meta & Crash State ---
  public async getMeta(): Promise<CanvasMeta | null> {
    const meta = await this.getStoreItem<CanvasMeta>(CANVAS_STORES.META, DEFAULT_META_ID);
    return meta ? validateCanvasMeta(meta) : null;
  }

  public async setMeta(meta: CanvasMeta): Promise<void> {
    const validated = validateCanvasMeta(meta);
    await this.setStoreItem(CANVAS_STORES.META, validated);
  }

  public async updateMeta(patch: Partial<CanvasMeta>): Promise<CanvasMeta> {
    const current = (await this.getMeta()) || {
      id: DEFAULT_META_ID,
      currentDraftId: null,
      lastSavedAt: Date.now(),
      isDirty: false,
      isCrashed: false,
      activeSessionId: generateUUID(),
      schemaVersion: 1,
    };
    const updated: CanvasMeta = {
      ...current,
      ...patch,
      id: DEFAULT_META_ID,
    };
    await this.setMeta(updated);
    return updated;
  }

  public markDirty(dirty: boolean | string = true): void {
    const isDirtyVal = typeof dirty === 'boolean' ? dirty : true;
    this.isDirtyState = isDirtyVal;
    this.updateMeta({ isDirty: isDirtyVal }).catch(() => {});
  }

  public isDirty(_draftId?: string): boolean {
    return this.isDirtyState;
  }

  public async flagSessionStart(draftId: string, sessionId?: string): Promise<void> {
    await this.updateMeta({
      currentDraftId: draftId,
      activeSessionId: sessionId || generateUUID(),
      isCrashed: true, // Optimistically set to crashed; reset on clean exit
      isDirty: false,
    });
  }

  public async flagSessionCleanExit(): Promise<void> {
    await this.updateMeta({
      isCrashed: false,
      isDirty: false,
    });
  }

  public async checkCrashStatus(): Promise<{ hasCrashed: boolean; meta: CanvasMeta | null }> {
    const meta = await this.getMeta();
    if (!meta) return { hasCrashed: false, meta: null };
    return {
      hasCrashed: Boolean(meta.isCrashed && meta.currentDraftId),
      meta,
    };
  }

  public async recoverFromCrash(draftId?: string): Promise<CrashRecoveryResult> {
    await this.init();
    const meta = await this.getMeta();
    const targetDraftId = draftId || meta?.currentDraftId;

    if (!targetDraftId) {
      return {
        recovered: false,
        draftId: null,
        state: null,
        replayedTransactionsCount: 0,
        lastSequenceNumber: 0,
        reason: 'No target draft ID found in session metadata',
      };
    }

    const baseDraft = await this.getDraft(targetDraftId);
    if (!baseDraft) {
      return {
        recovered: false,
        draftId: targetDraftId,
        state: null,
        replayedTransactionsCount: 0,
        lastSequenceNumber: 0,
        reason: 'Base draft record not found in drafts store',
      };
    }

    const transactions = await this.getHistory(targetDraftId);
    let currentState = baseDraft.state;
    let replayCount = 0;
    let lastSeq = 0;

    for (const tx of transactions) {
      if (tx.forwardPatches && tx.forwardPatches.length > 0) {
        currentState = JsonPatchEngine.applyPatch(currentState, tx.forwardPatches);
        replayCount++;
      }
      lastSeq = tx.sequenceNumber;
    }

    const recoveredState: CanvasState = {
      ...currentState,
      updatedAt: Date.now(),
      version: currentState.version + 1,
    };

    // Save recovered state as new fresh snapshot
    await this.saveDraft(recoveredState);
    await this.flagSessionCleanExit();

    return {
      recovered: true,
      draftId: targetDraftId,
      state: recoveredState,
      replayedTransactionsCount: replayCount,
      lastSequenceNumber: lastSeq,
    };
  }

  // --- Auto-Save Mechanism ---
  public startAutoSave(getState: () => CanvasState, intervalMs?: number): void {
    this.getStateFn = getState;
    if (intervalMs) {
      this.autoSaveIntervalMs = intervalMs;
    }

    this.stopAutoSave();

    this.autoSaveTimer = setInterval(async () => {
      await this.triggerAutoSave();
    }, this.autoSaveIntervalMs);

    // Bind browser lifecycle events if in browser context
    if (typeof window !== 'undefined') {
      this.boundBeforeUnload = (event) => {
        if (this.isDirtyState && this.getStateFn) {
          const currentState = this.getStateFn();
          this.saveDraft(currentState).catch(() => {});
          event.preventDefault();
          event.returnValue = '';
        }
      };
      window.addEventListener('beforeunload', this.boundBeforeUnload);
      window.addEventListener('pagehide', this.boundBeforeUnload);
    }
  }

  public stopAutoSave(): void {
    if (this.autoSaveTimer) {
      clearInterval(this.autoSaveTimer);
      this.autoSaveTimer = null;
    }
    if (typeof window !== 'undefined' && this.boundBeforeUnload) {
      window.removeEventListener('beforeunload', this.boundBeforeUnload);
      window.removeEventListener('pagehide', this.boundBeforeUnload);
      this.boundBeforeUnload = null;
    }
  }

  public async triggerAutoSave(): Promise<DraftRecord | null> {
    if (!this.getStateFn) return null;
    if (!this.isDirtyState) return null;

    try {
      const state = this.getStateFn();
      const saved = await this.saveDraft(state);
      return saved;
    } catch (err) {
      return null;
    }
  }

  // Clean-up & teardown
  public async close(): Promise<void> {
    this.stopAutoSave();
    if (this.db) {
      this.db.close();
      this.db = null;
    }
    if (this.memoryAdapter) {
      await this.memoryAdapter.clear();
    }
    this.isInitialized = false;
  }
}
