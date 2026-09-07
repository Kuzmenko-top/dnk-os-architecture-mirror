// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/ui/hooks/usePixelEvents.ts"
// purpose: "React Query hooks for Web Pixel real-time event analytics and metric monitoring"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

import { useQuery } from '@tanstack/react-query';

export interface WebPixelEventItem {
  event_type: string;
  shop_id: string;
  customer_id?: string | null;
  product_id?: string | null;
  variant_id?: string | null;
  quantity?: number;
  price?: number;
  currency: string;
  timestamp: number;
  url: string;
  referrer?: string | null;
  extra_data?: Record<string, unknown>;
}

export interface PixelMetrics {
  total_events: number;
  events_by_type: Record<string, number>;
  total_anomalies: number;
  latest_anomalies: Array<{
    timestamp: number;
    shop_id: string;
    event_type: string;
    anomalies: string[];
  }>;
}

export function usePixelEvents(shopId?: string, limit: number = 50) {
  return useQuery<{ status: string; count: number; events: WebPixelEventItem[] }>({
    queryKey: ['pixel-events', shopId, limit],
    queryFn: async () => {
      const url = shopId
        ? `/web-pixel/events?shop_id=${encodeURIComponent(shopId)}&limit=${limit}`
        : `/web-pixel/events?limit=${limit}`;
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error(`Failed to fetch pixel events: ${res.statusText}`);
      }
      return res.json();
    },
    refetchInterval: 5000,
  });
}

export function usePixelMetrics() {
  return useQuery<{ status: string; metrics: PixelMetrics }>({
    queryKey: ['pixel-metrics'],
    queryFn: async () => {
      const res = await fetch('/web-pixel/metrics');
      if (!res.ok) {
        throw new Error(`Failed to fetch pixel metrics: ${res.statusText}`);
      }
      return res.json();
    },
    refetchInterval: 5000,
  });
}
