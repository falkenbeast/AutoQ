import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import Topbar from '../components/Topbar';

export default function Layout() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#0B0F14] text-[#F1F5F9] flex">
      {/* Sidebar Navigation */}
      <Sidebar
        isCollapsed={isCollapsed}
        setIsCollapsed={setIsCollapsed}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
      />

      {/* Main Content Area */}
      <div
        className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ${
          isCollapsed ? 'md:ml-20' : 'md:ml-64'
        }`}
      >
        {/* Topbar */}
        <Topbar onMenuClick={() => setMobileOpen(true)} />

        {/* Page Content Outlet */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-[1600px] w-full mx-auto">
          <Outlet />
        </main>

        {/* Global Footer */}
        <footer className="border-t border-[#222E3E] bg-[#10151D] px-6 py-3 text-xs text-slate-400 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>AutoQ &bull; Automotive Quality Intelligence System &bull; Phase 2 UI</span>
          <span className="font-mono text-[11px] text-slate-400">Software-Only Architecture &bull; Final Year B.Tech CSE</span>
        </footer>
      </div>
    </div>
  );
}

