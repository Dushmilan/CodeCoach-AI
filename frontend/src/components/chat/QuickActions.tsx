'use client';

import { LightningBoltIcon, ClockIcon, ReaderIcon, ExclamationTriangleIcon } from '@radix-ui/react-icons';
import { Button } from '@/components/ui/button';

export interface QuickAction {
  id: string;
  label: string;
  icon: React.ElementType;
  mode: string;
}

export const QUICK_ACTIONS: QuickAction[] = [
  { id: 'hint', label: 'Hint', icon: LightningBoltIcon, mode: 'hint' },
  { id: 'review', label: 'Review', icon: ClockIcon, mode: 'review' },
  { id: 'explain', label: 'Explain', icon: ReaderIcon, mode: 'explain' },
  { id: 'debug', label: 'Debug', icon: ExclamationTriangleIcon, mode: 'debug' },
];

interface QuickActionsProps {
  onActionClick: (mode: string) => void;
  disabled?: boolean;
}

export function QuickActions({ onActionClick, disabled = false }: QuickActionsProps) {
  return (
    <div className="flex flex-wrap gap-1.5 mb-2">
      {QUICK_ACTIONS.map((action) => (
        <button
          key={action.id}
          onClick={() => onActionClick(action.mode)}
          disabled={disabled}
          className="inline-flex items-center gap-1 px-2.5 py-1.5 text-[10px] font-medium tracking-wide text-muted-foreground/60 hover:text-foreground/80 bg-transparent hover:bg-white/[0.04] rounded-md disabled:opacity-40 disabled:pointer-events-none transition-all active:scale-[0.97]"
        >
          <action.icon className="h-3 w-3" strokeWidth={1} />
          {action.label}
        </button>
      ))}
    </div>
  );
}
