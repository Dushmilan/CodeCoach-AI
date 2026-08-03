'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { PanelBoundary } from './useResizablePanels';

interface PanelResizerProps {
  boundary: PanelBoundary;
  label: string;
  onMouseDown: (e: React.MouseEvent) => void;
  onResizeBy: (boundary: PanelBoundary, deltaX: number) => void;
  isActive?: boolean;
}

const STEP = 16;

export function PanelResizer({
  boundary,
  label,
  onMouseDown,
  onResizeBy,
  isActive = false,
}: PanelResizerProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      onResizeBy(boundary, -STEP);
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      onResizeBy(boundary, STEP);
    }
  };

  return (
    <div
      role="separator"
      aria-orientation="vertical"
      aria-label={label}
      tabIndex={0}
      onMouseDown={onMouseDown}
      onKeyDown={handleKeyDown}
      className={cn(
        'group relative flex-shrink-0 w-1.5 cursor-col-resize outline-none transition-colors',
        isActive
          ? 'bg-white/[0.08]'
          : 'bg-transparent hover:bg-white/[0.06] focus-visible:bg-white/[0.08]',
      )}
    >
      <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 w-px bg-white/[0.08] transition-colors group-hover:bg-primary/40 group-focus-visible:bg-primary/40" />
    </div>
  );
}
