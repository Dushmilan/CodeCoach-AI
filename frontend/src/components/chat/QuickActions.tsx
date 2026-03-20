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
    <div className="flex flex-wrap gap-2 mb-3">
      {QUICK_ACTIONS.map((action) => (
        <Button
          key={action.id}
          variant="outline"
          size="sm"
          onClick={() => onActionClick(action.mode)}
          disabled={disabled}
          className="text-xs"
        >
          <action.icon className="h-3 w-3 mr-1" />
          {action.label}
        </Button>
      ))}
    </div>
  );
}
