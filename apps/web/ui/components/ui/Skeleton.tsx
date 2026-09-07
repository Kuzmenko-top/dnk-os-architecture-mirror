// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/ui/components/ui/Skeleton.tsx"
// purpose: "Design System Skeleton component"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-UI-GEN-003"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym & Gerych Builder"
// --- END DNK-MRH-HEADER ---

import * as React from "react";
import { cn } from "../../lib/utils";

export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("animate-pulse rounded-md bg-muted/60", className)} {...props} />;
}
