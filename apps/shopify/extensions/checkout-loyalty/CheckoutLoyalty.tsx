// --- DNK-MRH-HEADER ---
# mrh_id: "apps/shopify/extensions/checkout-loyalty/CheckoutLoyalty.tsx"
# purpose: "Shopify Checkout UI Extension component for customer loyalty points redemption"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
// --- END DNK-MRH-HEADER ---

import React, { useState } from 'react';

export interface CheckoutLoyaltyProps {
  customerId?: string;
  customerName?: string;
  availablePoints?: number;
  conversionRate?: number; // e.g. 10 points = $1.00 => rate = 0.1
  appliedPoints?: number;
  onApplyPoints?: (points: number) => Promise<{ success: boolean; discountAmount: number }>;
}

export const CheckoutLoyalty: React.FC<CheckoutLoyaltyProps> = ({
  customerId = 'cust_anon',
  customerName = 'Valued Customer',
  availablePoints = 250,
  conversionRate = 0.1,
  appliedPoints = 0,
  onApplyPoints,
}) => {
  const [pointsInput, setPointsInput] = useState<number>(Math.min(100, availablePoints));
  const [isApplying, setIsApplying] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const discountEquivalent = (pointsInput * conversionRate).toFixed(2);

  const handleApply = async () => {
    if (pointsInput <= 0 || pointsInput > availablePoints) return;
    setIsApplying(true);
    try {
      if (onApplyPoints) {
        const res = await onApplyPoints(pointsInput);
        if (res.success) {
          setStatusMessage(`Applied ${pointsInput} points (-$${res.discountAmount.toFixed(2)})!`);
        }
      } else {
        setStatusMessage(`Applied ${pointsInput} points (-$${discountEquivalent})!`);
      }
    } catch {
      setStatusMessage('Failed to apply loyalty points. Please try again.');
    } finally {
      setIsApplying(false);
    }
  };

  if (!availablePoints || availablePoints <= 0) {
    return null;
  }

  return (
    <div className="p-4 my-3 bg-gradient-to-r from-purple-950/40 to-indigo-950/40 border border-purple-500/30 rounded-xl text-purple-100 font-sans shadow-lg">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs uppercase font-bold tracking-wider text-purple-400">🎁 DNK Rewards & Loyalty</span>
        <span className="text-xs font-semibold text-purple-300">Balance: {availablePoints} pts</span>
      </div>
      <p className="text-sm text-slate-200 mb-3 font-medium">
        Redeem your loyalty points directly on this order for instant savings!
      </p>
      <div className="flex items-center gap-2">
        <input
          type="number"
          min="1"
          max={availablePoints}
          value={pointsInput}
          onChange={(e) => setPointsInput(Math.min(availablePoints, Math.max(0, parseInt(e.target.value) || 0)))}
          className="w-24 px-3 py-1.5 bg-slate-900/80 border border-purple-500/40 rounded-lg text-white text-sm font-semibold focus:outline-none focus:border-purple-400"
        />
        <button
          onClick={handleApply}
          disabled={isApplying || pointsInput <= 0}
          className="px-4 py-1.5 text-xs font-bold text-white bg-purple-600 hover:bg-purple-500 disabled:opacity-50 rounded-lg transition-all duration-200 cursor-pointer shadow-md"
        >
          {isApplying ? 'Applying...' : `Redeem ($${discountEquivalent} OFF)`}
        </button>
      </div>
      {statusMessage && (
        <p className="mt-2 text-xs font-semibold text-purple-300 animate-fadeIn">{statusMessage}</p>
      )}
    </div>
  );
};

export default CheckoutLoyalty;
