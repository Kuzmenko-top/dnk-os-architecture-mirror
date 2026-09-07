// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/stories/components/Card.stories.tsx"
// purpose: "Storybook stories for Card primitive"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-UI-GEN-003"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym & Gerych Builder"
// --- END DNK-MRH-HEADER ---

import type { Meta, StoryObj } from "@storybook/react";
import React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "../../ui/components/ui/Card";
import { Button } from "../../ui/components/ui/Button";

const meta = {
  title: "Primitives/Card",
  component: Card,
  tags: ["autodocs"],
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Agent Status</CardTitle>
        <CardDescription>gerych_builder swarm worker status.</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">Active and running 386 regression tests.</p>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button variant="outline">Inspect</Button>
        <Button>Deploy</Button>
      </CardFooter>
    </Card>
  ),
};
