import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Server,
  Layers,
  Palette,
  Info,
  CheckCircle2,
  RefreshCw,
  Shield,
  Database,
  Cpu,
  Monitor,
  Activity,
  AlertCircle,
  FileCheck,
} from 'lucide-react';
import PageHeader from '../components/PageHeader';
import FormInput from '../components/FormInput';
import api from '../services/api';

export default function Settings() {
  const [backendStatus, setBackendStatus] = useState({
    checking: false,
    healthy: null,
    info: null,
    error: null,
  });

  const DEFAULT_PREFERENCES = {
    defaultBatch: 'BATCH-2026-A2',
    defaultCategory: 'Powertrain',
    refreshInterval: '30s',
    defaultPeriod: 'Last 14 Days',
    showThresholds: true,
    denseTables: false,
  };

  const [preferences, setPreferences] = useState(() => {
    try {
      const saved = localStorage.getItem('autoq_user_preferences');
      return saved ? { ...DEFAULT_PREFERENCES, ...JSON.parse(saved) } : DEFAULT_PREFERENCES;
    } catch {
      return DEFAULT_PREFERENCES;
    }
  });

  const [saveToast, setSaveToast] = useState(false);

  const checkApi = () => {
    setBackendStatus((prev) => ({ ...prev, checking: true }));
    api.checkHealth()
      .then((data) => {
        setBackendStatus({
          checking: false,
          healthy: true,
          info: data,
          error: null,
        });
      })
      .catch((err) => {
        setBackendStatus({
          checking: false,
          healthy: false,
          info: null,
          error: err.message || 'Cannot reach FastAPI backend at http://localhost:8000',
        });
      });
  };

  useEffect(() => {
    checkApi();
  }, []);

  const handleSave = (e) => {
    e.preventDefault();
    try {
      localStorage.setItem('autoq_user_preferences', JSON.stringify(preferences));
    } catch (err) {
      console.warn('Failed to save to localStorage:', err);
    }
    setSaveToast({ msg: 'Preferences saved to persistent local storage.', type: 'success' });
    setTimeout(() => setSaveToast(false), 3000);
  };

  const handleResetDefaults = () => {
    setPreferences(DEFAULT_PREFERENCES);
    try {
      localStorage.removeItem('autoq_user_preferences');
    } catch (err) {
      console.warn('Failed to clear localStorage:', err);
    }
    setSaveToast({ msg: 'Preferences reset to system factory defaults.', type: 'info' });
    setTimeout(() => setSaveToast(false), 3000);
  };

  const dbInfo = backendStatus.info?.database || {};
  const mlInfo = backendStatus.info?.ml_engine || {};

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <PageHeader
        title="System Settings & Diagnostics"
        subtitle="Review platform runtime health, database connectivity, ML model readiness and configure client workspace preferences."
      >
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={handleResetDefaults}
            className="px-3 py-2 rounded-lg bg-[#1B2430] border border-[#222E3E] text-slate-300 hover:text-white font-semibold text-xs transition-colors"
          >
            Reset Defaults
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition-colors shadow-md shadow-blue-500/20"
          >
            Save Preferences
          </button>
        </div>
      </PageHeader>

      {saveToast && (
        <div className={`p-3 rounded-lg border text-xs flex items-center space-x-2 animate-in fade-in ${
          saveToast.type === 'info'
            ? 'bg-blue-950/40 border-blue-800/50 text-blue-300'
            : 'bg-emerald-950/40 border-emerald-800/50 text-emerald-300'
        }`}>
          <CheckCircle2 className="w-4 h-4" />
          <span>{saveToast.msg || 'Preferences updated successfully.'}</span>
        </div>
      )}

      {/* 1. APPLICATION & SYSTEM INFORMATION */}
      <div className="bg-[#151C26] border border-[#222E3E] rounded-xl p-5 shadow-lg shadow-black/20 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2.5">
            <Server className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Application Architecture & Diagnostics
            </h3>
          </div>
          <button
            type="button"
            onClick={checkApi}
            disabled={backendStatus.checking}
            className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded bg-[#10151D] border border-[#222E3E] text-slate-300 hover:text-blue-400 text-xs transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${backendStatus.checking ? 'animate-spin' : ''}`} />
            <span>Ping API Health</span>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
          <div className="bg-[#10151D] border border-[#222E3E] p-3 rounded-lg">
            <span className="text-slate-400 block text-[11px]">Application Name</span>
            <span className="font-bold text-slate-100 text-sm mt-0.5 block">AutoQ</span>
            <span className="text-[10px] text-slate-500 font-mono">
              {backendStatus.info?.version ? `v${backendStatus.info.version}` : 'v1.0.0'} • Production Release
            </span>
          </div>

          <div className="bg-[#10151D] border border-[#222E3E] p-3 rounded-lg">
            <span className="text-slate-400 block text-[11px]">Backend API</span>
            <span className="font-bold text-slate-100 text-sm mt-0.5 block">FastAPI</span>
            <div className="flex items-center space-x-1.5 mt-0.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  backendStatus.healthy ? 'bg-emerald-400' : 'bg-rose-400'
                }`}
              />
              <span className="text-[10px] font-mono text-slate-400">
                {backendStatus.healthy ? '200 OK (Healthy)' : 'Offline / Error'}
              </span>
            </div>
          </div>

          <div className="bg-[#10151D] border border-[#222E3E] p-3 rounded-lg">
            <span className="text-slate-400 block text-[11px]">Database Layer</span>
            <span className="font-bold text-slate-100 text-sm mt-0.5 block">SQLite</span>
            <span className="text-[10px] text-emerald-400 font-mono">
              {dbInfo.status === 'connected' ? 'Connected (SQLAlchemy)' : 'Checking...'}
            </span>
          </div>

          <div className="bg-[#10151D] border border-[#222E3E] p-3 rounded-lg">
            <span className="text-slate-400 block text-[11px]">ML Subsystem</span>
            <span className="font-bold text-slate-100 text-sm mt-0.5 block">Random Forest</span>
            <span className="text-[10px] text-cyan-400 font-mono">
              {mlInfo.status === 'READY' ? 'READY (v1.0.0-phase6)' : 'Initializing...'}
            </span>
          </div>
        </div>

        {/* Database & ML Deep Diagnostics Card */}
        {backendStatus.info && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
            <div className="bg-[#10151D] border border-[#222E3E] p-3.5 rounded-lg space-y-2 text-xs">
              <div className="flex items-center space-x-2 text-blue-400 font-semibold text-[11px] uppercase tracking-wider">
                <Database className="w-3.5 h-3.5" />
                <span>SQLite Store Telemetry</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center pt-1">
                <div className="bg-[#151C26] p-2 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Inspections</span>
                  <span className="font-mono font-bold text-slate-200">
                    {dbInfo.inspections_count ?? 'N/A'}
                  </span>
                </div>
                <div className="bg-[#151C26] p-2 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Components</span>
                  <span className="font-mono font-bold text-slate-200">
                    {dbInfo.components_count ?? 'N/A'}
                  </span>
                </div>
                <div className="bg-[#151C26] p-2 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Predictions</span>
                  <span className="font-mono font-bold text-blue-400">
                    {dbInfo.predictions_count ?? 'N/A'}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-[#10151D] border border-[#222E3E] p-3.5 rounded-lg space-y-2 text-xs">
              <div className="flex items-center space-x-2 text-cyan-400 font-semibold text-[11px] uppercase tracking-wider">
                <Cpu className="w-3.5 h-3.5" />
                <span>ML Inference Specifications</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center pt-1">
                <div className="bg-[#151C26] p-2 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">ROC-AUC</span>
                  <span className="font-mono font-bold text-emerald-400">
                    {mlInfo.test_roc_auc ?? '0.983'}
                  </span>
                </div>
                <div className="bg-[#151C26] p-2 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">F1-Score</span>
                  <span className="font-mono font-bold text-cyan-400">
                    {mlInfo.test_f1 ?? '0.8125'}
                  </span>
                </div>
                <div className="bg-[#151C26] p-2 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Default Cutoff</span>
                  <span className="font-mono font-bold text-amber-400">
                    {mlInfo.threshold ?? 0.35}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {backendStatus.error && (
          <div className="p-3 rounded-lg bg-rose-950/20 border border-rose-800/30 text-rose-400 text-xs flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Backend Connection Warning</p>
              <p className="font-mono text-[11px] mt-0.5">{backendStatus.error}</p>
            </div>
          </div>
        )}
      </div>

      {/* 2. GENERAL & DASHBOARD PREFERENCES */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-[#151C26] border border-[#222E3E] rounded-xl p-5 shadow-lg shadow-black/20 space-y-4">
          <div className="border-b border-slate-800 pb-3 flex items-center space-x-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              General Preferences
            </h3>
          </div>

          <div className="space-y-3">
            <FormInput
              label="Default Production Batch"
              type="select"
              value={preferences.defaultBatch}
              onChange={(e) =>
                setPreferences({ ...preferences, defaultBatch: e.target.value })
              }
              options={[
                { value: 'BATCH-2026-A1', label: 'BATCH-2026-A1' },
                { value: 'BATCH-2026-A2', label: 'BATCH-2026-A2' },
                { value: 'BATCH-2026-B1', label: 'BATCH-2026-B1' },
                { value: 'BATCH-2026-B2', label: 'BATCH-2026-B2' },
              ]}
            />

            <FormInput
              label="Default Component Category"
              type="select"
              value={preferences.defaultCategory}
              onChange={(e) =>
                setPreferences({ ...preferences, defaultCategory: e.target.value })
              }
              options={[
                { value: 'Powertrain', label: 'Powertrain' },
                { value: 'Engine', label: 'Engine' },
                { value: 'Braking System', label: 'Braking System' },
                { value: 'Transmission', label: 'Transmission' },
                { value: 'Chassis & Steering', label: 'Chassis & Steering' },
              ]}
            />

            <FormInput
              label="Metrics Auto-Refresh Rate"
              type="select"
              value={preferences.refreshInterval}
              onChange={(e) =>
                setPreferences({ ...preferences, refreshInterval: e.target.value })
              }
              options={[
                { value: 'None', label: 'Manual Only' },
                { value: '15s', label: 'Every 15 seconds' },
                { value: '30s', label: 'Every 30 seconds' },
                { value: '60s', label: 'Every 60 seconds' },
              ]}
            />
          </div>
        </div>

        <div className="bg-[#151C26] border border-[#222E3E] rounded-xl p-5 shadow-lg shadow-black/20 space-y-4">
          <div className="border-b border-slate-800 pb-3 flex items-center space-x-2">
            <Monitor className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Dashboard & Display Settings
            </h3>
          </div>

          <div className="space-y-4 text-xs">
            <FormInput
              label="Default Chart Time Horizon"
              type="select"
              value={preferences.defaultPeriod}
              onChange={(e) =>
                setPreferences({ ...preferences, defaultPeriod: e.target.value })
              }
              options={[
                { value: 'Last 7 Days', label: 'Last 7 Days' },
                { value: 'Last 14 Days', label: 'Last 14 Days' },
                { value: 'Last 30 Days', label: 'Last 30 Days' },
              ]}
            />

            <div className="flex items-center justify-between p-3 rounded-lg bg-[#10151D] border border-[#222E3E]">
              <div>
                <p className="font-semibold text-slate-200">Show Quality Tolerance Limits</p>
                <p className="text-[11px] text-slate-500">Render 10% defect threshold lines on charts</p>
              </div>
              <input
                type="checkbox"
                checked={preferences.showThresholds}
                onChange={(e) =>
                  setPreferences({ ...preferences, showThresholds: e.target.checked })
                }
                className="w-4 h-4 rounded text-blue-600 bg-slate-900 border-slate-700 cursor-pointer"
              />
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-[#10151D] border border-[#222E3E]">
              <div>
                <p className="font-semibold text-slate-200">Active Color Palette</p>
                <p className="text-[11px] text-slate-500">Dark Industrial (#0B0F14 / #151C26)</p>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-900/50 text-blue-300 border border-blue-700/50">
                Locked
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. ABOUT AUTOQ */}
      <div className="bg-[#151C26] border border-[#222E3E] rounded-xl p-5 shadow-lg shadow-black/20 space-y-3">
        <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
          <Info className="w-4 h-4 text-blue-400" />
          <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
            About AutoQ – Automotive Quality Intelligence System
          </h3>
        </div>

        <div className="text-xs text-slate-300 space-y-2 leading-relaxed">
          <p>
            <strong>AutoQ</strong> is an AI-powered Automotive Quality Intelligence System developed as a final-year B.Tech CSE major project. It is engineered to assist automotive assembly lines and quality control supervisors in logging inspection metrics, identifying defective automotive parts, predicting failure probabilities with machine learning, and auditing manufacturing yield.
          </p>
          <div className="bg-[#10151D] border border-[#222E3E] p-3 rounded-lg space-y-1 text-[11px]">
            <p>
              <strong className="text-slate-400">Software-Only Architecture:</strong> Strictly no Arduino, Raspberry Pi, OBD physical hardware, or extraneous chatbots.
            </p>
            <p>
              <strong className="text-slate-400">Locked Technology Stack:</strong> React 19, Vite, Tailwind CSS, Recharts, Lucide React, FastAPI, Uvicorn, SQLite, SQLAlchemy, Scikit-learn, Pandas, NumPy, Joblib, ReportLab.
            </p>
            <p>
              <strong className="text-slate-400">Dual API Mounting:</strong> Both <code className="text-cyan-400 font-mono">/api/v1/*</code> and <code className="text-cyan-400 font-mono">/api/*</code> are active and synchronized.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
