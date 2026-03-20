'use client';

import React, { useState } from 'react';
import { Question, QuestionSummary } from '@/types';
import { ChevronRight, ChevronDown, Lightbulb, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface QuestionDescriptionPanelProps {
  selectedQuestion: Question | QuestionSummary | null;
  difficultyBadge: string;
  onToggleView?: () => void;
}

export function QuestionDescriptionPanel({
  selectedQuestion,
  difficultyBadge,
  onToggleView,
}: QuestionDescriptionPanelProps) {
  const [hintsExpanded, setHintsExpanded] = useState(false);

  if (!selectedQuestion) return null;

  const hasFullData = 'description' in selectedQuestion && selectedQuestion.description;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4">
        <div className="mb-4">
          <h2 className="text-xl font-semibold mb-2">{selectedQuestion.title}</h2>
          <div className="flex items-center gap-2">
            <span
              className={cn('text-xs px-2 py-0.5 rounded-full border', difficultyBadge)}
            >
              {selectedQuestion.difficulty}
            </span>
            <span className="text-xs text-muted-foreground">
              {selectedQuestion.category}
            </span>
          </div>
        </div>

        {!hasFullData ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-sm text-muted-foreground">
              Loading description...
            </span>
          </div>
        ) : (
          <>
            <div className="prose prose-sm dark:prose-invert max-w-none mb-4">
              <p className="text-sm text-foreground">
                {(selectedQuestion as Question).description}
              </p>
            </div>

            {(selectedQuestion as Question).examples &&
              (selectedQuestion as Question).examples.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-sm font-semibold mb-2">Examples:</h3>
                  {(selectedQuestion as Question).examples.map((example, idx) => (
                    <div key={idx} className="mb-3 p-3 bg-secondary/50 rounded-lg border border-border">
                      <div className="text-xs font-medium text-muted-foreground mb-1">
                        Example {idx + 1}:
                      </div>
                      <pre className="text-xs bg-secondary p-2 rounded mt-1 overflow-x-auto">
                        <strong>Input:</strong> {example.input}
                      </pre>
                      <pre className="text-xs bg-secondary p-2 rounded mt-1 overflow-x-auto">
                        <strong>Output:</strong> {example.output}
                      </pre>
                    </div>
                  ))}
                </div>
              )}

            {(selectedQuestion as Question).hints &&
              (selectedQuestion as Question).hints.length > 0 && (
                <div className="border-t border-border pt-4">
                  <button
                    onClick={() => setHintsExpanded(!hintsExpanded)}
                    className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors w-full"
                  >
                    <Lightbulb className="h-4 w-4" />
                    <span>Hints</span>
                    {hintsExpanded ? (
                      <ChevronDown className="h-4 w-4 ml-auto" />
                    ) : (
                      <ChevronRight className="h-4 w-4 ml-auto" />
                    )}
                  </button>
                  {hintsExpanded && (
                    <div className="mt-3 space-y-2">
                      {(selectedQuestion as Question).hints.map((hint, idx) => (
                        <div
                          key={idx}
                          className="text-sm text-muted-foreground pl-6 border-l-2 border-primary/50"
                        >
                          {hint}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
          </>
        )}
      </div>
    </div>
  );
}
