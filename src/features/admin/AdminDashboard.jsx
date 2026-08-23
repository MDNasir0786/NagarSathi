import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Users, Lock, FileText, Settings, ArrowRight } from 'lucide-react';
import { StatCard } from '../../components/ui/StatCard';
import { Button } from '../../components/ui/Button';

export default function AdminDashboard() {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-white rounded-3xl p-6 sm:p-8 shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="bg-red-500/20 text-red-400 border border-red-400/30 text-[11px] font-bold px-3 py-1 rounded-full uppercase tracking-wider">
            Privileged Console
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold mt-2">Smart Bhopal System Administration</h1>
          <p className="text-xs sm:text-sm text-slate-300 mt-1">Platform RBAC, User Management & Security Audit Stream</p>
        </div>

        <div className="flex items-center gap-2">
          <Button onClick={() => navigate('/admin/users')} size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
            Manage Users
          </Button>
          <Button onClick={() => navigate('/admin/audit-logs')} variant="outline" size="sm" className="bg-slate-800 text-white border-slate-600">
            Audit Stream
          </Button>
        </div>
      </div>

      {/* Admin KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Registered Users" value="14,250" icon={<Users className="w-5 h-5 text-blue-600" />} />
        <StatCard title="Active Roles" value="6 Roles" icon={<Shield className="w-5 h-5 text-purple-600" />} iconBgColor="bg-purple-50" />
        <StatCard title="Audit Events (24h)" value="1,890" icon={<FileText className="w-5 h-5 text-emerald-600" />} iconBgColor="bg-emerald-50" />
        <StatCard title="System Health" value="100% Operational" icon={<Settings className="w-5 h-5 text-amber-600" />} iconBgColor="bg-amber-50" />
      </div>

      {/* Quick Navigation Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div onClick={() => navigate('/admin/users')} className="bg-white border border-gray-200 hover:border-slate-800 rounded-2xl p-6 shadow-xs cursor-pointer transition-all">
          <Users className="w-6 h-6 text-slate-800 mb-2" />
          <h3 className="font-bold text-gray-900 text-sm">User Management</h3>
          <p className="text-xs text-gray-500 mt-1">Add, edit, deactivate accounts and reassign ward permissions.</p>
        </div>
        <div onClick={() => navigate('/admin/roles')} className="bg-white border border-gray-200 hover:border-slate-800 rounded-2xl p-6 shadow-xs cursor-pointer transition-all">
          <Shield className="w-6 h-6 text-slate-800 mb-2" />
          <h3 className="font-bold text-gray-900 text-sm">Role & Permissions Matrix</h3>
          <p className="text-xs text-gray-500 mt-1">Configure granular RBAC boundaries across all 6 production roles.</p>
        </div>
        <div onClick={() => navigate('/admin/audit-logs')} className="bg-white border border-gray-200 hover:border-slate-800 rounded-2xl p-6 shadow-xs cursor-pointer transition-all">
          <FileText className="w-6 h-6 text-slate-800 mb-2" />
          <h3 className="font-bold text-gray-900 text-sm">Security Audit Logs</h3>
          <p className="text-xs text-gray-500 mt-1">Real-time system event logging, IP tracking & security audits.</p>
        </div>
      </div>
    </div>
  );
}
