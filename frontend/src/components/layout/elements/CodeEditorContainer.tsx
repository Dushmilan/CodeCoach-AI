'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { CodeEditor } from '@/components/editor/CodeEditor';
import { Language } from '@/types';
import { ChevronDown, ChevronUp, GripHorizontal } from 'lucide-react';
import { cn } from '@/lib/utils';

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
  const [outputHeight, setOutputHeight] = useState(200); // Default 200px
  const [outputCollapsed, setOutputCollapsed] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const startYRef = useRef(0);
  const startHeightRef = useRef(0);

  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
    startYRef.current = e.clientY;
    startHeightRef.current = outputHeight;
  }, [outputHeight]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      const deltaY = startYRef.current - e.clientY;
      const newHeight = Math.max(100, Math.min(500, startHeightRef.current + deltaY));
      setOutputHeight(newHeight);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  const hasOutput = output || error;

  return (
    <div ref={containerRef} className="flex-1 flex flex-col overflow-hidden">
      {/* Code Editor Section */}
      <div 
        className="flex-1 min-h-0 overflow-hidden"
        style={{ height: outputCollapsed || !hasOutput ? '100%' : `calc(100% - ${outputHeight}px - 32px)` }}
      >
        <CodeEditor
          language={language}
          code={currentCode}
          onCodeChange={onCodeChange}
          onLanguageChange={onLanguageChange}
          onRunCode={onRunCode}
          isRunning={isRunning}
        />
      </div>

      {/* Output Panel Section */}
      {hasOutput && (
        <>
          {/* Resize Handle */}
          {!outputCollapsed && (
            <div
              className={cn(
                "h-2 bg-border cursor-row-resize hover:bg-primary/50 transition-colors flex items-center justify-center",
                isResizing && "bg-primary/50"
              )}
              onMouseDown={handleResizeStart}
            >
              <GripHorizontal className="h-4 w-4 text-muted-foreground" />
            </div>
          )}

          {/* Output Panel */}
          <div
            className={cn(
              "border-t border-border bg-secondary/30 overflow-hidden flex flex-col",
              outputCollapsed && "h-auto"
            )}
            style={!outputCollapsed ? { height: `${outputHeight}px` } : undefined}
          >
            {/* Output Header with Collapse Button */}
            <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-secondary/50">
              <span className="text-sm font-medium">Output</span>
              <button
                onClick={() => setOutputCollapsed(!outputCollapsed)}
                className="p-1 hover:bg-secondary rounded transition-colors"
                aria-label={outputCollapsed ? "Expand output" : "Collapse output"}
              >
                {outputCollapsed ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </button>
            </div>

            {/* Output Content */}
            {!outputCollapsed && (
              <div className="flex-1 overflow-auto p-3">
                <pre className={cn(
                  "text-sm whitespace-pre-wrap",
                  error ? "text-red-400" : "text-foreground"
                )}>
                  {error || output}
                </pre>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
