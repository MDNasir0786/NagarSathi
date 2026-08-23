import React from 'react';
import { Users, Award, ShieldCheck } from 'lucide-react';
import { StatCard } from '../../components/ui/StatCard';

export default function AuthorityNGOPerformance() {
  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs">
        <h2 className="text-xl font-bold text-gray-900">NGO Partner Performance & Audits</h2>
        <p className="text-xs text-gray-500">Track community partner ward adoption and drive success metrics</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard title="Active Partner NGOs" value="12" icon={<Users className="w-5 h-5 text-teal-600" />} iconBgColor="bg-teal-50" />
        <StatCard title="Wards Covered" value="45 / 85" icon={<ShieldCheck className="w-5 h-5 text-emerald-600" />} iconBgColor="bg-emerald-50" />
        <StatCard title="Volunteers Active" value="1,240" icon={<Award className="w-5 h-5 text-amber-600" />} iconBgColor="bg-amber-50" />
      </div>
    </div>
  );
}
