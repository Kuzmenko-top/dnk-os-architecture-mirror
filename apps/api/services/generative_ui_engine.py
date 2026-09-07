# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/generative_ui_engine.py"
# purpose: "Generative UI Engine: Next.js 15, Tailwind v4, shadcn/ui, RHF + Zod Forms & TanStack Table v8"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-UI-GEN-001", "DNK-UI-GEN-002"]
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import re
import json
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class UIComponentKind(str, Enum):
    DASHBOARD = "Dashboard"
    FORM = "Form"
    TABLE = "Table"
    CHART = "Chart"
    METRIC_CARD = "MetricCard"
    REGISTRY = "Registry"


class MetricCardConfig(BaseModel):
    id: str
    title: str
    metric_key: str
    unit: Optional[str] = ""
    formatter: Optional[str] = "number" # number, percentage, duration_ms, currency
    description: Optional[str] = None
    variant: Optional[str] = "default" # default, success, warning, destructive


class ChartType(str, Enum):
    LINE = "line"
    BAR = "bar"
    AREA = "area"
    PIE = "pie"


class ChartConfig(BaseModel):
    id: str
    title: str
    chart_type: ChartType = ChartType.LINE
    x_key: str = "timestamp"
    y_keys: List[str] = Field(default_factory=lambda: ["value"])
    colors: Optional[List[str]] = Field(default_factory=lambda: ["#3b82f6", "#10b981", "#ef4444"])


class ColumnConfig(BaseModel):
    key: str
    header: str
    sortable: bool = True
    filterable: bool = False
    format_type: Optional[str] = "text" # text, badge, timestamp, number


class FormFieldConfig(BaseModel):
    name: str
    label: str
    field_type: str = "text" # text, select, password, boolean, number
    required: bool = True
    placeholder: Optional[str] = ""
    options: Optional[List[str]] = Field(default_factory=list)
    min_length: Optional[int] = None
    validation_pattern: Optional[str] = None
    default_value: Optional[Any] = None


class DataBindingSpec(BaseModel):
    endpoint: str
    method: str = "GET"
    query_key: str
    refetch_interval_ms: Optional[int] = 5000
    stale_time_ms: Optional[int] = 10000
    params: Optional[Dict[str, Any]] = Field(default_factory=dict)


class UISpec(BaseModel):
    title: str
    kind: UIComponentKind
    description: str
    design_system: str = "DNK-DS-001"
    metric_cards: List[MetricCardConfig] = Field(default_factory=list)
    charts: List[ChartConfig] = Field(default_factory=list)
    columns: List[ColumnConfig] = Field(default_factory=list)
    fields: List[FormFieldConfig] = Field(default_factory=list)
    data_binding: Optional[DataBindingSpec] = None


class GeneratedFile(BaseModel):
    relative_path: str
    is_client_component: bool = False
    code: str
    file_type: str = "tsx" # tsx, ts, css


class GeneratedUIBundle(BaseModel):
    spec: UISpec
    files: List[GeneratedFile]
    validation_status: str = "PASSED"
    validation_errors: List[str] = Field(default_factory=list)


