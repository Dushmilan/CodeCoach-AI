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
  difficultyBadge?: string;
}

export function Sidebar({
  questions,
  selectedQuestion,
  fullQuestion,
  onSelectQuestion,
  userProgress,
  difficultyBadge,
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
      <aside className="w-80 border-r border-border bg-card flex flex-col">
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Problems</h2>
            <div className="p-1 w-8 h-8 bg-secondary rounded animate-pulse" />
          </div>
        </div>
        <div className="flex-1 p-4">
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-secondary rounded animate-pulse" />
            ))}
          </div>
        </div>
      </aside>
    );
  }

  return (
    <aside
      className={cn(
        'border-r border-border bg-card transition-all duration-300 flex flex-col',
        isCollapsed ? 'w-16' : 'w-80'
      )}
    >
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div
            className={cn(
              'transition-all duration-300 overflow-hidden',
              isCollapsed ? 'w-0 opacity-0' : 'w-auto opacity-100'
            )}
          >
            <h2 className="text-lg font-semibold whitespace-nowrap">Problems</h2>
          </div>
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1 hover:bg-secondary rounded transition-colors"
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <ChevronRight
              className={cn(
                'h-4 w-4 transition-transform duration-300',
                isCollapsed ? 'rotate-0' : 'rotate-90'
              )}
            />
          </button>
        </div>
      </div>

      {/* View Mode Toggle */}
      <div
        className={cn(
          'p-3 border-b border-border transition-all duration-300',
          isCollapsed ? 'opacity-0 h-0 overflow-hidden' : 'opacity-100 h-auto'
        )}
      >
        <button
          onClick={() => setViewMode(viewMode === 'list' ? 'description' : 'list')}
          className="flex items-center gap-2 w-full px-3 py-2 text-sm font-medium rounded-md bg-secondary hover:bg-secondary/80 transition-colors"
        >
          {viewMode === 'list' ? (
            <>
              <FileText className="h-4 w-4" />
              <span className="flex-1 text-left">Show Active Question</span>
            </>
          ) : (
            <>
              <List className="h-4 w-4" />
              <span className="flex-1 text-left">Show All Questions</span>
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
            difficultyBadge={difficultyBadge || ''}
            onToggleView={() => setViewMode('list')}
          />
        )
      )}

      {/* Progress Summary */}
      <div
        className={cn(
          'p-3 border-t border-border text-xs text-muted-foreground transition-all duration-300',
          isCollapsed ? 'opacity-0 h-0 overflow-hidden' : 'opacity-100 h-auto'
        )}
      >
        <div className="flex justify-between">
          <span>Total: {filteredQuestions.length}</span>
          <span>Solved: {solvedCount}</span>
        </div>
      </div>
    </aside>
  );
}
