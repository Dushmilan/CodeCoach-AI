'use client';

import { useState, useMemo, useEffect } from 'react';
import { ChevronRight, CheckCircle, AlertCircle, ChevronLeft, ChevronRight as ChevronRightIcon, Shuffle, List, FileText } from 'lucide-react';
import { QuestionSummary, Question } from '@/types';
import { cn } from '@/lib/utils';
import { QuestionDescriptionPanel } from './elements/QuestionDescriptionPanel';

interface EnhancedSidebarProps {
  questions: QuestionSummary[];
  selectedQuestion: QuestionSummary | null;
  fullQuestion: Question | QuestionSummary | null;
  onSelectQuestion: (question: QuestionSummary) => void;
  userProgress: Record<string, 'attempted' | 'solved'>;
  difficultyBadge?: string;
}

export function EnhancedSidebar({ questions, selectedQuestion, fullQuestion, onSelectQuestion, userProgress, difficultyBadge }: EnhancedSidebarProps) {
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
    return questions.filter(q => q.difficulty === filter);
  }, [questions, filter]);

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'text-green-500 bg-green-500/10 border-green-500/20';
      case 'medium': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20';
      case 'hard': return 'text-red-500 bg-red-500/10 border-red-500/20';
      default: return 'text-gray-500 bg-gray-500/10 border-gray-500/20';
    }
  };

  const getDifficultyIcon = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return '🟢';
      case 'medium': return '🟡';
      case 'hard': return '🔴';
      default: return '⚪';
    }
  };

  const handleNext = () => {
    const nextIndex = (currentIndex + 1) % filteredQuestions.length;
    setCurrentIndex(nextIndex);
    onSelectQuestion(filteredQuestions[nextIndex]);
  };

  const handlePrevious = () => {
    const prevIndex = currentIndex === 0 ? filteredQuestions.length - 1 : currentIndex - 1;
    setCurrentIndex(prevIndex);
    onSelectQuestion(filteredQuestions[prevIndex]);
  };

  const handleRandom = () => {
    const randomIndex = Math.floor(Math.random() * filteredQuestions.length);
    setCurrentIndex(randomIndex);
    onSelectQuestion(filteredQuestions[randomIndex]);
  };

  const handleAll = () => {
    setFilter('all');
    setCurrentIndex(0);
    if (filteredQuestions.length > 0) {
      onSelectQuestion(filteredQuestions[0]);
    }
  };

  const handleFilterChange = (newFilter: 'easy' | 'medium' | 'hard') => {
    setFilter(newFilter);
    setCurrentIndex(0);
    const filtered = questions.filter(q => q.difficulty === newFilter);
    if (filtered.length > 0) {
      onSelectQuestion(filtered[0]);
    }
  };

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
    <aside className={cn(
      "border-r border-border bg-card transition-all duration-300 flex flex-col",
      isCollapsed ? "w-16" : "w-80"
    )}>
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div className={cn(
            "transition-all duration-300 overflow-hidden",
            isCollapsed ? "w-0 opacity-0" : "w-auto opacity-100"
          )}>
            <h2 className="text-lg font-semibold whitespace-nowrap">Problems</h2>
          </div>
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1 hover:bg-secondary rounded transition-colors"
            aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <ChevronRight className={cn(
              "h-4 w-4 transition-transform duration-300",
              isCollapsed ? "rotate-0" : "rotate-90"
            )} />
          </button>
        </div>
      </div>

	{/* Toggle Button - Single button that switches view */}
	<div className={cn(
		"p-3 border-b border-border transition-all duration-300",
		isCollapsed ? "opacity-0 h-0 overflow-hidden" : "opacity-100 h-auto"
	)}>
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

	{/* Navigation Buttons - Only shown in list mode */}
	{viewMode === 'list' && (
	<div className={cn(
		"p-3 border-b border-border transition-all duration-300",
		isCollapsed ? "opacity-0 h-0 overflow-hidden" : "opacity-100 h-auto"
	)}>
		<div className="grid grid-cols-2 gap-2 mb-3">
			<button
				onClick={handleAll}
				className={cn(
					"flex items-center justify-center px-2 py-1.5 text-xs font-medium rounded-md transition-colors",
					filter === 'all'
						? "bg-primary text-primary-foreground"
						: "bg-secondary hover:bg-secondary/80"
				)}
			>
				<List className="h-3 w-3 mr-1" />
				All
			</button>
			<button
				onClick={handleRandom}
				className="flex items-center justify-center px-2 py-1.5 text-xs font-medium rounded-md bg-secondary hover:bg-secondary/80 transition-colors"
			>
				<Shuffle className="h-3 w-3 mr-1" />
				Random
			</button>
		</div>

		<div className="grid grid-cols-2 gap-2">
			<button
				onClick={handlePrevious}
				disabled={filteredQuestions.length <= 1}
				className="flex items-center justify-center px-2 py-1.5 text-xs font-medium rounded-md bg-secondary hover:bg-secondary/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
			>
				<ChevronLeft className="h-3 w-3 mr-1" />
				Prev
			</button>
			<button
				onClick={handleNext}
				disabled={filteredQuestions.length <= 1}
				className="flex items-center justify-center px-2 py-1.5 text-xs font-medium rounded-md bg-secondary hover:bg-secondary/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
			>
				<ChevronRightIcon className="h-3 w-3 mr-1" />
				Next
			</button>
		</div>

		{/* Difficulty Filters */}
		<div className="flex gap-1 mt-3">
          {(['easy', 'medium', 'hard'] as const).map((diff) => (
            <button
              key={diff}
              onClick={() => handleFilterChange(diff)}
              className={cn(
                "flex-1 px-2 py-1 text-xs font-medium rounded-md transition-colors",
                filter === diff
                  ? getDifficultyColor(diff)
                  : "bg-secondary hover:bg-secondary/80"
              )}
            >
              <span className="mr-1">{getDifficultyIcon(diff)}</span>
              {diff.charAt(0).toUpperCase() + diff.slice(1)}
            </button>
          ))}
        </div>
	</div>
	)}

	{/* Content Area - Questions List or Description Panel */}
	<div className="overflow-y-auto flex-1">
	{viewMode === 'list' ? (
		filteredQuestions.map((question, index) => {
		const progress = userProgress[question.id];
		const isSelected = selectedQuestion?.id === question.id;

		return (
			<div
			key={question.id}
			className={cn(
				"p-3 border-b border-border cursor-pointer hover:bg-secondary/50 transition-colors",
				isSelected && "bg-secondary border-l-2 border-l-primary",
				currentIndex === index && !isSelected && "bg-secondary/30"
			)}
			onClick={() => {
				setCurrentIndex(index);
				onSelectQuestion(question);
			}}
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

				<div className={cn(
				"flex items-center space-x-2 mt-1 transition-all duration-300",
				isCollapsed ? "opacity-0 h-0 overflow-hidden" : "opacity-100 h-auto"
				)}>
				<span className={cn(
				"text-xs px-2 py-0.5 rounded-full border",
				getDifficultyColor(question.difficulty)
				)}>
				{getDifficultyIcon(question.difficulty)} {question.difficulty}
				</span>
				<span className="text-xs text-muted-foreground">
				{question.category}
				</span>
				</div>
			</div>
			</div>
			</div>
		);
		})
	) : (
		(fullQuestion || selectedQuestion) && (
		<QuestionDescriptionPanel
			selectedQuestion={fullQuestion || selectedQuestion}
			difficultyBadge={difficultyBadge || ''}
			onToggleView={() => setViewMode('list')}
		/>
		)
	)}
	</div>

      {/* Progress Summary - Always rendered but visibility controlled by CSS */}
      <div className={cn(
        "p-3 border-t border-border text-xs text-muted-foreground transition-all duration-300",
        isCollapsed ? "opacity-0 h-0 overflow-hidden" : "opacity-100 h-auto"
      )}>
        <div className="flex justify-between">
          <span>Total: {filteredQuestions.length}</span>
          <span>Solved: {Object.values(userProgress).filter(p => p === 'solved').length}</span>
        </div>
      </div>
    </aside>
  );
}