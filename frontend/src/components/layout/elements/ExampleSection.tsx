import React from 'react';
import { Question } from '@/types';

interface ExampleSectionProps {
  example: Question['examples'][0];
  index: number;
}

export function ExampleSection({ example, index }: ExampleSectionProps) {
  return (
    <section className="mt-4" aria-labelledby={`example-${index}`}>
      <h3 id={`example-${index}`} className="font-semibold mb-2">
        Example {index + 1}:
      </h3>
      <div className="bg-muted/50 p-3 rounded-md border" role="figure" aria-label={`Example ${index + 1} details`}>
        <div className="font-mono text-sm">
          <strong>Input:</strong> <code>{example.input}</code>
        </div>
        <div className="font-mono text-sm mt-1">
          <strong>Output:</strong> <code>{example.output}</code>
        </div>
        {example.explanation && (
          <div className="text-sm mt-2">
            <strong>Explanation:</strong> {example.explanation}
          </div>
        )}
      </div>
    </section>
  );
}