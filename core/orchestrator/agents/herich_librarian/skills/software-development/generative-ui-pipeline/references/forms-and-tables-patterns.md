# Forms and Tables Code Generation Patterns for Next.js 15

## 1. React Hook Form + Zod Form Generation Pattern

```tsx
"use client";
import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { useCreateEntity } from "../hooks/useCreateEntity";

export const entityFormSchema = z.object({
  name: z.string().min(3, "Must be at least 3 characters"),
  model: z.enum(["gpt-4o", "claude-3-5-sonnet", "gemini-1.5-pro"]),
  api_key: z.string().min(1, "API Key is required"),
  status: z.boolean().default(true),
});

export type EntityFormData = z.infer<typeof entityFormSchema>;

export function EntityForm() {
  const { mutate, isPending } = useCreateEntity();
  const form = useForm<EntityFormData>({
    resolver: zodResolver(entityFormSchema),
    defaultValues: { name: "", model: "gpt-4o", api_key: "", status: true },
  });

  const onSubmit = (values: EntityFormData) => {
    mutate(values);
  };

  return (
    <Card className="border-border/50 bg-card">
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <CardContent className="space-y-4 pt-6">
          <div className="space-y-2">
            <label className="text-sm font-medium">Name</label>
            <Input {...form.register("name")} />
            {form.formState.errors.name && (
              <p className="text-xs text-destructive">{form.formState.errors.name.message}</p>
            )}
          </div>
        </CardContent>
        <CardFooter className="flex justify-end gap-2 border-t px-6 py-4">
          <Button type="submit" disabled={isPending}>
            {isPending ? "Submitting..." : "Submit"}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
```

## 2. TanStack Table v8 Data Table Pattern

```tsx
"use client";
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
import { useEntities } from "../hooks/useEntities";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export function EntitiesTable() {
  const { data, isLoading } = useEntities();
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState("");

  const columns = [
    { accessorKey: "name", header: "Name" },
    { accessorKey: "status", header: "Status" },
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

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="space-y-4">
      <Input
        placeholder="Search..."
        value={globalFilter ?? ""}
        onChange={(e) => setGlobalFilter(e.target.value)}
      />
      <table className="w-full text-sm">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id}>
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```
