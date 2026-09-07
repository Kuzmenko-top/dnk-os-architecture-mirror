// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_lib_api_shopify_canvas_client"
// purpose: "Type-safe client for Shopify Theme Asset Tree, Section Inspections, and Canvas Whiteboard Graphs"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

export interface ThemeAsset {
  key: string;
  content_type: string;
  size?: number;
  created_at?: string;
  updated_at?: string;
  public_url?: string;
}

export interface ThemeAssetTree {
  store_domain: string;
  theme_id: string | number;
  total_files: number;
  layout: ThemeAsset[];
  templates: ThemeAsset[];
  sections: ThemeAsset[];
  snippets: ThemeAsset[];
  assets: ThemeAsset[];
  config: ThemeAsset[];
  locales: ThemeAsset[];
}

export interface CanvasNode {
  id: string;
  key: string;
  node_type: string;
  label: string;
  category: string;
  content_type: string;
  position_x: number;
  position_y: number;
  snippet_dependencies: string[];
  schema_title?: string;
  settings_count: number;
  size_bytes: number;
}

export interface CanvasEdge {
  id: string;
  source: string;
  target: string;
  relationship_type: string;
  label?: string;
}

export interface ShopifyCanvasGraph {
  store_domain: string;
  theme_id: string | number;
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  generated_at: string;
}

export interface AdapterEnvelope<T> {
  data: T | null;
  data_source: 'live' | 'cache' | 'fixture';
  stale: boolean;
  fetched_at: string;
  expires_at: string;
  error_code?: string | null;
}

export const shopifyCanvasApi = {
  async getThemeAssetTree(
    storeDomain: string = 'dnk-e-com.myshopify.com',
    themeId: string | number = '160000001',
    allowFixture: boolean = true
  ): Promise<AdapterEnvelope<ThemeAssetTree>> {
    try {
      const res = await fetch(
        `/api/shopify/${storeDomain}/themes/${themeId}/tree?allow_fixture=${allowFixture}`,
        {
          headers: { 'Content-Type': 'application/json' },
          cache: 'no-store'
        }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return {
        data: {
          store_domain: storeDomain,
          theme_id: themeId,
          total_files: 8,
          layout: [{ key: 'layout/theme.liquid', content_type: 'text/x-liquid', size: 12450 }],
          templates: [{ key: 'templates/index.json', content_type: 'application/json', size: 3200 }],
          sections: [
            { key: 'sections/header.liquid', content_type: 'text/x-liquid', size: 8900 },
            { key: 'sections/hero-banner.liquid', content_type: 'text/x-liquid', size: 5600 }
          ],
          snippets: [
            { key: 'snippets/price.liquid', content_type: 'text/x-liquid', size: 1200 },
            { key: 'snippets/card-product.liquid', content_type: 'text/x-liquid', size: 2400 }
          ],
          assets: [{ key: 'assets/base.css', content_type: 'text/css', size: 45000 }],
          config: [{ key: 'config/settings_schema.json', content_type: 'application/json', size: 18000 }],
          locales: [{ key: 'locales/en.default.json', content_type: 'application/json', size: 9500 }]
        },
        data_source: 'fixture',
        stale: false,
        fetched_at: new Date().toISOString(),
        expires_at: new Date().toISOString(),
        error_code: null
      };
    }
  },

  async getCanvasGraph(
    storeDomain: string = 'dnk-e-com.myshopify.com',
    themeId: string | number = '160000001',
    allowFixture: boolean = true
  ): Promise<AdapterEnvelope<ShopifyCanvasGraph>> {
    try {
      const res = await fetch(
        `/api/shopify/${storeDomain}/themes/${themeId}/canvas-graph?allow_fixture=${allowFixture}`,
        {
          headers: { 'Content-Type': 'application/json' },
          cache: 'no-store'
        }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return {
        data: {
          store_domain: storeDomain,
          theme_id: themeId,
          nodes: [
            {
              id: 'node_layout_0',
              key: 'layout/theme.liquid',
              node_type: 'layout',
              label: 'theme.liquid',
              category: 'layout',
              content_type: 'text/x-liquid',
              position_x: 100,
              position_y: 100,
              snippet_dependencies: [],
              settings_count: 0,
              size_bytes: 12450
            },
            {
              id: 'node_templates_0',
              key: 'templates/index.json',
              node_type: 'template',
              label: 'index.json',
              category: 'templates',
              content_type: 'application/json',
              position_x: 400,
              position_y: 100,
              snippet_dependencies: [],
              settings_count: 0,
              size_bytes: 3200
            },
            {
              id: 'node_sections_0',
              key: 'sections/header.liquid',
              node_type: 'section',
              label: 'header.liquid',
              category: 'sections',
              content_type: 'text/x-liquid',
              position_x: 700,
              position_y: 100,
              snippet_dependencies: ['snippets/price.liquid'],
              schema_title: 'Header Section',
              settings_count: 4,
              size_bytes: 8900
            },
            {
              id: 'node_snippets_0',
              key: 'snippets/price.liquid',
              node_type: 'snippet',
              label: 'price.liquid',
              category: 'snippets',
              content_type: 'text/x-liquid',
              position_x: 1000,
              position_y: 100,
              snippet_dependencies: [],
              settings_count: 0,
              size_bytes: 1200
            }
          ],
          edges: [
            {
              id: 'edge_node_sections_0_node_snippets_0',
              source: 'node_sections_0',
              target: 'node_snippets_0',
              relationship_type: 'renders',
              label: '{% render %}'
            }
          ],
          generated_at: new Date().toISOString()
        },
        data_source: 'fixture',
        stale: false,
        fetched_at: new Date().toISOString(),
        expires_at: new Date().toISOString(),
        error_code: null
      };
    }
  },

  async getAssetContent(
    storeDomain: string,
    themeId: string | number,
    assetKey: string,
    allowFixture: boolean = true
  ): Promise<AdapterEnvelope<{ key: string; value?: string; content_type: string }>> {
    try {
      const res = await fetch(
        `/api/shopify/${storeDomain}/themes/${themeId}/asset?asset_key=${encodeURIComponent(
          assetKey
        )}&allow_fixture=${allowFixture}`,
        {
          headers: { 'Content-Type': 'application/json' },
          cache: 'no-store'
        }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return {
        data: {
          key: assetKey,
          content_type: 'text/x-liquid',
          value: `<!-- Shopify Section: ${assetKey} -->\n<div class="shopify-section-container">\n  <h2>{{ section.settings.title | default: "Featured Section" }}</h2>\n  {% render 'price' %}\n</div>\n\n{% schema %}\n{\n  "name": "Header Banner",\n  "settings": [\n    {\n      "type": "text",\n      "id": "title",\n      "label": "Heading"\n    }\n  ]\n}\n{% endschema %}`
        },
        data_source: 'fixture',
        stale: false,
        fetched_at: new Date().toISOString(),
        expires_at: new Date().toISOString(),
        error_code: null
      };
    }
  }
};
