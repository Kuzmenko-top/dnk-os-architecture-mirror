// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_lib_swarm"
// purpose: "Canonical 14 DNK OS Swarm Agents Registry & Dispatch Integration"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

import { dispatchSwarmAgent, getA2AFederationStreamUrl, SwarmDispatchResult } from './dnk-api';

export interface DNKSwarmAgent {
  id: string;
  name: string;
  role: string;
  avatar: string;
  description: string;
  color: string;
  category: 'core' | 'ecom' | 'media' | 'dev' | 'security' | 'growth';
}

export const DNK_SWARM_AGENTS: DNKSwarmAgent[] = [
  {
    id: 'gerych_prime',
    name: 'Gerych Prime',
    role: 'Chief Builder & Swarm Manager',
    avatar: '🧬',
    description: 'Lead Orchestrator & Chief Builder for DNK OS',
    color: '#8b5cf6',
    category: 'core',
  },
  {
    id: 'gerych_researcher',
    name: 'Gerych Researcher',
    role: 'Deep R&D & GitHub Research',
    avatar: '🔬',
    description: 'SOTA Repository Assimilation & GitHub Deep Research',
    color: '#3b82f6',
    category: 'core',
  },
  {
    id: 'gerych_auditor',
    name: 'Gerych Auditor',
    role: 'Security & Quality Gate Auditor',
    avatar: '🛡️',
    description: 'Adversarial Security Review & Test Quality Gate',
    color: '#10b981',
    category: 'security',
  },
  {
    id: 'dnk_shopify',
    name: 'DNK Shopify',
    role: 'Liquid AST & E-Com Engine',
    avatar: '🛍️',
    description: 'Shopify Liquid AST Transpiler & Store Builder',
    color: '#9333ea',
    category: 'ecom',
  },
  {
    id: 'dnk_video_ai_creator',
    name: 'DNK Video Creator',
    role: 'Remotion & Media Generator',
    avatar: '🎬',
    description: 'Agentic Media, Remotion Video Synthesis & Animation',
    color: '#f59e0b',
    category: 'media',
  },
  {
    id: 'dnk_dev_fullstack',
    name: 'DNK Fullstack Dev',
    role: 'Backend FastAPI & Architecture',
    avatar: '⚡',
    description: 'FastAPI Router Generation & Fullstack Engineering',
    color: '#06b6d4',
    category: 'dev',
  },
  {
    id: 'dnk_security_guard',
    name: 'DNK Security Guard',
    role: 'Context Firewall & Guardrails',
    avatar: '🚨',
    description: 'Token Masking, Firewall & Path Hygiene Protection',
    color: '#ef4444',
    category: 'security',
  },
  {
    id: 'dnk_scones_memory',
    name: 'DNK SCONES Memory',
    role: 'Cognitive Memory Engine',
    avatar: '🧠',
    description: 'Long-term Semantic Memory & Vector Knowledge Graph',
    color: '#8b5cf6',
    category: 'core',
  },
  {
    id: 'dnk_ui_builder',
    name: 'DNK UI Builder',
    role: 'Stitch 2.0 UI & Canvas Design',
    avatar: '🎨',
    description: 'Spatial Canvas UI & Design System Components',
    color: '#ec4899',
    category: 'dev',
  },
  {
    id: 'dnk_data_engineer',
    name: 'DNK Data Engineer',
    role: 'Data Engineering & Pipelines',
    avatar: '📊',
    description: 'Data Pipeline Transformations & Analytics',
    color: '#14b8a6',
    category: 'dev',
  },
  {
    id: 'dnk_content_humanizer',
    name: 'DNK Humanizer',
    role: 'Brand Copywriting & Humanization',
    avatar: '✍️',
    description: 'Copywriting & Content Humanization',
    color: '#f43f5e',
    category: 'growth',
  },
  {
    id: 'dnk_marketing_growth',
    name: 'DNK Growth Hack',
    role: 'Growth Hacking & Analytics',
    avatar: '🚀',
    description: 'Growth Experiments, Conversions & Marketing',
    color: '#eab308',
    category: 'growth',
  },
  {
    id: 'dnk_seo_optimizer',
    name: 'DNK SEO Engine',
    role: 'SEO & Search Optimization',
    avatar: '🔍',
    description: 'Search Engine Optimization & Meta Architecture',
    color: '#84cc16',
    category: 'growth',
  },
  {
    id: 'dnk_devops_infra',
    name: 'DNK DevOps Infra',
    role: 'Docker & Cloud Infrastructure',
    avatar: '🐳',
    description: 'Container Orchestration, CI/CD & Deployments',
    color: '#6366f1',
    category: 'dev',
  },
];

export async function dispatchTaskToSwarm(
  goal: string,
  targetAgentId: string = 'gerych_prime',
  context?: Record<string, unknown>
): Promise<SwarmDispatchResult> {
  return dispatchSwarmAgent({
    goal,
    target_agent: targetAgentId,
    context,
  });
}

export function connectSwarmFederationStream(
  sessionToken: string,
  onEvent: (event: MessageEvent) => void,
  onError?: (error: Event) => void
): EventSource {
  const url = getA2AFederationStreamUrl(sessionToken);
  const eventSource = new EventSource(url);
  eventSource.onmessage = onEvent;
  if (onError) {
    eventSource.onerror = onError;
  }
  return eventSource;
}
