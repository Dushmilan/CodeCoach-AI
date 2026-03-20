'use client';

import { StructuredCoachingResponse } from '@/types';

interface StructuredResponseProps {
  structured: StructuredCoachingResponse;
  rawContent?: string;
}

/**
 * Formats text with basic markdown-like support for bold and code
 */
function FormattedText({ text }: { text: string }) {
  if (!text) return null;
  
  const lines = text.split('\n');
  
  return (
    <div className="space-y-2">
      {lines.map((line, idx) => {
        // Skip empty lines
        if (!line.trim()) return null;
        
        // Check for numbered list
        if (line.match(/^\d+\./)) {
          return (
            <div key={idx} className="flex gap-2 text-sm">
              <span className="text-muted-foreground">{line.match(/^\d+\./)?.[0]}</span>
              <span>{formatInlineStyles(line.replace(/^\d+\.\s*/, ''))}</span>
            </div>
          );
        }
        
        // Check for bullet points
        if (line.match(/^[\-\•\*]\s/)) {
          return (
            <div key={idx} className="flex gap-2 text-sm">
              <span className="text-muted-foreground">•</span>
              <span>{formatInlineStyles(line.replace(/^[\-\•\*]\s*/, ''))}</span>
            </div>
          );
        }
        
        // Check for section headers (lines ending with :)
        if (line.match(/^\w+[\s\w]*:$/)) {
          return (
            <div key={idx} className="font-semibold text-sm mt-3">
              {formatInlineStyles(line)}
            </div>
          );
        }
        
        // Regular paragraph
        return (
          <div key={idx} className="text-sm leading-relaxed">
            {formatInlineStyles(line)}
          </div>
        );
      })}
    </div>
  );
}

/**
 * Formats inline styles like **bold** and `code`
 */
function formatInlineStyles(text: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;
  
  // Process bold and code iteratively
  while (remaining.length > 0) {
    const boldMatch = remaining.match(/\*\*(.+?)\*\*/);
    const codeMatch = remaining.match(/`(.+?)`/);
    
    // Find which comes first
    const boldIndex = boldMatch ? remaining.indexOf(boldMatch[0]) : Infinity;
    const codeIndex = codeMatch ? remaining.indexOf(codeMatch[0]) : Infinity;
    
    if (boldIndex === Infinity && codeIndex === Infinity) {
      // No more matches, add remaining text
      parts.push(remaining);
      break;
    }
    
    if (boldIndex < codeIndex) {
      // Bold comes first
      if (boldIndex > 0) {
        parts.push(remaining.slice(0, boldIndex));
      }
      parts.push(
        <strong key={key++} className="font-semibold">
          {boldMatch![1]}
        </strong>
      );
      remaining = remaining.slice(boldIndex + boldMatch![0].length);
    } else {
      // Code comes first
      if (codeIndex > 0) {
        parts.push(remaining.slice(0, codeIndex));
      }
      parts.push(
        <code key={key++} className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono">
          {codeMatch![1]}
        </code>
      );
      remaining = remaining.slice(codeIndex + codeMatch![0].length);
    }
  }
  
  return parts.length === 1 ? parts[0] : parts;
}

/**
 * Validates if the structured response has valid data
 */
function isValidStructuredResponse(structured: StructuredCoachingResponse): boolean {
  if (!structured.summary || structured.summary.length < 5) return false;
  
  const trimmedSummary = structured.summary.trim();
  if (trimmedSummary.startsWith('{') || trimmedSummary.startsWith('[')) return false;
  if (trimmedSummary.includes('":') && !trimmedSummary.includes(': ')) return false;
  
  return true;
}

export function StructuredResponse({ structured, rawContent }: StructuredResponseProps) {
  // Validate structured response - fall back to raw text if malformed
  if (!structured || !isValidStructuredResponse(structured)) {
    if (rawContent) {
      return (
        <div className="space-y-2">
          <FormattedText text={rawContent} />
        </div>
      );
    }
    return null;
  }

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

  // Build response sections
  const sections: React.ReactNode[] = [];

  // Summary
  if (summary) {
    sections.push(<FormattedText key="summary" text={summary} />);
  }

  // Hints
  if (hints && hints.length > 0) {
    sections.push(
      <div key="hints" className="space-y-1 mt-3">
        {hints.map((hint, idx) => (
          <div key={idx} className="flex gap-2 text-sm">
            <span className="text-muted-foreground">{idx + 1}.</span>
            <span>{hint}</span>
          </div>
        ))}
      </div>
    );
  }

  // Code Review
  if (code_review) {
    sections.push(
      <div key="code_review" className="mt-3">
        <FormattedText text={code_review} />
      </div>
    );
  }

  // Complexity Analysis
  if (complexity_analysis) {
    sections.push(
      <div key="complexity" className="mt-3">
        <FormattedText text={complexity_analysis} />
      </div>
    );
  }

  // Suggestions
  if (suggestions && suggestions.length > 0) {
    sections.push(
      <div key="suggestions" className="space-y-1 mt-3">
        {suggestions.map((suggestion, idx) => (
          <div key={idx} className="flex gap-2 text-sm">
            <span className="text-muted-foreground">{idx + 1}.</span>
            <span>{suggestion}</span>
          </div>
        ))}
      </div>
    );
  }

  // Edge Cases
  if (edge_cases && edge_cases.length > 0) {
    sections.push(
      <div key="edge_cases" className="space-y-1 mt-3">
        {edge_cases.map((edgeCase, idx) => (
          <div key={idx} className="flex gap-2 text-sm">
            <span className="text-muted-foreground">{idx + 1}.</span>
            <span>{edgeCase}</span>
          </div>
        ))}
      </div>
    );
  }

  // Explanation
  if (explanation) {
    sections.push(
      <div key="explanation" className="mt-3">
        <FormattedText text={explanation} />
      </div>
    );
  }

  // Debug Help
  if (debug_help) {
    sections.push(
      <div key="debug_help" className="mt-3">
        <FormattedText text={debug_help} />
      </div>
    );
  }

  return <div className="space-y-2">{sections}</div>;
}
