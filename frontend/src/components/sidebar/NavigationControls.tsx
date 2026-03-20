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
        'p-3 border-b border-border transition-all duration-300',
        isCollapsed ? 'opacity-0 h-0 overflow-hidden' : 'opacity-100 h-auto'
      )}
    >
      <div className="grid grid-cols-2 gap-2">
        <button
          onClick={onPrevious}
          disabled={disabled}
          className="flex items-center justify-center px-2 py-1.5 text-xs font-medium rounded-md bg-secondary hover:bg-secondary/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronLeft className="h-3 w-3 mr-1" />
          Prev
        </button>
        <button
          onClick={onNext}
          disabled={disabled}
          className="flex items-center justify-center px-2 py-1.5 text-xs font-medium rounded-md bg-secondary hover:bg-secondary/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronRightIcon className="h-3 w-3 mr-1" />
          Next
        </button>
      </div>
    </div>
  );
}
