import React from 'react';
import { Gift, HeartHandshake, ShieldCheck } from 'lucide-react';
import { Button } from '../../components/ui/Button';

export default function NGODonations() {
  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs">
        <h2 className="text-xl font-bold text-gray-900">Civic Sponsorship & Equipment Donations</h2>
        <p className="text-xs text-gray-500">Corporate CSR & public donations for ward cleanliness tools and saplings</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs space-y-2">
          <Gift className="w-6 h-6 text-teal-600" />
          <h3 className="font-bold text-gray-900 text-sm">Shahpura Bio-Shield Plantation Fund</h3>
          <p className="text-xs text-gray-500">Raised: ₹45,000 / ₹50,000 target for 500 Neem saplings</p>
          <Button size="sm" className="mt-2">Contribute Equipment / Funds</Button>
        </div>
      </div>
    </div>
  );
}
