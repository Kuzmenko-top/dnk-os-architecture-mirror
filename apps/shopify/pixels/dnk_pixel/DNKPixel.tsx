// --- DNK-MRH-HEADER ---
// mrh_id: "apps/shopify/pixels/dnk_pixel/DNKPixel.tsx"
// purpose: "Shopify Web Pixel Extension component for background event tracking"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

import React, { useEffect } from 'react';

export interface ProductPayload {
  id: string;
  variantId?: string;
  quantity?: number;
  price?: number;
}

export interface OrderPayload {
  id: string;
  totalPrice: number;
  lineItems: Array<{
    id: string;
    variantId?: string;
    quantity: number;
    price: number;
  }>;
}

export function DNKPixel() {
  const publishEvent = async (eventType: string, payload: Record<string, unknown>) => {
    try {
      await fetch('/web-pixel/events', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Shopify-Topic': `web_pixel/${eventType}`,
        },
        body: JSON.stringify({
          event_type: eventType,
          timestamp: Date.now(),
          url: typeof window !== 'undefined' ? window.location.href : '',
          referrer: typeof document !== 'undefined' ? document.referrer : '',
          ...payload,
        }),
      });
    } catch (err) {
      console.error(`[DNKPixel] Failed to publish ${eventType}`, err);
    }
  };

  useEffect(() => {
    publishEvent('page_view', {
      shop_id: 'dnk-e-store',
      currency: 'USD',
    });
  }, []);

  return null;
}

export default DNKPixel;
