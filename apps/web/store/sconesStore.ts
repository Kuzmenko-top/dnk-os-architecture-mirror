// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/store/sconesStore.ts"
// purpose: "SCONES Brain Persistent Brand DNA Store: Tenant isolation, Brand Attributes, and CapCut AI Studio Generation Parameters"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["TaskDNA-PHASE-2-LAUNCHPAD-ONBOARDING-FINAL"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---

import { create } from 'zustand';

export interface AIStudioParams {
  fluxParams: {
    promptModifiers: string[];
    lighting: string;
    aspectRatio: '9:16' | '16:9' | '1:1';
    seed?: number;
  };
  icLightParams: {
    lightSource: string;
    ambientColor: string;
    intensity: number;
  };
  birefNetParams: {
    autoMatting: boolean;
    foregroundIsolation: boolean;
  };
}

export interface BrandDNA {
  id: string;
  workspaceId: string;
  brandName: string;
  tagline: string;
  industry: string;
  targetAudience: string;
  toneOfVoice: 'bold_energetic' | 'premium_luxury' | 'clean_minimal' | 'tech_futuristic' | 'warm_approachable';
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    text: string;
  };
  typography: {
    headingFont: string;
    bodyFont: string;
  };
  usp: string[];
  competitors: string[];
  goals: string[];
  aiParams: AIStudioParams;
  createdAt: number;
  updatedAt: number;
}

export interface SconesStoreState {
  workspaceId: string;
  currentBrand: BrandDNA;
  savedBrands: Record<string, BrandDNA>;
  
  // Actions
  setWorkspaceId: (workspaceId: string) => void;
  updateBrand: (partial: Partial<BrandDNA>) => void;
  updateAIParams: (partialAI: Partial<AIStudioParams>) => void;
  saveBrandToVault: () => string;
  loadBrandFromVault: (brandId: string) => boolean;
  listBrands: () => BrandDNA[];
  generateFluxPrompt: (basePrompt: string) => string;
  exportSconesMemory: () => string;
  importSconesMemory: (jsonString: string) => boolean;
  resetBrand: () => void;
}

export const DEFAULT_BRAND_DNA: BrandDNA = {
  id: 'brand-reburn-default',
  workspaceId: 'ws-alpha-001',
  brandName: 'ReBurn Energy',
  tagline: 'Fuel the Fire Within',
  industry: 'Beverages & Biohacking',
  targetAudience: 'High-performance athletes, biohackers, and founders',
  toneOfVoice: 'bold_energetic',
  colors: {
    primary: '#10b981', // Emerald neon
    secondary: '#047857',
    accent: '#f59e0b', // Amber fire
    background: '#090d16',
    text: '#f8fafc',
  },
  typography: {
    headingFont: 'Cabinet Grotesk',
    bodyFont: 'Satoshi',
  },
  usp: [
    'Zero sugar, zero crash clean energy',
    'Natural adaptogens & nootropics formula',
    '3D anodized sustainable aluminum can packaging'
  ],
  competitors: ['Red Bull', 'Monster', 'GHOST Energy'],
  goals: [
    'Scale Shopify DTC subscription sales',
    'Produce viral 9:16 UGC video hooks with Remotion',
    'Automate omnichannel customer journeys'
  ],
  aiParams: {
    fluxParams: {
      promptModifiers: [
        'dramatic rim lighting',
        'subtle moisture condensation droplets',
        'commercial product photography',
        'octane render 8k',
        'photorealistic 85mm lens'
      ],
      lighting: 'neon rim light + soft studio key light',
      aspectRatio: '9:16',
    },
    icLightParams: {
      lightSource: 'top-right glowing spotlight',
      ambientColor: '#10b981',
      intensity: 0.85,
    },
    birefNetParams: {
      autoMatting: true,
      foregroundIsolation: true,
    },
  },
  createdAt: Date.now(),
  updatedAt: Date.now(),
};

export const useSconesStore = create<SconesStoreState>((set, get) => ({
  workspaceId: 'ws-alpha-001',
  currentBrand: { ...DEFAULT_BRAND_DNA },
  savedBrands: {
    [DEFAULT_BRAND_DNA.id]: { ...DEFAULT_BRAND_DNA }
  },

  setWorkspaceId: (workspaceId: string) => {
    set({ workspaceId });
  },

  updateBrand: (partial: Partial<BrandDNA>) => {
    set((state) => ({
      currentBrand: {
        ...state.currentBrand,
        ...partial,
        updatedAt: Date.now(),
      }
    }));
  },

  updateAIParams: (partialAI: Partial<AIStudioParams>) => {
    set((state) => ({
      currentBrand: {
        ...state.currentBrand,
        aiParams: {
          ...state.currentBrand.aiParams,
          ...partialAI,
        },
        updatedAt: Date.now(),
      }
    }));
  },

  saveBrandToVault: () => {
    const { currentBrand, savedBrands } = get();
    const id = currentBrand.id || `brand-${Date.now()}`;
    const brandToSave: BrandDNA = {
      ...currentBrand,
      id,
      updatedAt: Date.now(),
    };

    set({
      currentBrand: brandToSave,
      savedBrands: {
        ...savedBrands,
        [id]: brandToSave,
      }
    });

    return id;
  },

  loadBrandFromVault: (brandId: string) => {
    const { savedBrands } = get();
    const found = savedBrands[brandId];
    if (found) {
      set({ currentBrand: { ...found } });
      return true;
    }
    return false;
  },

  listBrands: () => {
    const { savedBrands, workspaceId } = get();
    return Object.values(savedBrands).filter((b) => b.workspaceId === workspaceId);
  },

  generateFluxPrompt: (basePrompt: string) => {
    const { currentBrand } = get();
    const modifiers = currentBrand.aiParams.fluxParams.promptModifiers.join(', ');
    const colors = `dominant palette ${currentBrand.colors.primary} and ${currentBrand.colors.accent}`;
    const lighting = currentBrand.aiParams.fluxParams.lighting;
    return `${basePrompt}, ${colors}, ${lighting}, ${modifiers}, style: ${currentBrand.toneOfVoice.replace('_', ' ')}`;
  },

  exportSconesMemory: () => {
    const { workspaceId, currentBrand, savedBrands } = get();
    return JSON.stringify({
      version: '1.0.0',
      workspaceId,
      currentBrand,
      savedBrands,
      exportedAt: Date.now(),
    }, null, 2);
  },

  importSconesMemory: (jsonString: string) => {
    try {
      const data = JSON.parse(jsonString);
      if (data && data.currentBrand && data.savedBrands) {
        set({
          workspaceId: data.workspaceId || get().workspaceId,
          currentBrand: data.currentBrand,
          savedBrands: data.savedBrands,
        });
        return true;
      }
      return false;
    } catch {
      return false;
    }
  },

  resetBrand: () => {
    const newBrand: BrandDNA = {
      ...DEFAULT_BRAND_DNA,
      id: `brand-${Date.now()}`,
      brandName: '',
      tagline: '',
      industry: '',
      targetAudience: '',
      usp: [],
      competitors: [],
      goals: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    set({ currentBrand: newBrand });
  },
}));
