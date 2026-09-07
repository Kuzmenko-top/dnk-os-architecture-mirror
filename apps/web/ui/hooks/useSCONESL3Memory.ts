// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/ui/hooks/useSCONESL3Memory.ts"
// purpose: "React Hook for SCONES L3 Long-Term Memory (Retrieval, Filtering, Sleep Consolidation and Analytics)"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-SCONES-L3-001", "DNK-SCONES-L3-002"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

import { useState, useEffect, useCallback } from 'react';

export interface SCONESL3MemoryItem {
  id: string;
  content: string;
  memory_type: string;
  metadata: Record<string, any>;
  created_at: string;
  rrf_score: number;
  recency_score: number;
  final_score: number;
}

export interface MemoryStats {
  total: number;
  types: number;
  avg_recency: number;
}

export function useSCONESL3Memory(userId: string = 'user-alpha-101', workspaceId: string = 'ws-alpha-001') {
  const [memories, setMemories] = useState<SCONESL3MemoryItem[]>([]);
  const [stats, setStats] = useState<MemoryStats>({ total: 0, types: 0, avg_recency: 1.0 });
  const [loading, setLoading] = useState<boolean>(false);
  const [consolidating, setConsolidating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMemories = useCallback(async (query: string = '') => {
    setLoading(true);
    setError(null);
    try {
      const url = `/api/v1/memory/l3/memories?user_id=${encodeURIComponent(userId)}&workspace_id=${encodeURIComponent(workspaceId)}&query=${encodeURIComponent(query)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Fetch failed: ${res.statusText}`);
      const data = await res.json();
      setMemories(data.memories || []);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch long-term memories');
    } finally {
      setLoading(false);
    }
  }, [userId, workspaceId]);

  const fetchStats = useCallback(async () => {
    try {
      const url = `/api/v1/memory/l3/stats?user_id=${encodeURIComponent(userId)}&workspace_id=${encodeURIComponent(workspaceId)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Stats fetch failed: ${res.statusText}`);
      const data = await res.json();
      setStats(data);
    } catch (err) {
      console.error('Stats error:', err);
    }
  }, [userId, workspaceId]);

  const consolidate = async (olderThanDays: number = 7) => {
    setConsolidating(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/memory/l3/consolidate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          workspace_id: workspaceId,
          older_than_days: olderThanDays,
        }),
      });
      if (!res.ok) throw new Error('Consolidation failed');
      await fetchMemories();
      await fetchStats();
    } catch (err: any) {
      setError(err.message || 'Error triggering sleep consolidation');
    } finally {
      setConsolidating(false);
    }
  };

  useEffect(() => {
    fetchMemories();
    fetchStats();
  }, [fetchMemories, fetchStats]);

  return {
    memories,
    stats,
    loading,
    consolidating,
    error,
    fetchMemories,
    fetchStats,
    consolidate,
  };
}
