/*
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/adapters/teleprompter/indexed-db-session-store.ts"
// purpose: "IndexedDB Storage Adapter with In-Memory Fallback for Teleprompter Sessions."
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---
*/

import type { TeleprompterSession } from '@dnk/teleprompter-core';
import type { SessionStorePort } from './ports';

const DB_NAME = 'dnk_teleprompter_db';
const DB_VERSION = 1;
const STORE_NAME = 'sessions';

export class IndexedDbSessionStore implements SessionStorePort {
  private dbPromise: Promise<IDBDatabase> | null = null;
  private inMemoryStore: Map<string, TeleprompterSession> = new Map();

  private isIndexedDbAvailable(): boolean {
    return typeof window !== 'undefined' && typeof indexedDB !== 'undefined';
  }

  private getDB(): Promise<IDBDatabase> {
    if (!this.isIndexedDbAvailable()) {
      return Promise.reject(new Error('IndexedDB is not available in this environment.'));
    }

    if (this.dbPromise) {
      return this.dbPromise;
    }

    this.dbPromise = new Promise<IDBDatabase>((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          db.createObjectStore(STORE_NAME, { keyPath: 'sessionId' });
        }
      };

      request.onsuccess = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        resolve(db);
      };

      request.onerror = (event) => {
        this.dbPromise = null;
        reject((event.target as IDBOpenDBRequest).error);
      };
    });

    return this.dbPromise;
  }

  async saveSession(session: TeleprompterSession): Promise<void> {
    if (!this.isIndexedDbAvailable()) {
      this.inMemoryStore.set(session.sessionId, session);
      return;
    }
    const db = await this.getDB();
    return new Promise<void>((resolve, reject) => {
      const transaction = db.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.put(session);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async getSession(sessionId: string): Promise<TeleprompterSession | null> {
    if (!this.isIndexedDbAvailable()) {
      return this.inMemoryStore.get(sessionId) ?? null;
    }
    const db = await this.getDB();
    return new Promise<TeleprompterSession | null>((resolve, reject) => {
      const transaction = db.transaction([STORE_NAME], 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.get(sessionId);

      request.onsuccess = () => resolve((request.result as TeleprompterSession) || null);
      request.onerror = () => reject(request.error);
    });
  }

  async listSessions(): Promise<TeleprompterSession[]> {
    if (!this.isIndexedDbAvailable()) {
      return Array.from(this.inMemoryStore.values());
    }
    const db = await this.getDB();
    return new Promise<TeleprompterSession[]>((resolve, reject) => {
      const transaction = db.transaction([STORE_NAME], 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.getAll();

      request.onsuccess = () => resolve((request.result as TeleprompterSession[]) || []);
      request.onerror = () => reject(request.error);
    });
  }

  async deleteSession(sessionId: string): Promise<void> {
    if (!this.isIndexedDbAvailable()) {
      this.inMemoryStore.delete(sessionId);
      return;
    }
    const db = await this.getDB();
    return new Promise<void>((resolve, reject) => {
      const transaction = db.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.delete(sessionId);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }
}
