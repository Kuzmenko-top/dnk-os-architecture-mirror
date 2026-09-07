# --- DNK-MRH-HEADER ---
# mrh_id: "USER_GUIDE.md"
# purpose: "User Guide and Functional Walkthrough for DNK OS Canvas MVP"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# --- END DNK-MRH-HEADER ---

# 🎨 DNK OS Canvas MVP — User Guide & Walkthrough

Welcome to **DNK OS Canvas Studio**, an AI-native visual canvas environment designed to orchestrate autonomous multi-agent swarms for e-commerce, design, and software engineering.

---

## ⚡ Quick Start: 5-Minute Walkthrough

Follow these steps to launch your first AI-assisted project:

### 1. Open the Visual Shell
Once deployed, open your browser and navigate to:
👉 **[http://localhost:3000](http://localhost:3000)**

### 2. Launch "E-Com Швидкий Старт"
On the welcome dashboard or top bar, click the **"E-Com швидкий старт"** button to initiate the guided setup wizard.

### 3. Complete the 4-Step Onboarding Form
Fill in your core business parameters:
1. **Goal**: `Launch DTC brand`
2. **Target Audience**: `Women 25-40`
3. **Visual Style**: `Minimalist & Clean`
4. **Unique Selling Proposition (UTP)**: `Eco-friendly sustainable apparel`

Click **"Згенерувати Канвас" (Generate Canvas)**. The system will automatically instantiate a 4-node pipeline on the infinite canvas.

### 4. Trigger AI Co-Pilot
1. Select the **Strategy** node.
2. Click the **⚡ AI Co-Pilot** action button in the node toolbar.
3. Observe real-time streaming output as the AI agent synthesizes the brand identity and market positioning.

### 5. Swarm Propagation
1. Connect the output handle of the **Strategy** node to the input of the **Design** node.
2. Click **"Propagate Changes"** to flow strategic insights into visual layouts, Liquid template drafts, and code tasks.

### 6. Export Your Work
Click the **Export** icon in the top header and choose:
- **`.canvas` Format**: Native Obsidian/JSON compatible graph file.
- **`JSON State`**: Complete raw state for backup or multi-device sync.

---

## 🌟 Core Features & Capabilities

### 1. 🐝 Swarm Propagation Pipeline
The canvas utilizes a directed acyclic graph (DAG) workflow:
- **Strategy Node**: Generates product positioning, ICP definitions, and value propositions.
- **Design Node**: Produces design tokens, component hierarchies, and responsive wireframes.
- **Code Node**: Automatically scaffolds Next.js/React and Shopify Liquid templates.
- **Kanban Node**: Breaks down deliverables into actionable task cards for development and marketing sprints.

### 2. ⚡ AI Co-Pilot (Gemini + Claude Orchestration)
- Context-aware node assistants capable of code completion, copywriting, and architecture reviews.
- Real-time streaming generation over Server-Sent Events (SSE) with minimal latency.

### 3. ⏪ Undo / Redo & State Integrity
- **Undo**: `Ctrl + Z` (Windows/Linux) or `Cmd + Z` (macOS)
- **Redo**: `Ctrl + Y` (Windows/Linux) or `Cmd + Shift + Z` (macOS)
- Granular revision history stored locally and synced to PostgreSQL via `canvas-api`.

### 4. 💾 Import & Export Interoperability
- Seamlessly import pre-existing `.canvas` files.
- Export production-ready specs, Liquid templates, and architecture graphs in one click.

---

## 🛠️ Common Shortcuts & Navigation

| Action | Shortcut | Description |
| :--- | :--- | :--- |
| **Pan Canvas** | `Space + Drag` or Middle Click | Move around the infinite workspace |
| **Zoom In / Out** | `Scroll Wheel` or `+` / `-` | Zoom from 10% to 200% |
| **Select Multiple Nodes** | `Shift + Drag Box` | Multi-select nodes to move or align |
| **Delete Selected** | `Backspace` or `Delete` | Remove selected nodes or edges |
| **Fit View** | `Shift + 1` | Automatically center and frame all active nodes |

---

## 🔧 Troubleshooting

### Web Interface Not Loading
- Verify container status: `docker compose -f docker-compose.mvp.yml ps`
- Inspect frontend logs: `docker compose -f docker-compose.mvp.yml logs -f canvas-web`

### AI Co-Pilot Fails to Stream
- Verify the backend API health: `curl http://localhost:8000/health`
- Check API container logs: `docker compose -f docker-compose.mvp.yml logs -f canvas-api`

### Re-initializing Canvas State
- If the canvas state becomes corrupted, click **"Reset Canvas"** in the settings menu or reload the session.