class UISpecParser:
    """Parses natural language prompts or structured schemas into a UISpec."""

    @staticmethod
    def parse_natural_language(prompt: str) -> UISpec:
        lower_prompt = prompt.lower()
        title = "Agent Monitoring Dashboard"
        kind = UIComponentKind.DASHBOARD

        if "registry" in lower_prompt or "storybook" in lower_prompt or "компонент" in lower_prompt:
            kind = UIComponentKind.REGISTRY
            title = "Design System Component Registry"
        elif "form" in lower_prompt or "додавання агента" in lower_prompt or "створення" in lower_prompt:
            kind = UIComponentKind.FORM
            title = "Agent Provisioning Form"
        elif "table" in lower_prompt or "таблиц" in lower_prompt or "список" in lower_prompt:
            kind = UIComponentKind.TABLE
            title = "Agent Fleet Overview Table"
        elif "chart" in lower_prompt:
            kind = UIComponentKind.CHART
            title = "Agent Performance Chart"

        metric_cards = []
        charts = []
        columns = []
        fields = []

        if kind == UIComponentKind.FORM:
            fields = [
                FormFieldConfig(name="name", label="Agent Name", field_type="text", required=True, min_length=3, placeholder="e.g. gerych_builder"),
                FormFieldConfig(name="model", label="Foundation Model", field_type="select", required=True, options=["gpt-4o", "claude-3-5-sonnet", "gemini-1.5-pro", "deepseek-r1"]),
                FormFieldConfig(name="api_key", label="API Key Secret", field_type="password", required=True, validation_pattern="^[a-zA-Z0-9-_]+$", placeholder="sk-ant-..."),
                FormFieldConfig(name="status", label="Active Status", field_type="boolean", required=False, default_value=True),
            ]
            data_binding = DataBindingSpec(endpoint="/api/v1/agents", method="POST", query_key="createAgent")
            return UISpec(title=title, kind=kind, description=prompt, design_system="DNK-DS-001", fields=fields, data_binding=data_binding)

        if kind == UIComponentKind.TABLE:
            columns = [
                ColumnConfig(key="name", header="Agent Name", sortable=True, filterable=True, format_type="text"),
                ColumnConfig(key="model", header="Model", sortable=True, filterable=True, format_type="badge"),
                ColumnConfig(key="status", header="Status", sortable=True, filterable=True, format_type="badge"),
                ColumnConfig(key="latency_p95", header="Latency (P95 ms)", sortable=True, filterable=False, format_type="number"),
                ColumnConfig(key="asr", header="ASR Rate (%)", sortable=True, filterable=False, format_type="number"),
            ]
            data_binding = DataBindingSpec(endpoint="/api/v1/agents", method="GET", query_key="agentsList")
            return UISpec(title=title, kind=kind, description=prompt, design_system="DNK-DS-001", columns=columns, data_binding=data_binding)

        # Detect metrics for Dashboard
        if "asr" in lower_prompt or "attack success rate" in lower_prompt or "security" in lower_prompt:
            metric_cards.append(
                MetricCardConfig(
                    id="card-asr",
                    title="Attack Success Rate (ASR)",
                    metric_key="asr_rate",
                    unit="%",
                    formatter="percentage",
                    description="Red team adversarial resistance metric",
                    variant="success"
                )
            )
            charts.append(
                ChartConfig(
                    id="chart-asr-timeline",
                    title="ASR Security Resistance Timeline",
                    chart_type=ChartType.AREA,
                    x_key="timestamp",
                    y_keys=["asr_rate", "blocked_probes"]
                )
            )

        if "latency" in lower_prompt or "lag" in lower_prompt or "performance" in lower_prompt:
            metric_cards.append(
                MetricCardConfig(
                    id="card-latency",
                    title="Average Latency",
                    metric_key="p95_latency_ms",
                    unit="ms",
                    formatter="duration_ms",
                    description="P95 response latency across regions",
                    variant="default"
                )
            )
            charts.append(
                ChartConfig(
                    id="chart-latency-trend",
                    title="Cross-Region Latency (P50/P95/P99)",
                    chart_type=ChartType.LINE,
                    x_key="timestamp",
                    y_keys=["p50_latency_ms", "p95_latency_ms", "p99_latency_ms"]
                )
            )

        if "error" in lower_prompt or "error rate" in lower_prompt or "failures" in lower_prompt:
            metric_cards.append(
                MetricCardConfig(
                    id="card-error-rate",
                    title="Error Rate",
                    metric_key="error_rate",
                    unit="%",
                    formatter="percentage",
                    description="Autonomous self-healing error capture rate",
                    variant="warning"
                )
            )

        if not metric_cards and kind == UIComponentKind.DASHBOARD:
            metric_cards = [
                MetricCardConfig(id="card-asr", title="Attack Success Rate", metric_key="asr_rate", unit="%", formatter="percentage"),
                MetricCardConfig(id="card-latency", title="P95 Latency", metric_key="latency_ms", unit="ms", formatter="duration_ms"),
                MetricCardConfig(id="card-throughput", title="Throughput", metric_key="req_per_sec", unit="req/s", formatter="number")
            ]

        columns = [
            ColumnConfig(key="agent_id", header="Agent ID", sortable=True),
            ColumnConfig(key="role", header="Role", sortable=True, format_type="badge"),
            ColumnConfig(key="status", header="Status", sortable=True, format_type="badge"),
            ColumnConfig(key="latency_ms", header="Latency (ms)", sortable=True, format_type="number"),
            ColumnConfig(key="last_seen", header="Last Active", sortable=True, format_type="timestamp"),
        ]

        data_binding = DataBindingSpec(
            endpoint="/api/v1/agents/metrics",
            method="GET",
            query_key="agentMetrics",
            refetch_interval_ms=5000,
            stale_time_ms=10000
        )

        return UISpec(
            title=title,
            kind=kind,
            description=prompt,
            design_system="DNK-DS-001",
            metric_cards=metric_cards,
            charts=charts,
            columns=columns,
            fields=fields,
            data_binding=data_binding
        )


