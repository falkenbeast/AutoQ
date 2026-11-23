import React from 'react';
import { Filter } from 'lucide-react';

export default function FilterDropdown({
  label,
  value,
  onChange,
  options = [],
  className = "",
}) {
  return (
    <div className={`flex items-center space-x-2 bg-[#10151D] border border-[#222E3E] rounded-lg px-3 py-1.5 text-xs text-slate-300 ${className}`}>
      <Filter className="w-3.5 h-3.5 text-slate-400" />
      {label && <span className="text-slate-400 whitespace-nowrap">{label}:</span>}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="bg-transparent text-slate-200 font-medium focus:outline-none cursor-pointer"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value} className="bg-[#151C26] text-slate-200">
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

