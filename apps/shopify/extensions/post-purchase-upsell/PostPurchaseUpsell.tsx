// --- DNK-MRH-HEADER ---
# mrh_id: "apps/shopify/extensions/post-purchase-upsell/PostPurchaseUpsell.tsx"
# purpose: "Shopify Post-Purchase UI Extension component for 1-click order add-ons"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
// --- END DNK-MRH-HEADER ---

import React, { useState } from 'react';

export interface PostPurchaseOffer {
  id: string;
  title: string;
  description: string;
  originalPrice: number;
  discountedPrice: number;
  currency: string;
  variantId: string;
  imageUrl?: string;
  timerSeconds?: number;
}

export interface PostPurchaseUpsellProps {
  orderId: string;
  offer?: PostPurchaseOffer;
  onAcceptOffer?: (variantId: string) => Promise<{ success: boolean; updatedOrderId?: string }>;
  onDeclineOffer?: () => void;
}

export const PostPurchaseUpsell: React.FC<PostPurchaseUpsellProps> = ({
  orderId,
  offer = {
    id: 'offer_audio_case',
    title: 'DNK Cyber Armor Magnetic Storage Case',
    description: 'Exclusive 1-click addition to your completed order. No extra shipping fees!',
    originalPrice: 39.99,
    discountedPrice: 19.99,
    currency: 'USD',
    variantId: 'var_cyber_armor_001',
    timerSeconds: 180,
  },
  onAcceptOffer,
  onDeclineOffer,
}) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [isAccepted, setIsAccepted] = useState(false);

  const discountPercent = Math.round(
    ((offer.originalPrice - offer.discountedPrice) / offer.originalPrice) * 100
  );

  const handleAccept = async () => {
    setIsProcessing(true);
    try {
      if (onAcceptOffer) {
        const res = await onAcceptOffer(offer.variantId);
        if (res.success) {
          setIsAccepted(true);
        }
      } else {
        setIsAccepted(true);
      }
    } finally {
      setIsProcessing(false);
    }
  };

  if (isAccepted) {
    return (
      <div className="p-6 bg-emerald-950/50 border border-emerald-500/40 rounded-2xl text-center text-emerald-200">
        <h2 className="text-xl font-bold text-white mb-2">🎉 Item Added Successfully!</h2>
        <p className="text-sm">We've added <strong>{offer.title}</strong> directly to order #{orderId}.</p>
      </div>
    );
  }

  return (
    <div className="p-6 bg-slate-900 border border-amber-500/40 rounded-2xl text-slate-100 max-w-lg mx-auto shadow-2xl">
      <div className="flex items-center justify-between mb-4">
        <span className="px-3 py-1 bg-amber-500/20 text-amber-300 text-xs font-extrabold uppercase rounded-full border border-amber-500/30">
          ⚡ Limited Time Special Offer ({discountPercent}% OFF)
        </span>
        <span className="text-xs font-mono text-slate-400">Order #{orderId}</span>
      </div>

      <h2 className="text-xl font-black text-white mb-2">{offer.title}</h2>
      <p className="text-sm text-slate-300 mb-4">{offer.description}</p>

      <div className="flex items-baseline gap-3 mb-6">
        <span className="text-2xl font-black text-emerald-400">${offer.discountedPrice.toFixed(2)} {offer.currency}</span>
        <span className="text-sm text-slate-500 line-through">${offer.originalPrice.toFixed(2)}</span>
      </div>

      <div className="flex flex-col gap-3">
        <button
          onClick={handleAccept}
          disabled={isProcessing}
          className="w-full py-3 px-4 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-black text-sm rounded-xl transition-all duration-200 shadow-lg cursor-pointer disabled:opacity-50"
        >
          {isProcessing ? 'Processing 1-Click Order...' : `Pay $${offer.discountedPrice.toFixed(2)} with 1-Click`}
        </button>
        <button
          onClick={onDeclineOffer}
          disabled={isProcessing}
          className="text-xs text-slate-500 hover:text-slate-400 underline font-medium transition-colors"
        >
          No thanks, continue to order confirmation
        </button>
      </div>
    </div>
  );
};

export default PostPurchaseUpsell;
