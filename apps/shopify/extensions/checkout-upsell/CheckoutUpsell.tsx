// --- DNK-MRH-HEADER ---
# mrh_id: "apps/shopify/extensions/checkout-upsell/CheckoutUpsell.tsx"
# purpose: "Shopify Checkout UI Extension component for dynamic upsell & threshold offers"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
// --- END DNK-MRH-HEADER ---

import React, { useMemo } from 'react';

export interface CartLineCost {
  totalAmount: {
    amount: string | number;
    currencyCode?: string;
  };
}

export interface CartLine {
  id: string;
  cost: CartLineCost;
  merchandise?: {
    id: string;
    title: string;
  };
}

export interface CheckoutUpsellProps {
  cartLines: CartLine[];
  freeShippingThreshold?: number;
  recommendedProduct?: {
    id: string;
    title: string;
    price: number;
    currency: string;
    imageUrl?: string;
  };
  onAddUpsell?: (productId: string) => Promise<void>;
}

export const CheckoutUpsell: React.FC<CheckoutUpsellProps> = ({
  cartLines,
  freeShippingThreshold = 100,
  recommendedProduct = {
    id: 'prod_upsell_premium_care',
    title: 'DNK Premium Care & Express Warranty',
    price: 19.99,
    currency: 'USD',
  },
  onAddUpsell,
}) => {
  const currentTotal = useMemo(() => {
    return cartLines.reduce((sum, line) => {
      const amount = typeof line.cost.totalAmount.amount === 'string' 
        ? parseFloat(line.cost.totalAmount.amount) 
        : line.cost.totalAmount.amount;
      return sum + (isNaN(amount) ? 0 : amount);
    }, 0);
  }, [cartLines]);

  const shouldShow = currentTotal > 0 && currentTotal < freeShippingThreshold;
  const remaining = Math.max(0, freeShippingThreshold - currentTotal);

  if (!shouldShow) {
    return null;
  }

  return (
    <div className="p-4 my-3 bg-gradient-to-r from-emerald-950/40 to-cyan-950/40 border border-emerald-500/30 rounded-xl text-emerald-100 font-sans shadow-lg">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs uppercase font-bold tracking-wider text-emerald-400">✨ Free Shipping Threshold</span>
        <span className="text-xs font-semibold text-emerald-300">Remaining: ${remaining.toFixed(2)}</span>
      </div>
      <p className="text-sm text-slate-200 mb-3 font-medium">
        Add ${(remaining).toFixed(2)} more to your cart to qualify for <strong>FREE Priority Delivery</strong>!
      </p>
      {recommendedProduct && (
        <div className="flex items-center justify-between bg-slate-900/60 p-3 rounded-lg border border-slate-700/50">
          <div>
            <p className="text-sm font-semibold text-white">{recommendedProduct.title}</p>
            <p className="text-xs text-emerald-400 font-bold">${recommendedProduct.price.toFixed(2)} {recommendedProduct.currency}</p>
          </div>
          <button
            onClick={() => onAddUpsell?.(recommendedProduct.id)}
            className="px-3 py-1.5 text-xs font-bold text-slate-950 bg-emerald-400 hover:bg-emerald-300 rounded-md transition-all duration-200 cursor-pointer shadow-md"
          >
            + Add to Order
          </button>
        </div>
      )}
    </div>
  );
};

export default CheckoutUpsell;
