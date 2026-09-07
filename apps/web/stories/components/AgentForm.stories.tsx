// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/stories/components/AgentForm.stories.tsx"
// purpose: "Storybook stories for AgentForm component"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-UI-GEN-003"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym & Gerych Builder"
// --- END DNK-MRH-HEADER ---

import type { Meta, StoryObj } from "@storybook/react";
import { AgentForm } from "../../ui/components/forms/AgentForm";

const meta = {
  title: "Components/Forms/AgentForm",
  component: AgentForm,
  tags: ["autodocs"],
  argTypes: {
    onSuccess: { action: "onSuccess" },
  },
} satisfies Meta<typeof AgentForm>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    defaultValues: {
      name: "dnk_dev_fullstack",
      model: "gpt-4o",
      api_key: "sk-[REDACTED]",
      status: true,
    },
  },
};