class ComponentGenerator:
    """Generates Next.js 15 Server/Client Components."""

    @staticmethod
    def generate_dashboard_page(spec: UISpec) -> GeneratedFile:
        code = f"""// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/app/dashboard/page.tsx"
// purpose: "Next.js 15 React Server Component (RSC) for {spec.title}"
// --- END DNK-MRH-HEADER ---

import React, {{ Suspense }} from "react";
import {{ AgentMetricsContainer }} from "./components/AgentMetricsContainer";
import {{ Skeleton }} from "@/components/ui/skeleton";

export const metadata = {{
  title: "{spec.title} | DNK OS",
  description: "{spec.description}",
}};

export default function DashboardPage() {{
  return (
    <main className="flex-1 space-y-6 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight text-foreground">{spec.title}</h2>
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center rounded-md bg-primary/10 px-2 py-1 text-xs font-medium text-primary ring-1 ring-inset ring-primary/20">
            {spec.design_system}
          </span>
        </div>
      </div>
      <Suspense fallback={{<DashboardSkeleton />}}>
        <AgentMetricsContainer />
      </Suspense>
    </main>
  );
}}

function DashboardSkeleton() {{
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <Skeleton className="h-[120px] rounded-xl" />
      <Skeleton className="h-[120px] rounded-xl" />
      <Skeleton className="h-[120px] rounded-xl" />
    </div>
  );
}}
"""
        return GeneratedFile(
            relative_path="apps/web/app/dashboard/page.tsx",
            is_client_component=False,
            code=code,
            file_type="tsx"
        )

    @staticmethod
    def generate_metrics_card(spec: UISpec) -> GeneratedFile:
        cards_jsx = []
        for card in spec.metric_cards:
            variant_badge = (
                '<span className="text-xs font-semibold text-emerald-500">Normal</span>'
                if card.variant == "success"
                else '<span className="text-xs font-semibold text-amber-500">Monitored</span>'
            )
            cards_jsx.append(f"""
      <Card className="p-6 transition-all hover:shadow-md border-border/50 bg-card">
        <div className="flex flex-row items-center justify-between space-y-0 pb-2">
          <h3 className="tracking-tight text-sm font-medium text-muted-foreground">{card.title}</h3>
          {variant_badge}
        </div>
        <div className="flex items-baseline space-x-2">
          <div className="text-2xl font-bold text-foreground">
            {{data?.{card.metric_key} ?? "--"}}
            <span className="text-sm font-normal text-muted-foreground ml-1">{card.unit}</span>
          </div>
        </div>
        <p className="text-xs text-muted-foreground mt-1">{card.description or ""}</p>
      </Card>""")

        cards_body = "\n".join(cards_jsx)
        code = f""""use client";
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/app/dashboard/components/AgentMetricsCards.tsx"
// purpose: "Client component for animated Metric Cards with Tailwind v4 & shadcn/ui"
// --- END DNK-MRH-HEADER ---

import React from "react";
import {{ Card }} from "@/components/ui/card";
import {{ AgentMetricsData }} from "../types";

interface AgentMetricsCardsProps {{
  data?: AgentMetricsData;
  isLoading?: boolean;
}}

export function AgentMetricsCards({{ data, isLoading }}: AgentMetricsCardsProps) {{
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-{min(len(spec.metric_cards), 4)}">
{cards_body}
    </div>
  );
}}
"""
        return GeneratedFile(
            relative_path="apps/web/app/dashboard/components/AgentMetricsCards.tsx",
            is_client_component=True,
            code=code,
            file_type="tsx"
        )

    @staticmethod
    def generate_chart_component(spec: UISpec) -> GeneratedFile:
        code = """"use client";
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/app/dashboard/components/ASRChart.tsx"
// purpose: "Recharts / Tailwind v4 Responsive Chart for Real-Time Metrics"
// --- END DNK-MRH-HEADER ---

import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { AgentMetricsData } from "../types";

interface ChartProps {
  data?: AgentMetricsData;
  isLoading?: boolean;
}

export function ASRChart({ data, isLoading }: ChartProps) {
  const chartData = data?.timeline ?? [];

  return (
    <Card className="col-span-4 border-border/50 bg-card">
      <CardHeader>
        <CardTitle className="text-base font-semibold text-foreground">Security Resistance & Latency Timeline</CardTitle>
      </CardHeader>
      <CardContent className="pl-2">
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorAsr" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="timestamp" className="text-xs text-muted-foreground" />
              <YAxis className="text-xs text-muted-foreground" />
              <Tooltip contentStyle={{ backgroundColor: "var(--background)", borderColor: "var(--border)" }} />
              <Area type="monotone" dataKey="asr_rate" stroke="#10b981" fillOpacity={1} fill="url(#colorAsr)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
"""
        return GeneratedFile(
            relative_path="apps/web/app/dashboard/components/ASRChart.tsx",
            is_client_component=True,
            code=code,
            file_type="tsx"
        )


