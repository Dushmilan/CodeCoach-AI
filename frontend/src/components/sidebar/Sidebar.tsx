'use client';

import { useState, useMemo, useEffect, useCallback } from 'react';
import { ChevronRight, FileText, List } from 'lucide-react';
import { QuestionSummary, Question } from '@/types';
import { cn } from '@/lib/utils';
import { QuestionList } from './QuestionList';
import { FilterBar } from './FilterBar';
import { NavigationControls } from './NavigationControls';
import { QuestionDescriptionPanel } from './QuestionDescriptionPanel';

interface SidebarProps {
  questions: QuestionSummary[];
  selectedQuestion: QuestionSummary | null;
  fullQuestion: Question | QuestionSummary | null;
  onSelectQuestion: (question: QuestionSummary) => void;
  userProgress: Record<string, 'attempted' | 'solved'>;
}

export function Sidebar({
  questions,
  selectedQuestion,
  fullQuestion,
  onSelectQuestion,
  userProgress,
}: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [filter, setFilter] = useState<'all' | 'easy' | 'medium' | 'hard'>('all');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isMounted, setIsMounted] = useState(false);
  const [viewMode, setViewMode] = useState<'list' | 'description'>('list');

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const filteredQuestions = useMemo(() => {
    if (!Array.isArray(questions)) return [];
    if (filter === 'all') return questions;
    return questions.filter((q) => q.difficulty === filter);
  }, [questions, filter]);

  const handleSelectQuestion = useCallback(
    (question: QuestionSummary, index: number) => {
      setCurrentIndex(index);
      onSelectQuestion(question);
    },
    [onSelectQuestion]
  );

  const handleNext = useCallback(() => {
    const nextIndex = (currentIndex + 1) % filteredQuestions.length;
    handleSelectQuestion(filteredQuestions[nextIndex], nextIndex);
  }, [currentIndex, filteredQuestions, handleSelectQuestion]);

  const handlePrevious = useCallback(() => {
    const prevIndex =
      currentIndex === 0 ? filteredQuestions.length - 1 : currentIndex - 1;
    handleSelectQuestion(filteredQuestions[prevIndex], prevIndex);
  }, [currentIndex, filteredQuestions, handleSelectQuestion]);

  const handleRandom = useCallback(() => {
    const randomIndex = Math.floor(Math.random() * filteredQuestions.length);
    handleSelectQuestion(filteredQuestions[randomIndex], randomIndex);
  }, [filteredQuestions, handleSelectQuestion]);

  const handleAll = useCallback(() => {
    setFilter('all');
    setCurrentIndex(0);
    if (filteredQuestions.length > 0) {
      handleSelectQuestion(filteredQuestions[0], 0);
    }
  }, [filteredQuestions, handleSelectQuestion]);

  const handleFilterChange = useCallback(
    (newFilter: 'easy' | 'medium' | 'hard') => {
      setFilter(newFilter);
      setCurrentIndex(0);
      const filtered = questions.filter((q) => q.difficulty === newFilter);
      if (filtered.length > 0) {
        handleSelectQuestion(filtered[0], 0);
      }
    },
    [questions, handleSelectQuestion]
  );

  const solvedCount = Object.values(userProgress).filter(
    (p) => p === 'solved'
  ).length;

  if (!isMounted) {
    return (
      <aside className="flex flex-col w-80 p-1">
        <div className="flex-1 flex flex-col rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5 p-1.5 overflow-hidden">
          <div className="flex-1 flex flex-col rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] overflow-hidden">
            <div className="p-4 border-b border-white/5">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Problems</h2>
                <div className="p-1 w-8 h-8 bg-white/5 rounded-full animate-pulse" />
              </div>
            </div>
            <div className="flex-1 p-4">
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-16 bg-white/5 rounded-2xl animate-pulse" />
                ))}
              </div>
            </div>
          </div>
        </div>
      </aside>
    );
  }

  return (
    <aside className={cn('flex flex-col p-1', isCollapsed ? 'w-16' : 'w-80')}>
      <div className="flex-1 flex flex-col rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5 p-1.5 overflow-hidden">
        <div className="flex-1 flex flex-col rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] overflow-hidden">
          {/* Header */}
          <div className="px-4 py-3 border-b border-white/5">
            <div className="flex items-center justify-between">
              <div
                className={cn(
                  'transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] overflow-hidden',
                  isCollapsed ? 'w-0 opacity-0' : 'w-auto opacity-100'
                )}
              >
                <h2 className="text-sm font-semibold tracking-wide text-foreground/80">PROBLEMS</h2>
              </div>
              <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className="p-1.5 hover:bg-white/5 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"
                aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              >
                <ChevronRight
                  className={cn(
                    'h-3.5 w-3.5 text-muted-foreground transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]',
                    isCollapsed ? 'rotate-0' : 'rotate-180'
                  )}
                  strokeWidth={1}
                />
              </button>
            </div>
          </div>

          {/* View Mode Toggle */}
          <div
            className={cn(
              'px-3 py-2 border-b border-white/5 transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]',
              isCollapsed ? 'opacity-0 h-0 overflow-hidden py-0' : 'opacity-100 h-auto'
            )}
          >
            <button
              onClick={() => setViewMode(viewMode === 'list' ? 'description' : 'list')}
              className="flex items-center gap-2 w-full px-3 py-2 text-xs font-medium rounded-full bg-white/5 hover:bg-white/10 transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"
            >
              {viewMode === 'list' ? (
                <>
                  <FileText className="h-3.5 w-3.5" strokeWidth={1} />
                  <span className="flex-1 text-left text-muted-foreground">Show Active Question</span>
                </>
              ) : (
                <>
                  <List className="h-3.5 w-3.5" strokeWidth={1} />
                  <span className="flex-1 text-left text-muted-foreground">Show All Questions</span>
                </>
              )}
            </button>
          </div>

          {/* Filter Bar - Only in list mode */}
          {viewMode === 'list' && (
            <>
              <FilterBar
                currentFilter={filter}
                onFilterChange={handleFilterChange}
                onAll={handleAll}
                onRandom={handleRandom}
                isCollapsed={isCollapsed}
              />

              <NavigationControls
                onPrevious={handlePrevious}
                onNext={handleNext}
                disabled={filteredQuestions.length <= 1}
                isCollapsed={isCollapsed}
              />
            </>
          )}

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto">
            {viewMode === 'list' ? (
              <QuestionList
                questions={filteredQuestions}
                selectedQuestion={selectedQuestion}
                currentIndex={currentIndex}
                userProgress={userProgress}
                isCollapsed={isCollapsed}
                onSelectQuestion={handleSelectQuestion}
              />
            ) : (
                fullQuestion && (
                  <QuestionDescriptionPanel
                    selectedQuestion={fullQuestion}
                    onToggleView={() => setViewMode('list')}
                  />
              )
            )}
          </div>

          {/* Progress Summary */}
          <div
            className={cn(
              'px-4 py-3 border-t border-white/5 text-xs text-muted-foreground/60 transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]',
              isCollapsed ? 'opacity-0 h-0 overflow-hidden py-0' : 'opacity-100 h-auto'
            )}
          >
            <div className="flex justify-between">
              <span>Total: {filteredQuestions.length}</span>
              <span>Solved: {solvedCount}</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
