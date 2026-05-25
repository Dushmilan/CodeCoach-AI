'use client';

import { ChevronLeft, ChevronRight as ChevronRightIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavigationControlsProps {
  onPrevious: () => void;
  onNext: () => void;
  disabled?: boolean;
  isCollapsed?: boolean;
}

export function NavigationControls({
  onPrevious,
  onNext,
  disabled = false,
  isCollapsed = false,
}: NavigationControlsProps) {
  return (
    <div
      className={cn(
        'px-3 py-3 border-b border-white/5 transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]',
        isCollapsed ? 'opacity-0 h-0 overflow-hidden py-0' : 'opacity-100 h-auto'
      )}
    >
      <div className="grid grid-cols-2 gap-1.5">
        <button
          onClick={onPrevious}
          disabled={disabled}
          className="flex items-center justify-center px-2 py-1.5 text-[10px] font-medium rounded-full bg-white/5 hover:bg-white/10 text-muted-foreground disabled:opacity-40 disabled:pointer-events-none transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] active:scale-[0.97]"
        >
          <ChevronLeft className="h-3 w-3 mr-1" strokeWidth={1} />
          Prev
        </button>
        <button
          onClick={onNext}
          disabled={disabled}
          className="flex items-center justify-center px-2 py-1.5 text-[10px] font-medium rounded-full bg-white/5 hover:bg-white/10 text-muted-foreground disabled:opacity-40 disabled:pointer-events-none transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] active:scale-[0.97]"
        >
          <ChevronRightIcon className="h-3 w-3 mr-1" strokeWidth={1} />
          Next
        </button>
      </div>
    </div>
  );
}
