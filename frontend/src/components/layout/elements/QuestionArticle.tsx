import React from 'react';
import { Question } from '@/types';
import { QuestionHeader } from './QuestionHeader';
import { QuestionDescription } from './QuestionDescription';

interface QuestionArticleProps {
  selectedQuestion: Question;
  difficultyBadge: string;
  questionSummary: string | null;
}

export function QuestionArticle({ 
  selectedQuestion, 
  difficultyBadge, 
  questionSummary 
}: QuestionArticleProps) {
  if (!selectedQuestion) return null;

  return (
    <article className="mb-4" aria-labelledby="question-title">
      <QuestionHeader 
        selectedQuestion={selectedQuestion}
        difficultyBadge={difficultyBadge}
        questionSummary={questionSummary}
      />
      <QuestionDescription selectedQuestion={selectedQuestion} />
    </article>
  );
}