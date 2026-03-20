import React from 'react';
import { EnhancedSidebar } from '../EnhancedSidebar';
import { QuestionSummary } from '@/types';

interface SidebarContainerProps {
  questions: QuestionSummary[];
  selectedQuestion: QuestionSummary | null;
  onSelectQuestion: (question: QuestionSummary) => void;
  userProgress: Record<string, 'attempted' | 'solved'>;
  difficultyBadge?: string;
}

export function SidebarContainer({
  questions,
  selectedQuestion,
  onSelectQuestion,
  userProgress,
  difficultyBadge
}: SidebarContainerProps) {
  return (
    <EnhancedSidebar
      questions={questions}
      selectedQuestion={selectedQuestion}
      onSelectQuestion={onSelectQuestion}
      userProgress={userProgress}
      difficultyBadge={difficultyBadge}
    />
  );
}