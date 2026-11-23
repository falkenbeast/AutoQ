import React, { useState, useEffect, useCallback } from 'react';
import {
  FileText,
  Download,
  FileSpreadsheet,
  Calendar,
  Layers,
  Sparkles,
  Info,
  Clock,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Trash2,
} from 'lucide-react';
import PageHeader from '../components/PageHeader';
import DataTable from '../components/DataTable';
import StatusBadge from '../components/StatusBadge';
import FormInput from '../components/FormInput';
import Modal from '../components/Modal';
import api from '../services/api';

export default function Reports() {
  const [reports, setReports] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Form State
  const [selectedReportType, setSelectedReportType] = useState('Defect Analysis');
  const [selectedBatch, setSelectedBatch] = useState('ALL');
  const [selectedFormat, setSelectedFormat] = useState('PDF');
  const [dateRange, setDateRange] = useState('Last 30 Days');
  const [isCompiling, setIsCompiling] = useState(false);

  // Download & Notification States
  const [downloadModalReport, setDownloadModalReport] = useState(null);
  const [downloadingId, setDownloadingId] = useState(null);
  const [notice, setNotice] = useState(null);

  const showNotice = (msg, type = 'success') => {
    setNotice({ msg, type });
    setTimeout(() => setNotice(null), 5000);
  };

  const fetchReports = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getReports();
      const rawList = data?.reports || data?.items || (Array.isArray(data) ? data : []);
      const items = rawList.map((r) => ({
        id: r.id,
        displayId: `REP-2026-${String(r.id).padStart(4, '0')}`,
        title: `${r.report_type} - ${r.target_batch || r.batch || 'All Batches'}`,
        type: r.report_type,
        format: (r.format || 'PDF').toUpperCase(),
        generatedDate: r.created_at
          ? r.created_at.slice(0, 16).replace('T', ' ')
          : (r.generated_date ? r.generated_date.slice(0, 16).replace('T', ' ') : 'N/A'),
        size: r.file_size || (r.file_size_bytes
          ? r.file_size_bytes > 1024 * 1024
            ? `${(r.file_size_bytes / (1024 * 1024)).toFixed(1)} MB`
            : `${(r.file_size_bytes / 1024).toFixed(1)} KB`
          : 'Pending'),
        status: 'Generated',
        generatedBy: r.generated_by || 'Quality System',
        filePath: r.file_path,
        raw: r,
      }));
      setReports(items);
    } catch (err) {
      console.error('Failed to load reports:', err);
      setError(err.message || 'Error fetching report catalog.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  // Handle report generation
  const handleGenerateReport = async (e) => {
    e.preventDefault();
    setIsCompiling(true);
    try {
      const payload = {
        report_type: selectedReportType,
        batch: selectedBatch !== 'ALL' ? selectedBatch : 'ALL',
        target_batch: selectedBatch !== 'ALL' ? selectedBatch : 'ALL',
        format: selectedFormat.toUpperCase(),
        date_range: dateRange,
        generated_by: 'Lead Quality Engineer',
      };

      const res = await api.generateReport(payload);

      // Auto-trigger browser download
      try {
        const ext = (res.format || selectedFormat).toLowerCase();
        const safeTitle = `${res.report_type || 'Report'}-${res.target_batch || res.batch || selectedBatch}`.replace(/[^a-zA-Z0-9_-]/g, '_');
        const filename = `AutoQ_${safeTitle}_${Date.now()}.${ext}`;
        await api.downloadReport(res.id, filename);
      } catch (dlErr) {
        console.warn('Auto download trigger warning:', dlErr);
      }

      const sizeStr = res.file_size || (res.file_size_bytes ? `${(res.file_size_bytes / 1024).toFixed(1)} KB` : 'Generated');
      showNotice(
        `Report "${res.report_type}" successfully compiled and downloaded as ${res.format.toUpperCase()} (${sizeStr})!`
      );
      await fetchReports();
    } catch (err) {
      console.error('Error compiling report:', err);
      showNotice(err.message || 'Failed to compile report.', 'error');
    } finally {
      setIsCompiling(false);
    }
  };

  // Handle genuine file download
  const handleTriggerDownload = async (row) => {
    setDownloadingId(row.id);
    try {
      const ext = (row.format || 'pdf').toLowerCase();
      const safeTitle = (row.title || `Report-${row.id}`).replace(/[^a-zA-Z0-9_-]/g, '_');
      const filename = `AutoQ_${safeTitle}.${ext}`;
      await api.downloadReport(row.id, filename);
      showNotice(`Downloaded ${row.title} (${row.format}).`);
    } catch (err) {
      console.error('Download error:', err);
      showNotice(err.message || 'Failed to download report file.', 'error');
    } finally {
      setDownloadingId(null);
    }
  };

  const columns = [
    {
      header: 'Report ID',
      accessor: 'displayId',
      render: (row) => (
        <span className="font-mono font-semibold text-blue-400">
          {row.displayId}
        </span>
      ),
    },
    {
      header: 'Report Title',
      accessor: 'title',
      render: (row) => (
        <div className="flex items-center space-x-2">
          {row.format === 'PDF' ? (
            <FileText className="w-4 h-4 text-rose-400 flex-shrink-0" />
          ) : (
            <FileSpreadsheet className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          )}
          <span className="font-medium text-slate-200">{row.title}</span>
        </div>
      ),
    },
    {
      header: 'Category',
      accessor: 'type',
      render: (row) => <span className="text-slate-300 font-medium text-xs">{row.type}</span>,
    },
    {
      header: 'Format',
      accessor: 'format',
      render: (row) => (
        <span
          className={`font-mono text-xs font-semibold px-2 py-0.5 rounded border ${
            row.format === 'PDF'
              ? 'bg-rose-950/40 border-rose-800/50 text-rose-300'
              : 'bg-emerald-950/40 border-emerald-800/50 text-emerald-300'
          }`}
        >
          {row.format}
        </span>
      ),
    },
    {
      header: 'Generated Date',
      accessor: 'generatedDate',
      render: (row) => <span className="font-mono text-xs text-slate-400">{row.generatedDate}</span>,
    },
    {
      header: 'Size',
      accessor: 'size',
      render: (row) => <span className="font-mono text-xs text-slate-300">{row.size}</span>,
    },
    {
      header: 'Status',
      accessor: 'status',
      render: (row) => <StatusBadge status={row.status} size="xs" />,
    },
    {
      header: 'Action',
      render: (row) => (
        <button
          type="button"
          disabled={downloadingId === row.id}
          onClick={() => handleTriggerDownload(row)}
          className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded bg-[#10151D] border border-[#222E3E] text-slate-300 hover:text-cyan-400 hover:border-cyan-500/40 transition-colors text-xs disabled:opacity-50"
        >
          {downloadingId === row.id ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-cyan-400" />
          ) : (
            <Download className="w-3.5 h-3.5" />
          )}
          <span>{downloadingId === row.id ? 'Saving...' : 'Download'}</span>
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <PageHeader
        title="Quality Inspection Reports"
        subtitle="Generate, catalog and download certified automotive manufacturing quality reports in ReportLab PDF or CSV format."
      >
        <button
          type="button"
          onClick={fetchReports}
          disabled={isLoading}
          className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-lg bg-[#1B2430] border border-[#222E3E] text-slate-300 hover:text-white hover:bg-[#222E3E] transition-colors text-xs font-semibold disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-blue-400 ${isLoading ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline">Refresh Archive</span>
        </button>
      </PageHeader>

      {/* Generation success notice */}
      {notice && (
        <div
          className={`p-3 rounded-lg text-xs flex items-center justify-between border animate-in fade-in ${
            notice.type === 'error'
              ? 'bg-rose-950/40 border-rose-800/50 text-rose-300'
              : 'bg-emerald-950/40 border-emerald-800/50 text-emerald-300'
          }`}
        >
          <div className="flex items-center space-x-2">
            {notice.type === 'error' ? (
              <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            ) : (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            )}
            <span>{notice.msg}</span>
          </div>
          <button
            onClick={() => setNotice(null)}
            className="text-slate-400 hover:text-white text-xs ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-950/30 border border-rose-800/40 text-xs text-rose-300 flex items-start space-x-2.5">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-rose-200">Failed to fetch report archive</p>
            <p className="font-mono text-[11px] text-rose-300/80">{error}</p>
          </div>
        </div>
      )}

      {/* Report Generation Interface Card */}
      <div className="bg-[#151C26] border border-[#222E3E] rounded-xl p-5 shadow-lg shadow-black/20 space-y-4">
        <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-blue-400" />
              <span>Configure Quality Audit Report</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Select report specifications to generate an audit document directly from database inspection records.
            </p>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-900/50 text-emerald-300 border border-emerald-700/50">
            ReportLab PDF Engine Active
          </span>
        </div>

        <form onSubmit={handleGenerateReport} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <FormInput
            label="Report Category"
            type="select"
            value={selectedReportType}
            onChange={(e) => setSelectedReportType(e.target.value)}
            options={[
              { value: 'Defect Analysis', label: 'Defect Analysis Report' },
              { value: 'Inspection Summary', label: 'Component Inspection Summary' },
              { value: 'Quality Performance', label: 'Batch Quality & Yield Audit' },
              { value: 'Batch Audit', label: 'Batch Audit Report' },
            ]}
          />

          <FormInput
            label="Target Batch"
            type="select"
            value={selectedBatch}
            onChange={(e) => setSelectedBatch(e.target.value)}
            options={[
              { value: 'ALL', label: 'All Active Batches' },
              { value: 'BATCH-2026-A1', label: 'Batch 2026-A1' },
              { value: 'BATCH-2026-A2', label: 'Batch 2026-A2' },
              { value: 'BATCH-2026-B1', label: 'Batch 2026-B1' },
              { value: 'BATCH-2026-B2', label: 'Batch 2026-B2' },
              { value: 'BATCH-2026-C1', label: 'Batch 2026-C1' },
            ]}
          />

          <FormInput
            label="Audit Period"
            type="select"
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            options={[
              { value: 'Last 7 Days', label: 'Last 7 Days' },
              { value: 'Last 14 Days', label: 'Last 14 Days' },
              { value: 'Last 30 Days', label: 'Last 30 Days' },
              { value: 'Current Month', label: 'Current Month' },
            ]}
          />

          <FormInput
            label="Output Format"
            type="select"
            value={selectedFormat}
            onChange={(e) => setSelectedFormat(e.target.value)}
            options={[
              { value: 'PDF', label: 'PDF Document (.pdf)' },
              { value: 'CSV', label: 'Raw CSV Dataset (.csv)' },
            ]}
          />

          <div className="sm:col-span-2 lg:col-span-4 flex items-center justify-between pt-2">
            <span className="text-[11px] text-slate-400">
              Generated reports are physically rendered in <code className="text-cyan-400 font-mono">backend/reports/</code> and streamable via API.
            </span>
            <button
              type="submit"
              disabled={isCompiling}
              className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition-colors flex items-center space-x-1.5 shadow-md shadow-blue-500/20 disabled:opacity-50"
            >
              {isCompiling ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <FileText className="w-3.5 h-3.5" />
              )}
              <span>{isCompiling ? 'Rendering Report...' : 'Compile & Save Report'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Report History Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-200 tracking-tight">
              Generated Report Archive
            </h3>
            <p className="text-xs text-slate-400">
              Previously compiled quality inspection records and analytics documents persisted in database
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {reports.length} Reports Archived
          </span>
        </div>

        {reports.length === 0 && !isLoading ? (
          <div className="bg-[#151C26] border border-[#222E3E] rounded-xl p-10 text-center space-y-2">
            <FileText className="w-10 h-10 text-slate-600 mx-auto" />
            <p className="text-sm font-semibold text-slate-300">No reports generated yet</p>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Configure parameters above and click "Compile & Save Report" to render your first PDF or CSV document.
            </p>
          </div>
        ) : (
          <DataTable columns={columns} data={reports} pageSize={8} />
        )}
      </div>
    </div>
  );
}
