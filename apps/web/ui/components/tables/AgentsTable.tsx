"use client";
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/ui/components/tables/AgentsTable.tsx"
// purpose: "Design System AgentsTable composite component (TanStack Table v8)"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-UI-GEN-003"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym & Gerych Builder"
// --- END DNK-MRH-HEADER ---

import * as React from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  SortingState,
} from "@tanstack/react-table";
import { useAgents } from "../../hooks/useAgents";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";

export interface AgentsTableProps {
  onRowClick?: (agentId: string) => void;
}

export function AgentsTable({ onRowClick }: AgentsTableProps) {
  const { data, isLoading } = useAgents();
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = React.useState("");

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
    return <div className="p-8 text-center text-sm text-muted-foreground">Loading agent fleet telemetry...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Input
          placeholder="Filter agent fleet..."
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
                  <th key={header.id} className="h-10 px-4 text-left font-medium text-muted-foreground">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="border-b transition-colors hover:bg-muted/50 cursor-pointer"
                onClick={() => onRowClick?.(row.original.name)}
              >
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
