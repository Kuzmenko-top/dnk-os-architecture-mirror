// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_ui_hooks_usePatentShield"
// purpose: "React hook and state manager for Patent Shield & Clean-Room IP Guard API"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-PATENT-001"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

import { useState, useCallback } from 'react';

export interface RiskFactor {
  factor: string;
  patent_id: string;
  score?: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  overlap_ratio?: number;
  overlapping_claims?: Array<{ claim: string; overlap: number }>;
}

export interface RiskAssessmentResponse {
  overall_risk: 'low' | 'medium' | 'high' | 'critical';
  max_similarity: number;
  risk_factors: RiskFactor[];
  recommendations: string[];
}

export interface PatentItem {
  patent_id: string;
  title: string;
  abstract: string;
  claims: string[];
  classifications?: string[];
  similarity_score?: number;
  rrf_score?: number;
}

export function usePatentShield() {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [assessment, setAssessment] = useState<RiskAssessmentResponse | null>(null);
  const [patents, setPatents] = useState<PatentItem[]>([]);

  const searchPatents = useCallback(async (query: string, jurisdiction = 'US', limit = 20) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/patent-shield/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, jurisdiction, limit }),
      });
      if (!res.ok) throw new Error(`Search failed with status ${res.status}`);
      const data = await res.json();
      setPatents(data.patents || []);
      return data.patents;
    } catch (err: any) {
      setError(err.message || 'Error executing patent search');
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  const assessRisk = useCallback(
    async (cleanRoomSpec: string, queryText: string, topK = 20) => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch('/api/v1/patent-shield/risk-assessment', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            clean_room_spec: cleanRoomSpec,
            query_text: queryText,
            top_k: topK,
          }),
        });
        if (!res.ok) throw new Error(`Risk assessment failed with status ${res.status}`);
        const data: RiskAssessmentResponse = await res.json();
        setAssessment(data);
        return data;
      } catch (err: any) {
        setError(err.message || 'Error executing risk assessment');
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return {
    loading,
    error,
    assessment,
    patents,
    searchPatents,
    assessRisk,
  };
}
