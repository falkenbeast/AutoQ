import React, { useEffect } from 'react';
import { X } from 'lucide-react';

export default function Modal({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  footer,
  maxWidth = "max-w-2xl",
}) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="fixed inset-0"
        onClick={onClose}
        aria-hidden="true"
      />
      
      <div className={`relative bg-[#151C26] border border-[#222E3E] rounded-xl shadow-2xl w-full ${maxWidth} z-10 overflow-hidden flex flex-col max-h-[90vh]`}>
        {/* Modal Header */}
        <div className="flex items-start justify-between p-5 border-b border-[#222E3E] bg-[#10151D]/60">
          <div>
            <h3 className="text-base sm:text-lg font-bold text-[#F1F5F9] tracking-tight">
              {title}
            </h3>
            {subtitle && (
              <p className="text-xs text-[#94A3B8] mt-0.5">
                {subtitle}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-100 p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-4">
          {children}
        </div>

        {/* Modal Footer */}
        {footer && (
          <div className="flex items-center justify-end space-x-3 p-4 border-t border-[#222E3E] bg-[#10151D]/40">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}

