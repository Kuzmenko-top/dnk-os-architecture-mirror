// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/ui/components/ui/Table.tsx"
// purpose: "Design System Table primitives"
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

export interface TableProps extends React.HTMLAttributes<HTMLTableElement> {
  data?: any[];
  columns?: Array<{ header: string; accessorKey?: string; cell?: (row: any) => React.ReactNode }>;
  isLoading?: boolean;
}

export const Table = React.forwardRef<HTMLTableElement, TableProps>(
  ({ className, data, columns, isLoading, children, ...props }, ref) => {
    if (columns && data !== undefined) {
      return (
        <div className="relative w-full overflow-auto">
          <table ref={ref} className={cn("w-full caption-bottom text-sm", className)} {...props}>
            <thead className="[&_tr]:border-b bg-muted/50">
              <tr>
                {columns.map((c, i) => (
                  <th key={i} className="h-10 px-4 text-left align-middle font-medium text-muted-foreground">
                    {c.header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="[&_tr:last-child]:border-0">
              {isLoading ? (
                <tr>
                  <td colSpan={columns.length} className="p-4 text-center text-muted-foreground">
                    Loading...
                  </td>
                </tr>
              ) : data.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="p-4 text-center text-muted-foreground">
                    No records found
                  </td>
                </tr>
              ) : (
                data.map((row, rIdx) => (
                  <tr key={rIdx} className="border-b transition-colors hover:bg-muted/50">
                    {columns.map((c, cIdx) => (
                      <td key={cIdx} className="p-4 align-middle">
                        {c.cell ? c.cell(row) : c.accessorKey ? String(row[c.accessorKey] ?? '') : null}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      );
    }

    return (
      <div className="relative w-full overflow-auto">
        <table ref={ref} className={cn("w-full caption-bottom text-sm", className)} {...props}>
          {children}
        </table>
      </div>
    );
  }
);
Table.displayName = "Table";

export const TableHeader = React.forwardRef<HTMLTableSectionElement, React.HTMLAttributes<HTMLTableSectionElement>>(
  ({ className, ...props }, ref) => <thead ref={ref} className={cn("[&_tr]:border-b bg-muted/50", className)} {...props} />
);
TableHeader.displayName = "TableHeader";

export const TableBody = React.forwardRef<HTMLTableSectionElement, React.HTMLAttributes<HTMLTableSectionElement>>(
  ({ className, ...props }, ref) => (
    <tbody ref={ref} className={cn("[&_tr:last-child]:border-0", className)} {...props} />
  )
);
TableBody.displayName = "TableBody";

export const TableRow = React.forwardRef<HTMLTableRowElement, React.HTMLAttributes<HTMLTableRowElement>>(
  ({ className, ...props }, ref) => (
    <tr
      ref={ref}
      className={cn("border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted", className)}
      {...props}
    />
  )
);
TableRow.displayName = "TableRow";

export const TableHead = React.forwardRef<HTMLTableCellElement, React.ThHTMLAttributes<HTMLTableCellElement>>(
  ({ className, ...props }, ref) => (
    <th
      ref={ref}
      className={cn("h-10 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0", className)}
      {...props}
    />
  )
);
TableHead.displayName = "TableHead";

export const TableCell = React.forwardRef<HTMLTableCellElement, React.TdHTMLAttributes<HTMLTableCellElement>>(
  ({ className, ...props }, ref) => (
    <td ref={ref} className={cn("p-4 align-middle [&:has([role=checkbox])]:pr-0", className)} {...props} />
  )
);
TableCell.displayName = "TableCell";
