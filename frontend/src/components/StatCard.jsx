import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function StatCard({
  title,
  value,
  subtitle,
  change,
  isPositive,
  icon: Icon,
  accentColor = "blue",
  isDemo = false,
  badgeText = null,
}) {
  const getAccentClass = () => {
    switch (accentColor) {
      case "emerald":
        return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
      case "rose":
        return "text-rose-400 bg-rose-500/10 border-rose-500/20";
      case "amber":
        return "text-amber-400 bg-amber-500/10 border-amber-500/20";
      case "cyan":
        return "text-cyan-400 bg-cyan-500/10 border-cyan-500/20";
      default:
        return "text-blue-400 bg-blue-500/10 border-blue-500/20";
    }
  };

  return (
    <div className="relative bg-[#151C26] border border-[#222E3E] rounded-xl p-5 hover:border-slate-700/80 transition-all duration-200 shadow-lg shadow-black/20 flex flex-col justify-between">
      {/* Top row */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            {title}
          </span>
          {badgeText && (
            <span className="text-[9px] font-mono tracking-tight px-1.5 py-0.5 rounded bg-blue-950/60 text-cyan-300 border border-blue-800/50">
              {badgeText}
            </span>
          )}
          {isDemo && !badgeText && (
            <span className="text-[9px] font-mono tracking-tight px-1.5 py-0.5 rounded bg-slate-800/80 text-cyan-300 border border-slate-700">
              DEMO
            </span>
          )}
        </div>
        {Icon && (
          <div className={`p-2 rounded-lg border ${getAccentClass()}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      {/* Main value */}
      <div className="my-1">
        <div className="text-2xl sm:text-3xl font-extrabold text-[#F1F5F9] tracking-tight">
          {value}
        </div>
      </div>

      {/* Trend & Subtitle footer */}
      <div className="flex items-center justify-between text-xs mt-3 pt-3 border-t border-slate-800/80">
        {change && (
          <div className="flex items-center space-x-1 font-medium">
            {isPositive === true ? (
              <span className="flex items-center text-emerald-400">
                <TrendingUp className="w-3.5 h-3.5 mr-0.5" />
                {change}
              </span>
            ) : isPositive === false ? (
              <span className="flex items-center text-rose-400">
                <TrendingDown className="w-3.5 h-3.5 mr-0.5" />
                {change}
              </span>
            ) : (
              <span className="flex items-center text-slate-400">
                <Minus className="w-3.5 h-3.5 mr-0.5" />
                {change}
              </span>
            )}
          </div>
        )}
        {subtitle && (
          <span className="text-slate-400 text-[11px] truncate ml-auto">
            {subtitle}
          </span>
        )}
      </div>
    </div>
  );
}

