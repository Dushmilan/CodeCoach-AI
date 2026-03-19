'use client';

import { useState, useRef, useEffect } from 'react';
import { Editor } from '@monaco-editor/react';
import { useCodeCoach } from '@/contexts/CodeCoachContext';

interface CodeEditorProps {
  className?: string;
}

export function CodeEditor({ className = '' }: CodeEditorProps) {
  const { state, dispatch } = useCodeCoach();
  const [isEditorReady, setIsEditorReady] = useState(false);
  const editorRef = useRef<any>(null);

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor;
    setIsEditorReady(true);
  };

  const handleCodeChange = (value: string | undefined) => {
    if (value !== undefined) {
      dispatch({ type: 'SET_CODE', payload: value });
    }
  };

  const getLanguageFromExtension = (language: string) => {
    switch (language) {
      case 'python':
        return 'python';
      case 'javascript':
        return 'javascript';
      case 'java':
        return 'java';
      default:
        return 'python';
    }
  };

  return (
    <div className={`flex flex-col h-full ${className}`}>
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center space-x-4">
          <h3 className="text-sm font-medium text-gray-300">Code Editor</h3>
          <select
            value={state.language}
            onChange={(e) => dispatch({ type: 'SET_LANGUAGE', payload: e.target.value as any })}
            className="px-2 py-1 text-xs bg-gray-700 border border-gray-600 rounded text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="python">Python</option>
            <option value="javascript">JavaScript</option>
            <option value="java">Java</option>
          </select>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => {
              if (state.currentQuestion) {
                dispatch({ type: 'SET_CODE', payload: state.currentQuestion.starter[state.language] });
              }
            }}
            className="px-3 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-gray-300 rounded transition-colors"
          >
            Reset
          </button>
        </div>
      </div>
      
      <div className="flex-1 min-h-0">
        <Editor
          height="100%"
          language={getLanguageFromExtension(state.language)}
          value={state.code}
          onChange={handleCodeChange}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            wordWrap: 'on',
            automaticLayout: true,
            scrollBeyondLastLine: false,
            renderLineHighlight: 'line',
            selectOnLineNumbers: true,
            cursorBlinking: 'blink',
            cursorStyle: 'line',
            lineNumbers: 'on',
            folding: true,
            lineDecorationsWidth: 10,
            overviewRulerBorder: false,
            hideCursorInOverviewRuler: false,
            scrollbar: {
              vertical: 'visible',
              horizontal: 'visible',
              useShadows: false,
              verticalHasArrows: false,
              horizontalHasArrows: false,
            },
          }}
          onMount={handleEditorDidMount}
          loading={
            <div className="flex items-center justify-center h-full bg-gray-900">
              <div className="text-gray-400">Loading editor...</div>
            </div>
          }
        />
      </div>
    </div>
  );
}