class FormGenerator:
    """Generates React Hook Form + Zod Components."""

    @staticmethod
    def generate_form_page(spec: UISpec) -> GeneratedFile:
        code = f"""// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/app/agents/new/page.tsx"
// purpose: "Server Page component for {spec.title}"
// --- END DNK-MRH-HEADER ---

import React from "react";
import {{ AgentForm }} from "./components/AgentForm";

export const metadata = {{
  title: "{spec.title} | DNK OS",
  description: "{spec.description}",
}};

export default function NewAgentPage() {{
  return (
    <div className="flex-1 space-y-6 p-8 max-w-2xl mx-auto">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-foreground">{spec.title}</h2>
        <p className="text-sm text-muted-foreground">Provision and register a new autonomous agent in the DNK swarm.</p>
      </div>
      <AgentForm />
    </div>
  );
}}
"""
        return GeneratedFile(
            relative_path="apps/web/app/agents/new/page.tsx",
            is_client_component=False,
            code=code,
            file_type="tsx"
        )

    @staticmethod
    def generate_form_component(spec: UISpec) -> GeneratedFile:
        zod_rules = []
        for field in spec.fields:
            if field.field_type == "text":
                rule = "z.string()"
                if field.min_length:
                    rule += f'.min({field.min_length}, "Must be at least {field.min_length} characters")'
                zod_rules.append(f"  {field.name}: {rule},")
            elif field.field_type == "select":
                opts_str = ", ".join([f'"{opt}"' for opt in (field.options or [])])
                zod_rules.append(f"  {field.name}: z.enum([{opts_str}]),")
            elif field.field_type == "password":
                zod_rules.append(f'  {field.name}: z.string().min(1, "API Key is required"),')
            elif field.field_type == "boolean":
                zod_rules.append(f"  {field.name}: z.boolean().default(true),")

        zod_schema_str = "\n".join(zod_rules)

        code = f""""use client";
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/app/agents/new/components/AgentForm.tsx"
// purpose: "React Hook Form + Zod Client Component for Agent creation"
// --- END DNK-MRH-HEADER ---

import React from "react";
import {{ useForm }} from "react-hook-form";
import {{ zodResolver }} from "@hookform/resolvers/zod";
import * as z from "zod";
import {{ Button }} from "@/components/ui/button";
import {{ Input }} from "@/components/ui/input";
import {{ Card, CardContent, CardFooter }} from "@/components/ui/card";
import {{ useCreateAgent }} from "../hooks/useCreateAgent";

export const agentFormSchema = z.object({{
{zod_schema_str}
}});

export type AgentFormData = z.infer<typeof agentFormSchema>;

export function AgentForm() {{
  const {{ mutate, isPending }} = useCreateAgent();
  const form = useForm<AgentFormData>({{
    resolver: zodResolver(agentFormSchema),
    defaultValues: {{
      name: "",
      model: "gpt-4o",
      api_key: "",
      status: true,
    }},
  }});

  const onSubmit = (values: AgentFormData) => {{
    mutate(values);
  }};

  return (
    <Card className="border-border/50 bg-card">
      <form onSubmit={{form.handleSubmit(onSubmit)}}>
        <CardContent className="space-y-4 pt-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Agent Name</label>
            <Input {{...form.register("name")}} placeholder="e.g. gerych_builder" />
            {{form.formState.errors.name && (
              <p className="text-xs text-destructive">{{form.formState.errors.name.message}}</p>
            )}}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Foundation Model</label>
            <select
              {{...form.register("model")}}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="gpt-4o">GPT-4o (OpenAI)</option>
              <option value="claude-3-5-sonnet">Claude 3.5 Sonnet (Anthropic)</option>
              <option value="gemini-1.5-pro">Gemini 1.5 Pro (Google)</option>
              <option value="deepseek-r1">DeepSeek R1</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">API Key Secret</label>
            <Input type="password" {{...form.register("api_key")}} placeholder="sk-..." />
            {{form.formState.errors.api_key && (
              <p className="text-xs text-destructive">{{form.formState.errors.api_key.message}}</p>
            )}}
          </div>
        </CardContent>
        <CardFooter className="flex justify-end gap-2 border-t px-6 py-4">
          <Button type="submit" disabled={{isPending}}>
            {{isPending ? "Creating..." : "Create Agent"}}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}}
"""
        return GeneratedFile(
            relative_path="apps/web/app/agents/new/components/AgentForm.tsx",
            is_client_component=True,
            code=code,
            file_type="tsx"
        )

    @staticmethod
    def generate_mutation_hook(spec: UISpec) -> GeneratedFile:
        code = """"use client";
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/app/agents/new/hooks/useCreateAgent.ts"
// purpose: "TanStack React Query mutation hook for agent creation"
// --- END DNK-MRH-HEADER ---

import { useMutation, useQueryClient } from "@tanstack/react-query";

export function useCreateAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: any) => {
      const res = await fetch("/api/v1/agents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        throw new Error("Failed to create agent");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agentsList"] });
    },
  });
}
"""
        return GeneratedFile(
            relative_path="apps/web/app/agents/new/hooks/useCreateAgent.ts",
            is_client_component=True,
            code=code,
            file_type="ts"
        )


