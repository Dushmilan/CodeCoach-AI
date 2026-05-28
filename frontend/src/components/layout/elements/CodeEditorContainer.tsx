'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { CodeEditor } from '@/components/editor/CodeEditor';
import { Language } from '@/types';
import { ChevronDownIcon, ChevronUpIcon, DragHandleDots2Icon, PlayIcon } from '@radix-ui/react-icons';
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
        style={{ height: outputCollapsed || !hasOutput ? '100%' : `calc(100% - ${outputHeight}px)` }}
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

      {/* Output Panel - Flush 1px border */}
      <div className="border-t border-white/[0.04] flex-shrink-0">
        {hasOutput ? (
          <div className="flex flex-col">
            {/* Resize Handle */}
            {!outputCollapsed && (
              <div
                className={cn(
                  "h-2 bg-transparent hover:bg-white/[0.03] cursor-row-resize transition-colors flex items-center justify-center relative",
                  isResizing && "bg-white/[0.04]"
                )}
                onMouseDown={handleResizeStart}
              >
                <div className="absolute inset-x-4 top-1/2 h-px bg-white/[0.06]" />
                <DragHandleDots2Icon className="relative h-3 w-3 text-muted-foreground/30" />
              </div>
            )}

            <div
              className={cn("flex flex-col", outputCollapsed && "h-auto")}
              style={!outputCollapsed ? { height: `${outputHeight}px` } : undefined}
            >
              <div className="flex items-center justify-between px-3 py-2">
                <span className="text-xs font-medium tracking-wide text-muted-foreground/60">OUTPUT</span>
                <button
                  onClick={() => setOutputCollapsed(!outputCollapsed)}
                  className="p-1 hover:bg-white/[0.04] rounded transition-colors"
                  aria-label={outputCollapsed ? "Expand output" : "Collapse output"}
                >
                  {outputCollapsed ? (
                    <ChevronUpIcon className="h-3.5 w-3.5 text-muted-foreground/40" />
                  ) : (
                    <ChevronDownIcon className="h-3.5 w-3.5 text-muted-foreground/40" />
                  )}
                </button>
              </div>

              {!outputCollapsed && (
                <div className="flex-1 overflow-auto px-3 pb-3">
                  <pre className={cn(
                    "text-sm whitespace-pre-wrap font-mono",
                    error ? "text-red-400" : "text-foreground/80"
                  )}>
                    {error || output}
                  </pre>
                </div>
              )}
            </div>
          </div>
        ) : (
          <EmptyState
            icon={PlayIcon}
            title="Write code and hit Run"
            description="Your output will appear here when you run your code."
          />
        )}
      </div>
    </div>
  );
}
