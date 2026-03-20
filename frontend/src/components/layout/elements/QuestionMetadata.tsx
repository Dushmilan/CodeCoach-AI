import React from 'react';
import { Question } from '@/types';

interface QuestionMetadataProps {
  selectedQuestion: Question;
  difficultyBadge: string;
  questionSummary: string | null;
}

export function QuestionMetadata({ 
  selectedQuestion, 
  difficultyBadge, 
  questionSummary 
}: QuestionMetadataProps) {
  return (
    <div className="flex items-center gap-2 mb-4" role="group" aria-label="Question metadata">
      <span
        className={`px-2 py-1 text-xs font-medium rounded-full ${difficultyBadge}`}
        aria-label={`Difficulty: ${selectedQuestion.difficulty}`}
      >
        {selectedQuestion.difficulty}
      </span>
      <span className="text-sm text-muted-foreground" aria-label={`Category: ${selectedQuestion.category}`}>
        {selectedQuestion.category}
      </span>
      <span className="text-sm text-muted-foreground" aria-label={`Status: ${questionSummary?.split(' - ')[1] || 'Not started'}`}>
        {questionSummary?.split(' - ')[1] || ''}
      </span>
    </div>
  );
}