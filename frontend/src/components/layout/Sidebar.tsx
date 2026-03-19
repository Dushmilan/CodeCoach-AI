'use client';

import { useState } from 'react';
import { ChevronRight, CheckCircle, AlertCircle } from 'lucide-react';
import { Question } from '@/types';
import { cn } from '@/lib/utils';

interface SidebarProps {
  questions: Question[];
  selectedQuestion: Question | null;
  onSelectQuestion: (question: Question) => void;
  userProgress: Record<string, 'attempted' | 'solved'>;
}

export function Sidebar({ questions, selectedQuestion, onSelectQuestion, userProgress }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'text-green-500 bg-green-500/10';
      case 'medium': return 'text-yellow-500 bg-yellow-500/10';
      case 'hard': return 'text-red-500 bg-red-500/10';
      default: return 'text-gray-500 bg-gray-500/10';
    }
  };

  return (
    <aside className={cn(
      "border-r border-border bg-card transition-all duration-300",
      isCollapsed ? "w-16" : "w-80"
    )}>
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <h2 className="text-lg font-semibold">Problems</h2>
          )}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1 hover:bg-secondary rounded"
          >
            <ChevronRight className={cn(
              "h-4 w-4 transition-transform",
              isCollapsed ? "rotate-0" : "rotate-90"
            )} />
          </button>
        </div>
      </div>

      <div className="overflow-y-auto h-[calc(100vh-120px)]">
        {questions.map((question) => {
          const progress = userProgress[question.id];
          const isSelected = selectedQuestion?.id === question.id;

          return (
            <div
              key={question.id}
              className={cn(
                "p-3 border-b border-border cursor-pointer hover:bg-secondary/50 transition-colors",
                isSelected && "bg-secondary border-l-2 border-l-primary"
              )}
              onClick={() => onSelectQuestion(question)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    {!isCollapsed && (
                      <>
                        {progress === 'solved' && (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        )}
                        {progress === 'attempted' && (
                          <AlertCircle className="h-4 w-4 text-yellow-500" />
                        )}
                        <h3 className="text-sm font-medium truncate">{question.title}</h3>
                      </>
                    )}
                  </div>
                  {!isCollapsed && (
                    <div className="flex items-center space-x-2 mt-1">
                      <span className={cn(
                        "text-xs px-2 py-1 rounded-full",
                        getDifficultyColor(question.difficulty)
                      )}>
                        {question.difficulty}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {question.category}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
}