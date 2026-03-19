'use client';

export default function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="relative">
        <div className="w-12 h-12 rounded-full border-2 border-slate-700"></div>
        <div className="absolute top-0 left-0 w-12 h-12 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin"></div>
        <div className="absolute top-2 left-2 w-8 h-8 rounded-full border-2 border-cyan-300 border-t-transparent animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
      </div>
    </div>
  );
}