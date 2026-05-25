'use client';

import React, { useState, useMemo } from 'react';
import { Question, QuestionSummary } from '@/types';
import { ChevronRight, ChevronDown, Lightbulb, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface QuestionDescriptionPanelProps {
  selectedQuestion: Question | QuestionSummary | null;
  onToggleView?: () => void;
}

export function QuestionDescriptionPanel({
  selectedQuestion,
  onToggleView,
}: QuestionDescriptionPanelProps) {
  const [hintsExpanded, setHintsExpanded] = useState(false);
  const difficultyBadge = useMemo(() => {
    if (!selectedQuestion) return '';
    const styles: Record<string, string> = {
      easy: 'text-green-400 bg-green-500/10',
      medium: 'text-yellow-400 bg-yellow-500/10',
      hard: 'text-red-400 bg-red-500/10',
    };
    return styles[selectedQuestion.difficulty] || styles.easy;
  }, [selectedQuestion]);

  if (!selectedQuestion) return null;

  const hasFullData = 'description' in selectedQuestion && selectedQuestion.description;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4">
        <div className="mb-5">
          <h2 className="text-base font-semibold text-foreground/90 mb-2 tracking-tight">{selectedQuestion.title}</h2>
          <div className="flex items-center gap-2">
            <span
              className={cn('text-[10px] px-2 py-0.5 rounded-full font-medium uppercase tracking-wide', difficultyBadge)}
            >
              {selectedQuestion.difficulty}
            </span>
            <span className="text-[10px] text-muted-foreground/60 tracking-wide uppercase">
              {selectedQuestion.category}
            </span>
          </div>
        </div>

        {!hasFullData ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground/40" strokeWidth={1} />
            <span className="ml-2 text-xs text-muted-foreground/60">
              Loading description...
            </span>
          </div>
        ) : (
          <>
            <div className="mb-5">
              <p className="text-sm text-foreground/70 leading-relaxed">
                {(selectedQuestion as Question).description}
              </p>
            </div>

            {(selectedQuestion as Question).examples &&
              (selectedQuestion as Question).examples.length > 0 && (
                <div className="mb-5">
                  <h3 className="text-[10px] font-semibold tracking-wide text-muted-foreground/60 uppercase mb-3">Examples:</h3>
                  {(selectedQuestion as Question).examples.map((example, idx) => (
                    <div key={idx} className="mb-2 rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-1.5">
                      <div className="rounded-[calc(1rem-0.25rem)] bg-card p-3 shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]">
                        <div className="text-[10px] font-medium text-muted-foreground/60 mb-1.5 tracking-wide">
                          Example {idx + 1}
                        </div>
                        <pre className="text-[11px] text-foreground/70 font-mono bg-white/[0.02] p-2 rounded-lg overflow-x-auto leading-relaxed">
                          Input: {example.input}
                        </pre>
                        <pre className="text-[11px] text-foreground/70 font-mono bg-white/[0.02] p-2 rounded-lg mt-1 overflow-x-auto leading-relaxed">
                          Output: {example.output}
                        </pre>
                      </div>
                    </div>
                  ))}
                </div>
              )}

            {(selectedQuestion as Question).hints &&
              (selectedQuestion as Question).hints.length > 0 && (
                <div className="border-t border-white/5 pt-4">
                  <button
                    onClick={() => setHintsExpanded(!hintsExpanded)}
                    className="flex items-center gap-2 text-xs font-medium text-muted-foreground/70 hover:text-foreground transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] w-full"
                  >
                    <Lightbulb className="h-3.5 w-3.5" strokeWidth={1} />
                    <span>Hints</span>
                    {hintsExpanded ? (
                      <ChevronDown className="h-3.5 w-3.5 ml-auto" strokeWidth={1} />
                    ) : (
                      <ChevronRight className="h-3.5 w-3.5 ml-auto" strokeWidth={1} />
                    )}
                  </button>
                  {hintsExpanded && (
                    <div className="mt-3 space-y-2">
                      {(selectedQuestion as Question).hints.map((hint, idx) => (
                        <div
                          key={idx}
                          className="text-xs text-muted-foreground/60 pl-4 border-l-[1.5px] border-primary/40 leading-relaxed"
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
