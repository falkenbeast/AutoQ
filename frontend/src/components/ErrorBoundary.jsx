import React from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[AutoQ ErrorBoundary] Captured unhandled React error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[400px] flex items-center justify-center p-6">
          <div className="bg-[#151C26] border border-rose-500/40 rounded-2xl p-6 sm:p-8 max-w-lg w-full shadow-2xl shadow-black/40 text-center space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 mx-auto shadow-inner">
              <AlertTriangle className="w-7 h-7" />
            </div>

            <div className="space-y-1">
              <h3 className="text-base font-bold text-slate-100">
                View Rendering Error
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                An unexpected interface rendering issue was caught by the AutoQ runtime boundary. The underlying service or model responded, but rendering encountered an invalid parameter.
              </p>
            </div>

            {this.state.error && (
              <div className="bg-[#10151D] border border-rose-950/60 rounded-lg p-3 text-left">
                <span className="text-[10px] font-mono uppercase tracking-wider text-rose-400 block mb-1">
                  Exception Detail
                </span>
                <p className="text-xs font-mono text-rose-200/90 break-words">
                  {this.state.error.message || String(this.state.error)}
                </p>
              </div>
            )}

            <div className="pt-2 flex items-center justify-center gap-3">
              <button
                type="button"
                onClick={this.handleReset}
                className="px-4 py-2 rounded-lg bg-[#1B2430] border border-[#222E3E] text-slate-300 hover:text-white hover:bg-[#222E3E] transition-colors text-xs font-semibold"
              >
                Reset Component View
              </button>
              <button
                type="button"
                onClick={this.handleReload}
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-colors text-xs font-semibold flex items-center gap-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Reload Page</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

