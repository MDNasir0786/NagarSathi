import React from 'react';
import { NavLink } from 'react-router-dom';
import { X, Shield } from 'lucide-react';
import { useUIStore } from '../../stores/uiStore';
import { useAuthStore } from '../../stores/authStore';
import { Sidebar } from './Sidebar';

export const MobileDrawer = () => {
  const { sidebarOpen, setSidebarOpen } = useUIStore();
  const { user, role } = useAuthStore();

  if (!sidebarOpen) return null;

  return (
    <div className="fixed inset-0 z-50 lg:hidden flex">
      {/* Backdrop */}
      <div
        onClick={() => setSidebarOpen(false)}
        className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs transition-opacity"
      />

      {/* Drawer panel */}
      <div className="relative bg-white w-72 max-w-full h-full shadow-2xl z-10 flex flex-col p-4">
        <div className="flex items-center justify-between pb-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-emerald-600 text-white rounded-lg flex items-center justify-center font-bold text-sm">
              SB
            </div>
            <div>
              <h2 className="font-bold text-gray-900 text-sm">Smart Bhopal</h2>
              <span className="bg-emerald-100 text-emerald-800 text-[9px] font-bold px-1.5 py-0.5 rounded">
                {role}
              </span>
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-2">
          {/* Re-use Sidebar link generator */}
          <div onClick={() => setSidebarOpen(false)}>
            <Sidebar />
          </div>
        </div>
      </div>
    </div>
  );
};
