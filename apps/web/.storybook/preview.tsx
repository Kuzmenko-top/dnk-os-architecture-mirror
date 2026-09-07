// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/.storybook/preview.tsx"
// purpose: "Storybook preview setup with React Query provider and Tailwind styles"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-UI-GEN-003"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym & Gerych Builder"
// --- END DNK-MRH-HEADER ---

import React from "react";
import type { Preview } from "@storybook/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "../app/globals.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: "^on[A-Z].*" },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
  },
  decorators: [
    (Story) => (
      <QueryClientProvider client={queryClient}>
        <div className="dark bg-background text-foreground p-6 rounded-lg min-h-[300px]">
          <Story />
        </div>
      </QueryClientProvider>
    ),
  ],
};

export default preview;
