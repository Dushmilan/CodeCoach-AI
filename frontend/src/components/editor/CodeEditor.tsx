'use client';

import { useState, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { Play, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Language } from '@/types';

interface CodeEditorProps {
  language: Language;
  code: string;
  onCodeChange: (code: string) => void;
  onLanguageChange: (language: Language) => void;
  onRunCode: () => void;
  isRunning?: boolean;
}

const languageOptions = [
  { value: 'python', label: 'Python', version: '3.10', disabled: false },
  { value: 'javascript', label: 'JavaScript', version: '18.15.0', disabled: true },
  { value: 'java', label: 'Java', version: '15.0.2', disabled: true },
];

export function CodeEditor({
  language,
  code,
  onCodeChange,
  onLanguageChange,
  onRunCode,
  isRunning,
}: CodeEditorProps) {
  const editorRef = useRef<any>(null);

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor;
  };

  const handleLanguageChange = (newLanguage: Language) => {
    onLanguageChange(newLanguage);
  };

  const resetCode = () => {
    onCodeChange('');
  };

  return (
    <div className="flex flex-col h-full bg-card rounded-lg border border-border">
      <div className="flex items-center justify-between p-3 border-b border-border">
        <div className="flex items-center space-x-2">
          <select
            value={language}
            onChange={(e) => handleLanguageChange(e.target.value as Language)}
            className="px-3 py-1 text-sm bg-secondary border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {languageOptions.map((option) => (
              <option
                key={option.value}
                value={option.value}
                disabled={option.disabled}
              >
                {option.label} {option.version}
                {option.disabled && ' (still in progress)'}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={resetCode}
            disabled={isRunning}
          >
            <RotateCcw className="h-3 w-3 mr-1" />
            Reset
          </Button>
          <Button
            size="sm"
            onClick={onRunCode}
            disabled={isRunning}
            className="bg-primary hover:bg-primary/90"
          >
            <Play className="h-3 w-3 mr-1" />
            {isRunning ? 'Running...' : 'Run'}
          </Button>
        </div>
      </div>

      <div className="flex-1 min-h-0">
        <Editor
          height="100%"
          language={language}
          value={code}
          onChange={(value) => onCodeChange(value || '')}
          onMount={handleEditorDidMount}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: 'on',
            roundedSelection: false,
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 2,
            wordWrap: 'on',
          }}
        />
      </div>
    </div>
  );
}
