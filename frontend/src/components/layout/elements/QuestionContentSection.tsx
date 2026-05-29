import React from 'react';

interface QuestionContentSectionProps {
  children: React.ReactNode;
}

export function QuestionContentSection({ children }: QuestionContentSectionProps) {
  return (
    <section
      className="flex-1 flex flex-col p-1 overflow-hidden min-w-[300px]"
      aria-labelledby="question-content"
    >
      <div className="flex-1 flex flex-col rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5 p-1.5 overflow-hidden">
        <div className="flex-1 flex flex-col rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] overflow-hidden">
          {children}
        </div>
      </div>
    </section>
  );
}