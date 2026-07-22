'use client';

import { cn } from '@/lib/utils';
import { QuestionSummary } from '@/types';
import { CheckCircle, XCircle } from 'lucide-react';

interface QuestionItemProps {
  question: QuestionSummary;
  isSelected: boolean;
  isCurrentIndex: boolean;
  progress?: 'solved' | 'attempted';
  onClick: () => void;
  isCollapsed?: boolean;
}

export function QuestionItem({
  question,
  isSelected,
  isCurrentIndex,
  progress,
  onClick,
  isCollapsed = false,
}: QuestionItemProps) {
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
        'px-4 py-3 border-b border-white/5 cursor-pointer hover:bg-white/[0.03] transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]',
        isSelected && 'bg-white/[0.05] border-l-[1.5px] border-l-primary/60',
        isCurrentIndex && !isSelected && 'bg-white/[0.02]',
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {progress === 'solved' && (
              <CheckCircle className="h-3.5 w-3.5 text-green-400 flex-shrink-0" />
            )}
            {progress === 'attempted' && (
              <XCircle className="h-3.5 w-3.5 text-yellow-400 flex-shrink-0" />
            )}
            <h3 className="text-sm font-medium text-foreground/90 truncate">{question.title}</h3>
          </div>

          <div
            className={cn(
              'flex items-center gap-2 mt-1.5 transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]',
              isCollapsed ? 'opacity-0 h-0 overflow-hidden' : 'opacity-100 h-auto',
            )}
          >
            <span
              className={cn(
                'text-[10px] px-2 py-0.5 rounded-full font-medium tracking-wide uppercase',
                getDifficultyColor(question.difficulty),
              )}
            >
              {question.difficulty}
            </span>
            <span className="text-[10px] text-muted-foreground/60 tracking-wide">
              {question.category}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
