import React from 'react';
import { Question } from '@/types';
import { ExampleContainer } from './ExampleContainer';

interface QuestionDescriptionProps {
  selectedQuestion: Question;
}

export function QuestionDescription({ selectedQuestion }: QuestionDescriptionProps) {
  if (!selectedQuestion) return null;

  return (
    <div className="prose prose-sm dark:prose-invert max-w-none" role="article">
      <p>{selectedQuestion.description}</p>
      {selectedQuestion.examples && selectedQuestion.examples.length > 0 && (
        <ExampleContainer examples={selectedQuestion.examples} />
      )}
    </div>
  );
}