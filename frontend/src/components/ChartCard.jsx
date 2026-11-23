import React from 'react';

export default function ChartCard({
  title,
  subtitle,
  children,
  action,
  isDemo = false,
  badgeText = null,
  className = "",
}) {
  return (
    <div className={`bg-[#151C26] border border-[#222E3E] rounded-xl p-5 shadow-lg shadow-black/20 flex flex-col ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-4 border-b border-slate-800/80 gap-2">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-sm sm:text-base font-semibold text-[#F1F5F9] tracking-tight">
              {title}
            </h3>
            {badgeText && (
              <span className="text-[9px] font-mono tracking-tight px-1.5 py-0.5 rounded bg-blue-950/60 text-cyan-300 border border-blue-800/50">
                {badgeText}
              </span>
            )}
            {isDemo && !badgeText && (
              <span className="text-[9px] font-mono tracking-tight px-1.5 py-0.5 rounded bg-slate-800/80 text-cyan-300 border border-slate-700">
                DEMO DATA
              </span>
            )}
          </div>
          {subtitle && (
            <p className="text-xs text-slate-400 mt-0.5">
              {subtitle}
            </p>
          )}
        </div>

        {action && (
          <div className="flex items-center space-x-2 text-xs">
            {action}
          </div>
        )}
      </div>

      {/* Chart Canvas */}
      <div className="flex-1 min-h-[260px] w-full flex items-center justify-center">
        {children}
      </div>
    </div>
  );
}

