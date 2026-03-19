'use client';

import { useState, useRef, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { motion } from 'framer-motion';
import { Play, Copy, Download, Settings } from 'lucide-react';

interface CodeEditorProps {
  defaultValue?: string;
  language?: string;
  onChange?: (value: string) => void;
}

export default function CodeEditor({
  defaultValue = `// Welcome to LeetCode Clone
// Solve your coding challenges here

function twoSum(nums, target) {
  const map = new Map();

  for (let i = 0; i < nums.length; i++) {
    const complement = target - nums[i];

    if (map.has(complement)) {
      return [map.get(complement), i];
    }

    map.set(nums[i], i);
  }

  return [];
}

console.log(twoSum([2, 7, 11, 15], 9)); // [0, 1]`,
  language = 'javascript',
  onChange,
}: CodeEditorProps) {
  const [code, setCode] = useState(defaultValue);
  const [isRunning, setIsRunning] = useState(false);
  const editorRef = useRef<any>(null);

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor;
  };

  const handleCodeChange = (value: string | undefined) => {
    const newCode = value || '';
    setCode(newCode);
    onChange?.(newCode);
  };

  const handleRunCode = () => {
    setIsRunning(true);
    // Simulate code execution
    setTimeout(() => {
      setIsRunning(false);
    }, 2000);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleRunCode();
    }
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(code);
  };

  const handleDownloadCode = () => {
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'solution.js';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="h-full flex flex-col"
      onKeyDown={handleKeyDown}
    >
      {/* Editor Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-800 neon-border rounded-t-lg">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
          </div>
          <span className="text-sm text-slate-400">solution.js</span>
        </div>

        <div className="flex items-center space-x-2">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleRunCode}
            disabled={isRunning}
            className="flex items-center space-x-1 px-3 py-1 bg-cyan-600 hover:bg-cyan-500 rounded text-sm transition-colors disabled:opacity-50"
            title="Run code (Ctrl+Enter)"
          >
            <Play size={14} />
            <span>{isRunning ? 'Running...' : 'Run'}</span>
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleCopyCode}
            className="flex items-center space-x-1 px-3 py-1 bg-slate-700 hover:bg-slate-600 rounded text-sm transition-colors"
            title="Copy code"
          >
            <Copy size={14} />
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleDownloadCode}
            className="flex items-center space-x-1 px-3 py-1 bg-slate-700 hover:bg-slate-600 rounded text-sm transition-colors"
            title="Download code"
          >
            <Download size={14} />
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="flex items-center space-x-1 px-3 py-1 bg-slate-700 hover:bg-slate-600 rounded text-sm transition-colors"
            title="Settings"
          >
            <Settings size={14} />
          </motion.button>
        </div>
      </div>

      {/* Monaco Editor */}
      <div className="flex-1 neon-border border-t-0 rounded-b-lg overflow-hidden">
        <Editor
          height="100%"
          defaultLanguage={language}
          value={code}
          onChange={handleCodeChange}
          onMount={handleEditorDidMount}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            fontFamily: 'JetBrains Mono, monospace',
            lineNumbers: 'on',
            roundedSelection: false,
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 2,
            insertSpaces: true,
            wordWrap: 'on',
            bracketPairColorization: { enabled: true },
            guides: {
              bracketPairs: true,
              indentation: true,
            },
            renderLineHighlight: 'line',
            cursorBlinking: 'smooth',
            smoothScrolling: true,
            contextmenu: true,
            mouseWheelZoom: true,
            folding: true,
            lineDecorationsWidth: 10,
            lineNumbersMinChars: 3,
          }}
          loading={
            <div className="flex items-center justify-center h-full bg-slate-900">
              <div className="text-cyan-400 animate-pulse">Loading editor...</div>
            </div>
          }
        />
      </div>
    </motion.div>
  );
}