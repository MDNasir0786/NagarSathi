import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  PlusCircle, 
  FileText, 
  Award, 
  History, 
  UserCheck, 
  CheckSquare, 
  MapPin, 
  Users, 
  BarChart3, 
  ShieldAlert, 
  Settings, 
  HelpCircle,
  Calendar,
  Gift
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';

export const Sidebar = () => {
  const { role } = useAuthStore();

  const getRoleLinks = () => {
    switch (role) {
      case 'CITIZEN':
        return [
          { to: '/citizen/dashboard', label: 'Dashboard', icon: LayoutDashboard },
          { to: '/citizen/complaints/new', label: 'Register Complaint', icon: PlusCircle },
          { to: '/citizen/complaints', label: 'Track Complaint', icon: FileText },
          { to: '/citizen/history', label: 'Complaint History', icon: History },
          { to: '/citizen/rewards', label: 'Rewards & Badges', icon: Award },
          { to: '/citizen/profile', label: 'My Profile', icon: UserCheck },
          { to: '/help', label: 'Help & Support', icon: HelpCircle },
        ];

      case 'WORKER':
        return [
          { to: '/worker/dashboard', label: 'Worker Dashboard', icon: LayoutDashboard },
          { to: '/worker/tasks', label: 'Assigned Tasks', icon: CheckSquare },
          { to: '/worker/completed', label: 'Completed Tasks', icon: FileText },
          { to: '/worker/rewards', label: 'My Reward Points', icon: Award },
          { to: '/worker/profile', label: 'Profile & Ward', icon: UserCheck },
          { to: '/help', label: 'Support Desk', icon: HelpCircle },
        ];

      case 'NODAL_OFFICER':
        return [
          { to: '/nodal/dashboard', label: 'Nodal Overview', icon: LayoutDashboard },
          { to: '/nodal/requests', label: 'Complaint Verification', icon: FileText },
          { to: '/nodal/assignments', label: 'Worker Assignment', icon: Users },
          { to: '/nodal/workers', label: 'Field Staff Roster', icon: UserCheck },
          { to: '/nodal/reports', label: 'Ward Reports', icon: BarChart3 },
          { to: '/help', label: 'Officer Support', icon: HelpCircle },
        ];

      case 'NGO':
        return [
          { to: '/ngo/dashboard', label: 'NGO Dashboard', icon: LayoutDashboard },
          { to: '/ngo/areas', label: 'Assigned Wards', icon: MapPin },
          { to: '/ngo/complaints', label: 'Community Complaints', icon: FileText },
          { to: '/ngo/volunteers', label: 'Volunteer Roster', icon: Users },
          { to: '/ngo/events', label: 'Community Drives', icon: Calendar },
          { to: '/ngo/donations', label: 'Donations & Support', icon: Gift },
          { to: '/help', label: 'Support', icon: HelpCircle },
        ];

      case 'HIGHER_AUTHORITY':
        return [
          { to: '/authority/dashboard', label: 'Executive Dashboard', icon: LayoutDashboard },
          { to: '/authority/analytics', label: 'City Analytics', icon: BarChart3 },
          { to: '/authority/escalations', label: 'Escalation Desk', icon: ShieldAlert },
          { to: '/authority/ngo-performance', label: 'NGO Performance', icon: Users },
          { to: '/authority/worker-performance', label: 'Worker Performance', icon: UserCheck },
          { to: '/help', label: 'Help', icon: HelpCircle },
        ];

      case 'SUPER_ADMIN':
        return [
          { to: '/admin/dashboard', label: 'Admin Dashboard', icon: LayoutDashboard },
          { to: '/admin/users', label: 'User Management', icon: Users },
          { to: '/admin/roles', label: 'Role Permissions', icon: ShieldAlert },
          { to: '/admin/audit-logs', label: 'Audit Logs', icon: FileText },
          { to: '/admin/settings', label: 'Platform Settings', icon: Settings },
          { to: '/help', label: 'Help', icon: HelpCircle },
        ];

      default:
        return [];
    }
  };

  const links = getRoleLinks();

  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-[calc(100vh-61px)] hidden lg:block py-4 px-3 shrink-0">
      <div className="mb-4 px-3">
        <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">Navigation</span>
      </div>
      <nav className="space-y-1">
        {links.map((link) => {
          const Icon = link.icon;
          return (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all duration-200 ${
                  isActive
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'text-gray-700 hover:bg-emerald-50 hover:text-emerald-800'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{link.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
};
