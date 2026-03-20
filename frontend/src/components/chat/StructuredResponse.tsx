'use client';

import { Lightbulb, Code, Clock, Sparkles, AlertTriangle, BookOpen, Bug, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import { StructuredCoachingResponse } from '@/types';

interface StructuredResponseProps {
  structured: StructuredCoachingResponse;
}

interface SectionProps {
  title: string;
  icon: React.ElementType;
  children: React.ReactNode;
  defaultOpen?: boolean;
  colorClass: string;
}

function Section({ title, icon: Icon, children, defaultOpen = true, colorClass }: SectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  if (!children) return null;

  return (
    <div className="border border-border rounded-lg overflow-hidden mb-3">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full flex items-center justify-between px-4 py-3 ${colorClass} hover:opacity-90 transition-opacity`}
      >
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4" />
          <span className="font-semibold text-sm">{title}</span>
        </div>
        {isOpen ? (
          <ChevronUp className="h-4 w-4" />
        ) : (
          <ChevronDown className="h-4 w-4" />
        )}
      </button>
      {isOpen && (
        <div className="px-4 py-3 bg-card border-t border-border">
          {children}
        </div>
      )}
    </div>
  );
}

export function StructuredResponse({ structured }: StructuredResponseProps) {
  if (!structured) return null;

  const {
    summary,
    hints,
    code_review,
    complexity_analysis,
    suggestions,
    edge_cases,
    explanation,
    debug_help,
  } = structured;

  return (
    <div className="space-y-3">
      {/* Summary - Always visible */}
      {summary && (
        <div className="bg-primary/10 border border-primary/20 rounded-lg p-4">
          <div className="flex items-start gap-2">
            <div className="mt-0.5">
              <Sparkles className="h-4 w-4 text-primary" />
            </div>
            <div>
              <p className="text-sm text-foreground">{summary}</p>
            </div>
          </div>
        </div>
      )}

      {/* Hints */}
      {hints && hints.length > 0 && (
        <Section
          title="Hints"
          icon={Lightbulb}
          colorClass="bg-yellow-500/10 text-yellow-500"
        >
          <ul className="space-y-2">
            {hints.map((hint, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-foreground">
                <span className="text-yellow-500 font-semibold">{index + 1}.</span>
                <span>{hint}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}

      {/* Code Review */}
      {code_review && (
        <Section
          title="Code Review"
          icon={Code}
          colorClass="bg-blue-500/10 text-blue-500"
        >
          <p className="text-sm text-foreground whitespace-pre-wrap">{code_review}</p>
        </Section>
      )}

      {/* Complexity Analysis */}
      {complexity_analysis && (
        <Section
          title="Complexity Analysis"
          icon={Clock}
          colorClass="bg-purple-500/10 text-purple-500"
        >
          <p className="text-sm text-foreground whitespace-pre-wrap">{complexity_analysis}</p>
        </Section>
      )}

      {/* Suggestions */}
      {suggestions && suggestions.length > 0 && (
        <Section
          title="Suggestions"
          icon={Sparkles}
          colorClass="bg-green-500/10 text-green-500"
        >
          <ul className="space-y-2">
            {suggestions.map((suggestion, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-foreground">
                <span className="text-green-500 font-semibold">{index + 1}.</span>
                <span>{suggestion}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}

      {/* Edge Cases */}
      {edge_cases && edge_cases.length > 0 && (
        <Section
          title="Edge Cases"
          icon={AlertTriangle}
          colorClass="bg-orange-500/10 text-orange-500"
        >
          <ul className="space-y-2">
            {edge_cases.map((edgeCase, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-foreground">
                <span className="text-orange-500 font-semibold">{index + 1}.</span>
                <span>{edgeCase}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}

      {/* Explanation */}
      {explanation && (
        <Section
          title="Explanation"
          icon={BookOpen}
          colorClass="bg-cyan-500/10 text-cyan-500"
          defaultOpen={false}
        >
          <p className="text-sm text-foreground whitespace-pre-wrap">{explanation}</p>
        </Section>
      )}

      {/* Debug Help */}
      {debug_help && (
        <Section
          title="Debug Help"
          icon={Bug}
          colorClass="bg-red-500/10 text-red-500"
          defaultOpen={false}
        >
          <p className="text-sm text-foreground whitespace-pre-wrap">{debug_help}</p>
        </Section>
      )}
    </div>
  );
}
