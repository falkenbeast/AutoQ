import React, { useState, useEffect, useCallback } from 'react';
import {
  Plus,
  Upload,
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle,
  Eye,
  Trash2,
  RefreshCw,
  Search,
  Check,
  X,
  FileDown,
} from 'lucide-react';
import PageHeader from '../components/PageHeader';
import DataTable from '../components/DataTable';
import StatusBadge from '../components/StatusBadge';
import SearchBar from '../components/SearchBar';
import FilterDropdown from '../components/FilterDropdown';
import Modal from '../components/Modal';
import FormInput from '../components/FormInput';
import api from '../services/api';

export default function Inspections() {
  const [inspections, setInspections] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [batchFilter, setBatchFilter] = useState('ALL');
  const [selectedInspection, setSelectedInspection] = useState(null);

  // Add Inspection Form State
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formValues, setFormValues] = useState({
    componentId: '',
    componentName: '',
    category: 'Powertrain',
    temperature: '',
    pressure: '',
    batch: 'BATCH-2026-A2',
    status: 'PASSED',
    defectCategory: 'None',
    notes: '',
  });
  const [formErrors, setFormErrors] = useState({});

  // CSV Upload State
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  // Delete Action State
  const [deletingId, setDeletingId] = useState(null);

  // Notification Toast
  const [toastMessage, setToastMessage] = useState(null);

  const showToast = (msg, type = 'success') => {
    setToastMessage({ msg, type });
    setTimeout(() => setToastMessage(null), 5000);
  };

  // Fetch Inspections from Backend API
  const fetchInspections = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = {
        limit: 100,
        status: statusFilter !== 'ALL' ? statusFilter : undefined,
        category: categoryFilter !== 'ALL' ? categoryFilter : undefined,
        batch: batchFilter !== 'ALL' ? batchFilter : undefined,
      };
      if (searchQuery.trim()) {
        params.search = searchQuery.trim();
      }
      const data = await api.getInspections(params);
      const items = data.items || data || [];
      // Normalize items for table display
      const normalized = items.map((item) => ({
        id: item.id,
        displayId: `AQ-2026-${String(item.id).padStart(4, '0')}`,
        componentId: item.component_id || item.componentId,
        componentName: item.component_name || item.componentName || 'General Component',
        category: item.component_category || item.category || 'Standard Subsystem',
        batch: item.production_batch || item.batch || 'BATCH-DEFAULT',
        temperature: item.manufacturing_temperature ?? item.temperature ?? 0,
        pressure: item.pressure ?? 0,
        date: item.inspection_date ? item.inspection_date.slice(0, 16).replace('T', ' ') : 'N/A',
        status: (item.inspection_result || item.status || 'Passed').toUpperCase(),
        defectCategory: item.defect_category || item.defectCategory || 'None',
        notes: item.notes || 'Routine physical inspection logged in database.',
        raw: item,
      }));
      setInspections(normalized);
      setTotalCount(data.total ?? normalized.length);
    } catch (err) {
      console.error('Failed to load inspections:', err);
      setError(err.message || 'Error fetching inspections from backend.');
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter, categoryFilter, batchFilter, searchQuery]);

  useEffect(() => {
    fetchInspections();
  }, [fetchInspections]);

  // Client-side quick filter fallback
  const filteredData = inspections.filter((item) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.componentId.toLowerCase().includes(q) ||
      item.componentName.toLowerCase().includes(q) ||
      item.batch.toLowerCase().includes(q)
    );
  });

  // Validate Add Form
  const validateForm = () => {
    const errors = {};
    if (!formValues.componentId.trim()) {
      errors.componentId = 'Component ID is required (e.g. CMP-BRK-101)';
    }
    if (!formValues.componentName.trim()) {
      errors.componentName = 'Component name is required';
    }
    if (!formValues.temperature || isNaN(formValues.temperature)) {
      errors.temperature = 'Valid temperature required (°C)';
    } else if (Number(formValues.temperature) <= 0 || Number(formValues.temperature) > 2500) {
      errors.temperature = 'Temperature must be between 1 and 2500°C';
    }
    if (!formValues.pressure || isNaN(formValues.pressure)) {
      errors.pressure = 'Valid pressure required (bar)';
    } else if (Number(formValues.pressure) <= 0 || Number(formValues.pressure) > 1000) {
      errors.pressure = 'Pressure must be between 1 and 1000 bar';
    }
    if (!formValues.batch.trim()) {
      errors.batch = 'Batch code is required';
    }
    if (formValues.status === 'DEFECTIVE' && formValues.defectCategory === 'None') {
      errors.defectCategory = 'Please specify defect category for defective parts';
    }
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Submit New Inspection to Backend
  const handleCreateInspection = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      const payload = {
        component_id: formValues.componentId.toUpperCase().trim(),
        component_name: formValues.componentName.trim(),
        component_category: formValues.category,
        manufacturing_temperature: parseFloat(formValues.temperature),
        pressure: parseFloat(formValues.pressure),
        production_batch: formValues.batch.trim(),
        inspection_result: formValues.status === 'DEFECTIVE' ? 'Defective' : 'Passed',
        defect_category: formValues.status === 'DEFECTIVE' ? formValues.defectCategory : null,
        notes: formValues.notes.trim() || 'Manual quality record logged via AutoQ dashboard.',
      };

      await api.createInspection(payload);
      showToast(`Inspection record for ${payload.component_id} saved successfully!`);
      setIsAddModalOpen(false);
      setFormValues({
        componentId: '',
        componentName: '',
        category: 'Powertrain',
        temperature: '',
        pressure: '',
        batch: 'BATCH-2026-A2',
        status: 'PASSED',
        defectCategory: 'None',
        notes: '',
      });
      fetchInspections();
    } catch (err) {
      console.error('Error saving inspection:', err);
      showToast(err.message || 'Failed to save inspection record.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle CSV file selection
  const handleFileChange = (e) => {
    const file = e.target.files && e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setUploadError(null);
      setUploadResult(null);
    }
  };

  // Submit CSV to backend
  const handleUploadSubmit = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadError(null);
    try {
      const res = await api.uploadInspectionsCsv(selectedFile);
      setUploadResult(res);
      showToast(`Batch CSV uploaded: ${res.imported_rows} rows imported successfully!`);
      fetchInspections();
    } catch (err) {
      console.error('CSV upload error:', err);
      setUploadError(err.message || 'Failed to process batch CSV.');
    } finally {
      setIsUploading(false);
    }
  };

  // Delete Inspection Record
  const handleDeleteInspection = async (id, componentId) => {
    if (!window.confirm(`Are you sure you want to delete inspection record #${id} (${componentId})?`)) {
      return;
    }

    setDeletingId(id);
    try {
      await api.deleteInspection(id);
      showToast(`Inspection record #${id} deleted.`);
      fetchInspections();
    } catch (err) {
      console.error('Error deleting inspection:', err);
      showToast(err.message || 'Failed to delete inspection record.', 'error');
    } finally {
      setDeletingId(null);
    }
  };

  // Table Columns
  const columns = [
    {
      header: 'Record ID',
      accessor: 'displayId',
      render: (row) => (
        <span className="font-mono text-xs font-semibold text-slate-400">
          {row.displayId}
        </span>
      ),
    },
    {
      header: 'Component ID',
      accessor: 'componentId',
      render: (row) => (
        <span className="font-mono font-semibold text-blue-400">
          {row.componentId}
        </span>
      ),
    },
    {
      header: 'Component Name',
      accessor: 'componentName',
      render: (row) => (
        <div>
          <span className="font-medium text-slate-200 block text-xs">{row.componentName}</span>
          <span className="text-[10px] text-slate-400">{row.category}</span>
        </div>
      ),
    },
    {
      header: 'Batch',
      accessor: 'batch',
      render: (row) => <span className="font-mono text-xs text-slate-300">{row.batch}</span>,
    },
    {
      header: 'Temp (°C)',
      accessor: 'temperature',
      render: (row) => (
        <span className="font-mono text-xs text-amber-400 font-semibold">
          {typeof row.temperature === 'number' ? row.temperature.toFixed(1) : row.temperature}
        </span>
      ),
    },
    {
      header: 'Pressure (bar)',
      accessor: 'pressure',
      render: (row) => (
        <span className="font-mono text-xs text-cyan-400 font-semibold">
          {typeof row.pressure === 'number' ? row.pressure.toFixed(1) : row.pressure}
        </span>
      ),
    },
    {
      header: 'Inspection Date',
      accessor: 'date',
      render: (row) => <span className="font-mono text-[11px] text-slate-400">{row.date}</span>,
    },
    {
      header: 'Result',
      accessor: 'status',
      render: (row) => <StatusBadge status={row.status} size="xs" />,
    },
    {
      header: 'Actions',
      render: (row) => (
        <div className="flex items-center space-x-1.5" onClick={(e) => e.stopPropagation()}>
          <button
            type="button"
            onClick={() => setSelectedInspection(row)}
            className="inline-flex items-center space-x-1 px-2 py-1 rounded bg-[#10151D] border border-[#222E3E] text-slate-300 hover:text-blue-400 hover:border-blue-500/50 transition-colors text-xs"
            title="View Details"
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Details</span>
          </button>
          <button
            type="button"
            disabled={deletingId === row.id}
            onClick={() => handleDeleteInspection(row.id, row.componentId)}
            className="p-1 rounded bg-[#10151D] border border-[#222E3E] text-slate-400 hover:text-rose-400 hover:border-rose-500/40 transition-colors text-xs disabled:opacity-50"
            title="Delete Record"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <PageHeader
        title="Component Inspections"
        subtitle="Manage automotive component inspection records, audit physical parameters and import batch inspection sheets from SQLite database."
      >
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={fetchInspections}
            disabled={isLoading}
            className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-lg bg-[#1B2430] border border-[#222E3E] text-slate-300 hover:text-white hover:bg-[#222E3E] transition-colors text-xs font-semibold disabled:opacity-50"
            title="Refresh Inspections"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-blue-400 ${isLoading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setSelectedFile(null);
              setUploadResult(null);
              setUploadError(null);
              setIsUploadModalOpen(true);
            }}
            className="inline-flex items-center space-x-2 px-3 py-2 rounded-lg bg-[#1B2430] border border-[#222E3E] text-slate-200 hover:text-white hover:bg-[#222E3E] transition-colors text-xs font-semibold"
          >
            <Upload className="w-3.5 h-3.5 text-cyan-400" />
            <span>Upload Batch CSV</span>
          </button>

          <button
            type="button"
            onClick={() => setIsAddModalOpen(true)}
            className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-colors text-xs font-semibold shadow-md shadow-blue-600/20"
          >
            <Plus className="w-4 h-4" />
            <span>Log Inspection</span>
          </button>
        </div>
      </PageHeader>

      {/* Toast Notification */}
      {toastMessage && (
        <div
          className={`p-3 rounded-lg text-xs flex items-center justify-between border animate-in fade-in ${
            toastMessage.type === 'error'
              ? 'bg-rose-950/40 border-rose-800/50 text-rose-300'
              : 'bg-emerald-950/40 border-emerald-800/50 text-emerald-300'
          }`}
        >
          <div className="flex items-center space-x-2">
            {toastMessage.type === 'error' ? (
              <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            ) : (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            )}
            <span>{toastMessage.msg}</span>
          </div>
          <button
            onClick={() => setToastMessage(null)}
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
          <div className="space-y-1">
            <p className="font-semibold text-rose-200">Unable to load inspections from database</p>
            <p className="font-mono text-[11px] text-rose-300/80">{error}</p>
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-[#151C26] border border-[#222E3E] rounded-xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 shadow-lg shadow-black/20">
        <SearchBar
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Search by Component ID, Part Name, or Batch Code..."
          className="w-full md:w-80"
        />

        <div className="flex flex-wrap items-center gap-2">
          <FilterDropdown
            label="Result"
            value={statusFilter}
            onChange={setStatusFilter}
            options={[
              { value: 'ALL', label: 'All Results' },
              { value: 'PASSED', label: 'Passed Only' },
              { value: 'DEFECTIVE', label: 'Defective Only' },
            ]}
          />

          <FilterDropdown
            label="Category"
            value={categoryFilter}
            onChange={setCategoryFilter}
            options={[
              { value: 'ALL', label: 'All Categories' },
              { value: 'Powertrain', label: 'Powertrain' },
              { value: 'Braking System', label: 'Braking System' },
              { value: 'Engine', label: 'Engine' },
              { value: 'Transmission', label: 'Transmission' },
              { value: 'Chassis & Steering', label: 'Chassis & Steering' },
            ]}
          />

          <FilterDropdown
            label="Batch"
            value={batchFilter}
            onChange={setBatchFilter}
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
      </div>

      {/* Table & Empty State */}
      {filteredData.length === 0 && !isLoading ? (
        <div className="bg-[#151C26] border border-[#222E3E] rounded-xl p-12 text-center space-y-3">
          <FileSpreadsheet className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-base font-semibold text-slate-200">No inspection records found</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            {searchQuery || statusFilter !== 'ALL' || categoryFilter !== 'ALL' || batchFilter !== 'ALL'
              ? 'No records match the current filter criteria. Try resetting filters or search terms.'
              : 'The database currently contains no inspection records. Use "Log Inspection" or "Upload Batch CSV" to register components.'}
          </p>
          <div className="pt-2">
            <button
              type="button"
              onClick={() => setIsAddModalOpen(true)}
              className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition-colors"
            >
              Log First Inspection
            </button>
          </div>
        </div>
      ) : (
        <DataTable
          columns={columns}
          data={filteredData}
          pageSize={10}
          onRowClick={(row) => setSelectedInspection(row)}
        />
      )}

      {/* Record Counter */}
      <div className="text-[11px] text-slate-500 font-mono text-right">
        Displaying {filteredData.length} of {totalCount} total inspection records in SQLite
      </div>

      {/* ADD INSPECTION MODAL */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Log Component Inspection Record"
        subtitle="Submit inspected parameters for quality audit cataloging and SQLite persistence."
        footer={
          <>
            <button
              type="button"
              onClick={() => setIsAddModalOpen(false)}
              disabled={isSubmitting}
              className="px-4 py-2 rounded-lg bg-[#10151D] border border-[#222E3E] text-slate-300 hover:text-white text-xs font-semibold"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleCreateInspection}
              disabled={isSubmitting}
              className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-500/20 disabled:opacity-50 flex items-center space-x-1.5"
            >
              {isSubmitting && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              <span>{isSubmitting ? 'Saving...' : 'Save Inspection'}</span>
            </button>
          </>
        }
      >
        <form onSubmit={handleCreateInspection} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormInput
              label="Component ID"
              name="componentId"
              value={formValues.componentId}
              onChange={(e) =>
                setFormValues({ ...formValues, componentId: e.target.value })
              }
              placeholder="e.g. CMP-BRK-501"
              required={true}
              error={formErrors.componentId}
            />

            <FormInput
              label="Component Name"
              name="componentName"
              value={formValues.componentName}
              onChange={(e) =>
                setFormValues({ ...formValues, componentName: e.target.value })
              }
              placeholder="e.g. High-Pressure Fuel Rail"
              required={true}
              error={formErrors.componentName}
            />

            <FormInput
              label="Subsystem Category"
              type="select"
              value={formValues.category}
              onChange={(e) =>
                setFormValues({ ...formValues, category: e.target.value })
              }
              options={[
                { value: 'Powertrain', label: 'Powertrain' },
                { value: 'Braking System', label: 'Braking System' },
                { value: 'Engine', label: 'Engine' },
                { value: 'Transmission', label: 'Transmission' },
                { value: 'Chassis & Steering', label: 'Chassis & Steering' },
              ]}
            />

            <FormInput
              label="Production Batch"
              name="batch"
              value={formValues.batch}
              onChange={(e) =>
                setFormValues({ ...formValues, batch: e.target.value })
              }
              placeholder="e.g. BATCH-2026-A2"
              required={true}
              error={formErrors.batch}
            />

            <FormInput
              label="Manufacturing Temperature (°C)"
              type="number"
              value={formValues.temperature}
              onChange={(e) =>
                setFormValues({ ...formValues, temperature: e.target.value })
              }
              placeholder="e.g. 742.5"
              step="0.1"
              required={true}
              error={formErrors.temperature}
            />

            <FormInput
              label="Hydraulic / Injection Pressure (bar)"
              type="number"
              value={formValues.pressure}
              onChange={(e) =>
                setFormValues({ ...formValues, pressure: e.target.value })
              }
              placeholder="e.g. 145.0"
              step="0.1"
              required={true}
              error={formErrors.pressure}
            />

            <FormInput
              label="Inspection Result"
              type="select"
              value={formValues.status}
              onChange={(e) =>
                setFormValues({
                  ...formValues,
                  status: e.target.value,
                  defectCategory: e.target.value === 'PASSED' ? 'None' : formValues.defectCategory,
                })
              }
              options={[
                { value: 'PASSED', label: 'Passed (Quality Compliant)' },
                { value: 'DEFECTIVE', label: 'Defective (Non-Compliant)' },
              ]}
            />

            {formValues.status === 'DEFECTIVE' ? (
              <FormInput
                label="Defect Category"
                type="select"
                value={formValues.defectCategory}
                onChange={(e) =>
                  setFormValues({ ...formValues, defectCategory: e.target.value })
                }
                options={[
                  { value: 'None', label: 'Select Defect Mode...' },
                  { value: 'Heat Dissipation Failure', label: 'Heat Dissipation Failure (HDF)' },
                  { value: 'Power Failure', label: 'Power Failure (PWF)' },
                  { value: 'Overstrain Failure', label: 'Overstrain Failure (OSF)' },
                  { value: 'Tool Wear Failure', label: 'Tool Wear Failure (TWF)' },
                  { value: 'Process Anomaly', label: 'Process Anomaly / Random Failure' },
                  { value: 'Multi-mode Failure', label: 'Multi-mode Failure' },
                ]}
                error={formErrors.defectCategory}
              />
            ) : (
              <div className="flex items-center text-xs text-emerald-400 bg-emerald-950/20 p-3 rounded-lg border border-emerald-800/30">
                <Check className="w-4 h-4 mr-2 flex-shrink-0" />
                <span>Component meets standard quality and tolerance specs.</span>
              </div>
            )}
          </div>

          <FormInput
            label="Inspector Observations & Notes"
            type="textarea"
            value={formValues.notes}
            onChange={(e) =>
              setFormValues({ ...formValues, notes: e.target.value })
            }
            placeholder="Add ultrasonic scan findings, dimension tolerance measurements or line supervisor observations..."
            rows={3}
          />
        </form>
      </Modal>

      {/* CSV UPLOAD MODAL */}
      <Modal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        title="Batch CSV Inspection Importer"
        subtitle="Ingest multiple automotive inspection records directly into the SQLite database."
        footer={
          <div className="flex items-center justify-between w-full">
            <span className="text-[11px] text-slate-500 font-mono">
              Accepted format: .csv (UTF-8)
            </span>
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => setIsUploadModalOpen(false)}
                className="px-4 py-2 rounded-lg bg-[#10151D] border border-[#222E3E] text-slate-300 hover:text-white text-xs font-semibold"
              >
                Close
              </button>
              <button
                type="button"
                disabled={!selectedFile || isUploading}
                onClick={handleUploadSubmit}
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition-colors disabled:opacity-50 flex items-center space-x-1.5 shadow-md shadow-blue-500/20"
              >
                {isUploading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                <span>{isUploading ? 'Ingesting...' : 'Import to Database'}</span>
              </button>
            </div>
          </div>
        }
      >
        <div className="space-y-4">
          {/* Dropzone */}
          <div className="border-2 border-dashed border-[#222E3E] hover:border-blue-500/60 rounded-xl p-6 text-center transition-colors bg-[#10151D]/60 flex flex-col items-center justify-center">
            <FileSpreadsheet className="w-10 h-10 text-cyan-400 mb-2" />
            <p className="text-xs font-semibold text-slate-200">
              Select an automotive inspection CSV file
            </p>
            <p className="text-[11px] text-slate-500 mt-1 max-w-sm">
              Columns: component_id, component_name, component_category, manufacturing_temperature, pressure, production_batch, inspection_result
            </p>
            <label className="mt-4 inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/40 text-xs font-medium cursor-pointer hover:bg-blue-600/30 transition-colors">
              <Upload className="w-3.5 h-3.5" />
              <span>Browse CSV File</span>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>
          </div>

          {/* Selected File Notice */}
          {selectedFile && (
            <div className="bg-[#10151D] border border-[#222E3E] rounded-lg p-3 flex items-center justify-between text-xs">
              <div className="flex items-center space-x-2">
                <FileSpreadsheet className="w-4 h-4 text-cyan-400" />
                <span className="font-mono text-slate-200">{selectedFile.name}</span>
                <span className="text-[10px] text-slate-500 font-mono">
                  ({(selectedFile.size / 1024).toFixed(1)} KB)
                </span>
              </div>
              <span className="text-emerald-400 text-[11px] font-semibold flex items-center space-x-1">
                <Check className="w-3.5 h-3.5" />
                <span>Ready to Import</span>
              </span>
            </div>
          )}

          {/* Upload Result Feedback */}
          {uploadResult && (
            <div className="bg-[#10151D] border border-[#222E3E] rounded-lg p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-200">Ingestion Result</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-950 border border-emerald-800 text-emerald-300">
                  {uploadResult.status}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="bg-[#151C26] p-2 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Total Rows</span>
                  <span className="font-mono font-bold text-slate-100 text-sm">{uploadResult.total_rows}</span>
                </div>
                <div className="bg-[#151C26] p-2 rounded border border-slate-800">
                  <span className="text-[10px] text-emerald-400 block">Imported</span>
                  <span className="font-mono font-bold text-emerald-400 text-sm">{uploadResult.imported_rows}</span>
                </div>
                <div className="bg-[#151C26] p-2 rounded border border-slate-800">
                  <span className="text-[10px] text-rose-400 block">Rejected / Dups</span>
                  <span className="font-mono font-bold text-rose-400 text-sm">{uploadResult.rejected_rows}</span>
                </div>
              </div>

              {uploadResult.errors && uploadResult.errors.length > 0 && (
                <div className="space-y-1">
                  <span className="text-[10px] font-semibold text-rose-400 uppercase tracking-wider block">
                    Validation Warnings
                  </span>
                  <div className="max-h-28 overflow-y-auto bg-rose-950/20 border border-rose-900/30 rounded p-2 text-[10px] font-mono text-rose-300 space-y-1">
                    {uploadResult.errors.map((err, idx) => (
                      <div key={idx}>• {err}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {uploadError && (
            <div className="p-3 rounded bg-rose-950/40 border border-rose-800/40 text-xs text-rose-300 flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
              <span>{uploadError}</span>
            </div>
          )}
        </div>
      </Modal>

      {/* COMPONENT DETAILS MODAL */}
      <Modal
        isOpen={Boolean(selectedInspection)}
        onClose={() => setSelectedInspection(null)}
        title={`Component Inspection: ${selectedInspection?.componentId || ''}`}
        subtitle={selectedInspection?.componentName}
        footer={
          <button
            type="button"
            onClick={() => setSelectedInspection(null)}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-500 transition-colors"
          >
            Close Details
          </button>
        }
      >
        {selectedInspection && (
          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 bg-[#10151D] p-4 rounded-lg border border-[#222E3E]">
              <div>
                <span className="text-slate-400 block text-[11px]">Database Primary Key</span>
                <span className="font-mono font-bold text-slate-200 mt-1 block">
                  #{selectedInspection.id}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Inspection Outcome</span>
                <div className="mt-1">
                  <StatusBadge status={selectedInspection.status} />
                </div>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Production Batch</span>
                <span className="font-mono font-bold text-slate-200 mt-1 block">
                  {selectedInspection.batch}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Subsystem Category</span>
                <span className="font-semibold text-slate-200 mt-1 block">
                  {selectedInspection.category}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Mfg Temperature</span>
                <span className="font-mono font-bold text-amber-400 mt-1 block">
                  {typeof selectedInspection.temperature === 'number'
                    ? selectedInspection.temperature.toFixed(1)
                    : selectedInspection.temperature}{' '}
                  °C
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Injection Pressure</span>
                <span className="font-mono font-bold text-cyan-400 mt-1 block">
                  {typeof selectedInspection.pressure === 'number'
                    ? selectedInspection.pressure.toFixed(1)
                    : selectedInspection.pressure}{' '}
                  bar
                </span>
              </div>
            </div>

            <div className="bg-[#10151D] p-4 rounded-lg border border-[#222E3E] space-y-2">
              <span className="text-slate-400 block font-semibold text-[11px]">
                Defect Classification & Quality Findings
              </span>
              <p
                className={`font-semibold ${
                  selectedInspection.defectCategory === 'None' || !selectedInspection.defectCategory
                    ? 'text-emerald-400'
                    : 'text-rose-400'
                }`}
              >
                {selectedInspection.defectCategory || 'No Defect Detected'}
              </p>
              <p className="text-slate-300 leading-relaxed bg-[#151C26] p-3 rounded border border-slate-800 text-[11px]">
                {selectedInspection.notes}
              </p>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
