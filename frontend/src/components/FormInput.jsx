import React from 'react';

export default function FormInput({
  label,
  name,
  type = "text",
  value,
  onChange,
  placeholder,
  error,
  unit,
  required = false,
  options = [],
  rows = 3,
  disabled = false,
  helperText,
}) {
  const baseClasses =
    "w-full bg-[#10151D] border text-slate-100 placeholder-slate-500 text-xs rounded-lg px-3 py-2.5 focus:outline-none transition-colors " +
    (error
      ? "border-rose-500/80 focus:border-rose-500"
      : "border-[#222E3E] focus:border-blue-500") +
    (disabled ? " opacity-50 cursor-not-allowed" : "");

  return (
    <div className="space-y-1">
      {label && (
        <label className="block text-xs font-medium text-slate-300">
          {label}
          {required && <span className="text-rose-400 ml-1">*</span>}
          {unit && <span className="text-slate-400 font-normal ml-1">({unit})</span>}
        </label>
      )}

      <div className="relative">
        {type === "select" ? (
          <select
            name={name}
            value={value}
            onChange={onChange}
            disabled={disabled}
            className={`${baseClasses} cursor-pointer`}
          >
            {options.map((opt) => (
              <option key={opt.value} value={opt.value} className="bg-[#151C26] text-slate-200">
                {opt.label}
              </option>
            ))}
          </select>
        ) : type === "textarea" ? (
          <textarea
            name={name}
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            rows={rows}
            disabled={disabled}
            className={baseClasses}
          />
        ) : (
          <div className="relative flex items-center">
            <input
              type={type}
              name={name}
              value={value}
              onChange={onChange}
              placeholder={placeholder}
              disabled={disabled}
              className={`${baseClasses} ${unit ? "pr-12" : ""}`}
            />
            {unit && (
              <span className="absolute right-3 text-xs text-slate-400 font-mono pointer-events-none">
                {unit}
              </span>
            )}
          </div>
        )}
      </div>

      {error ? (
        <p className="text-[11px] text-rose-400 font-medium">{error}</p>
      ) : helperText ? (
        <p className="text-[11px] text-slate-400">{helperText}</p>
      ) : null}
    </div>
  );
}

