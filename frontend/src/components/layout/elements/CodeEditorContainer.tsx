'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { CodeEditor } from '@/components/editor/CodeEditor';
import { Language } from '@/types';
import { ChevronDown, ChevronUp, GripHorizontal, Play } from 'lucide-react';
import { cn } from '@/lib/utils';
import { EmptyState } from '@/components/ui/EmptyState';

interface CodeEditorContainerProps {
  language: Language;
  currentCode: string;
  isRunning: boolean;
  output: string;
  error: string;
  onCodeChange: (code: string) => void;
  onLanguageChange: (language: Language) => void;
  onRunCode: () => void;
  onSubmitCode: () => void;
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
  onSubmitCode,
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
    <div ref={containerRef} className="flex-1 flex flex-col overflow-hidden p-0">
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
            onSubmitCode={onSubmitCode}
            isRunning={isRunning}
        />
      </div>

      {/* Output Panel - Double-Bezel */}
      <div className="mx-2 mb-2 rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-1">
        <div className={cn(
          "rounded-[calc(1rem-0.25rem)] bg-secondary/30 overflow-hidden flex flex-col shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)]",
          !hasOutput && "h-auto bg-transparent"
        )}>
          {hasOutput ? (
            <>
              {/* Resize Handle */}
              {!outputCollapsed && (
                <div
                  className={cn(
                    "h-2 bg-border/50 cursor-row-resize hover:bg-primary/50 transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] flex items-center justify-center",
                    isResizing && "bg-primary/50"
                  )}
                  onMouseDown={handleResizeStart}
                >
                  <GripHorizontal className="h-4 w-4 text-muted-foreground/50" strokeWidth={1} />
                </div>
              )}

              <div
                className={cn(
                  "flex flex-col",
                  outputCollapsed && "h-auto"
                )}
                style={!outputCollapsed ? { height: `${outputHeight}px` } : undefined}
              >
                <div className="flex items-center justify-between px-3 py-2 border-b border-white/5">
                  <span className="text-xs font-medium tracking-wide text-muted-foreground">OUTPUT</span>
                  <button
                    onClick={() => setOutputCollapsed(!outputCollapsed)}
                    className="p-1 hover:bg-white/5 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"
                    aria-label={outputCollapsed ? "Expand output" : "Collapse output"}
                  >
                    {outputCollapsed ? (
                      <ChevronUp className="h-3.5 w-3.5" strokeWidth={1} />
                    ) : (
                      <ChevronDown className="h-3.5 w-3.5" strokeWidth={1} />
                    )}
                  </button>
                </div>

                {!outputCollapsed && (
                  <div className="flex-1 overflow-auto p-3">
                    <pre className={cn(
                      "text-sm whitespace-pre-wrap font-mono",
                      error ? "text-red-400" : "text-foreground/80"
                    )}>
                      {error || output}
                    </pre>
                  </div>
                )}
              </div>
            </>
          ) : (
            <EmptyState
              icon={Play}
              title="Write code and hit Run"
              description="Your output will appear here when you run your code."
            />
          )}
        </div>
      </div>
    </div>
  );
}
