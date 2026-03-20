'use client';

import { CheckCircle, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { QuestionSummary } from '@/types';

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
        'p-3 border-b border-border cursor-pointer hover:bg-secondary/50 transition-colors',
        isSelected && 'bg-secondary border-l-2 border-l-primary',
        isCurrentIndex && !isSelected && 'bg-secondary/30'
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            {progress === 'solved' && (
              <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />
            )}
            {progress === 'attempted' && (
              <AlertCircle className="h-4 w-4 text-yellow-500 flex-shrink-0" />
            )}
            <h3 className="text-sm font-medium truncate">{question.title}</h3>
          </div>

          <div
            className={cn(
              'flex items-center space-x-2 mt-1 transition-all duration-300',
              isCollapsed ? 'opacity-0 h-0 overflow-hidden' : 'opacity-100 h-auto'
            )}
          >
            <span
              className={cn(
                'text-xs px-2 py-0.5 rounded-full border',
                getDifficultyColor(question.difficulty)
              )}
            >
              {getDifficultyIcon(question.difficulty)} {question.difficulty}
            </span>
            <span className="text-xs text-muted-foreground">{question.category}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
