'use client';

import { Lightbulb, Clock, BookOpen, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface QuickAction {
  id: string;
  label: string;
  icon: React.ElementType;
  mode: string;
}

export const QUICK_ACTIONS: QuickAction[] = [
  { id: 'hint', label: 'Hint', icon: Lightbulb, mode: 'hint' },
  { id: 'review', label: 'Review', icon: Clock, mode: 'review' },
  { id: 'explain', label: 'Explain', icon: BookOpen, mode: 'explain' },
  { id: 'debug', label: 'Debug', icon: AlertTriangle, mode: 'debug' },
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
          className="inline-flex items-center gap-1 px-3 py-1.5 text-[10px] font-medium tracking-wide text-muted-foreground/70 bg-white/[0.03] hover:bg-white/[0.07] rounded-full ring-1 ring-white/5 disabled:opacity-40 disabled:pointer-events-none transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] active:scale-[0.97]"
        >
          <action.icon className="h-3 w-3" strokeWidth={1} />
          {action.label}
        </button>
      ))}
    </div>
  );
}