class TableGenerator:
    """Generates TanStack Table v8 Components."""

    @staticmethod
    def generate_table_page(spec: UISpec) -> GeneratedFile:
        code = f"""// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/app/agents/page.tsx"
// purpose: "Server Page component for {spec.title}"
// --- END DNK-MRH-HEADER ---

import React, {{ Suspense }} from "react";
import {{ AgentsTable }} from "./components/AgentsTable";
import {{ Skeleton }} from "@/components/ui/skeleton";

export const metadata = {{
  title: "{spec.title} | DNK OS",
  description: "{spec.description}",
}};

export default function AgentsPage() {{
  return (
    <main className="flex-1 space-y-6 p-8 pt-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight text-foreground">{spec.title}</h2>
      </div>
      <Suspense fallback={{<Skeleton className="h-[400px] w-full rounded-xl" />}}>
        <AgentsTable />
      </Suspense>
    </main>
  );
}}
"""
        return GeneratedFile(
            relative_path="apps/web/app/agents/page.tsx",
            is_client_component=False,
            code=code,
            file_type="tsx"
        )

    @staticmethod
    def generate_table_component(spec: UISpec) -> GeneratedFile:
        code = """"use client";
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/app/agents/components/AgentsTable.tsx"
// purpose: "TanStack Table v8 Client Component with sorting and filtering"
// --- END DNK-MRH-HEADER ---

import React, { useState } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  SortingState,
} from "@tanstack/react-table";
import { useAgents } from "../hooks/useAgents";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export function AgentsTable() {
  const { data, isLoading } = useAgents();
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState("");

  const columns = [
    { accessorKey: "name", header: "Agent Name" },
    { accessorKey: "model", header: "Model" },
    { accessorKey: "status", header: "Status" },
    { accessorKey: "latency_p95", header: "Latency (P95 ms)" },
    { accessorKey: "asr", header: "ASR Rate (%)" },
  ];

  const table = useReactTable({
    data: data ?? [],
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  if (isLoading) {
    return <div className="p-8 text-center text-sm text-muted-foreground">Loading agent fleet data...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Input
          placeholder="Filter agents..."
          value={globalFilter ?? ""}
          onChange={(e) => setGlobalFilter(e.target.value)}
          className="max-w-sm"
        />
      </div>
      <div className="rounded-md border border-border bg-card">
        <table className="w-full text-sm">
          <thead className="border-b bg-muted/50">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th key={header.id} className="h-12 px-4 text-left font-medium text-muted-foreground">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="border-b transition-colors hover:bg-muted/50">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="p-4">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-end space-x-2">
        <Button variant="outline" size="sm" onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>
          Previous
        </Button>
        <Button variant="outline" size="sm" onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>
          Next
        </Button>
      </div>
    </div>
  );
}
"""
        return GeneratedFile(
            relative_path="apps/web/app/agents/components/AgentsTable.tsx",
            is_client_component=True,
            code=code,
            file_type="tsx"
        )

    @staticmethod
    def generate_query_hook(spec: UISpec) -> GeneratedFile:
        code = """"use client";
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/app/agents/hooks/useAgents.ts"
// purpose: "TanStack React Query hook for agents fleet"
// --- END DNK-MRH-HEADER ---

import { useQuery } from "@tanstack/react-query";

export interface AgentRecord {
  name: string;
  model: string;
  status: string;
  latency_p95: number;
  asr: number;
}

export function useAgents() {
  return useQuery<AgentRecord[], Error>({
    queryKey: ["agentsList"],
    queryFn: async () => {
      const res = await fetch("/api/v1/agents");
      if (!res.ok) {
        throw new Error("Failed to fetch agent list");
      }
      return res.json();
    },
    staleTime: 15000,
  });
}
"""
        return GeneratedFile(
            relative_path="apps/web/app/agents/hooks/useAgents.ts",
            is_client_component=True,
            code=code,
            file_type="ts"
        )


