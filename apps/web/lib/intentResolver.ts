// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/lib/intentResolver.ts"
// purpose: "Swarm AI Co-Pilot Intent Resolver: Classifies user prompt, maps to specialized agent, determines target nodes & evaluates budget"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["TaskDNA-PHASE-3-INTENT-RESOLVER"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-03"
// author: "DNK-e.com Maksym & Gerych"
// license: "DNK-INTERNAL"
// --- END DNK-MRH-HEADER ---

import { budgetGuard, CostEstimate } from './budgetGuard';

export type SwarmAgentId =
  | 'gerych_prime'
  | 'gerych_builder'
  | 'dnk_shopify'
  | 'dnk_video_ai_creator'
  | 'dnk_dev_fullstack'
  | 'gerych_researcher'
  | 'gerych_auditor'
  | 'dnk_security_guard';

export type IntentActionType =
  | 'generate'
  | 'expand'
  | 'reskin'
  | 'liquid'
  | 'storyboard'
  | 'audit'
  | 'translate';

export interface IntentResolutionContext {
  selectedNodeIds: string[];
  selectedNodeType?: string;
  selectedNodeTitle?: string;
  brandContext?: {
    brandName?: string;
    tone?: string;
  };
}

export interface IntentResult {
  agent: SwarmAgentId;
  agentLabel: string;
  agentAvatar: string;
  action: IntentActionType;
  actionLabel: string;
  targetNodeIds: string[];
  budget: CostEstimate;
  enrichedPrompt: string;
  suggestedPatch: Record<string, any>;
}

export const AGENT_META: Record<
  SwarmAgentId,
  { label: string; avatar: string; color: string }
> = {
  gerych_prime: { label: 'Gerych Prime', avatar: '🧬', color: '#8b5cf6' },
  gerych_builder: { label: 'Gerych Builder', avatar: '🛠️', color: '#3b82f6' },
  dnk_shopify: { label: 'DNK Shopify', avatar: '🛍️', color: '#9333ea' },
  dnk_video_ai_creator: { label: 'DNK Video Creator', avatar: '🎬', color: '#f59e0b' },
  dnk_dev_fullstack: { label: 'DNK Fullstack', avatar: '⚡', color: '#06b6d4' },
  gerych_researcher: { label: 'Gerych Researcher', avatar: '🔬', color: '#3b82f6' },
  gerych_auditor: { label: 'Gerych Auditor', avatar: '🛡️', color: '#10b981' },
  dnk_security_guard: { label: 'DNK Security Guard', avatar: '🚨', color: '#ef4444' },
};

export const ACTION_LABELS: Record<IntentActionType, string> = {
  generate: '⚡ Згенерувати',
  expand: '📖 Розгорнути деталі',
  reskin: '🎨 Рескінінг (Brand DNA)',
  liquid: '🛒 Транспіляція в Liquid',
  storyboard: '🎬 Генерація розкадровки',
  audit: '🛡️ Аудит безпеки та коду',
  translate: '🌐 Переклад / Локалізація',
};

