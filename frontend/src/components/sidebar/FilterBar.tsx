'use client';

import { ShuffleIcon, RadixCodeIcon } from '@/components/ui/icons';
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
        return 'text-green-400 bg-green-500/10';
      case 'medium':
        return 'text-yellow-400 bg-yellow-500/10';
      case 'hard':
        return 'text-red-400 bg-red-500/10';
      default:
        return 'text-gray-400 bg-gray-500/10';
    }
  };

  return (
    <div
      className={cn(
        'px-3 py-3 border-b border-white/5 transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]',
        isCollapsed ? 'opacity-0 h-0 overflow-hidden py-0' : 'opacity-100 h-auto'
      )}
    >
      <div className="grid grid-cols-2 gap-2 mb-2">
        <button
          onClick={onAll}
          className={cn(
            'flex items-center justify-center px-2 py-1.5 text-[10px] font-medium rounded-full tracking-wide transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] active:scale-[0.97]',
            currentFilter === 'all'
              ? 'bg-primary text-primary-foreground'
              : 'bg-white/5 hover:bg-white/10 text-muted-foreground'
          )}
        >
          <RadixCodeIcon className="h-3 w-3 mr-1.5" />
          All
        </button>
        <button
          onClick={onRandom}
          className="flex items-center justify-center px-2 py-1.5 text-[10px] font-medium rounded-full tracking-wide bg-white/5 hover:bg-white/10 text-muted-foreground transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] active:scale-[0.97]"
        >
          <ShuffleIcon className="h-3 w-3 mr-1.5" />
          Random
        </button>
      </div>

      <div className="flex gap-1.5">
        {(['easy', 'medium', 'hard'] as const).map((diff) => (
          <button
            key={diff}
            onClick={() => onFilterChange(diff)}
            className={cn(
              'flex-1 px-2 py-1 text-[10px] font-medium rounded-full tracking-wide uppercase transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] active:scale-[0.97]',
              currentFilter === diff
                ? getDifficultyColor(diff)
                : 'bg-white/5 hover:bg-white/10 text-muted-foreground/60'
            )}
          >
            {diff}
          </button>
        ))}
      </div>
    </div>
  );
}
