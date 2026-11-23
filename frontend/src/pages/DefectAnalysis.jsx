import React, { useState, useEffect, useCallback } from 'react';
import {
  Microscope,
  AlertOctagon,
  Layers,
  Flame,
  Gauge,
  TrendingDown,
  CheckCircle,
  RefreshCw,
  Cpu,
  BarChart3,
  AlertCircle,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  Cell,
  ScatterChart,
  Scatter,
  ZAxis,
} from 'recharts';
import PageHeader from '../components/PageHeader';
import ChartCard from '../components/ChartCard';
import FilterDropdown from '../components/FilterDropdown';
import StatusBadge from '../components/StatusBadge';
import api from '../services/api';

const PALETTE = ['#EF4444', '#F59E0B', '#3B82F6', '#06B6D4', '#8B5CF6', '#10B981'];

export default function DefectAnalysis() {
  const [selectedBatch, setSelectedBatch] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Live Data States
  const [defectCategories, setDefectCategories] = useState([]);
  const [totalDefects, setTotalDefects] = useState(0);
  const [affectedComponents, setAffectedComponents] = useState([]);
  const [batchComparison, setBatchComparison] = useState([]);
  const [modelInsights, setModelInsights] = useState(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const batchParam = selectedBatch !== 'ALL' ? selectedBatch : undefined;
      const [defectData, perfData, batchData, insightsData] = await Promise.all([
        api.getDefectDistribution({ batch: batchParam }).catch(() => ({ categories: [], distribution: [], total_defects: 0 })),
        api.getQualityPerformance({ batch: batchParam }).catch(() => ({ performance: [] })),
        api.getBatchComparison().catch(() => []),
        api.getModelInsights().catch((err) => ({ error: err.message || 'Failed to connect to model insights service.' })),
      ]);

      // 1. Defect Distribution
      const rawCategories = defectData?.categories || defectData?.distribution || [];
      const categories = rawCategories.map((cat, idx) => ({
        name: cat.name || cat.defect_category || cat.category || 'Unclassified',
        count: cat.count || 0,
        percentage: cat.percentage ?? 0,
        color: cat.color || PALETTE[idx % PALETTE.length],
      }));
      setDefectCategories(categories);
      setTotalDefects(defectData?.total_defects ?? 0);

      // 2. Affected Components
      const rawPerf = Array.isArray(perfData) ? perfData : (perfData?.performance || []);
      const compList = rawPerf.map((item) => ({
        category: item.category || 'General',
        total: item.total ?? ((item.passed || 0) + (item.defective || 0)),
        passed: item.passed || 0,
        defective: item.defective || 0,
        passRate: item.pass_rate || 0,
        defectRate: item.defect_rate || 0,
      })).sort((a, b) => b.defective - a.defective);
      setAffectedComponents(compList);

      // 3. Batch Comparison
      const rawBatches = Array.isArray(batchData) ? batchData : (batchData?.batches || []);
      const batchList = rawBatches.map((b) => ({
        batch: b.batch,
        total: b.total_inspections ?? b.inspections ?? 0,
        passed: b.passed_count ?? b.passed ?? 0,
        defective: b.defective_count ?? b.defective ?? 0,
        defectRate: b.defect_rate_percent ?? b.defectRate ?? b.defect_rate ?? 0,
        avgTemp: b.avg_temperature ?? 0,
        avgPressure: b.avg_pressure ?? 0,
      }));
      setBatchComparison(batchList);

      // 4. Model Insights
      setModelInsights(insightsData);
    } catch (err) {
      console.error('Error fetching defect analysis data:', err);
      setError(err.message || 'Failed to load defect analysis metrics.');
    } finally {
      setIsLoading(false);
    }
  }, [selectedBatch]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#151C26] border border-[#222E3E] rounded-lg p-3 shadow-xl text-xs">
          <p className="font-semibold text-slate-200 mb-1 border-b border-slate-800 pb-1">
            {label || payload[0]?.payload?.name || payload[0]?.name}
          </p>
          {payload.map((entry, idx) => (
            <div key={idx} className="flex items-center justify-between space-x-4 py-0.5">
              <span className="flex items-center space-x-1.5" style={{ color: entry.color }}>
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
                <span>{entry.name}:</span>
              </span>
              <span className="font-mono font-bold text-slate-100">{entry.value}</span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <PageHeader
        title="Defect Analysis & Patterns"
        subtitle="Examine recurring defect categories, affected automotive assemblies and manufacturing parameter correlations from live database records."
      >
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={fetchData}
            disabled={isLoading}
            className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-lg bg-[#1B2430] border border-[#222E3E] text-slate-300 hover:text-white hover:bg-[#222E3E] transition-colors text-xs font-semibold disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-blue-400 ${isLoading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>

          <FilterDropdown
            label="Batch"
            value={selectedBatch}
            onChange={setSelectedBatch}
            options={[
              { value: 'ALL', label: 'All Batches' },
              { value: 'BATCH-2026-A1', label: 'Batch 2026-A1' },
              { value: 'BATCH-2026-A2', label: 'Batch 2026-A2' },
              { value: 'BATCH-2026-B1', label: 'Batch 2026-B1' },
              { value: 'BATCH-2026-B2', label: 'Batch 2026-B2' },
              { value: 'BATCH-2026-C1', label: 'Batch 2026-C1' },
            ]}
          />
        </div>
      </PageHeader>

      {/* Error state */}
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-950/30 border border-rose-800/40 text-xs text-rose-300 flex items-start space-x-2.5">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-rose-200">Failed to aggregate defect data</p>
            <p className="font-mono text-[11px] text-rose-300/80">{error}</p>
          </div>
        </div>
      )}

      {/* Top 2 Charts: Defect Distribution & Frequently Affected Components */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 1. Defect Category Distribution */}
        <ChartCard
          title="Defect Category Breakdown"
          subtitle={`Frequency breakdown of flagged failure types (Total: ${totalDefects})`}
        >
          {defectCategories.length === 0 ? (
            <div className="h-[260px] flex flex-col items-center justify-center text-slate-500 text-xs">
              <CheckCircle className="w-8 h-8 text-emerald-500/60 mb-2" />
              <span>No defect records found in the database for this selection.</span>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart
                data={defectCategories}
                layout="vertical"
                margin={{ top: 10, right: 20, left: 40, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#222E3E" horizontal={false} opacity={0.6} />
                <XAxis type="number" stroke="#64748B" fontSize={11} tickLine={false} />
                <YAxis
                  type="category"
                  dataKey="name"
                  stroke="#64748B"
                  fontSize={10}
                  tickLine={false}
                  width={130}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" name="Defect Count" fill="#EF4444" radius={[0, 4, 4, 0]}>
                  {defectCategories.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* 2. Frequently Affected Components */}
        <ChartCard
          title="Affected Subsystem Families"
          subtitle="Automotive part categories exhibiting highest defect counts"
        >
          {affectedComponents.length === 0 ? (
            <div className="h-[260px] flex flex-col items-center justify-center text-slate-500 text-xs">
              <CheckCircle className="w-8 h-8 text-emerald-500/60 mb-2" />
              <span>No component records available to display.</span>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart
                data={affectedComponents}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#222E3E" opacity={0.6} />
                <XAxis dataKey="category" stroke="#64748B" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="defective" name="Defective Count" fill="#F59E0B" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      {/* Bottom 2 Charts: Feature Importance & Batch Defect Rate */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 3. ML Feature Importance */}
        <ChartCard
          title="Machine Learning Feature Importances"
          subtitle="Top predictive indicators identified by Champion Random Forest Classifier"
          badgeText="ML Model Metadata"
        >
          {modelInsights?.top_features && modelInsights.top_features.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart
                data={modelInsights.top_features.slice(0, 6)}
                layout="vertical"
                margin={{ top: 10, right: 20, left: 40, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#222E3E" horizontal={false} opacity={0.6} />
                <XAxis
                  type="number"
                  stroke="#64748B"
                  fontSize={11}
                  tickLine={false}
                  tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                />
                <YAxis
                  type="category"
                  dataKey="feature"
                  stroke="#64748B"
                  fontSize={10}
                  tickLine={false}
                  width={140}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="importance" name="Importance" fill="#06B6D4" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : modelInsights?.error ? (
            <div className="h-[260px] flex flex-col items-center justify-center text-rose-400 text-xs text-center px-4">
              <AlertTriangle className="w-8 h-8 text-rose-500 mb-2" />
              <span className="font-semibold text-rose-300">Model Insights Unavailable</span>
              <span className="text-slate-400 mt-1 max-w-xs">{modelInsights.error}</span>
            </div>
          ) : (
            <div className="h-[260px] flex flex-col items-center justify-center text-slate-500 text-xs">
              <Cpu className="w-8 h-8 text-cyan-500/60 mb-2" />
              <span>Model feature importances loading from ML subsystem...</span>
            </div>
          )}
        </ChartCard>

        {/* 4. Defect Rate by Production Batch */}
        <ChartCard
          title="Defect Rate by Production Batch"
          subtitle="Comparison of defect percentage across manufacturing batches in database"
        >
          {batchComparison.length === 0 ? (
            <div className="h-[260px] flex flex-col items-center justify-center text-slate-500 text-xs">
              <CheckCircle className="w-8 h-8 text-emerald-500/60 mb-2" />
              <span>No batch comparison records in database.</span>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart
                data={batchComparison}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#222E3E" opacity={0.6} />
                <XAxis dataKey="batch" stroke="#64748B" fontSize={10} tickLine={false} />
                <YAxis
                  stroke="#64748B"
                  fontSize={11}
                  tickLine={false}
                  unit="%"
                  domain={[0, (dataMax) => Math.max(15, Math.ceil(dataMax * 1.2))]}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="defectRate" name="Defect Rate (%)" fill="#EF4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      {/* RECURRING DEFECT PATTERNS / RISK DIRECTIVES */}
      <div className="space-y-3">
        <div>
          <h3 className="text-base font-bold text-slate-200 tracking-tight">
            High-Risk Manufacturing Failure Modes & Directives
          </h3>
          <p className="text-xs text-slate-400">
            Systematic quality failure classifications derived from AI4I predictive telemetry and physical inspections
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-[#151C26] border border-[#222E3E] rounded-xl p-5 shadow-lg shadow-black/20 flex flex-col justify-between hover:border-slate-700 transition-colors">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-blue-400">HDF-01</span>
                <StatusBadge status="HIGH" size="xs" />
              </div>
              <h4 className="text-xs font-bold text-slate-100 leading-snug">
                Heat Dissipation & Thermal Overload
              </h4>
              <div className="space-y-1.5 text-[11px] bg-[#10151D] p-3 rounded-lg border border-[#222E3E]">
                <div>
                  <span className="text-slate-400">Primary Domain:</span>
                  <span className="text-slate-200 font-medium ml-1">Powertrain & Engine</span>
                </div>
                <div>
                  <span className="text-slate-400">Root Mechanism:</span>
                  <span className="text-rose-400 font-semibold ml-1">Delta Temperature &lt; 8.6 K &amp; RPM &lt; 1380</span>
                </div>
              </div>
              <p className="text-[11px] text-slate-300 leading-relaxed">
                <strong className="text-slate-400">Parameter Triggers:</strong> High process temperature exceeding cooling capacity causes micro-cracking in precision cast assemblies.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-amber-300/90 bg-amber-950/20 p-2.5 rounded border border-amber-800/30">
              <strong className="block text-amber-200 uppercase tracking-wider text-[10px] mb-0.5">
                Action Recommendation:
              </strong>
              Audit coolant flow rates, verify dielectric fluid pressures, and calibrate machine thermal dissipation nozzles.
            </div>
          </div>

          <div className="bg-[#151C26] border border-[#222E3E] rounded-xl p-5 shadow-lg shadow-black/20 flex flex-col justify-between hover:border-slate-700 transition-colors">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-blue-400">PWF-02</span>
                <StatusBadge status="CRITICAL" size="xs" />
              </div>
              <h4 className="text-xs font-bold text-slate-100 leading-snug">
                Power Strain Failure (Torque × RPM)
              </h4>
              <div className="space-y-1.5 text-[11px] bg-[#10151D] p-3 rounded-lg border border-[#222E3E]">
                <div>
                  <span className="text-slate-400">Primary Domain:</span>
                  <span className="text-slate-200 font-medium ml-1">Drivetrain & Transmission</span>
                </div>
                <div>
                  <span className="text-slate-400">Root Mechanism:</span>
                  <span className="text-rose-400 font-semibold ml-1">Power Product &lt; 3500 W or &gt; 9000 W</span>
                </div>
              </div>
              <p className="text-[11px] text-slate-300 leading-relaxed">
                <strong className="text-slate-400">Parameter Triggers:</strong> Excessive torque during CNC milling or lathe turning creates shear stress beyond alloy yield limits.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-amber-300/90 bg-amber-950/20 p-2.5 rounded border border-amber-800/30">
              <strong className="block text-amber-200 uppercase tracking-wider text-[10px] mb-0.5">
                Action Recommendation:
              </strong>
              Clamp feed rate velocity, reduce torque setpoints on high-hardness workpiece runs, and inspect drive gears.
            </div>
          </div>

          <div className="bg-[#151C26] border border-[#222E3E] rounded-xl p-5 shadow-lg shadow-black/20 flex flex-col justify-between hover:border-slate-700 transition-colors">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-blue-400">TWF-03</span>
                <StatusBadge status="MEDIUM" size="xs" />
              </div>
              <h4 className="text-xs font-bold text-slate-100 leading-snug">
                Tool Wear Degradation
              </h4>
              <div className="space-y-1.5 text-[11px] bg-[#10151D] p-3 rounded-lg border border-[#222E3E]">
                <div>
                  <span className="text-slate-400">Primary Domain:</span>
                  <span className="text-slate-200 font-medium ml-1">Braking & Caliper Discs</span>
                </div>
                <div>
                  <span className="text-slate-400">Root Mechanism:</span>
                  <span className="text-rose-400 font-semibold ml-1">Tool Wear Time &gt; 200 minutes</span>
                </div>
              </div>
              <p className="text-[11px] text-slate-300 leading-relaxed">
                <strong className="text-slate-400">Parameter Triggers:</strong> Cumulative tool blade friction causes dimensional warpage and surface roughness degradation.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-amber-300/90 bg-amber-950/20 p-2.5 rounded border border-amber-800/30">
              <strong className="block text-amber-200 uppercase tracking-wider text-[10px] mb-0.5">
                Action Recommendation:
              </strong>
              Implement automated tool replacement at 190 minutes runtime and perform optical surface profile scans.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
