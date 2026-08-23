import React from 'react';
import { User, Mail, Phone, MapPin, Shield, Bell, Save } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { Button } from '../../components/ui/Button';

export default function CitizenProfile() {
  const { user } = useAuthStore();

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs flex items-center gap-4">
        <img
          src={user?.avatar || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80'}
          alt={user?.name}
          className="w-16 h-16 rounded-full object-cover border-2 border-emerald-500 shadow-xs"
        />
        <div>
          <h2 className="text-xl font-bold text-gray-900">{user?.name}</h2>
          <p className="text-xs text-gray-500">{user?.email}</p>
          <span className="mt-1 inline-block bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full">
            {user?.ward || 'Ward 48 - Arera Colony'}
          </span>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-4">
        <h3 className="font-bold text-gray-900 text-sm border-b border-gray-100 pb-3">Personal & Ward Information</h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Full Name</label>
            <input
              type="text"
              defaultValue={user?.name}
              className="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Phone Number</label>
            <input
              type="text"
              defaultValue={user?.phone || '+91 98930 12345'}
              className="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Email Address</label>
            <input
              type="email"
              defaultValue={user?.email}
              disabled
              className="w-full px-3 py-2 text-xs border border-gray-200 bg-gray-50 rounded-xl text-gray-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Assigned Ward</label>
            <input
              type="text"
              defaultValue={user?.ward || 'Ward 48 - Arera Colony'}
              className="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            />
          </div>
        </div>

        <div className="pt-4 border-t border-gray-100 flex justify-end">
          <Button leftIcon={<Save className="w-4 h-4" />}>Save Profile Updates</Button>
        </div>
      </div>
    </div>
  );
}
