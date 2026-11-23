import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart3,
  TrendingUp,
  Percent,
  CheckCircle2,
  Calendar,
  Layers,
  ArrowUpRight,
  ShieldCheck,
  RefreshCw,
  AlertCircle,
  Clock,
} from 'lucide-react';
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  BarChart,
} from 'recharts';
import PageHeader from '../components/PageHeader';
import ChartCard from '../components/ChartCard';
import StatCard from '../components/StatCard';
import FilterDropdown from '../components/FilterDropdown';
import api from '../services/api';

export default function QualityAnalytics() {
  const [dateRange, setDateRange] = useState('Last 30 Days');
  const [selectedBatch, setSelectedBatch] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Live Data States
  const [overview, setOverview] = useState({
    total_inspections: 0,
    total_passed: 0,
    total_defective: 0,
    pass_rate_percentage: 0.0,
    defect_rate_percentage: 0.0,
    batches_evaluated: 0,
    highest_yield_batch: 'N/A',
  });
  const [trends, setTrends] = useState([]);
  const [batchComparison, setBatchComparison] = useState([]);
  const [qualityPerformance, setQualityPerformance] = useState([]);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const batchParam = selectedBatch !== 'ALL' ? selectedBatch : undefined;
      const [ovData, trendsData, batchData, perfData] = await Promise.all([
        api.getAnalyticsOverview({ batch: batchParam }).catch(() => null),
        api.getInspectionTrends({ days: 14, batch: batchParam }).catch(() => ({ trends: [] })),
        api.getBatchComparison().catch(() => []),
        api.getQualityPerformance({ batch: batchParam }).catch(() => ({ performance: [] })),
      ]);

      if (ovData) {
        setOverview(ovData);
      }

      // Normalize trends
      const rawTrends = Array.isArray(trendsData) ? trendsData : (trendsData?.trends || []);
      const normTrends = rawTrends.map((t) => ({
        date: t.date,
        inspections: t.inspections || 0,
        passed: t.passed || 0,
        defective: t.defective || 0,
        defectRate: t.defect_rate ?? t.defectRate ?? 0,
      }));
      setTrends(normTrends);

      // Normalize batches
      const rawBatches = Array.isArray(batchData) ? batchData : (batchData?.batches || []);
      const normBatches = rawBatches.map((b) => ({
        batch: b.batch,
        total: b.total_inspections ?? b.inspections ?? 0,
        passed: b.passed_count ?? b.passed ?? 0,
        defective: b.defective_count ?? b.defective ?? 0,
        defectRate: b.defect_rate_percent ?? b.defectRate ?? b.defect_rate ?? 0,
        avgTemp: b.avg_temperature ?? 0,
        avgPressure: b.avg_pressure ?? 0,
      }));
      setBatchComparison(normBatches);

      // Normalize performance
      const rawPerf = Array.isArray(perfData) ? perfData : (perfData?.performance || []);
      const normPerf = rawPerf.map((p) => ({
        category: p.category || 'General',
        total: p.total ?? ((p.passed || 0) + (p.defective || 0)),
        passed: p.passed || 0,
        defective: p.defective || 0,
        passRate: p.pass_rate || 0,
        defectRate: p.defect_rate || 0,
      }));
      setQualityPerformance(normPerf);
    } catch (err) {
      console.error('Error fetching quality analytics:', err);
      setError(err.message || 'Failed to load quality analytics metrics.');
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
            {label}
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
        title="Quality Analytics Workspace"
        subtitle="Holistic manufacturing quality metrics, yield comparisons and tolerance deviation aggregated from database records."
        showDateSelector={true}
        dateRange={dateRange}
        onDateRangeChange={setDateRange}
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
            <p className="font-semibold text-rose-200">Failed to aggregate quality analytics</p>
            <p className="font-mono text-[11px] text-rose-300/80">{error}</p>
          </div>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Overall Pass Percentage"
          value={`${Number(overview.pass_rate_percentage ?? overview.pass_rate ?? 0).toFixed(1)}%`}
          subtitle="Target threshold: > 90.0%"
          change={`${overview.total_passed ?? overview.passed_components ?? 0} units passed`}
          isPositive={(overview.pass_rate_percentage ?? overview.pass_rate ?? 0) >= 90.0}
          icon={CheckCircle2}
          accentColor="emerald"
        />
        <StatCard
          title="Average Defect Rate"
          value={`${Number(overview.defect_rate_percentage ?? overview.defect_rate ?? 0).toFixed(1)}%`}
          subtitle="Lower is better"
          change={`${overview.total_defective ?? overview.defective_components ?? 0} units defective`}
          isPositive={(overview.defect_rate_percentage ?? overview.defect_rate ?? 0) <= 10.0}
          icon={Percent}
          accentColor="amber"
        />
        <StatCard
          title="Batches Evaluated"
          value={`${overview.batches_evaluated} Batches`}
          subtitle={`${overview.total_inspections} inspected units`}
          change="Live SQLite aggregate"
          isPositive={null}
          icon={Layers}
          accentColor="blue"
        />
        <StatCard
          title="Highest Yield Batch"
          value={overview.highest_yield_batch || 'None'}
          subtitle="Best yield in database"
          change="Peak compliance"
          isPositive={true}
          icon={ShieldCheck}
          accentColor="cyan"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 1. Overall Inspection Performance & Pass Rate Trends */}
        <ChartCard
          title="Inspection Volume & Defect Rate Trend"
          subtitle="Daily inspection volume compared against defect percentage (Last 14 Days)"
        >
          {trends.length === 0 ? (
            <div className="h-[260px] flex flex-col items-center justify-center text-slate-500 text-xs">
              <Clock className="w-8 h-8 text-slate-600 mb-2" />
              <span>No daily trend records available in database.</span>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <ComposedChart
                data={trends}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#222E3E" opacity={0.6} />
                <XAxis dataKey="date" stroke="#64748B" fontSize={11} tickLine={false} />
                <YAxis yAxisId="left" stroke="#64748B" fontSize={11} tickLine={false} />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  stroke="#64748B"
                  fontSize={11}
                  tickLine={false}
                  unit="%"
                  domain={[0, (dataMax) => Math.max(20, Math.ceil(dataMax * 1.2))]}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar
                  yAxisId="left"
                  dataKey="inspections"
                  name="Inspections (Units)"
                  fill="#1E293B"
                  stroke="#3B82F6"
                  strokeWidth={1}
                  radius={[4, 4, 0, 0]}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="defectRate"
                  name="Defect Rate (%)"
                  stroke="#EF4444"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#EF4444' }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* 2. Production Batch Comparison */}
        <ChartCard
          title="Production Batch Yield Comparison"
          subtitle="Passed versus defective count across batches in database"
        >
          {batchComparison.length === 0 ? (
            <div className="h-[260px] flex flex-col items-center justify-center text-slate-500 text-xs">
              <CheckCircle2 className="w-8 h-8 text-emerald-500/60 mb-2" />
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
                <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="passed" name="Passed" fill="#22C55E" radius={[4, 4, 0, 0]} />
                <Bar dataKey="defective" name="Defective" fill="#EF4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* 3. Component Category Pass Rate Comparison */}
        <ChartCard
          title="Category Pass Rate vs Target (95%)"
          subtitle="Quality pass percentage by component family against the 95% threshold"
        >
          {qualityPerformance.length === 0 ? (
            <div className="h-[260px] flex flex-col items-center justify-center text-slate-500 text-xs">
              <CheckCircle2 className="w-8 h-8 text-emerald-500/60 mb-2" />
              <span>No component quality records available.</span>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart
                data={qualityPerformance}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#222E3E" opacity={0.6} />
                <XAxis dataKey="category" stroke="#64748B" fontSize={10} tickLine={false} />
                <YAxis
                  stroke="#64748B"
                  fontSize={11}
                  tickLine={false}
                  unit="%"
                  domain={[50, 100]}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="passRate" name="Pass Rate (%)" fill="#06B6D4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* 4. Batch Parameter Overview Table */}
        <div className="bg-[#151C26] border border-[#222E3E] rounded-xl p-5 shadow-lg shadow-black/20 flex flex-col justify-between">
          <div className="pb-3 border-b border-slate-800">
            <h3 className="text-sm font-semibold text-slate-100 tracking-tight">
              Batch Performance Summary
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Production yield and operating temperature metrics per batch
            </p>
          </div>

          <div className="overflow-x-auto my-auto py-2">
            {batchComparison.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-xs">
                No manufacturing batches logged yet.
              </div>
            ) : (
              <table className="w-full text-left text-xs">
                <thead className="bg-[#10151D] text-slate-400 uppercase text-[10px] font-mono border-b border-[#222E3E]">
                  <tr>
                    <th className="px-3 py-2">Batch</th>
                    <th className="px-3 py-2">Total</th>
                    <th className="px-3 py-2">Yield %</th>
                    <th className="px-3 py-2">Avg Temp</th>
                    <th className="px-3 py-2">Avg Press</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#222E3E]/60 text-slate-300">
                  {batchComparison.map((b, i) => (
                    <tr key={i} className="hover:bg-[#1B2430]/50 transition-colors">
                      <td className="px-3 py-2.5 font-mono font-semibold text-blue-400">
                        {b.batch}
                      </td>
                      <td className="px-3 py-2.5 font-mono">{b.total}</td>
                      <td className="px-3 py-2.5 font-mono font-semibold">
                        <span
                          className={
                            (b.defectRate ?? 0) < 8.5
                              ? 'text-emerald-400'
                              : (b.defectRate ?? 0) < 10
                              ? 'text-amber-400'
                              : 'text-rose-400'
                          }
                        >
                          {(100 - (b.defectRate ?? 0)).toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-3 py-2.5 font-mono text-amber-400">
                        {b.avgTemp != null ? `${Number(b.avgTemp).toFixed(1)} °C` : '—'}
                      </td>
                      <td className="px-3 py-2.5 font-mono text-cyan-400">
                        {b.avgPressure != null ? `${Number(b.avgPressure).toFixed(1)} bar` : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="pt-3 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Live SQLite manufacturing batch records.</span>
            <span className="font-mono text-[10px] text-slate-500">{batchComparison.length} Active Batches</span>
          </div>
        </div>
      </div>
    </div>
  );
}
