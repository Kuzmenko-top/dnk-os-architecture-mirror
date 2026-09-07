# --- DNK-MRH-HEADER ---
# mrh_id: "core/adapters/dnk_stitch_adapter.py"
# purpose: "Hexagonal Adapter & MCP Bridge for Google Stitch Open Canvas Interop with DESIGN.md and WCAG AA Linter."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-02"
# author: "Gerych (Hermes Prime)"
# --- END DNK-MRH-HEADER ---

import re
import uuid
import yaml
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

# --- Pydantic Models & DTOs ---

class ColorTokens(BaseModel):
    primary: str = "#0F172A"
    secondary: str = "#38BDF8"
    tertiary: Optional[str] = None
    neutral: Optional[str] = None
    background: Optional[str] = None

class DesignSystemTokenSpec(BaseModel):
    name: str = "Default Theme"
    version: str = "1.0.0"
    description: str = ""
    colors: ColorTokens = Field(default_factory=ColorTokens)
    components: Dict[str, Any] = Field(default_factory=dict)

class ScreenNode(BaseModel):
    id: str
    title: str
    prompt: str
    device_type: str = "mobile"
    html_content: str = ""
    css_classes: str = ""
    meta: Dict[str, Any] = Field(default_factory=dict)

class ScreenEdge(BaseModel):
    id: str
    source_screen_id: str
    target_screen_id: str
    trigger_element_selector: Optional[str] = None
    label: Optional[str] = None

class CanvasProjectGraph(BaseModel):
    project_id: str
    name: str
    screens: List[ScreenNode] = Field(default_factory=list)
    edges: List[ScreenEdge] = Field(default_factory=list)


# --- Helper Functions ---

def parse_design_md(content: str) -> Dict[str, Any]:
    """Parses a DESIGN.md content string containing YAML frontmatter and markdown body."""
    # Match YAML frontmatter between '---' blocks at start of string
    pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
    match = pattern.match(content.strip())
    if match:
        frontmatter_str = match.group(1)
        markdown_body = match.group(2)
        try:
            frontmatter = yaml.safe_load(frontmatter_str) or {}
        except Exception:
            frontmatter = {}
        return {
            "frontmatter": frontmatter,
            "markdown": markdown_body
        }
    return {
        "frontmatter": {},
        "markdown": content
    }

