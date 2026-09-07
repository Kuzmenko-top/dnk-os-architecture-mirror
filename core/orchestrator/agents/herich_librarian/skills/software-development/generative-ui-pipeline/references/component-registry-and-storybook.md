# Component Registry & Storybook Integration Reference

## 1. Component Registry Layout (`apps/web/ui/`)

Centralized design system directory with modular barrel exports:

```
apps/web/ui/
├── components/
│   ├── ui/          # Primitives (Button, Card, Input, Table, Skeleton)
│   ├── forms/       # Composite Forms (AgentForm - RHF + Zod)
│   ├── tables/      # Composite Data Tables (AgentsTable - TanStack Table v8)
│   └── charts/      # Composite Visualizations (ASRChart)
├── hooks/           # Telemetry & Mutation Hooks (useAgents, useCreateAgent, useAgentMetrics)
├── lib/             # Utilities (utils.ts cn helper, api.ts fetcher client)
└── index.ts         # Main Barrel Export
```

### Main Barrel Export Example (`apps/web/ui/index.ts`)
```typescript
export * from "./components/ui";
export * from "./components/forms";
export * from "./components/tables";
export * from "./components/charts";
export * from "./hooks";
export * from "./lib/utils";
export * from "./lib/api";
```

## 2. Storybook Integration (`apps/web/.storybook/` & `apps/web/stories/`)

### Main Configuration (`apps/web/.storybook/main.ts`)
```typescript
import type { StorybookConfig } from "@storybook/nextjs";

const config: StorybookConfig = {
  stories: ["../stories/**/*.mdx", "../stories/**/*.stories.@(js|jsx|mjs|ts|tsx)"],
  addons: ["@storybook/addon-links", "@storybook/addon-essentials"],
  framework: { name: "@storybook/nextjs", options: {} },
};

export default config;
```

### Component Story Example (`apps/web/stories/components/AgentForm.stories.tsx`)
```typescript
import type { Meta, StoryObj } from '@storybook/react';
import { AgentForm } from '../../ui/components/forms/AgentForm';

const meta = {
  title: 'Components/Forms/AgentForm',
  component: AgentForm,
  tags: ['autodocs'],
  argTypes: { onSubmit: { action: 'submitted' } },
} satisfies Meta<typeof AgentForm>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
```
