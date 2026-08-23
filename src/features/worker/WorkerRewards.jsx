import React from 'react';
import { Award, ShieldCheck, Star } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { StatCard } from '../../components/ui/StatCard';

export default function WorkerRewards() {
  const { user } = useAuthStore();

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-blue-700 to-indigo-800 text-white rounded-3xl p-6 sm:p-8 shadow-md">
        <h2 className="text-2xl font-extrabold">Worker Performance & Reward Incentives</h2>
        <p className="text-xs text-blue-100 mt-1">Earn performance bonuses for fast SLA resolution times</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard title="Incentive Points" value={user?.points || 820} icon={<Award className="w-5 h-5 text-amber-600" />} iconBgColor="bg-amber-50" />
        <StatCard title="Field Rating" value="4.9 / 5.0" icon={<Star className="w-5 h-5 text-yellow-600" />} iconBgColor="bg-yellow-50" />
        <StatCard title="Badge Tier" value="Field Star" icon={<ShieldCheck className="w-5 h-5 text-emerald-600" />} iconBgColor="bg-emerald-50" />
      </div>
    </div>
  );
}
