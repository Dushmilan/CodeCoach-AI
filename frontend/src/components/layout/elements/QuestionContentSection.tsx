import React from 'react';

interface QuestionContentSectionProps {
  children: React.ReactNode;
}

export function QuestionContentSection({ children }: QuestionContentSectionProps) {
  return (
    <section
      className="flex-1 flex flex-col p-4"
      aria-labelledby="question-content"
    >
      {children}
    </section>
  );
}