class DataBindingLayer:
    """Generates TanStack React Query v5 hooks and types."""

    @staticmethod
    def generate_types(spec: UISpec) -> GeneratedFile:
        fields = ["  timestamp: string;"]
        for card in spec.metric_cards:
            fields.append(f"  {card.metric_key}: number;")
        fields_str = "\n".join(fields)

        code = f"""// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/app/dashboard/types.ts"
// purpose: "TypeScript Data Contract definitions for {spec.title}"
// --- END DNK-MRH-HEADER ---

export interface AgentMetricsData {{
{fields_str}
  timeline?: Array<{{
    timestamp: string;
    asr_rate: number;
    latency_ms: number;
    error_rate: number;
  }}>;
}}

export interface AgentLogEntry {{
  agent_id: string;
  role: string;
  status: "idle" | "running" | "completed" | "failed";
  latency_ms: number;
  last_seen: string;
}}
"""
        return GeneratedFile(
            relative_path="apps/web/app/dashboard/types.ts",
            is_client_component=False,
            code=code,
            file_type="ts"
        )

    @staticmethod
    def generate_react_query_hook(spec: UISpec) -> GeneratedFile:
        binding = spec.data_binding or DataBindingSpec(
            endpoint="/api/v1/agents/metrics",
            query_key="agentMetrics"
        )

        code = f""""use client";
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/app/dashboard/hooks/useAgentMetrics.ts"
// purpose: "TanStack React Query v5 Hook for autonomous real-time polling"
// --- END DNK-MRH-HEADER ---

import {{ useQuery }} from "@tanstack/react-query";
import {{ AgentMetricsData }} from "../types";

async function fetchAgentMetrics(): Promise<AgentMetricsData> {{
  const res = await fetch("{binding.endpoint}");
  if (!res.ok) {{
    throw new Error(`Failed to fetch metrics: ${{res.statusText}}`);
  }}
  return res.json();
}}

export function useAgentMetrics() {{
  return useQuery<AgentMetricsData, Error>({{
    queryKey: ["{binding.query_key}"],
    queryFn: fetchAgentMetrics,
    refetchInterval: {binding.refetch_interval_ms},
    staleTime: {binding.stale_time_ms},
    retry: 3,
  }});
}}
"""
        return GeneratedFile(
            relative_path="apps/web/app/dashboard/hooks/useAgentMetrics.ts",
            is_client_component=True,
            code=code,
            file_type="ts"
        )

    @staticmethod
    def generate_container_component(spec: UISpec) -> GeneratedFile:
        code = """"use client";
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/app/dashboard/components/AgentMetricsContainer.tsx"
// purpose: "Client Container wiring React Query data to UI components"
// --- END DNK-MRH-HEADER ---

import React from "react";
import { useAgentMetrics } from "../hooks/useAgentMetrics";
import { AgentMetricsCards } from "./AgentMetricsCards";
import { ASRChart } from "./ASRChart";

export function AgentMetricsContainer() {
  const { data, isLoading, error } = useAgentMetrics();

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
        <p className="text-sm font-semibold">Error loading agent telemetry</p>
        <p className="text-xs">{error.message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <AgentMetricsCards data={data} isLoading={isLoading} />
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <ASRChart data={data} isLoading={isLoading} />
      </div>
    </div>
  );
}
"""
        return GeneratedFile(
            relative_path="apps/web/app/dashboard/components/AgentMetricsContainer.tsx",
            is_client_component=True,
            code=code,
            file_type="tsx"
        )


