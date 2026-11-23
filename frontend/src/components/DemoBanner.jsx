import React from 'react';
import { Info } from 'lucide-react';

export default function DemoBanner({ message = "Pre-production demonstration dataset. Live data ingestion connects in Phase 3." }) {
  return (
    <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs text-slate-400">
      <div className="flex items-center space-x-1.5 text-cyan-400 font-semibold uppercase tracking-wider text-[10px] bg-cyan-950/60 border border-cyan-800/50 px-2 py-0.5 rounded">
        <Info className="w-3 h-3 text-cyan-400" />
        <span>DEMO DATA</span>
      </div>
      <span className="truncate">{message}</span>
    </div>
  );
}

