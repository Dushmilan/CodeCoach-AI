import React from 'react';
import { EnhancedSidebar } from '../EnhancedSidebar';
import { Question } from '@/types';

interface SidebarContainerProps {
  questions: Question[];
  selectedQuestion: Question;
  onSelectQuestion: (question: Question) => void;
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