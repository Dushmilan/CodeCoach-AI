import React from 'react';
import { CodeEditor } from '@/components/editor/CodeEditor';
import { Language } from '@/types';

interface CodeEditorContainerProps {
  language: Language;
  currentCode: string;
  isRunning: boolean;
  output: string;
  error: string;
  onCodeChange: (code: string) => void;
  onLanguageChange: (language: Language) => void;
  onRunCode: () => void;
}

export function CodeEditorContainer({
  language,
  currentCode,
  isRunning,
  output,
  error,
  onCodeChange,
  onLanguageChange,
  onRunCode,
}: CodeEditorContainerProps) {
  return (
    <div className="flex-1">
      <CodeEditor
        language={language}
        code={currentCode}
        onCodeChange={onCodeChange}
        onLanguageChange={onLanguageChange}
        onRunCode={onRunCode}
        isRunning={isRunning}
        output={output}
        error={error}
      />
    </div>
  );
}