class RegistryGenerator:
    """Generates Design System Component Registry (apps/web/ui/) and Storybook stories."""

    @staticmethod
    def generate_barrel_export(spec: UISpec) -> GeneratedFile:
        code = """// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/ui/index.ts"
// purpose: "Design System Component Registry Barrel Export"
// --- END DNK-MRH-HEADER ---

export * from "./components/ui";
export * from "./components/forms";
export * from "./components/tables";
export * from "./components/charts";
export * from "./hooks";
export * from "./lib/utils";
export * from "./lib/api";
"""
        return GeneratedFile(
            relative_path="apps/web/ui/index.ts",
            is_client_component=False,
            code=code,
            file_type="ts"
        )

    @staticmethod
    def generate_storybook_config(spec: UISpec) -> GeneratedFile:
        code = """// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/.storybook/main.ts"
// purpose: "Storybook main configuration for Next.js 15"
// --- END DNK-MRH-HEADER ---

import type { StorybookConfig } from "@storybook/nextjs";

const config: StorybookConfig = {
  stories: ["../stories/**/*.mdx", "../stories/**/*.stories.@(js|jsx|mjs|ts|tsx)"],
  addons: ["@storybook/addon-links", "@storybook/addon-essentials"],
  framework: { name: "@storybook/nextjs", options: {} },
};

export default config;
"""
        return GeneratedFile(
            relative_path="apps/web/.storybook/main.ts",
            is_client_component=False,
            code=code,
            file_type="ts"
        )


