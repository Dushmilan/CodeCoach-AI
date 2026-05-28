'use client';

import { useState, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { PlayIcon, ResetIcon, CheckCircledIcon } from '@radix-ui/react-icons';
import { Language } from '@/types';
import { LANGUAGE_OPTIONS } from './constants';

interface CodeEditorProps {
  language: Language;
  code: string;
  onCodeChange: (code: string) => void;
  onLanguageChange: (language: Language) => void;
  onRunCode: () => void;
  onSubmitCode: () => void;
  isRunning?: boolean;
}

export function CodeEditor({
  language,
  code,
  onCodeChange,
  onLanguageChange,
  onRunCode,
  onSubmitCode,
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
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 border-b border-white/5">
        <div className="flex items-center gap-1">
          <div className="rounded-full bg-white/[0.03] ring-1 ring-white/5 p-0.5">
            <select
              value={language}
              onChange={(e) => handleLanguageChange(e.target.value as Language)}
              className="px-2.5 py-1 text-[11px] tracking-wide bg-transparent text-foreground/70 focus:outline-none cursor-pointer appearance-none"
              style={{
                backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
                backgroundPosition: 'right 4px center',
                backgroundRepeat: 'no-repeat',
                backgroundSize: '16px 12px',
                paddingRight: '24px',
              }}
            >
              {LANGUAGE_OPTIONS.map((option) => (
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
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={resetCode}
            disabled={isRunning}
            className="inline-flex items-center gap-1 px-3 py-1.5 text-[10px] font-medium tracking-wide text-muted-foreground/60 bg-white/[0.03] hover:bg-white/[0.07] rounded-full ring-1 ring-white/5 disabled:opacity-40 disabled:pointer-events-none transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] active:scale-[0.97]"
          >
            <ResetIcon className="h-3 w-3" />
            Reset
          </button>
          <button
            onClick={onRunCode}
            disabled={isRunning}
            className="inline-flex items-center gap-1 px-3 py-1.5 text-[10px] font-medium tracking-wide text-muted-foreground/60 bg-white/[0.03] hover:bg-white/[0.07] rounded-full ring-1 ring-white/5 disabled:opacity-40 disabled:pointer-events-none transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] active:scale-[0.97]"
          >
            <PlayIcon className="h-3 w-3" />
            Run
          </button>
          <button
            onClick={onSubmitCode}
            disabled={isRunning}
            className="inline-flex items-center gap-1 px-4 py-1.5 text-[10px] font-medium tracking-wide text-emerald-300 bg-emerald-500/10 hover:bg-emerald-500/20 rounded-full ring-1 ring-emerald-500/20 disabled:opacity-40 disabled:pointer-events-none transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] active:scale-[0.97]"
          >
            <CheckCircledIcon className="h-3 w-3" />
            {isRunning ? 'Running...' : 'Submit'}
          </button>
        </div>
      </div>

      <div className="flex-1 min-h-0 rounded-b-[calc(2rem-0.375rem)] overflow-hidden">
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
