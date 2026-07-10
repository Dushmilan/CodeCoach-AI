'use client';

import ReactMarkdown from 'react-markdown';

interface MarkdownPreviewProps {
  content: string;
  className?: string;
}

export default function MarkdownPreview({ content, className }: MarkdownPreviewProps) {
  if (!content) {
    return (
      <div className={`text-sm text-muted-foreground italic ${className || ''}`}>
        Nothing to preview
      </div>
    );
  }

  return (
    <div
      className={`prose prose-sm dark:prose-invert max-w-none text-sm leading-relaxed ${
        className || ''
      }`}
    >
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
