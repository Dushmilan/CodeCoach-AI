import React from 'react';
import { Question } from '@/types';
import { QuestionMetadata } from './QuestionMetadata';

interface QuestionHeaderProps {
  selectedQuestion: Question;
  difficultyBadge: string;
  questionSummary: string | null;
}

export function QuestionHeader({ 
  selectedQuestion, 
  difficultyBadge, 
  questionSummary 
}: QuestionHeaderProps) {
  return (
    <header className="mb-4">
      <h1 id="question-title" className="text-2xl font-bold mb-2">
        {selectedQuestion.title}
      </h1>
      <QuestionMetadata 
        selectedQuestion={selectedQuestion}
        difficultyBadge={difficultyBadge}
        questionSummary={questionSummary}
      />
    </header>
  );
}