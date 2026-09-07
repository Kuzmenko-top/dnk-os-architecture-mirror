// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/stories/components/AgentsTable.stories.tsx"
// purpose: "Storybook stories for AgentsTable component"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-UI-GEN-003"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym & Gerych Builder"
// --- END DNK-MRH-HEADER ---

import type { Meta, StoryObj } from "@storybook/react";
import { AgentsTable } from "../../ui/components/tables/AgentsTable";

const meta = {
  title: "Components/Tables/AgentsTable",
  component: AgentsTable,
  tags: ["autodocs"],
  argTypes: {
    onRowClick: { action: "onRowClick" },
  },
} satisfies Meta<typeof AgentsTable>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {},
};
