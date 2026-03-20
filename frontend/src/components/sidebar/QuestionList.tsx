'use client';

import { QuestionSummary } from '@/types';
import { QuestionItem } from './QuestionItem';

interface QuestionListProps {
  questions: QuestionSummary[];
  selectedQuestion: QuestionSummary | null;
  currentIndex: number;
  userProgress: Record<string, 'attempted' | 'solved'>;
  isCollapsed?: boolean;
  onSelectQuestion: (question: QuestionSummary, index: number) => void;
}

export function QuestionList({
  questions,
  selectedQuestion,
  currentIndex,
  userProgress,
  isCollapsed = false,
  onSelectQuestion,
}: QuestionListProps) {
  if (questions.length === 0) {
    return (
      <div className="p-4 text-center text-sm text-muted-foreground">
        No questions found
      </div>
    );
  }

  return (
    <div className="overflow-y-auto flex-1">
      {questions.map((question, index) => {
        const progress = userProgress[question.id];
        const isSelected = selectedQuestion?.id === question.id;

        return (
          <QuestionItem
            key={question.id}
            question={question}
            isSelected={isSelected}
            isCurrentIndex={index === currentIndex}
            progress={progress}
            isCollapsed={isCollapsed}
            onClick={() => onSelectQuestion(question, index)}
          />
        );
      })}
    </div>
  );
}