class UIValidator:
    """Validates generated TSX/TS files for AST integrity, type correctness and Next.js invariants."""

    @staticmethod
    def validate_bundle(bundle: GeneratedUIBundle) -> GeneratedUIBundle:
        errors = []
        for file in bundle.files:
            # 1. Check MRH header
            if "DNK-MRH-HEADER" not in file.code:
                errors.append(f"Missing DNK-MRH-HEADER in {file.relative_path}")

            # 2. Check Balanced braces
            open_curly = file.code.count("{")
            close_curly = file.code.count("}")
            if open_curly != close_curly:
                errors.append(f"Unbalanced curly braces in {file.relative_path}: {open_curly} vs {close_curly}")

            # 3. Client Component directive check
            if file.is_client_component and not file.code.startswith('"use client";'):
                errors.append(f"Client component {file.relative_path} missing '\"use client\";' directive at top")

            # 4. Check for forbidden absolute paths
            if "/Users/" in file.code or "/home/" in file.code:
                errors.append(f"Absolute path violation detected in {file.relative_path}")

        bundle.validation_errors = errors
        bundle.validation_status = "PASSED" if len(errors) == 0 else "FAILED"
        return bundle


class GenerativeUIEngine:
    """Main orchestrator for Generative UI Engine."""

    def __init__(self):
        self.parser = UISpecParser()
        self.generator = ComponentGenerator()
        self.form_generator = FormGenerator()
        self.table_generator = TableGenerator()
        self.registry_generator = RegistryGenerator()
        self.data_layer = DataBindingLayer()
        self.validator = UIValidator()

    def generate_ui_from_prompt(self, prompt: str) -> GeneratedUIBundle:
        # 1. Parse prompt into UISpec
        spec = self.parser.parse_natural_language(prompt)
        files: List[GeneratedFile] = []

        # 2. Dispatch based on component kind
        if spec.kind == UIComponentKind.REGISTRY:
            files.append(self.registry_generator.generate_barrel_export(spec))
            files.append(self.registry_generator.generate_storybook_config(spec))
        elif spec.kind == UIComponentKind.FORM:
            files.append(self.form_generator.generate_form_page(spec))
            files.append(self.form_generator.generate_form_component(spec))
            files.append(self.form_generator.generate_mutation_hook(spec))
        elif spec.kind == UIComponentKind.TABLE:
            files.append(self.table_generator.generate_table_page(spec))
            files.append(self.table_generator.generate_table_component(spec))
            files.append(self.table_generator.generate_query_hook(spec))
        else: # DASHBOARD / CHART
            files.append(self.generator.generate_dashboard_page(spec))
            files.append(self.generator.generate_metrics_card(spec))
            files.append(self.generator.generate_chart_component(spec))
            files.append(self.data_layer.generate_types(spec))
            files.append(self.data_layer.generate_react_query_hook(spec))
            files.append(self.data_layer.generate_container_component(spec))

        # 3. Assemble bundle
        bundle = GeneratedUIBundle(spec=spec, files=files)

        # 4. Run AST & invariant validation
        return self.validator.validate_bundle(bundle)
