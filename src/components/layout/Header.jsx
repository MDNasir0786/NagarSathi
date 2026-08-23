import React, { useState } from 'react';
import { Menu, Bell, Shield, LogOut, ChevronDown, UserCheck } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { useUIStore } from '../../stores/uiStore';
import { useNotificationStore } from '../../stores/notificationStore';
import { USER_ROLES } from '../../types';

export const Header = () => {
  const { user, role, setRole, logout } = useAuthStore();
  const { toggleSidebar } = useUIStore();
  const { notifications, toggleOpen: toggleNotifications } = useNotificationStore();
  const [profileOpen, setProfileOpen] = useState(false);
  const [roleMenuOpen, setRoleMenuOpen] = useState(false);

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-30 shadow-2xs">
      <div className="px-4 sm:px-6 py-3 flex items-center justify-between">
        {/* Left: Brand & Mobile Menu */}
        <div className="flex items-center gap-3">
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-100 lg:hidden focus:outline-none"
            aria-label="Toggle Mobile Menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 bg-emerald-600 text-white rounded-xl flex items-center justify-center font-extrabold text-sm shadow-sm">
              SB
            </div>
            <div>
              <h1 className="font-bold text-gray-900 leading-tight text-base sm:text-lg flex items-center gap-2">
                Smart Bhopal
                <span className="bg-emerald-100 text-emerald-800 text-[10px] uppercase font-bold px-2 py-0.5 rounded-full hidden sm:inline-block">
                  Civic-Tech
                </span>
              </h1>
              <p className="text-[10px] text-gray-500 font-medium hidden sm:block">AI Governance & Citizen Platform</p>
            </div>
          </div>
        </div>

        {/* Right Actions: Role Selector, Notifications, Profile */}
        <div className="flex items-center gap-3">
          {/* Quick Role Switcher for Testing */}
          <div className="relative">
            <button
              onClick={() => setRoleMenuOpen(!roleMenuOpen)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-800 text-xs font-semibold hover:bg-emerald-100 transition-colors"
            >
              <Shield className="w-3.5 h-3.5 text-emerald-600" />
              <span>{role.replace('_', ' ')}</span>
              <ChevronDown className="w-3 h-3 text-emerald-600" />
            </button>

            {roleMenuOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-xl shadow-lg py-1 z-50 text-xs">
                <div className="px-3 py-1.5 text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                  Switch Active Role
                </div>
                {Object.keys(USER_ROLES).map((r) => (
                  <button
                    key={r}
                    onClick={() => {
                      setRole(r);
                      setRoleMenuOpen(false);
                    }}
                    className={`w-full text-left px-3 py-2 flex items-center justify-between hover:bg-emerald-50 ${
                      role === r ? 'font-bold text-emerald-700 bg-emerald-50/60' : 'text-gray-700'
                    }`}
                  >
                    <span>{r.replace('_', ' ')}</span>
                    {role === r && <UserCheck className="w-3.5 h-3.5 text-emerald-600" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Notifications Center Toggle */}
          <button
            onClick={toggleNotifications}
            className="relative p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="View Notifications"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 w-4 h-4 bg-emerald-600 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                {unreadCount}
              </span>
            )}
          </button>

          {/* User Profile */}
          <div className="relative">
            <button
              onClick={() => setProfileOpen(!profileOpen)}
              className="flex items-center gap-2 p-1 rounded-full hover:bg-gray-100 transition-colors"
            >
              <img
                src={user?.avatar || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80'}
                alt={user?.name || 'User'}
                className="w-8 h-8 rounded-full object-cover border border-emerald-300"
              />
            </button>

            {profileOpen && (
              <div className="absolute right-0 mt-2 w-56 bg-white border border-gray-200 rounded-xl shadow-lg py-2 z-50 text-xs">
                <div className="px-4 py-2 border-b border-gray-100">
                  <p className="font-bold text-gray-900 text-sm">{user?.name}</p>
                  <p className="text-gray-500 text-[11px] truncate">{user?.email}</p>
                  <span className="mt-1 inline-block bg-emerald-100 text-emerald-800 font-semibold px-2 py-0.5 rounded text-[10px]">
                    {user?.ward || role}
                  </span>
                </div>
                <button
                  onClick={logout}
                  className="w-full text-left px-4 py-2 text-red-600 hover:bg-red-50 flex items-center gap-2 font-medium"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
