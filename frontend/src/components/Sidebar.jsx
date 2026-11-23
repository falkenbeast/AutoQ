import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  ClipboardList,
  Cpu,
  Microscope,
  BarChart3,
  FileText,
  Settings,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  X,
} from 'lucide-react';

export default function Sidebar({
  isCollapsed,
  setIsCollapsed,
  mobileOpen,
  setMobileOpen,
}) {
  const navItems = [
    { name: 'Overview', path: '/', icon: LayoutDashboard },
    { name: 'Inspections', path: '/inspections', icon: ClipboardList },
    { name: 'Defect Prediction', path: '/prediction', icon: Cpu },
    { name: 'Defect Analysis', path: '/analysis', icon: Microscope },
    { name: 'Quality Analytics', path: '/analytics', icon: BarChart3 },
    { name: 'Reports', path: '/reports', icon: FileText },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 bg-[#10151D] border-r border-[#222E3E] transition-all duration-300 flex flex-col justify-between ${
          mobileOpen ? 'translate-x-0 w-64' : '-translate-x-full md:translate-x-0'
        } ${isCollapsed ? 'md:w-20' : 'md:w-64'}`}
      >
        {/* Brand Header */}
        <div>
          <div className="h-16 flex items-center justify-between px-4 border-b border-[#222E3E]">
            <div className="flex items-center space-x-3 overflow-hidden">
              <div className="w-9 h-9 rounded-lg bg-blue-600/90 border border-blue-400/30 flex items-center justify-center flex-shrink-0 shadow-lg shadow-blue-500/20">
                <ShieldCheck className="w-5 h-5 text-white" />
              </div>
              {(!isCollapsed || mobileOpen) && (
                <div className="flex flex-col">
                  <span className="font-extrabold text-base text-[#F1F5F9] tracking-tight">
                    AutoQ
                  </span>
                  <span className="text-[10px] text-blue-400 font-semibold uppercase tracking-wider -mt-0.5">
                    Automotive Intelligence
                  </span>
                </div>
              )}
            </div>

            {/* Mobile close button */}
            <button
              type="button"
              onClick={() => setMobileOpen(false)}
              className="md:hidden text-slate-400 hover:text-white p-1 rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1.5 mt-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center px-3 py-2.5 rounded-lg text-xs font-medium transition-all group relative ${
                      isActive
                        ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-sm'
                        : 'text-slate-400 hover:text-slate-100 hover:bg-[#151C26]'
                    } ${isCollapsed && !mobileOpen ? 'justify-center' : 'space-x-3'}`
                  }
                  title={isCollapsed && !mobileOpen ? item.name : undefined}
                >
                  {({ isActive }) => (
                    <>
                      <Icon
                        className={`w-4 h-4 flex-shrink-0 transition-colors ${
                          isActive
                            ? 'text-blue-400'
                            : 'text-slate-400 group-hover:text-slate-200'
                        }`}
                      />
                      {(!isCollapsed || mobileOpen) && (
                        <span className="truncate">{item.name}</span>
                      )}
                      {/* Active indicator bar */}
                      {isActive && (
                        <span className="absolute left-0 top-1.5 bottom-1.5 w-1 bg-blue-500 rounded-r-full" />
                      )}
                    </>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Bottom Section: Settings & Collapse Toggle */}
        <div className="p-3 border-t border-[#222E3E] space-y-2">
          <NavLink
            to="/settings"
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) =>
              `flex items-center px-3 py-2.5 rounded-lg text-xs font-medium transition-all group relative ${
                isActive
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-[#151C26]'
              } ${isCollapsed && !mobileOpen ? 'justify-center' : 'space-x-3'}`
            }
            title={isCollapsed && !mobileOpen ? 'Settings' : undefined}
          >
            {({ isActive }) => (
              <>
                <Settings
                  className={`w-4 h-4 flex-shrink-0 transition-colors ${
                    isActive
                      ? 'text-blue-400'
                      : 'text-slate-400 group-hover:text-slate-200'
                  }`}
                />
                {(!isCollapsed || mobileOpen) && (
                  <span className="truncate">Settings</span>
                )}
                {isActive && (
                  <span className="absolute left-0 top-1.5 bottom-1.5 w-1 bg-blue-500 rounded-r-full" />
                )}
              </>
            )}
          </NavLink>

          {/* Desktop collapse button */}
          <div className="hidden md:flex justify-end pt-1">
            <button
              type="button"
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-1.5 w-full rounded-lg text-slate-400 hover:text-slate-200 hover:bg-[#151C26] transition-colors flex items-center justify-center text-xs"
              title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {isCollapsed ? (
                <ChevronRight className="w-4 h-4" />
              ) : (
                <div className="flex items-center space-x-2">
                  <ChevronLeft className="w-4 h-4" />
                  <span className="text-[11px] font-medium">Collapse</span>
                </div>
              )}
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}

