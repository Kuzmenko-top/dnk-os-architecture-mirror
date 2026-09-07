"use client";
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/ui/components/forms/AgentForm.tsx"
// purpose: "Design System AgentForm composite component"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-UI-GEN-003"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym & Gerych Builder"
// --- END DNK-MRH-HEADER ---

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Card, CardContent, CardFooter } from "../ui/Card";
import { useCreateAgent } from "../../hooks/useCreateAgent";

export const agentFormSchema = z.object({
  name: z.string().min(3, "Must be at least 3 characters"),
  model: z.enum(["gpt-4o", "claude-3-5-sonnet", "gemini-1.5-pro", "deepseek-r1"]),
  api_key: z.string().min(1, "API Key is required"),
  status: z.boolean().default(true),
});

export type AgentFormData = z.infer<typeof agentFormSchema>;

export interface AgentFormProps {
  onSuccess?: () => void;
  defaultValues?: Partial<AgentFormData>;
}

export function AgentForm({ onSuccess, defaultValues }: AgentFormProps) {
  const { mutate, isPending } = useCreateAgent();
  const form = useForm<AgentFormData>({
    resolver: zodResolver(agentFormSchema),
    defaultValues: {
      name: defaultValues?.name ?? "",
      model: defaultValues?.model ?? "gpt-4o",
      api_key: defaultValues?.api_key ?? "",
      status: defaultValues?.status ?? true,
    },
  });

  const onSubmit = (values: AgentFormData) => {
    mutate({
      name: values.name,
      model: values.model,
      api_key: values.api_key,
      status: Boolean(values.status),
    }, {
      onSuccess: () => {
        onSuccess?.();
      },
    });
  };

  return (
    <Card className="border-border/50 bg-card">
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <CardContent className="space-y-4 pt-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Agent Name</label>
            <Input {...form.register("name")} placeholder="e.g. gerych_builder" />
            {form.formState.errors.name && (
              <p className="text-xs text-destructive">{form.formState.errors.name.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Foundation Model</label>
            <select
              {...form.register("model")}
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              <option value="gpt-4o">GPT-4o (OpenAI)</option>
              <option value="claude-3-5-sonnet">Claude 3.5 Sonnet (Anthropic)</option>
              <option value="gemini-1.5-pro">Gemini 1.5 Pro (Google)</option>
              <option value="deepseek-r1">DeepSeek R1</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">API Key Secret</label>
            <Input type="password" {...form.register("api_key")} placeholder="sk-..." />
            {form.formState.errors.api_key && (
              <p className="text-xs text-destructive">{form.formState.errors.api_key.message}</p>
            )}
          </div>
        </CardContent>
        <CardFooter className="flex justify-end gap-2 border-t px-6 py-4">
          <Button type="submit" disabled={isPending}>
            {isPending ? "Creating..." : "Create Agent"}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
