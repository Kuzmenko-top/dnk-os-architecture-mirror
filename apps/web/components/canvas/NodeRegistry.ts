// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_NodeRegistry"
// purpose: "TypeScript Node Registry declaring UI schemas, port types, risk colors, and icons for all executable canvas nodes"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.1.0"
// updated_at: "2026-08-31"
// --- END DNK-MRH-HEADER ---

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';
export type NodeCategory = 'goal' | 'task' | 'agent' | 'approval' | 'artifact' | 'ecommerce' | 'media' | 'research' | 'deployment' | 'note' | 'architecture';
export type PortType = 'data' | 'control' | 'approval' | 'reference';

export interface PortSpec {
  name: string;
  dataType: string;
  portType: PortType;
  required?: boolean;
  description?: string;
}

export interface NodeMetadata {
  type: string;
  title: string;
  category: NodeCategory;
  icon: string;
  description: string;
  riskLevel: RiskLevel;
  inputs: PortSpec[];
  outputs: PortSpec[];
  capabilities: string[];
}

export const NODE_REGISTRY_MAP: Record<string, NodeMetadata> = {
  SwarmAgentNode: {
    type: 'SwarmAgentNode',
    title: 'Gerych & Swarm Agent Node',
    category: 'agent',
    icon: 'Bot',
    description: 'Displays real-time reasoning thoughts, TaskDNA progress, execution logs, and interactive chat for Gerych Prime and Swarm workers.',
    riskLevel: 'low',
    inputs: [
      { name: 'task_directive', dataType: 'taskdna.goal', portType: 'control' },
      { name: 'chat_prompt', dataType: 'user.prompt', portType: 'data' }
    ],
    outputs: [
      { name: 'thought_stream', dataType: 'agent.thoughts', portType: 'data' },
      { name: 'execution_result', dataType: 'swarm.result', portType: 'data' },
      { name: 'status_signal', dataType: 'control.signal', portType: 'control' }
    ],
    capabilities: ['a2a.delegate_task', 'scones.retrieve_patterns', 'taskdna.decompose_goal']
  },
  ArchifySpatialNode: {
    type: 'ArchifySpatialNode',
    title: 'Archify Spatial Architecture',
    category: 'architecture',
    icon: 'Layers',
    description: 'Interactive self-contained spatial architecture & workflow diagrams with pan/zoom, guided views, and Live Mesh telemetry.',
    riskLevel: 'low',
    inputs: [
      { name: 'diagram_ir', dataType: 'archify.ir', portType: 'data' },
      { name: 'telemetry_stream', dataType: 'mesh.event', portType: 'control' }
    ],
    outputs: [
      { name: 'rendered_html', dataType: 'html.artifact', portType: 'data' },
      { name: 'view_change', dataType: 'control.signal', portType: 'control' }
    ],
    capabilities: ['archify.render_spatial', 'archify.stream_telemetry', 'archify.switch_view']
  },
  ShopifyBuilderNode: {
    type: 'ShopifyBuilderNode',
    title: 'Shopify OS 2.0 Theme Builder',
    category: 'ecommerce',
    icon: 'ShoppingBag',
    description: 'Visual preview of theme sections, AST configurator, and one-click build/deploy dispatch to /api/shopify/build.',
    riskLevel: 'medium',
    inputs: [
      { name: 'theme_config', dataType: 'shopify.theme_config', portType: 'data' },
      { name: 'build_trigger', dataType: 'control.signal', portType: 'control' }
    ],
    outputs: [
      { name: 'theme_ast', dataType: 'shopify.ast', portType: 'data' },
      { name: 'deployment_status', dataType: 'deploy.status', portType: 'control' }
    ],
    capabilities: ['shopify.build_theme', 'shopify.deploy_cdn', 'shopify.ast_transpile']
  },
  SmartNoteNode: {
    type: 'SmartNoteNode',
    title: 'Smart Note & Architecture Plan',
    category: 'note',
    icon: 'FileText',
    description: 'Dynamic rich note, checklist, and architectural plan node with 4-way mesh handles for connecting to other nodes.',
    riskLevel: 'low',
    inputs: [
      { name: 'context_in', dataType: 'any', portType: 'data' }
    ],
    outputs: [
      { name: 'plan_context', dataType: 'note.markdown', portType: 'data' },
      { name: 'checklist_state', dataType: 'note.checklist', portType: 'data' }
    ],
    capabilities: ['note.edit', 'note.checklist_sync']
  },
  GoalNode: {
    type: 'GoalNode',
    title: 'Goal Intake Node',
    category: 'goal',
    icon: 'Target',
    description: 'Receives natural language goal and triggers TaskDNA evolutionary decomposition.',
    riskLevel: 'low',
    inputs: [],
    outputs: [
      { name: 'taskdna_dag', dataType: 'taskdna.dag', portType: 'control' },
      { name: 'goal_context', dataType: 'core.context', portType: 'data' }
    ],
    capabilities: ['taskdna.decompose_goal']
  },
  TaskNode: {
    type: 'TaskNode',
    title: 'Executable Subtask',
    category: 'task',
    icon: 'CheckSquare',
    description: 'Executes a discrete subtask assigned to a specialized swarm agent.',
    riskLevel: 'low',
    inputs: [
      { name: 'input_data', dataType: 'any', portType: 'data' },
      { name: 'trigger', dataType: 'control.signal', portType: 'control' }
    ],
    outputs: [
      { name: 'result', dataType: 'any', portType: 'data' },
      { name: 'status', dataType: 'task.status', portType: 'control' }
    ],
    capabilities: ['a2a.delegate_task', 'research.market_brief']
  },
  AgentNode: {
    type: 'AgentNode',
    title: 'Swarm Agent Worker',
    category: 'agent',
    icon: 'Bot',
    description: 'Displays real-time reasoning, telemetry, and thought streams of a Swarm domain agent.',
    riskLevel: 'low',
    inputs: [
      { name: 'task_spec', dataType: 'taskdna.task', portType: 'data' }
    ],
    outputs: [
      { name: 'thought_stream', dataType: 'agent.stream', portType: 'data' },
      { name: 'artifact_out', dataType: 'artifact.ref', portType: 'data' }
    ],
    capabilities: ['a2a.delegate_task']
  },
  ApprovalNode: {
    type: 'ApprovalNode',
    title: 'Human Approval Gate',
    category: 'approval',
    icon: 'ShieldAlert',
    description: 'Enforces human authorization before executing external writes, deployments, or payments.',
    riskLevel: 'high',
    inputs: [
      { name: 'plan_proposal', dataType: 'workflow.plan', portType: 'approval' }
    ],
    outputs: [
      { name: 'approved_signal', dataType: 'control.signal', portType: 'control' }
    ],
    capabilities: ['governance.request_approval']
  },
  ArtifactNode: {
    type: 'ArtifactNode',
    title: 'Deliverable Artifact',
    category: 'artifact',
    icon: 'FileText',
    description: 'Encapsulates generated deliverables (Landing Page, Video, Shopify Theme, PR, Evidence).',
    riskLevel: 'low',
    inputs: [
      { name: 'content', dataType: 'any', portType: 'data' }
    ],
    outputs: [
      { name: 'artifact_uri', dataType: 'artifact.uri', portType: 'reference' }
    ],
    capabilities: ['memory.store_evidence']
  },
  VideoCreatorNode: {
    type: 'VideoCreatorNode',
    title: 'AI Video & Motion Studio',
    category: 'media',
    icon: 'Video',
    description: 'Spatial video generation studio supporting 9:16 vertical reels, 16:9 cinematic widescreen, Remotion composition, and AI motion rendering.',
    riskLevel: 'medium',
    inputs: [
      { name: 'video_prompt', dataType: 'prompt.text', portType: 'data' },
      { name: 'aspect_ratio', dataType: 'video.aspect_ratio', portType: 'data' },
      { name: 'render_trigger', dataType: 'control.signal', portType: 'control' }
    ],
    outputs: [
      { name: 'video_artifact', dataType: 'media.video_uri', portType: 'reference' },
      { name: 'render_telemetry', dataType: 'render.status', portType: 'control' }
    ],
    capabilities: ['video.render_remotion', 'video.synthesize_diffusion', 'video.export_mp4']
  },
  PhotoStudioNode: {
    type: 'PhotoStudioNode',
    title: 'AI Photo & Visual Studio',
    category: 'media',
    icon: 'Camera',
    description: 'Spatial visual studio synthesizing 3 tailored prompt variants before generation, supporting 1:1, 9:16, 16:9 aspect ratios and direct export to Shopify & Video nodes.',
    riskLevel: 'low',
    inputs: [
      { name: 'base_goal', dataType: 'goal.text', portType: 'data' },
      { name: 'style_reference', dataType: 'image.uri', portType: 'reference' }
    ],
    outputs: [
      { name: 'photo_artifacts', dataType: 'image.batch', portType: 'data' },
      { name: 'selected_prompt', dataType: 'prompt.text', portType: 'data' }
    ],
    capabilities: ['image.synthesize_variants', 'image.render_diffusion', 'image.export_shopify']
  },
  BaseMindMapNode: {
    type: 'BaseMindMapNode',
    title: 'Base Mind Map Card',
    category: 'note',
    icon: 'Layers',
    description: 'Foundational mind map card with 4-way handles, glassmorphism styling, and inline title/description editor.',
    riskLevel: 'low',
    inputs: [
      { name: 'parent_link', dataType: 'any', portType: 'data' }
    ],
    outputs: [
      { name: 'child_link', dataType: 'any', portType: 'data' }
    ],
    capabilities: ['mindmap.connect', 'mindmap.inline_edit']
  },
  MindMapIdeaNode: {
    type: 'MindMapIdeaNode',
    title: 'Mind Map Idea Node',
    category: 'note',
    icon: 'Lightbulb',
    description: 'Yellow/Amber sticker card for brainstorming hypotheses, tagging ideas, and rating confidence.',
    riskLevel: 'low',
    inputs: [
      { name: 'context_in', dataType: 'any', portType: 'data' }
    ],
    outputs: [
      { name: 'idea_context', dataType: 'idea.hypothesis', portType: 'data' }
    ],
    capabilities: ['mindmap.tag_ideas', 'mindmap.confidence_rate']
  },
  MindMapGoalNode: {
    type: 'MindMapGoalNode',
    title: 'Mind Map Goal Node',
    category: 'goal',
    icon: 'Target',
    description: 'Emerald green card for tracking project deadlines, completion percentages, and key performance metrics (KPIs).',
    riskLevel: 'low',
    inputs: [
      { name: 'milestone_trigger', dataType: 'control.signal', portType: 'control' }
    ],
    outputs: [
      { name: 'goal_state', dataType: 'goal.metrics', portType: 'data' }
    ],
    capabilities: ['goal.progress_track', 'goal.deadline_monitor']
  },
  MindMapTaskNode: {
    type: 'MindMapTaskNode',
    title: 'Mind Map Task Node',
    category: 'task',
    icon: 'CheckSquare',
    description: 'Blue card for actionable tasks with interactive status toggle, priority levels, and assignee metadata.',
    riskLevel: 'low',
    inputs: [
      { name: 'dependency_in', dataType: 'task.status', portType: 'control' }
    ],
    outputs: [
      { name: 'task_complete', dataType: 'task.status', portType: 'control' }
    ],
    capabilities: ['task.toggle_status', 'task.assign']
  },
  MindMapAgentNode: {
    type: 'MindMapAgentNode',
    title: 'Mind Map Agent Node',
    category: 'agent',
    icon: 'Bot',
    description: 'Orange card dispatching specialized Swarm workers with live status telemetry and one-click execution.',
    riskLevel: 'medium',
    inputs: [
      { name: 'task_directive', dataType: 'task.directive', portType: 'control' }
    ],
    outputs: [
      { name: 'execution_result', dataType: 'swarm.result', portType: 'data' },
      { name: 'trace_id', dataType: 'telemetry.trace_id', portType: 'reference' }
    ],
    capabilities: ['swarm.trigger_agent', 'telemetry.track_trace']
  },
  MindMapEvidenceNode: {
    type: 'MindMapEvidenceNode',
    title: 'Mind Map Evidence Node',
    category: 'artifact',
    icon: 'FolderGit2',
    description: 'Purple card linking source files, documentation, and external research with snippet previews.',
    riskLevel: 'low',
    inputs: [
      { name: 'artifact_source', dataType: 'artifact.uri', portType: 'reference' }
    ],
    outputs: [
      { name: 'evidence_ref', dataType: 'artifact.reference', portType: 'reference' }
    ],
    capabilities: ['evidence.link_artifact', 'evidence.preview']
  }
};


