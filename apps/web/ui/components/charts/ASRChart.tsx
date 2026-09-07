"use client";
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/ui/components/charts/ASRChart.tsx"
// purpose: "Design System ASRChart component"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-UI-GEN-003"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym & Gerych Builder"
// --- END DNK-MRH-HEADER ---

import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/Card";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

export interface ASRTimelinePoint {
  timestamp: string;
  asr_rate: number;
  blocked_probes?: number;
}

export interface ASRChartProps {
  timeline?: ASRTimelinePoint[];
  title?: string;
}

export function ASRChart({ timeline = [], title = "Security Resistance (ASR Timeline)" }: ASRChartProps) {
  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="text-base font-semibold text-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent className="pl-2">
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={timeline}>
              <defs>
                <linearGradient id="colorAsrUi" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="timestamp" className="text-xs text-muted-foreground" />
              <YAxis className="text-xs text-muted-foreground" />
              <Tooltip contentStyle={{ backgroundColor: "var(--background)", borderColor: "var(--border)" }} />
              <Area type="monotone" dataKey="asr_rate" stroke="#10b981" fillOpacity={1} fill="url(#colorAsrUi)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
