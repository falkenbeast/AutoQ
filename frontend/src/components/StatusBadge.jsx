import React from 'react';

export default function StatusBadge({ status, size = 'sm' }) {
  const norm = String(status || '').toUpperCase();

  const getStyle = () => {
    switch (norm) {
      case 'PASSED':
      case 'PASS':
      case 'NORMAL':
      case 'HEALTHY':
      case 'GENERATED':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'DEFECTIVE':
      case 'DEFECT':
      case 'FAIL':
      case 'HIGH':
      case 'CRITICAL':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      case 'MEDIUM':
      case 'WARNING':
      case 'PENDING':
      case 'IN_PROGRESS':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'LOW':
      case 'INFO':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      default:
        return 'bg-slate-700/30 text-slate-300 border-slate-700/50';
    }
  };

  const sizeClasses = size === 'xs' 
    ? 'text-[11px] px-2 py-0.5' 
    : size === 'md' 
    ? 'text-xs px-3 py-1 font-semibold' 
    : 'text-xs px-2.5 py-0.5';

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full border ${getStyle()} ${sizeClasses} tracking-wide transition-colors`}
    >
      <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${
        norm === 'PASSED' || norm === 'NORMAL' || norm === 'HEALTHY' || norm === 'GENERATED'
          ? 'bg-emerald-400'
          : norm === 'DEFECTIVE' || norm === 'HIGH' || norm === 'CRITICAL'
          ? 'bg-rose-400'
          : norm === 'MEDIUM' || norm === 'WARNING' || norm === 'PENDING'
          ? 'bg-amber-400'
          : 'bg-blue-400'
      }`} />
      {status}
    </span>
  );
}

