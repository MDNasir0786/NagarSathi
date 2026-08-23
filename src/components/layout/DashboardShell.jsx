import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { MobileDrawer } from './MobileDrawer';
import { NotificationCenter } from './NotificationCenter';
import { ErrorBoundary } from '../feedback/ErrorBoundary';

export const DashboardShell = () => {
  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-[#F5F7FA] flex flex-col font-sans">
        <Header />
        <div className="flex flex-1">
          <Sidebar />
          <MobileDrawer />
          <NotificationCenter />
          <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto max-w-7xl mx-auto w-full">
            <Outlet />
          </main>
        </div>
      </div>
    </ErrorBoundary>
  );
};
