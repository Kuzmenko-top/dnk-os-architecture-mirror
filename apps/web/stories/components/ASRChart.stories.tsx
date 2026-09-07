// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/stories/components/ASRChart.stories.tsx"
// purpose: "Storybook stories for ASRChart component"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-UI-GEN-003"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym & Gerych Builder"
// --- END DNK-MRH-HEADER ---

import type { Meta, StoryObj } from "@storybook/react";
import { ASRChart } from "../../ui/components/charts/ASRChart";

const meta = {
  title: "Components/Charts/ASRChart",
  component: ASRChart,
  tags: ["autodocs"],
} satisfies Meta<typeof ASRChart>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    title: "Master Quality Gate - ASR Timeline",
    timeline: [
      { timestamp: "10:00", asr_rate: 0.0, blocked_probes: 12 },
      { timestamp: "10:05", asr_rate: 0.0, blocked_probes: 28 },
      { timestamp: "10:10", asr_rate: 0.0, blocked_probes: 45 },
      { timestamp: "10:15", asr_rate: 0.0, blocked_probes: 89 },
    ],
  },
};
