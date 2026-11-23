import React from 'react';

export default function LoadingState({ message = "Loading intelligence metrics..." }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mb-3"></div>
      <p className="text-xs text-slate-400 font-medium">{message}</p>
    </div>
  );
}