export const intentResolver = {
  detectKeywords(prompt: string): string[] {
    const raw = (prompt || '').toLowerCase();
    const keywords: string[] = [];

    if (raw.includes('shopify') || raw.includes('liquid') || raw.includes('store') || raw.includes('магазин') || raw.includes('секці')) {
      keywords.push('shopify', 'liquid');
    }
    if (raw.includes('video') || raw.includes('відео') || raw.includes('storyboard') || raw.includes('розкадровк') || raw.includes('remotion') || raw.includes('tiktok') || raw.includes('reels')) {
      keywords.push('video', 'storyboard');
    }
    if (raw.includes('api') || raw.includes('fastapi') || raw.includes('endpoint') || raw.includes('backend') || raw.includes('бекенд') || raw.includes('база')) {
      keywords.push('backend', 'api');
    }
    if (raw.includes('research') || raw.includes('аналіз') || raw.includes('дослідження') || raw.includes('competitor') || raw.includes('конкурент')) {
      keywords.push('research');
    }
    if (raw.includes('audit') || raw.includes('аудит') || raw.includes('перевірк') || raw.includes('verify') || raw.includes('security') || raw.includes('безпек')) {
      keywords.push('audit');
    }
    if (raw.includes('дизайн') || raw.includes('design') || raw.includes('стиль') || raw.includes('колір') || raw.includes('рескін') || raw.includes('reskin')) {
      keywords.push('reskin');
    }
    if (raw.includes('детал') || raw.includes('expand') || raw.includes('розгорн') || raw.includes('поглиб')) {
      keywords.push('expand');
    }

    return keywords;
  },

  detectAction(prompt: string, forcedAction?: IntentActionType): IntentActionType {
    if (forcedAction) return forcedAction;

    const raw = (prompt || '').toLowerCase();
    if (raw.includes('liquid') || raw.includes('shopify')) return 'liquid';
    if (raw.includes('розкадровк') || raw.includes('storyboard') || raw.includes('відео') || raw.includes('video')) return 'storyboard';
    if (raw.includes('аудит') || raw.includes('audit') || raw.includes('перевір')) return 'audit';
    if (raw.includes('рескін') || raw.includes('reskin') || raw.includes('стиль') || raw.includes('колір')) return 'reskin';
    if (raw.includes('розгорн') || raw.includes('expand') || raw.includes('детал')) return 'expand';
    if (raw.includes('переклад') || raw.includes('локаліз') || raw.includes('translate')) return 'translate';

    return 'generate';
  },

  detectAgent(
    keywords: string[],
    action: IntentActionType,
    nodeType?: string
  ): SwarmAgentId {
    if (action === 'liquid' || keywords.includes('shopify') || nodeType === 'ShopifyBuilderNode') {
      return 'dnk_shopify';
    }
    if (action === 'storyboard' || keywords.includes('video') || nodeType === 'VideoStoryboardNoteNode') {
      return 'dnk_video_ai_creator';
    }
    if (action === 'audit' || keywords.includes('audit')) {
      return 'gerych_auditor';
    }
    if (keywords.includes('backend') || keywords.includes('api') || nodeType === 'ApiDocsCodeNode') {
      return 'dnk_dev_fullstack';
    }
    if (keywords.includes('research') || nodeType === 'MarketResearchNode') {
      return 'gerych_researcher';
    }
    return 'gerych_builder';
  },

  resolve(
    prompt: string,
    context: IntentResolutionContext,
    forcedAction?: IntentActionType
  ): IntentResult {
    const keywords = this.detectKeywords(prompt);
    const action = this.detectAction(prompt, forcedAction);
    const agent = this.detectAgent(keywords, action, context.selectedNodeType);
    const budget = budgetGuard.getEstimate(agent, action, prompt);

    const brandPrefix = context.brandContext?.brandName
      ? `[Brand: ${context.brandContext.brandName}] `
      : '';
    const enrichedPrompt = `${brandPrefix}${prompt.trim()}`;

    // Synthesize suggested patch based on action and agent
    let suggestedPatch: Record<string, any> = {};
    if (action === 'expand') {
      suggestedPatch = {
        badge: 'Expanded with AI ✨',
        lastAiAction: action,
        aiGeneratedAt: new Date().toISOString(),
      };
    } else if (action === 'reskin') {
      suggestedPatch = {
        badge: 'Reskinned to Brand DNA 🎨',
        lastAiAction: action,
        aiGeneratedAt: new Date().toISOString(),
      };
    } else if (action === 'liquid') {
      suggestedPatch = {
        badge: 'Liquid Transpiled 🛍️',
        lastAiAction: action,
        liquidReady: true,
      };
    } else if (action === 'storyboard') {
      suggestedPatch = {
        badge: 'Storyboard Generated 🎬',
        lastAiAction: action,
        storyboardReady: true,
      };
    } else if (action === 'audit') {
      suggestedPatch = {
        badge: 'Audited & Verified 🛡️',
        lastAiAction: action,
        auditPassed: true,
      };
    } else {
      suggestedPatch = {
        badge: 'AI Generated ⚡',
        lastAiAction: action,
        aiGeneratedAt: new Date().toISOString(),
      };
    }

    return {
      agent,
      agentLabel: AGENT_META[agent].label,
      agentAvatar: AGENT_META[agent].avatar,
      action,
      actionLabel: ACTION_LABELS[action],
      targetNodeIds: context.selectedNodeIds,
      budget,
      enrichedPrompt,
      suggestedPatch,
    };
  },
};