def calculate_contrast_ratio(fg_hex: str, bg_hex: str) -> float:
    """Calculates relative luminance and WCAG contrast ratio for sRGB hex values."""
    def get_luminance(hex_str: str) -> float:
        hex_str = hex_str.lstrip('#')
        if len(hex_str) == 3:
            hex_str = "".join([c*2 for c in hex_str])
        if len(hex_str) != 6:
            return 0.0
        
        rgb = [int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
        linear_rgb = []
        for c in rgb:
            if c <= 0.03928:
                linear_rgb.append(c / 12.92)
            else:
                linear_rgb.append(((c + 0.055) / 1.055) ** 2.4)
        
        r, g, b = linear_rgb
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    l1 = get_luminance(fg_hex)
    l2 = get_luminance(bg_hex)
    
    brightest = max(l1, l2)
    darkest = min(l1, l2)
    
    return (brightest + 0.05) / (darkest + 0.05)

def validate_wcag_contrast(frontmatter: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Runs WCAG 2.1 AA linter across primary colors and components."""
    findings = []
    colors = frontmatter.get("colors", {})
    components = frontmatter.get("components", {})
    
    # Check primary vs background
    primary = colors.get("primary")
    background = colors.get("background", "#FFFFFF")
    if primary and background:
        ratio = calculate_contrast_ratio(primary, background)
        if ratio < 4.5:
            findings.append({
                "type": "contrast_warning",
                "message": f"Primary color ({primary}) vs background ({background}) contrast ratio ({ratio:.2f}:1) is under WCAG AA threshold 4.5:1."
            })
            
    # Check components
    for name, comp in components.items():
        bg = comp.get("backgroundColor")
        fg = comp.get("textColor")
        if bg and fg:
            ratio = calculate_contrast_ratio(fg, bg)
            if ratio < 4.5:
                findings.append({
                    "component": name,
                    "type": "contrast_warning",
                    "message": f"Component '{name}' textColor ({fg}) vs backgroundColor ({bg}) contrast ratio ({ratio:.2f}:1) is under WCAG AA threshold 4.5:1."
                })
                
    return findings

def export_to_tailwind_v4(frontmatter: Dict[str, Any]) -> str:
    """Exports structured tokens to modern CSS variable-based Tailwind CSS v4 `@theme` block."""
    colors = frontmatter.get("colors", {})
    name = frontmatter.get("name", "stitch-theme").lower().replace(" ", "-")
    
    lines = [f"/* Tailwind CSS v4 Theme for {frontmatter.get('name', 'Stitch')} */", "@theme {"]
    for key, val in colors.items():
        if val:
            lines.append(f"  --color-{key}: {val};")
    lines.append("}")
    return "\n".join(lines)

def export_to_dtcg_json(frontmatter: Dict[str, Any]) -> Dict[str, Any]:
    """Exports structured tokens to compliant W3C Design Tokens Community Group JSON format."""
    colors = frontmatter.get("colors", {})
    tokens: Dict[str, Any] = {"colors": {}}
    for key, val in colors.items():
        if val:
            tokens["colors"][key] = {
                "$value": val,
                "$type": "color"
            }
    return tokens


# --- Main Adapter Class ---

class DNKStitchAdapter:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "[REDACTED]"
        
        # Pre-populate in-memory main project for canvas
        self.projects: Dict[str, CanvasProjectGraph] = {
            "proj-main-001": CanvasProjectGraph(
                project_id="proj-main-001",
                name="Main Project",
                screens=[],
                edges=[]
            )
        }

    async def list_projects(self) -> List[Dict[str, Any]]:
        """Lists active projects and screen counts."""
        return [
            {
                "project_id": pid,
                "name": proj.name,
                "screens_count": len(proj.screens)
            }
            for pid, proj in self.projects.items()
        ]

    async def get_project(self, project_id: str) -> Optional[CanvasProjectGraph]:
        """Fetches complete CanvasProjectGraph containing screens and link transitions."""
        return self.projects.get(project_id)

    async def generate_screen(
        self,
        project_id: str,
        prompt: str,
        device_type: str = "mobile",
        parent_screen_id: Optional[str] = None
    ) -> ScreenNode:
        """Simulates AI-driven or Gemini-ready UI screen generation with full layout & interactive routing."""
        proj = self.projects.get(project_id)
        if not proj:
            proj = CanvasProjectGraph(project_id=project_id, name=f"Project {project_id}", screens=[], edges=[])
            self.projects[project_id] = proj
            
        screen_id = f"scr-{len(proj.screens) + 1:03d}"
        
        # Generate clean layout with CSS based on prompt
        title = f"Screen {len(proj.screens) + 1} - {prompt}"
        html_content = f"""
<div class="p-6 bg-slate-900 text-white min-h-[400px] flex flex-col justify-between rounded-xl shadow-xl">
  <div>
    <h1 class="text-2xl font-bold mb-2">{title}</h1>
    <p class="text-slate-400 text-sm">Prompt: {prompt}</p>
    <div class="mt-4 p-4 bg-slate-800 rounded border border-slate-700">
      <p class="text-slate-300">This screen represents {prompt}. Enjoy interactive live prototyping!</p>
    </div>
  </div>
  <div class="mt-6 flex gap-4">
    <button id="btn-next" data-stitch-target="next" class="px-4 py-2 bg-sky-500 hover:bg-sky-600 rounded text-sm font-semibold transition-all">
      Continue
    </button>
  </div>
</div>
"""
        screen = ScreenNode(
            id=screen_id,
            title=title,
            prompt=prompt,
            device_type=device_type,
            html_content=html_content.strip(),
            css_classes="bg-slate-900 text-white p-6"
        )
        proj.screens.append(screen)
        
        # Automatically link if parent_screen_id is specified
        if parent_screen_id:
            edge_id = f"edge-{len(proj.edges) + 1:03d}"
            edge = ScreenEdge(
                id=edge_id,
                source_screen_id=parent_screen_id,
                target_screen_id=screen_id,
                trigger_element_selector="#btn-next",
                label="navigateToNext"
            )
            proj.edges.append(edge)
            
        return screen

    def generate_screen_sync(
        self,
        prompt: str,
        project_id: str = "proj-main-001",
        device_type: str = "mobile",
        parent_screen_id: Optional[str] = None
    ) -> ScreenNode:
        """Synchronous wrapper for generating a Stitch UI screen."""
        import asyncio
        try:
            return asyncio.run(self.generate_screen(project_id, prompt, device_type, parent_screen_id))
        except RuntimeError:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, self.generate_screen(project_id, prompt, device_type, parent_screen_id)).result()

    def transpile_screen_to_shopify_liquid(self, screen_id: str, project_id: str = "proj-main-001") -> str:
        """Transpiles a generated UI screen into production-ready Shopify Liquid section with schema."""
        proj = self.projects.get(project_id)
        screen = None
        if proj:
            for s in proj.screens:
                if s.id == screen_id:
                    screen = s
                    break
        title = screen.title if screen else f"Screen {screen_id}"
        prompt = screen.prompt if screen else "Stitch UI Section"
        
        liquid = f"""{{% comment %}}
  --- DNK-LIQUID-SECTION ---
  section_id: "stitch_{screen_id.replace('-', '_')}"
  purpose: "Generated Shopify Liquid Section for: {prompt}"
  author: "DNK OS Stitch Engine"
  --- END DNK-LIQUID-SECTION ---
{{% endcomment %}}

<div id="stitch-section-{{{{ section.id }}}}" class="shopify-section stitch-canvas-section bg-slate-900 text-white p-6 rounded-2xl shadow-2xl">
  <div class="container mx-auto max-w-4xl">
    <header class="section-header mb-6">
      <h2 class="text-3xl font-extrabold tracking-tight text-white mb-2">{{{{ section.settings.heading | default: "{title[:40]}" }}}}</h2>
      <p class="text-slate-400 text-sm leading-relaxed">{{{{ section.settings.subheading | default: "AI-Generated Stitch Experience" }}}}</p>
    </header>

    <div class="stitch-content-wrapper grid grid-cols-1 md:grid-cols-2 gap-6 my-6">
      <div class="p-6 bg-slate-800/80 backdrop-blur border border-slate-700/50 rounded-xl">
        <h3 class="text-lg font-bold text-sky-400 mb-2">Interactive Preview</h3>
        <p class="text-slate-300 text-sm mb-4">{{{{ section.settings.body_text | default: "Dynamic preview synchronized with DNK Studio Canvas." }}}}</p>
        <button type="button" class="inline-flex items-center px-5 py-2.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold rounded-lg transition-all shadow-lg shadow-sky-500/20">
          {{{{ section.settings.cta_label | default: "Explore Collection" }}}}
        </button>
      </div>
      <div class="p-6 bg-slate-800/40 border border-slate-700/30 rounded-xl flex items-center justify-center">
        <span class="text-xs font-mono uppercase tracking-widest text-slate-500">Stitch Engine v1.1.0 • Liquid Transpiled</span>
      </div>
    </div>
  </div>
</div>

{{% schema %}}
{{
  "name": "{title[:25]}",
  "settings": [
    {{
      "type": "text",
      "id": "heading",
      "label": "Heading",
      "default": "{title[:40]}"
    }},
    {{
      "type": "text",
      "id": "subheading",
      "label": "Subheading",
      "default": "AI Generated Section"
    }},
    {{
      "type": "textarea",
      "id": "body_text",
      "label": "Body Text",
      "default": "Dynamic preview synchronized with DNK Studio Canvas."
    }},
    {{
      "type": "text",
      "id": "cta_label",
      "label": "CTA Button Label",
      "default": "Add to Bag"
    }}
  ],
  "presets": [
    {{
      "name": "{title[:25]}",
      "category": "Custom Content"
    }}
  ]
}}
{{% endschema %}}
"""
        return liquid.strip()

    async def extract_design_system_from_url(self, url: str) -> DesignSystemTokenSpec:
        """Extracts and parses Google Stitch design tokens from a target system URL."""
        # Simulated extraction returning valid sRGB tokens
        return DesignSystemTokenSpec(
            name="Stitch Corporate",
            version="1.0.0",
            description=f"Extracted design tokens from {url}",
            colors=ColorTokens(
                primary="#0F172A",
                secondary="#38BDF8",
                tertiary="#B8422E",
                neutral="#F7F5F2",
                background="#FFFFFF"
            )
        )


# --- Global Instance Singleton ---
dnk_stitch_adapter = DNKStitchAdapter()
