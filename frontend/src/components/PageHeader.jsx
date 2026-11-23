import React from 'react';
import { Calendar } from 'lucide-react';

export default function PageHeader({
  title,
  subtitle,
  children,
  showDateSelector = false,
  dateRange = "Last 14 Days",
  onDateRangeChange,
}) {
  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 mb-6 border-b border-[#222E3E] gap-4">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-[#F1F5F9] tracking-tight">
          {title}
        </h1>
        {subtitle && (
          <p className="text-sm text-[#94A3B8] mt-1 max-w-3xl leading-relaxed">
            {subtitle}
          </p>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        {showDateSelector && (
          <div className="flex items-center space-x-2 bg-[#1B2430] border border-[#222E3E] rounded-lg px-3 py-1.5 text-xs text-slate-300">
            <Calendar className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-slate-400 font-medium">Period:</span>
            <select
              value={dateRange}
              onChange={(e) => onDateRangeChange && onDateRangeChange(e.target.value)}
              className="bg-transparent text-slate-200 font-medium focus:outline-none cursor-pointer"
            >
              <option value="Today" className="bg-[#151C26] text-slate-200">Today</option>
              <option value="Last 7 Days" className="bg-[#151C26] text-slate-200">Last 7 Days</option>
              <option value="Last 14 Days" className="bg-[#151C26] text-slate-200">Last 14 Days</option>
              <option value="Last 30 Days" className="bg-[#151C26] text-slate-200">Last 30 Days</option>
              <option value="Current Batch (A2)" className="bg-[#151C26] text-slate-200">Current Batch (A2)</option>
            </select>
          </div>
        )}

        {children}
      </div>
    </div>
  );
}

