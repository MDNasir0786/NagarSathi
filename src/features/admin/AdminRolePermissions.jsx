import React from 'react';
import { ShieldCheck, Lock } from 'lucide-react';

const PERMISSIONS_MATRIX = [
  { feature: 'Register Complaints', citizen: true, worker: false, nodal: false, ngo: true, authority: false, admin: true },
  { feature: 'View Assigned Field Tasks', citizen: false, worker: true, nodal: true, ngo: false, authority: false, admin: true },
  { feature: 'Verify & Dispatched Tasks', citizen: false, worker: false, nodal: true, ngo: false, authority: true, admin: true },
  { feature: 'Adopt Community Wards', citizen: false, worker: false, nodal: false, ngo: true, authority: false, admin: true },
  { feature: 'City Governance Analytics', citizen: false, worker: false, nodal: false, ngo: false, authority: true, admin: true },
  { feature: 'User & System Administration', citizen: false, worker: false, nodal: false, ngo: false, authority: false, admin: true },
];

export default function AdminRolePermissions() {
  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs">
        <h2 className="text-xl font-bold text-gray-900">Role Permissions & RBAC Matrix</h2>
        <p className="text-xs text-gray-500">System authorization boundaries across Smart Bhopal user roles</p>
      </div>

      <div className="overflow-x-auto border border-gray-200 rounded-2xl bg-white shadow-xs">
        <table className="min-w-full divide-y divide-gray-200 text-xs">
          <thead className="bg-slate-900 text-white font-bold uppercase tracking-wider">
            <tr>
              <th className="px-4 py-3.5 text-left">Feature / Permission</th>
              <th className="px-3 py-3.5 text-center">Citizen</th>
              <th className="px-3 py-3.5 text-center">Worker</th>
              <th className="px-3 py-3.5 text-center">Nodal</th>
              <th className="px-3 py-3.5 text-center">NGO</th>
              <th className="px-3 py-3.5 text-center">Authority</th>
              <th className="px-3 py-3.5 text-center">Admin</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {PERMISSIONS_MATRIX.map((p, i) => (
              <tr key={i} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-semibold text-gray-900">{p.feature}</td>
                <td className="px-3 py-3 text-center">{p.citizen ? '✅' : '❌'}</td>
                <td className="px-3 py-3 text-center">{p.worker ? '✅' : '❌'}</td>
                <td className="px-3 py-3 text-center">{p.nodal ? '✅' : '❌'}</td>
                <td className="px-3 py-3 text-center">{p.ngo ? '✅' : '❌'}</td>
                <td className="px-3 py-3 text-center">{p.authority ? '✅' : '❌'}</td>
                <td className="px-3 py-3 text-center">{p.admin ? '✅' : '❌'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
