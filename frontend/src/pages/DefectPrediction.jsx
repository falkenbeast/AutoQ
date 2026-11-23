import React, { useState, useEffect, useCallback } from 'react';
import {
  Cpu,
  AlertTriangle,
  CheckCircle2,
  Sliders,
  Sparkles,
  Info,
  Layers,
  ArrowRight,
  ShieldAlert,
  Server,
  Activity,
  Gauge,
  HelpCircle,
  History,
  RefreshCw,
} from 'lucide-react';
import PageHeader from '../components/PageHeader';
import FormInput from '../components/FormInput';
import StatusBadge from '../components/StatusBadge';
import DataTable from '../components/DataTable';
import ErrorBoundary from '../components/ErrorBoundary';
import api from '../services/api';

export default function DefectPrediction() {
  // Input parameters
  const [params, setParams] = useState({
    componentId: 'CMP-TRB-809',
    category: 'Powertrain',
    temperature: 745.0,
    pressure: 148.0,
    rotationalSpeed: 1520.0,
    toolWear: 110.0,
    stressTolerance: 340.0,
    cycleTime: 45.0,
    torqueResistance: 42.0,
    batch: 'BATCH-2026-B1',
    decisionThreshold: 0.50,
  });

  const [isEvaluating, setIsEvaluating] = useState(false);
  const [predictionResult, setPredictionResult] = useState(null);
  const [apiError, setApiError] = useState(null);
  const [engineHealth, setEngineHealth] = useState({
    isOnline: true,
    modelName: 'Random Forest Champion Pipeline',
    version: '1.0.0',
    rocAuc: '0.9830',
  });

  // Prediction History State
  const [predictionHistory, setPredictionHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const fetchPredictionHistory = useCallback(async () => {
    setLoadingHistory(true);
    try {
      const res = await api.getPredictions({ limit: 10 });
      const rawList = res?.items || (Array.isArray(res) ? res : []);
      const mapped = rawList.map((p) => ({
        id: p.id,
        displayId: `PRED-${String(p.id).padStart(4, '0')}`,
        componentId: p.component_id,
        batch: p.production_batch || 'N/A',
        threshold: p.decision_threshold ? `τ = ${Number(p.decision_threshold).toFixed(2)}` : 'τ = 0.50',
        probability: `${((p.defect_probability ?? 0) * 100).toFixed(1)}%`,
        status: (p.predicted_status || 'UNKNOWN').toUpperCase(),
        defectCategory: p.predicted_defect_category || 'None',
        date: p.created_at ? p.created_at.slice(0, 16).replace('T', ' ') : 'Just now',
        raw: p,
      }));
      setPredictionHistory(mapped);
    } catch (err) {
      console.warn('Failed to load prediction history:', err);
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    fetchPredictionHistory();
  }, [fetchPredictionHistory]);

  useEffect(() => {
    api.checkHealth()
      .then((res) => {
        if (res && res.ml_engine) {
          setEngineHealth({
            isOnline: Boolean(res.ml_engine.model_available),
            modelName: res.ml_engine.model_name || 'Random Forest Champion Pipeline',
            version: res.ml_engine.model_version || '1.0.0',
            rocAuc: String(res.ml_engine.test_roc_auc || '0.9830'),
          });
        }
      })
      .catch(() => {
        setEngineHealth((prev) => ({ ...prev, isOnline: false }));
      });
  }, []);

  const handleInputChange = (field, value) => {
    setParams((prev) => ({ ...prev, [field]: value }));
  };

  const handleEvaluateClick = async (e) => {
    e.preventDefault();
    setIsEvaluating(true);
    setApiError(null);

    const payload = {
      component_id: params.componentId.trim().toUpperCase(),
      component_category: params.category,
      manufacturing_temperature: Number(params.temperature),
      pressure: Number(params.pressure),
      production_batch: params.batch.trim().toUpperCase(),
      decision_threshold: Number(params.decisionThreshold),
      rotational_speed: Number(params.rotationalSpeed),
      tool_wear: Number(params.toolWear),
      stress_tolerance: params.stressTolerance ? Number(params.stressTolerance) : null,
      cycle_time: params.cycleTime ? Number(params.cycleTime) : null,
      torque_resistance: params.torqueResistance ? Number(params.torqueResistance) : null,
    };

    try {
      const response = await api.predictDefect(payload);
      setPredictionResult(response);
      fetchPredictionHistory();
    } catch (err) {
      console.error('Prediction API Error:', err);
      setApiError(err.message || 'Failed to communicate with AutoQ ML Inference Engine.');
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <PageHeader
        title="Defect Prediction Engine"
        subtitle="Evaluate automotive component inspection parameters using the AutoQ machine learning engine."
      />

      {/* Architectural Operational State Banner */}
      <div className="bg-[#151C26] border border-blue-500/30 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-lg shadow-black/20">
        <div className="flex items-start space-x-3">
          <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400 mt-0.5 sm:mt-0 flex-shrink-0">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-xs sm:text-sm font-bold text-slate-100 flex items-center gap-2">
              <span>ML Engine: {engineHealth.modelName}</span>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                engineHealth.isOnline
                  ? 'bg-emerald-900/60 text-emerald-300 border-emerald-700/50'
                  : 'bg-rose-900/60 text-rose-300 border-rose-700/50'
              }`}>
                {engineHealth.isOnline ? `Live Inference Active (v${engineHealth.version})` : 'ML Subsystem Offline'}
              </span>
            </h4>
            <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">
              Evaluating physical parameters through Scikit-learn ColumnTransformer and Random Forest (ROC-AUC: {engineHealth.rocAuc}). Calibrated probabilities and root-cause failure mode attribution are persisted to SQLite.
            </p>
          </div>
        </div>

        {/* Operating Point / Threshold Configuration */}
        <div className="flex items-center space-x-2 bg-[#10151D] border border-[#222E3E] rounded-lg p-1.5 self-end sm:self-auto">
          <span className="text-[11px] text-slate-400 font-medium pl-1.5 flex items-center gap-1">
            <Sliders className="w-3.5 h-3.5 text-cyan-400" />
            <span>Threshold (τ):</span>
          </span>
          <button
            type="button"
            onClick={() => handleInputChange('decisionThreshold', 0.50)}
            className={`px-2.5 py-1 rounded text-xs font-mono font-semibold transition-colors ${
              params.decisionThreshold === 0.50
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            0.50 (Standard)
          </button>
          <button
            type="button"
            onClick={() => handleInputChange('decisionThreshold', 0.35)}
            className={`px-2.5 py-1 rounded text-xs font-mono font-semibold transition-colors ${
              params.decisionThreshold === 0.35
                ? 'bg-cyan-600 text-white'
                : 'text-slate-400 hover:text-slate-200'
            }`}
            title="High-Sensitivity QA Threshold (Recommended: Maximize Defect Recall to 89.7%)"
          >
            0.35 (High-Recall)
          </button>
        </div>
      </div>

      {apiError && (
        <div className="bg-rose-950/40 border border-rose-800/50 rounded-xl p-4 text-xs text-rose-200 flex items-start space-x-2.5 shadow-lg animate-in fade-in">
          <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-bold uppercase tracking-wider block mb-0.5">Prediction Service Warning</span>
            <span>{apiError}</span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Form: Parameter Inputs (7 cols) */}
        <div className="lg:col-span-7 bg-[#151C26] border border-[#222E3E] rounded-xl p-6 shadow-lg shadow-black/20 space-y-5">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
                <Layers className="w-4 h-4 text-blue-400" />
                <span>Inspection Parameter Inputs</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Enter component manufacturing readings to evaluate defect probability.
              </p>
            </div>
            <span className="text-[11px] font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-800/40 px-2 py-0.5 rounded">
              Active τ = {params.decisionThreshold.toFixed(2)}
            </span>
          </div>

          <form onSubmit={handleEvaluateClick} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormInput
                label="Component ID"
                name="componentId"
                value={params.componentId}
                onChange={(e) => handleInputChange('componentId', e.target.value)}
                placeholder="e.g. CMP-TRB-809"
                disabled={isEvaluating}
                required
              />

              <FormInput
                label="Production Batch Code"
                name="batch"
                value={params.batch}
                onChange={(e) => handleInputChange('batch', e.target.value)}
                placeholder="e.g. BATCH-2026-B1"
                disabled={isEvaluating}
                required
              />

              <FormInput
                label="Component Subsystem Category"
                name="category"
                type="select"
                value={params.category}
                onChange={(e) => handleInputChange('category', e.target.value)}
                disabled={isEvaluating}
                options={[
                  { value: 'Powertrain', label: 'Powertrain (Heavy-Duty: Variant H)' },
                  { value: 'Engine', label: 'Engine Subsystem (Heavy-Duty: Variant H)' },
                  { value: 'Braking System', label: 'Braking System (Medium-Duty: Variant M)' },
                  { value: 'Transmission', label: 'Transmission (Medium-Duty: Variant M)' },
                  { value: 'Chassis & Steering', label: 'Chassis & Mounts (Light-Duty: Variant L)' },
                ]}
              />

              <FormInput
                label="Manufacturing Temp"
                name="temperature"
                type="number"
                unit="°C"
                step="0.1"
                value={params.temperature}
                onChange={(e) => handleInputChange('temperature', e.target.value)}
                disabled={isEvaluating}
                helperText="Optimal casting window: 720°C - 760°C (or ambient ~35°C)"
                required
              />

              <FormInput
                label="Die Injection / Clamping Pressure"
                name="pressure"
                type="number"
                unit="bar"
                step="0.5"
                value={params.pressure}
                onChange={(e) => handleInputChange('pressure', e.target.value)}
                disabled={isEvaluating}
                helperText="Standard hydraulic pressure: 135 - 155 bar"
                required
              />

              <FormInput
                label="Spindle Rotational Speed"
                name="rotationalSpeed"
                type="number"
                unit="rpm"
                step="1"
                value={params.rotationalSpeed}
                onChange={(e) => handleInputChange('rotationalSpeed', e.target.value)}
                disabled={isEvaluating}
                helperText="Milling speed: 1350 - 1800 rpm"
                required
              />

              <FormInput
                label="Cumulative Tool Wear"
                name="toolWear"
                type="number"
                unit="min"
                step="1"
                value={params.toolWear}
                onChange={(e) => handleInputChange('toolWear', e.target.value)}
                disabled={isEvaluating}
                helperText="Warning threshold: > 200 min"
                required
              />

              <FormInput
                label="Torsional Resistance"
                name="torqueResistance"
                type="number"
                unit="Nm"
                step="0.5"
                value={params.torqueResistance}
                onChange={(e) => handleInputChange('torqueResistance', e.target.value)}
                disabled={isEvaluating}
                helperText="Torque envelope: 20 - 55 Nm"
              />
            </div>

            <div className="pt-2 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <span className="text-[11px] text-slate-400 flex items-center gap-1.5">
                <Server className="w-3.5 h-3.5 text-blue-400" />
                <span>Endpoint: <code className="font-mono text-slate-300">POST /api/predictions</code></span>
              </span>

              <button
                type="submit"
                disabled={isEvaluating}
                className="w-full sm:w-auto px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs flex items-center justify-center space-x-2 transition-colors disabled:opacity-60 shadow-lg shadow-blue-600/20"
              >
                {isEvaluating ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Executing ML Pipeline...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Run Defect Prediction</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Right Panel: Live Prediction Result Area (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <ErrorBoundary>
            {isEvaluating ? (
              /* INFERENCE IN PROGRESS STATE */
              <div className="bg-[#151C26] border border-blue-500/40 rounded-xl p-6 shadow-lg shadow-black/20 text-center flex flex-col items-center justify-center min-h-[420px] animate-pulse">
                <div className="w-14 h-14 rounded-2xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400 mb-4 shadow-inner">
                  <div className="w-7 h-7 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                </div>

                <span className="px-2.5 py-1 rounded-full bg-blue-500/20 border border-blue-500/40 text-blue-300 font-mono text-[11px] font-bold uppercase tracking-wider mb-2">
                  EVALUATING SENSORS
                </span>

                <h4 className="text-base font-bold text-slate-100 mb-2">
                  Executing Random Forest Inference
                </h4>

                <p className="text-xs text-slate-400 max-w-sm mb-4 leading-relaxed">
                  Transforming mechanical parameters through Scikit-learn ColumnTransformer and evaluating defect probability...
                </p>

                <div className="text-[11px] font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-800/40 px-3 py-1 rounded">
                  Evaluating at τ = {params.decisionThreshold.toFixed(2)}
                </div>
              </div>
            ) : !predictionResult ? (
              /* AWAITING INFERENCE STATE */
              <div className="bg-[#151C26] border border-[#222E3E] rounded-xl p-6 shadow-lg shadow-black/20 text-center flex flex-col items-center justify-center min-h-[420px]">
                <div className="w-14 h-14 rounded-2xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400 mb-4 shadow-inner">
                  <Activity className="w-7 h-7" />
                </div>

                <span className="px-2.5 py-1 rounded-full bg-blue-500/20 border border-blue-500/40 text-blue-300 font-mono text-[11px] font-bold uppercase tracking-wider mb-2">
                  AWAITING PARAMETERS
                </span>

                <h4 className="text-base font-bold text-slate-100 mb-2">
                  AutoQ Real-Time Inference Engine
                </h4>

                <p className="text-xs text-slate-400 max-w-sm mb-6 leading-relaxed">
                  Enter component inspection parameters on the left and submit to execute the trained Random Forest model. Calibrated probabilities and root-cause failure mode attribution will appear here.
                </p>

                <div className="w-full bg-[#10151D] border border-[#222E3E] rounded-lg p-3 text-left space-y-2 text-xs">
                  <div className="flex items-center justify-between text-[11px] border-b border-slate-800 pb-1.5">
                    <span className="text-slate-400 font-medium">Champion Classifier:</span>
                    <span className="font-mono text-blue-400 font-semibold">{engineHealth.modelName}</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] border-b border-slate-800 pb-1.5">
                    <span className="text-slate-400 font-medium">Test ROC-AUC:</span>
                    <span className="font-mono text-emerald-400 font-semibold">{engineHealth.rocAuc}</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400 font-medium">Active Operating Point:</span>
                    <span className="font-mono text-cyan-400 font-semibold">τ = {params.decisionThreshold.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            ) : predictionResult.model_status === 'MODEL_NOT_TRAINED' ? (
              /* MODEL AWAITING TRAINING NOTICE */
              <div className="bg-[#151C26] border border-amber-500/40 rounded-xl p-5 shadow-2xl space-y-4 animate-in fade-in duration-200">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold block">
                      Prediction Subsystem Status
                    </span>
                    <div className="mt-1 flex items-center space-x-2">
                      <StatusBadge status="MODEL_AWAITING_TRAINING" size="md" />
                      <span className="text-[10px] font-mono text-slate-400">
                        Component: {predictionResult.component_id || params.componentId}
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold block">
                      Inference State
                    </span>
                    <span className="text-xs font-mono font-bold text-amber-400">
                      Awaiting Artifacts
                    </span>
                  </div>
                </div>

                <div className="bg-amber-950/20 border border-amber-800/40 rounded-lg p-3 space-y-1.5">
                  <span className="font-bold text-[11px] text-amber-300 uppercase tracking-wider flex items-center gap-1.5">
                    <Info className="w-3.5 h-3.5 text-amber-400" />
                    <span>ML Pipeline Status Notice</span>
                  </span>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {predictionResult.message || predictionResult.recommendation || 'The ML inference engine is currently awaiting serialized model artifacts.'}
                  </p>
                </div>

                <div className="text-[10px] text-slate-500 flex items-center justify-between pt-1 border-t border-slate-800">
                  <span>Model: {predictionResult.model_name || engineHealth.modelName}</span>
                  <span>Evaluated: {new Date(predictionResult.evaluated_at || Date.now()).toLocaleTimeString()}</span>
                </div>
              </div>
            ) : (
              /* LIVE PREDICTION RESULT CARD */
              <div className={`bg-[#151C26] border rounded-xl p-5 shadow-2xl space-y-4 animate-in fade-in duration-200 ${
                (predictionResult.predicted_status || '').toUpperCase() === 'PASSED' ? 'border-emerald-500/40' : 'border-rose-500/40'
              }`}>
                {/* Header Status */}
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold block">
                      Prediction Outcome
                    </span>
                    <div className="mt-1 flex items-center space-x-2">
                      <StatusBadge status={(predictionResult.predicted_status || 'UNKNOWN').toUpperCase()} size="md" />
                      <span className="text-[10px] font-mono text-slate-400">
                        ID: #{predictionResult.id || predictionResult.prediction_id || 'N/A'}
                      </span>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold block">
                      Defect Probability
                    </span>
                    <span className={`text-2xl font-mono font-bold ${
                      (predictionResult.predicted_status || '').toUpperCase() === 'PASSED' ? 'text-emerald-400' : 'text-rose-400'
                    }`}>
                      {((predictionResult.defect_probability ?? 0) * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Confidence & Risk Level Bar */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Model Confidence</span>
                    <span className="font-mono font-bold text-slate-200">
                      {predictionResult.confidence != null ? ((Number(predictionResult.confidence) * 100).toFixed(1)) : '95.0'}%
                    </span>
                  </div>
                  <div className="w-full bg-[#10151D] rounded-full h-2.5 overflow-hidden border border-[#222E3E]">
                    <div
                      className={`h-2.5 rounded-full transition-all duration-500 ${
                        (predictionResult.predicted_status || '').toUpperCase() === 'PASSED' ? 'bg-emerald-500' : 'bg-rose-500'
                      }`}
                      style={{ width: `${Math.max(5, (predictionResult.defect_probability ?? 0) * 100)}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-slate-500">
                    <span>0% (Safe)</span>
                    <span className="font-mono text-cyan-400">
                      Threshold: {((predictionResult.decision_threshold ?? params.decisionThreshold ?? 0.50) * 100).toFixed(0)}%
                    </span>
                    <span>100% (Defect)</span>
                  </div>
                </div>

                {/* Secondary Root-Cause Failure Attribution */}
                {(predictionResult.predicted_status || '').toUpperCase() === 'DEFECTIVE' && (
                  <div className="bg-rose-950/30 border border-rose-800/40 rounded-lg p-3 space-y-1">
                    <span className="text-[11px] font-bold text-rose-300 uppercase tracking-wider block">
                      Attributed Root-Cause Failure Mode
                    </span>
                    <p className="text-xs font-semibold text-rose-400">
                      {predictionResult.predicted_defect_category || 'General Manufacturing Non-Conformance'}
                    </p>
                  </div>
                )}

                {/* Contributing Factors */}
                {Array.isArray(predictionResult.contributing_factors) && predictionResult.contributing_factors.length > 0 && (
                  <div className="bg-[#10151D] border border-[#222E3E] rounded-lg p-3.5 space-y-2">
                    <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider block">
                      Key Influencing Telemetry Drivers
                    </span>
                    <div className="space-y-2 text-xs">
                      {predictionResult.contributing_factors.map((factor, idx) => (
                        <div key={idx} className="border-b border-slate-800/60 pb-1.5 last:border-0 last:pb-0">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-slate-300">{factor.factor_name || factor.name || 'Telemetry Feature'}</span>
                            <span className="font-mono text-rose-400 font-semibold">
                              +{((factor.impact_weight ?? 0.2) * 100).toFixed(0)}% weight
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400 mt-0.5">{factor.description || 'Observed deviation from normal operating tolerances.'}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Actionable Engineering Recommendation */}
                <div className={`rounded-lg p-3 text-xs space-y-1 border ${
                  (predictionResult.predicted_status || '').toUpperCase() === 'PASSED'
                    ? 'bg-emerald-950/20 border-emerald-800/30 text-emerald-200'
                    : 'bg-rose-950/20 border-rose-800/30 text-rose-200'
                }`}>
                  <span className="font-bold text-[11px] uppercase tracking-wide flex items-center gap-1.5">
                    {(predictionResult.predicted_status || '').toUpperCase() === 'PASSED' ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                    )}
                    <span>Quality Assurance Directive</span>
                  </span>
                  <p className="text-[11px] text-slate-300 leading-relaxed">
                    {predictionResult.recommendation || 'Proceed with standard component QA process.'}
                  </p>
                </div>

                {/* Footer Meta */}
                <div className="text-[10px] text-slate-500 flex items-center justify-between pt-1 border-t border-slate-800">
                  <span>Model: {predictionResult.model_name || engineHealth.modelName || 'Random Forest'}</span>
                  <span>Evaluated: {predictionResult.evaluated_at ? new Date(predictionResult.evaluated_at).toLocaleTimeString() : new Date().toLocaleTimeString()}</span>
                </div>
              </div>
            )}
          </ErrorBoundary>
        </div>
      </div>

      {/* Historical Prediction Evaluations Table */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-200 tracking-tight flex items-center gap-2">
              <History className="w-4 h-4 text-cyan-400" />
              <span>Recent ML Predictions History</span>
            </h3>
            <p className="text-xs text-slate-400">
              Evaluations executed by the Random Forest model and persisted to SQLite
            </p>
          </div>
          <button
            type="button"
            onClick={fetchPredictionHistory}
            disabled={loadingHistory}
            className="inline-flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-[#1B2430] border border-[#222E3E] text-slate-300 hover:text-white text-xs font-semibold disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-blue-400 ${loadingHistory ? 'animate-spin' : ''}`} />
            <span>Refresh History</span>
          </button>
        </div>

        {predictionHistory.length === 0 && !loadingHistory ? (
          <div className="bg-[#151C26] border border-[#222E3E] rounded-xl p-8 text-center space-y-2">
            <Cpu className="w-8 h-8 text-slate-600 mx-auto" />
            <p className="text-sm font-semibold text-slate-300">No predictions logged yet</p>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Configure parameters above and click "Run Defect Prediction" to evaluate components with the machine learning engine.
            </p>
          </div>
        ) : (
          <DataTable
            columns={[
              {
                header: 'Transaction ID',
                accessor: 'displayId',
                render: (row) => <span className="font-mono text-xs text-blue-400 font-semibold">{row.displayId}</span>,
              },
              {
                header: 'Component ID',
                accessor: 'componentId',
                render: (row) => <span className="font-mono text-xs text-slate-200 font-semibold">{row.componentId}</span>,
              },
              {
                header: 'Batch',
                accessor: 'batch',
                render: (row) => <span className="font-mono text-xs text-slate-300">{row.batch}</span>,
              },
              {
                header: 'Operating Point',
                accessor: 'threshold',
                render: (row) => <span className="font-mono text-xs text-cyan-400 bg-cyan-950/40 border border-cyan-800/40 px-1.5 py-0.5 rounded">{row.threshold}</span>,
              },
              {
                header: 'Defect Probability',
                accessor: 'probability',
                render: (row) => <span className="font-mono text-xs font-bold text-slate-100">{row.probability}</span>,
              },
              {
                header: 'Predicted Outcome',
                accessor: 'status',
                render: (row) => <StatusBadge status={row.status} size="xs" />,
              },
              {
                header: 'Failure Mode Attribution',
                accessor: 'defectCategory',
                render: (row) => (
                  <span className={`text-xs font-medium ${row.defectCategory && row.defectCategory !== 'None' ? 'text-rose-400' : 'text-slate-500'}`}>
                    {row.defectCategory}
                  </span>
                ),
              },
              {
                header: 'Timestamp',
                accessor: 'date',
                render: (row) => <span className="font-mono text-xs text-slate-400">{row.date}</span>,
              },
            ]}
            data={predictionHistory}
            pageSize={5}
          />
        )}
      </div>
    </div>
  );
}
