import React from 'react';
import { Users, Phone, ShieldCheck, MapPin } from 'lucide-react';

const WORKERS_LIST = [
  { id: '1', name: 'Vikram Singh', department: 'Road Maintenance Wing', phone: '+91 94250 67890', ward: 'Ward 43', completed: 48, rating: 4.9, status: 'Active' },
  { id: '2', name: 'Ramesh Patel', department: 'Electrical & Lighting Cell', phone: '+91 98261 44556', ward: 'Ward 48', completed: 42, rating: 4.8, status: 'Active' },
  { id: '3', name: 'Sanjay Kumar', department: 'Jal Nigam & Hydraulics', phone: '+91 99264 55667', ward: 'Ward 52', completed: 39, rating: 4.7, status: 'Active' },
  { id: '4', name: 'Deepak Chouhan', department: 'Solid Waste Wing', phone: '+91 98933 11224', ward: 'Ward 12', completed: 35, rating: 4.6, status: 'On Leave' },
];

export default function NodalWorkers() {
  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs">
        <h2 className="text-xl font-bold text-gray-900">Field Worker Roster & Deployment</h2>
        <p className="text-xs text-gray-500">Monitor technician availability, contact info & resolution metrics</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {WORKERS_LIST.map((w) => (
          <div key={w.id} className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs flex items-center gap-4">
            <div className="w-12 h-12 bg-purple-100 text-purple-700 rounded-2xl flex items-center justify-center font-bold text-base shrink-0">
              {w.name[0]}
            </div>
            <div className="space-y-1 flex-1">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-gray-900 text-sm">{w.name}</h3>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${w.status === 'Active' ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-600'}`}>
                  {w.status}
                </span>
              </div>
              <p className="text-xs text-gray-500">{w.department}</p>
              <div className="flex items-center gap-3 text-[11px] text-gray-600 pt-1">
                <span>Phone: {w.phone}</span>
                <span>•</span>
                <span>Rating: ★ {w.rating}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
