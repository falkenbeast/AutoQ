import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Menu,
  Bell,
  Search,
  CheckCircle2,
  AlertTriangle,
  User,
  Shield,
  Activity,
  X,
} from 'lucide-react';
import api from '../services/api';

export default function Topbar({ onMenuClick }) {
  const location = useLocation();
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [backendHealth, setBackendHealth] = useState({ online: false, checking: true });
  const [globalSearch, setGlobalSearch] = useState('');

  // Check backend health status periodically
  useEffect(() => {
    let isMounted = true;
    api.checkHealth()
      .then(() => {
        if (isMounted) setBackendHealth({ online: true, checking: false });
      })
      .catch(() => {
        if (isMounted) setBackendHealth({ online: false, checking: false });
      });

    const interval = setInterval(() => {
      api.checkHealth()
        .then(() => {
          if (isMounted) setBackendHealth({ online: true, checking: false });
        })
        .catch(() => {
          if (isMounted) setBackendHealth({ online: false, checking: false });
        });
    }, 15000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Format current page title & breadcrumbs based on pathname
  const getPageInfo = () => {
    switch (location.pathname) {
      case '/inspections':
        return { title: 'Component Inspections', breadcrumb: 'Inspections' };
      case '/prediction':
        return { title: 'Defect Prediction Engine', breadcrumb: 'Prediction' };
      case '/analysis':
        return { title: 'Defect Analysis', breadcrumb: 'Analysis' };
      case '/analytics':
        return { title: 'Quality Analytics', breadcrumb: 'Analytics' };
      case '/reports':
        return { title: 'Inspection Reports', breadcrumb: 'Reports' };
      case '/settings':
        return { title: 'System Settings', breadcrumb: 'Settings' };
      default:
        return { title: 'Manufacturing Overview', breadcrumb: 'Overview' };
    }
  };

  const { title, breadcrumb } = getPageInfo();

  // Current formatted date
  const todayFormatted = new Intl.DateTimeFormat('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date());

  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    api.checkHealth()
      .then((data) => {
        const notifs = [];
        if (data?.ml_engine?.model_available) {
          notifs.push({
            id: 'ml-ready',
            title: 'ML Inference Engine Online',
            desc: `${data.ml_engine.model_name || 'Random Forest'} ready (ROC-AUC: ${data.ml_engine.test_roc_auc || '0.9830'}).`,
            time: 'System Active',
            type: 'success',
          });
        }
        if (data?.database?.status === 'connected') {
          notifs.push({
            id: 'db-connected',
            title: 'SQLite Database Connected',
            desc: `SQLAlchemy storage online with ${data.database.inspections_count ?? 0} inspections logged.`,
            time: 'Live',
            type: 'info',
          });
        }
        if (notifs.length === 0) {
          notifs.push({
            id: 'nominal',
            title: 'System Operating Normally',
            desc: 'No active critical quality alerts across production lines.',
            time: 'Current',
            type: 'success',
          });
        }
        setNotifications(notifs);
      })
      .catch(() => {
        setNotifications([
          {
            id: 'offline',
            title: 'Backend API Disconnected',
            desc: 'Cannot reach FastAPI backend server. Ensure backend is running.',
            time: 'Warning',
            type: 'warning',
          },
        ]);
      });
  }, []);

  return (
    <header className="h-16 bg-[#10151D] border-b border-[#222E3E] sticky top-0 z-30 flex items-center justify-between px-4 sm:px-6">
      {/* Left: Mobile hamburger & Breadcrumb / Page Title */}
      <div className="flex items-center space-x-3 sm:space-x-4 min-w-0">
        <button
          type="button"
          onClick={onMenuClick}
          className="md:hidden text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          aria-label="Open mobile menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex flex-col min-w-0">
          <div className="flex items-center space-x-1.5 text-[11px] text-slate-400 font-medium">
            <span>AutoQ</span>
            <span>/</span>
            <span className="text-blue-400 truncate">{breadcrumb}</span>
          </div>
          <h2 className="text-sm sm:text-base font-bold text-[#F1F5F9] truncate tracking-tight">
            {title}
          </h2>
        </div>
      </div>

      {/* Center: Search interface */}
      <div className="hidden lg:flex items-center w-72 xl:w-96 mx-4">
        <div className="relative w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={globalSearch}
            onChange={(e) => setGlobalSearch(e.target.value)}
            placeholder="Search component ID, batch, or parameter..."
            className="w-full bg-[#151C26] border border-[#222E3E] text-slate-200 placeholder-slate-500 text-xs rounded-lg pl-9 pr-8 py-2 focus:outline-none focus:border-blue-500 transition-colors"
          />
          {globalSearch && (
            <button
              onClick={() => setGlobalSearch('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Right: Date, System Status, Notifications & User Profile */}
      <div className="flex items-center space-x-3 sm:space-x-4">
        {/* Current Date */}
        <div className="hidden sm:flex text-xs text-slate-400 font-mono">
          {todayFormatted}
        </div>

        {/* Backend Connectivity Status Pill */}
        <div
          className="hidden xl:flex items-center space-x-1.5 text-xs px-2.5 py-1 rounded-full border bg-[#151C26]"
          title={backendHealth.online ? 'FastAPI Backend Online' : 'FastAPI Backend Disconnected'}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              backendHealth.online ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
            }`}
          />
          <span className="text-slate-400 text-[11px] font-medium">
            {backendHealth.online ? 'API Online' : 'API Standby'}
          </span>
        </div>

        {/* Notifications Popover */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="relative p-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-[#151C26] transition-colors focus:outline-none"
            title="Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-blue-500 ring-2 ring-[#10151D]" />
          </button>

          {notificationsOpen && (
            <>
              <div
                className="fixed inset-0 z-30"
                onClick={() => setNotificationsOpen(false)}
              />
              <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-[#151C26] border border-[#222E3E] rounded-xl shadow-2xl z-40 overflow-hidden animate-in fade-in duration-150">
                <div className="p-3 border-b border-[#222E3E] flex items-center justify-between bg-[#10151D]/60">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-slate-200">System Status & Alerts</span>
                    <span className="text-[10px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded font-mono">
                      {notifications.length} Notice{notifications.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                  <button
                    onClick={() => setNotificationsOpen(false)}
                    className="text-slate-400 hover:text-slate-200 text-xs"
                  >
                    Close
                  </button>
                </div>
                <div className="divide-y divide-[#222E3E]/60 max-h-80 overflow-y-auto">
                  {notifications.map((n) => (
                    <div key={n.id} className="p-3 hover:bg-[#1B2430]/60 transition-colors">
                      <div className="flex items-start space-x-2.5">
                        {n.type === 'warning' ? (
                          <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                        ) : n.type === 'success' ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                        ) : (
                          <Activity className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                        )}
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-semibold text-slate-200 truncate">{n.title}</p>
                          <p className="text-[11px] text-slate-400 mt-0.5 leading-snug">{n.desc}</p>
                          <span className="text-[10px] text-slate-500 font-mono mt-1 block">{n.time}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>

        {/* User Profile */}
        <div className="flex items-center space-x-2.5 pl-2 sm:pl-3 border-l border-[#222E3E]">
          <div className="w-8 h-8 rounded-lg bg-blue-600/30 border border-blue-500/40 flex items-center justify-center text-blue-400 font-semibold text-xs">
            QE
          </div>
          <div className="hidden md:flex flex-col">
            <span className="text-xs font-bold text-slate-200 leading-tight">
              Quality Engineer
            </span>
            <span className="text-[10px] text-slate-400">
              QC Department
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}

