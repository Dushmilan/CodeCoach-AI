'use client';

import { Shuffle, List } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FilterBarProps {
  currentFilter: 'all' | 'easy' | 'medium' | 'hard';
  onFilterChange: (filter: 'easy' | 'medium' | 'hard') => void;
  onAll: () => void;
  onRandom: () => void;
  isCollapsed?: boolean;
}

export function FilterBar({
  currentFilter,
  onFilterChange,
  onAll,
  onRandom,
  isCollapsed = false,
}: FilterBarProps) {
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy':
        return 'text-green-500 bg-green-500/10 border-green-500/20';
      case 'medium':
        return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20';
      case 'hard':
        return 'text-red-500 bg-red-500/10 border-red-500/20';
      default:
        return 'text-gray-500 bg-gray-500/10 border-gray-500/20';
    }
  };

  const getDifficultyIcon = (difficulty: string) => {
    switch (difficulty) {
      case 'easy':
        return '🟢';
      case 'medium':
        return '🟡';
      case 'hard':
        return '🔴';
      default:
        return '⚪';
    }
  };

  return (
    <div
      className={cn(
        'p-3 border-b border-border transition-all duration-300',
        isCollapsed ? 'opacity-0 h-0 overflow-hidden' : 'opacity-100 h-auto'
      )}
    >
      <div className="grid grid-cols-2 gap-2 mb-3">
        <button
          onClick={onAll}
          className={cn(
            'flex items-center justify-center px-2 py-1.5 text-xs font-medium rounded-md transition-colors',
            currentFilter === 'all'
              ? 'bg-primary text-primary-foreground'
              : 'bg-secondary hover:bg-secondary/80'
          )}
        >
          <List className="h-3 w-3 mr-1" />
          All
        </button>
        <button
          onClick={onRandom}
          className="flex items-center justify-center px-2 py-1.5 text-xs font-medium rounded-md bg-secondary hover:bg-secondary/80 transition-colors"
        >
          <Shuffle className="h-3 w-3 mr-1" />
          Random
        </button>
      </div>

      <div className="flex gap-1">
        {(['easy', 'medium', 'hard'] as const).map((diff) => (
          <button
            key={diff}
            onClick={() => onFilterChange(diff)}
            className={cn(
              'flex-1 px-2 py-1 text-xs font-medium rounded-md transition-colors',
              currentFilter === diff
                ? getDifficultyColor(diff)
                : 'bg-secondary hover:bg-secondary/80'
            )}
          >
            <span className="mr-1">{getDifficultyIcon(diff)}</span>
            {diff.charAt(0).toUpperCase() + diff.slice(1)}
          </button>
        ))}
      </div>
    </div>
  );
}
