// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/app/analytics/pixel-events/page.tsx"
// purpose: "Real-time Shopify Web Pixel Event Ingestion Analytics Dashboard"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

"use client";

export const dynamic = "force-dynamic";

import React, { useState } from "react";
import { usePixelEvents, usePixelMetrics } from "@/ui/hooks/usePixelEvents";
import { Card, CardHeader, CardTitle, CardContent } from "@/ui/components/ui/Card";
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from "@/ui/components/ui/Table";
import { Button } from "@/ui/components/ui/Button";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  },
});

function PixelEventsContent() {
  const [shopFilter, setShopFilter] = useState<string>("");
  const { data: eventsData, isLoading: eventsLoading, refetch: refetchEvents } = usePixelEvents(shopFilter || undefined);
  const { data: metricsData, isLoading: metricsLoading } = usePixelMetrics();

  const events = eventsData?.events || [];
  const metrics = metricsData?.metrics;

  return (
    <div className="p-8 space-y-6 bg-slate-950 min-h-screen text-slate-100">
      <div className="flex justify-between items-center border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Shopify Web Pixel Event Stream</h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time event ingestion, HMAC verification, PII anonymization & telemetry
          </p>
        </div>
        <div className="flex gap-3 items-center">
          <input
            type="text"
            placeholder="Filter by shop ID..."
            value={shopFilter}
            onChange={(e) => setShopFilter(e.target.value)}
            className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-md text-sm text-white focus:outline-none focus:ring-1 focus:ring-cyan-500"
          />
          <Button variant="outline" size="sm" onClick={() => refetchEvents()}>
            Refresh
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs text-slate-400 uppercase">Total Ingested Events</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-cyan-400">
              {metricsLoading ? "..." : metrics?.total_events ?? 0}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs text-slate-400 uppercase">Page Views</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-400">
              {metricsLoading ? "..." : metrics?.events_by_type?.["page_view"] ?? 0}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs text-slate-400 uppercase">Purchases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-400">
              {metricsLoading ? "..." : metrics?.events_by_type?.["purchase"] ?? 0}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs text-slate-400 uppercase">Detected Anomalies</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-rose-400">
              {metricsLoading ? "..." : metrics?.total_anomalies ?? 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Events Table */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle className="text-lg text-white">Live Event Feed</CardTitle>
        </CardHeader>
        <CardContent>
          {eventsLoading ? (
            <div className="text-center py-8 text-slate-500">Loading live pixel stream...</div>
          ) : events.length === 0 ? (
            <div className="text-center py-8 text-slate-500">No events captured yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-800">
                    <TableHead className="text-slate-400">Time</TableHead>
                    <TableHead className="text-slate-400">Event</TableHead>
                    <TableHead className="text-slate-400">Shop ID</TableHead>
                    <TableHead className="text-slate-400">Anonymized Customer (SHA256)</TableHead>
                    <TableHead className="text-slate-400">Product / Variant</TableHead>
                    <TableHead className="text-slate-400">Price</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {events.map((evt, idx) => (
                    <TableRow key={idx} className="border-slate-800/50 hover:bg-slate-800/30">
                      <TableCell className="text-xs font-mono text-slate-400">
                        {new Date(evt.timestamp).toLocaleTimeString()}
                      </TableCell>
                      <TableCell>
                        <span className="px-2 py-0.5 rounded text-xs font-medium bg-cyan-950 text-cyan-400 border border-cyan-800/40">
                          {evt.event_type}
                        </span>
                      </TableCell>
                      <TableCell className="text-sm text-slate-300 font-mono">{evt.shop_id}</TableCell>
                      <TableCell className="text-xs font-mono text-slate-400 truncate max-w-[160px]">
                        {evt.customer_id || "—"}
                      </TableCell>
                      <TableCell className="text-xs text-slate-300">
                        {evt.product_id ? `${evt.product_id} (${evt.variant_id || "base"})` : "—"}
                      </TableCell>
                      <TableCell className="text-xs font-semibold text-emerald-400">
                        {evt.price != null ? `$${evt.price.toFixed(2)} ${evt.currency}` : "—"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function PixelEventsDashboardPage() {
  return (
    <QueryClientProvider client={queryClient}>
      <PixelEventsContent />
    </QueryClientProvider>
  );
}
