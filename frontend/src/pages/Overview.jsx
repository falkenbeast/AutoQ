import React, { useState, useEffect } from 'react';
import {
  ClipboardCheck,
  CheckCircle,
  AlertTriangle,
  Percent,
  BrainCircuit,
  Eye,
  RefreshCw,
  Inbox,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';
import PageHeader from '../components/PageHeader';
import StatCard from '../components/StatCard';
import ChartCard from '../components/ChartCard';
import DataTable from '../components/DataTable';
import StatusBadge from '../components/StatusBadge';
import SearchBar from '../components/SearchBar';
import FilterDropdown from '../components/FilterDropdown';
import Modal from '../components/Modal';
import api from '../services/api';

export default function Overview() {
  const [dateRange, setDateRange] = useState('Last 14 Days');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedInspection, setSelectedInspection] = useState(null);

  // Live Data States
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [overviewKPIs, setOverviewKPIs] = useState({
    total_inspections: 0,
    passed_components: 0,
    defective_components: 0,
    defect_rate: 0.0,
    pass_rate: 0.0,
    target_defect_rate: 10.0,
  });
  const [trendData, setTrendData] = useState([]);
  const [defectDist, setDefectDist] = useState([]);
  const [qualityPerf, setQualityPerf] = useState([]);
  const [inspectionsList, setInspectionsList] = useState([]);
  const [modelInsights, setModelInsights] = useState(null);
  const [mlEngineStatus, setMlEngineStatus] = useState({
    active: false,
    version: '1.0.0',
    modelName: 'Random Forest',
    rocAuc: '0.9830',
  });

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [kpiRes, trendRes, distRes, perfRes, inspRes, modelRes, healthRes] = await Promise.allSettled([
        api.getAnalyticsOverview({ date_range: dateRange }),
        api.getInspectionTrends({ days: 14 }),
        api.getDefectDistribution(),
        api.getQualityPerformance(),
        api.getInspections({ page: 1, page_size: 10 }),
        api.getModelInsights(),
        api.checkHealth(),
      ]);

      if (kpiRes.status === 'fulfilled' && kpiRes.value) {
        setOverviewKPIs(kpiRes.value);
      }
      if (trendRes.status === 'fulfilled' && trendRes.value?.trends) {
        setTrendData(trendRes.value.trends);
      }
      if (distRes.status === 'fulfilled' && distRes.value?.distribution) {
        setDefectDist(distRes.value.distribution);
      }
      if (perfRes.status === 'fulfilled' && perfRes.value?.performance) {
        setQualityPerf(perfRes.value.performance);
      }
      if (inspRes.status === 'fulfilled' && inspRes.value?.items) {
        setInspectionsList(inspRes.value.items);
      }
      if (modelRes.status === 'fulfilled' && modelRes.value && !modelRes.value.error) {
        setModelInsights(modelRes.value);
      }

      // Reconcile unified ML Engine health status
      const healthData = healthRes.status === 'fulfilled' ? healthRes.value : null;
      const modelData = modelRes.status === 'fulfilled' && !modelRes.value?.error ? modelRes.value : null;
      const isOnline = Boolean(healthData?.ml_engine?.model_available || modelData);

      setMlEngineStatus({
        active: isOnline,
        version: healthData?.ml_engine?.model_version || modelData?.model_version || '1.0.0',
        modelName: healthData?.ml_engine?.model_name || modelData?.model_name || 'Random Forest',
        rocAuc: String(healthData?.ml_engine?.test_roc_auc ?? modelData?.champion_test_metrics?.roc_auc ?? '0.9830'),
      });
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError('Could not connect to AutoQ analytics backend. Verify server is online.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [dateRange]);

  // Filter recent inspections
  const filteredInspections = inspectionsList.filter((item) => {
    const matchesSearch =
      (item.component_id || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.component_name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.production_batch || '').toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus =
      statusFilter === 'ALL' || (item.inspection_result || '').toUpperCase() === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const columns = [
    {
      header: 'Component ID',
      accessor: 'component_id',
      render: (row) => (
        <span className="font-mono font-semibold text-blue-400">
          {row.component_id}
        </span>
      ),
    },
    {
      header: 'Component Details',
      accessor: 'component_name',
      render: (row) => (
        <div>
          <span className="font-medium text-slate-200 block">{row.component_name || 'Generic Part'}</span>
          <span className="text-[10px] text-slate-400">{row.component_category || 'Automotive Component'}</span>
        </div>
      ),
    },
    {
      header: 'Batch',
      accessor: 'production_batch',
      render: (row) => <span className="font-mono text-slate-300 text-xs">{row.production_batch}</span>,
    },
    {
      header: 'Inspection Date',
      accessor: 'inspection_date',
      render: (row) => (
        <span className="font-mono text-slate-400 text-xs">
          {new Date(row.inspection_date).toLocaleDateString()}
        </span>
      ),
    },
    {
      header: 'Status',
      accessor: 'inspection_result',
      render: (row) => <StatusBadge status={(row.inspection_result || 'PASSED').toUpperCase()} />,
    },
    {
      header: 'Defect Category',
      accessor: 'defect_category',
      render: (row) => (
        <span
          className={`font-medium text-xs ${
            !row.defect_category || row.defect_category === 'None' || row.defect_category === 'No Defect'
              ? 'text-slate-500'
              : 'text-rose-400'
          }`}
        >
          {row.defect_category || 'None'}
        </span>
      ),
    },
    {
      header: 'Action',
      render: (row) => (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            setSelectedInspection(row);
          }}
          className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-[#10151D] border border-[#222E3E] text-slate-300 hover:text-blue-400 hover:border-blue-500/50 transition-colors text-xs"
        >
          <Eye className="w-3.5 h-3.5" />
          <span>Details</span>
        </button>
      ),
    },
  ];

  // Custom Dark Recharts Tooltip
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
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: entry.color }}
                />
                <span>{entry.name}:</span>
              </span>
              <span className="font-mono font-bold text-slate-100">
                {entry.value}
                {entry.unit || ''}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  const DEFECT_COLORS = ['#EF4444', '#F59E0B', '#3B82F6', '#8B5CF6', '#06B6D4', '#EC4899'];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        title="Manufacturing Overview"
        subtitle="Monitor component quality, inspection performance and manufacturing defects from actual SQLite records."
        showDateSelector={true}
        dateRange={dateRange}
        onDateRangeChange={setDateRange}
      >
        <button
          type="button"
          onClick={fetchDashboardData}
          disabled={loading}
          className="px-3 py-1.5 rounded-lg bg-[#1B2430] border border-[#222E3E] hover:border-slate-700 text-slate-300 hover:text-white text-xs font-semibold flex items-center space-x-1.5 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-400' : ''}`} />
          <span>Sync Data</span>
        </button>
      </PageHeader>

      {error && (
        <div className="bg-amber-950/40 border border-amber-800/50 rounded-xl p-4 text-xs text-amber-200 flex items-center justify-between">
          <span>{error}</span>
          <button
            type="button"
            onClick={fetchDashboardData}
            className="underline font-bold hover:text-amber-100"
          >
            Retry Connection
          </button>
        </div>
      )}

      {/* 5 KPI CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        <StatCard
          title="Total Inspections"
          value={overviewKPIs.total_inspections.toLocaleString()}
          subtitle="All recorded components"
          change="Real DB Count"
          isPositive={true}
          icon={ClipboardCheck}
          accentColor="blue"
        />
        <StatCard
          title="Passed Components"
          value={overviewKPIs.passed_components.toLocaleString()}
          subtitle={`${overviewKPIs.pass_rate}% yield`}
          change={`${overviewKPIs.pass_rate}% Passed`}
          isPositive={true}
          icon={CheckCircle}
          accentColor="emerald"
        />
        <StatCard
          title="Defective Parts"
          value={overviewKPIs.defective_components.toLocaleString()}
          subtitle="Non-conforming items"
          change={`${overviewKPIs.defective_components} Detected`}
          isPositive={false}
          icon={AlertTriangle}
          accentColor="rose"
        />
        <StatCard
          title="Defect Rate"
          value={`${overviewKPIs.defect_rate}%`}
          subtitle={`Target: ≤ ${overviewKPIs.target_defect_rate}%`}
          change={overviewKPIs.defect_rate <= overviewKPIs.target_defect_rate ? 'Within Target' : 'Exceeds Spec'}
          isPositive={overviewKPIs.defect_rate <= overviewKPIs.target_defect_rate}
          icon={Percent}
          accentColor="amber"
        />
        <StatCard
          title="ML Engine Status"
          value={mlEngineStatus.active ? `Active (v${mlEngineStatus.version})` : 'Offline'}
          subtitle={mlEngineStatus.active ? `ROC-AUC: ${mlEngineStatus.rocAuc}` : 'Inference Subsystem'}
          change={mlEngineStatus.active ? 'Champion Ready' : 'Service Offline'}
          isPositive={mlEngineStatus.active}
          icon={BrainCircuit}
          accentColor={mlEngineStatus.active ? 'cyan' : 'rose'}
        />
      </div>

      {/* 4 CHARTS GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 1. Daily Inspection Volume (Line Chart) */}
        <ChartCard
          title="Inspection Trends"
          subtitle="Daily volume of component inspections logged in SQLite database"
        >
          {trendData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#222E3E" opacity={0.6} />
                <XAxis dataKey="date" stroke="#64748B" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Line
                  type="monotone"
                  dataKey="inspections"
                  name="Total Volume"
                  stroke="#3B82F6"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#3B82F6' }}
                  activeDot={{ r: 6, fill: '#60A5FA' }}
                />
                <Line
                  type="monotone"
                  dataKey="passed"
                  name="Passed"
                  stroke="#22C55E"
                  strokeWidth={2}
                  dot={{ r: 2, fill: '#22C55E' }}
                />
                <Line
                  type="monotone"
                  dataKey="defective"
                  name="Defective"
                  stroke="#EF4444"
                  strokeWidth={2}
                  dot={{ r: 2, fill: '#EF4444' }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[260px] flex flex-col items-center justify-center text-slate-500 text-xs">
              <Inbox className="w-8 h-8 mb-2 opacity-50" />
              <span>No daily inspection telemetry recorded yet.</span>
            </div>
          )}
        </ChartCard>

        {/* 2. Defect Category Distribution (Donut Chart) */}
        <ChartCard
          title="Defect Category Breakdown"
          subtitle="Proportion of verified failure modes recorded in database"
        >
          {defectDist.length > 0 ? (
            <div className="flex flex-col sm:flex-row items-center justify-between h-[260px]">
              <div className="w-full sm:w-1/2 h-full flex items-center justify-center">
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie
                      data={defectDist}
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={85}
                      paddingAngle={3}
                      dataKey="count"
                      nameKey="category"
                    >
                      {defectDist.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={DEFECT_COLORS[index % DEFECT_COLORS.length]}
                          stroke="#151C26"
                          strokeWidth={2}
                        />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Legend with Counts */}
              <div className="w-full sm:w-1/2 space-y-1.5 pl-0 sm:pl-4">
                {defectDist.map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between text-xs py-1 border-b border-slate-800/60 last:border-0">
                    <span className="flex items-center space-x-2 text-slate-300">
                      <span
                        className="w-2.5 h-2.5 rounded-full"
                        style={{ backgroundColor: DEFECT_COLORS[idx % DEFECT_COLORS.length] }}
                      />
                      <span className="truncate max-w-[130px]">{item.category}</span>
                    </span>
                    <span className="font-mono font-semibold text-slate-200">
                      {item.count} ({item.percentage}%)
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="h-[260px] flex flex-col items-center justify-center text-slate-500 text-xs">
              <CheckCircle className="w-8 h-8 mb-2 text-emerald-500/50" />
              <span>No defect categories registered. All parts conforming!</span>
            </div>
          )}
        </ChartCard>

        {/* 3. Component Quality Performance (Bar Chart) */}
        <ChartCard
          title="Subsystem Yield Performance"
          subtitle="First-pass pass rate across automotive component families"
        >
          {qualityPerf.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart
                data={qualityPerf}
                layout="vertical"
                margin={{ top: 10, right: 20, left: 30, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#222E3E" opacity={0.6} horizontal={false} />
                <XAxis type="number" stroke="#64748B" fontSize={11} domain={[0, 100]} unit="%" />
                <YAxis dataKey="category" type="category" stroke="#64748B" fontSize={10} width={90} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="pass_rate" name="Pass Rate (%)" fill="#06B6D4" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[260px] flex flex-col items-center justify-center text-slate-500 text-xs">
              <Inbox className="w-8 h-8 mb-2 opacity-50" />
              <span>No component performance records yet.</span>
            </div>
          )}
        </ChartCard>

        {/* 4. Defect Rate Trend (Area Chart) */}
        <ChartCard
          title="Defect Percentage Trend"
          subtitle="Daily defect percentage relative to standard 10% maximum tolerance"
        >
          {trendData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="defectGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#EF4444" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#EF4444" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#222E3E" opacity={0.6} />
                <XAxis dataKey="date" stroke="#64748B" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={11} tickLine={false} unit="%" />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="defect_rate"
                  name="Defect Rate"
                  stroke="#EF4444"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#defectGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[260px] flex flex-col items-center justify-center text-slate-500 text-xs">
              <Inbox className="w-8 h-8 mb-2 opacity-50" />
              <span>No defect rate time-series data available.</span>
            </div>
          )}
        </ChartCard>
      </div>

      {/* RECENT INSPECTIONS TABLE */}
      <div className="bg-[#151C26] border border-[#222E3E] rounded-xl p-6 shadow-lg shadow-black/20 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <ClipboardCheck className="w-5 h-5 text-blue-400" />
              <span>Recent Component Inspection Records</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Live records persisted in the SQLite database.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <SearchBar
              value={searchQuery}
              onChange={setSearchQuery}
              placeholder="Filter by ID, component, or batch..."
            />
            <FilterDropdown
              label="Status"
              value={statusFilter}
              onChange={setStatusFilter}
              options={[
                { value: 'ALL', label: 'All Statuses' },
                { value: 'PASSED', label: 'Passed Only' },
                { value: 'DEFECTIVE', label: 'Defective Only' },
              ]}
            />
          </div>
        </div>

        <DataTable
          columns={columns}
          data={filteredInspections}
          emptyMessage="No inspection records found in SQLite database matching query."
          onRowClick={(row) => setSelectedInspection(row)}
        />
      </div>

      {/* INSPECTION DETAIL MODAL */}
      <Modal
        isOpen={!!selectedInspection}
        onClose={() => setSelectedInspection(null)}
        title={`Inspection Audit Record: ${selectedInspection?.component_id || ''}`}
        size="md"
      >
        {selectedInspection && (
          <div className="space-y-4 text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="text-slate-400 text-[11px] block">Component Name</span>
                <span className="text-sm font-bold text-slate-100">
                  {selectedInspection.component_name || 'Standard Automotive Component'}
                </span>
              </div>
              <StatusBadge status={(selectedInspection.inspection_result || 'PASSED').toUpperCase()} size="md" />
            </div>

            <div className="grid grid-cols-2 gap-3 bg-[#10151D] border border-[#222E3E] rounded-lg p-3">
              <div>
                <span className="text-slate-400 text-[11px]">Subsystem Category</span>
                <span className="block font-semibold text-slate-200 mt-0.5">
                  {selectedInspection.component_category || 'Powertrain'}
                </span>
              </div>
              <div>
                <span className="text-slate-400 text-[11px]">Production Batch</span>
                <span className="block font-mono font-semibold text-blue-400 mt-0.5">
                  {selectedInspection.production_batch}
                </span>
              </div>
              <div>
                <span className="text-slate-400 text-[11px]">Manufacturing Temp</span>
                <span className="block font-mono font-semibold text-slate-200 mt-0.5">
                  {selectedInspection.manufacturing_temperature}°C
                </span>
              </div>
              <div>
                <span className="text-slate-400 text-[11px]">Injection Pressure</span>
                <span className="block font-mono font-semibold text-slate-200 mt-0.5">
                  {selectedInspection.pressure} bar
                </span>
              </div>
            </div>

            {selectedInspection.inspection_result === 'Defective' && (
              <div className="bg-rose-950/30 border border-rose-800/40 rounded-lg p-3 space-y-1">
                <span className="text-[11px] font-bold text-rose-300 uppercase tracking-wide block">
                  Defect Classification
                </span>
                <span className="text-rose-400 font-semibold block">
                  {selectedInspection.defect_category || 'Unclassified Defect'}
                </span>
              </div>
            )}

            <div>
              <span className="text-slate-400 text-[11px] block mb-1">Inspector Notes & Observations</span>
              <p className="bg-[#10151D] border border-[#222E3E] rounded-lg p-3 text-slate-300 leading-relaxed">
                {selectedInspection.notes || 'Routine physical quality check passed within ±0.02mm mechanical tolerance bounds.'}
              </p>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
