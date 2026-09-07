// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/stories/components/Button.stories.tsx"
// purpose: "Storybook stories for Button primitive"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-UI-GEN-003"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym & Gerych Builder"
// --- END DNK-MRH-HEADER ---

import type { Meta, StoryObj } from "@storybook/react";
import { Button } from "../../ui/components/ui/Button";

const meta = {
  title: "Primitives/Button",
  component: Button,
  tags: ["autodocs"],
  argTypes: {
    variant: {
      control: "select",
      options: ["default", "destructive", "outline", "secondary", "ghost", "link"],
    },
    size: {
      control: "select",
      options: ["default", "sm", "lg", "icon"],
    },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: "Execute Task",
    variant: "default",
  },
};

export const Destructive: Story = {
  args: {
    children: "Terminate Agent",
    variant: "destructive",
  },
};

export const Outline: Story = {
  args: {
    children: "View Logs",
    variant: "outline",
  },
};
