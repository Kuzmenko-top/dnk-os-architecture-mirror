// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/.storybook/manager.js"
// purpose: "Storybook UI Manager theme customization"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-UI-GEN-003"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym & Gerych Builder"
// --- END DNK-MRH-HEADER ---

import { addons } from "@storybook/manager-api";
import { create } from "@storybook/theming";

const theme = create({
  base: "dark",
  brandTitle: "DNK OS Design System",
  brandUrl: "https://dnk-e.com",
  brandTarget: "_self",
  appBg: "#09090b",
  appContentBg: "#18181b",
  appBorderColor: "#27272a",
  textColor: "#fafafa",
  barBg: "#09090b",
});

addons.setConfig({
  theme,
});
