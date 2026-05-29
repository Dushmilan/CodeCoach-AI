'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { CodeEditor } from '@/components/editor/CodeEditor';
import { Language } from '@/types';
import { ChevronDownIcon, ChevronUpIcon, DragHandleDots2Icon, PlayIcon } from '@radix-ui/react-icons';
import { cn } from '@/lib/utils';
import { EmptyState } from '@/components/ui/EmptyState';
import TerminalSimulation from '@/components/terminal/TerminalSimulation';

interface CodeEditorContainerProps {
  language: Language;
  currentCode: string;
  initialCode: string;
  isRunning: boolean;
  output: string;
  error: string;
  isInteractive?: boolean;
  onCodeChange: (code: string) => void;
  onLanguageChange: (language: Language) => void;
  onRunCode: (stdin: string) => void;
  onSubmitCode: () => void;
}

export function CodeEditorContainer({
  language,
  currentCode,
  initialCode,
  isRunning,
  output,
  error,
  isInteractive = false,
  onCodeChange,
  onLanguageChange,
  onRunCode,
  onSubmitCode,
}: CodeEditorContainerProps) {
  const [outputHeight, setOutputHeight] = useState(200); // Default 200px
  const [outputCollapsed, setOutputCollapsed] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [stdin, setStdin] = useState(''); // New state for interactive input
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
      const containerHeight = containerRef.current?.clientHeight || 0;
      const maxOutputHeight = Math.max(150, containerHeight - 150); // Ensure at least 150px for editor
      const newHeight = Math.max(100, Math.min(maxOutputHeight, startHeightRef.current + deltaY));
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

  const handleRun = () => {
    onRunCode(stdin); // Pass stdin to onRunCode
  };

  const handleSubmit = () => {
    onSubmitCode();
  };

  return (
    <div ref={containerRef} className="flex-1 flex flex-col overflow-hidden p-0 min-w-[300px]">
      {isResizing && <div className="fixed inset-0 z-[9999] cursor-row-resize bg-transparent select-none" />}
      
      {/* Code Editor Section */}
      <div 
        className="min-h-0 overflow-hidden flex flex-col"
        style={{ flex: '1 1 auto' }}
      >
        <CodeEditor
          language={language}
          code={currentCode}
          initialCode={initialCode}
          onCodeChange={onCodeChange}
          onLanguageChange={onLanguageChange}
          onRunCode={handleRun} // Use wrapped handler
          onSubmitCode={handleSubmit} // Use wrapped handler
          isRunning={isRunning}
          isResizing={isResizing}
        />
        
        {/* Interactive Input Area */}
        {isInteractive && (
          <div className="bg-white/[0.02] border-t border-white/[0.04] p-3">
             <div className="text-xs font-medium tracking-wide text-muted-foreground/60 mb-2">INPUT (STDIN)</div>
             <textarea 
                className="w-full h-16 bg-background rounded border border-white/[0.1] p-2 text-sm font-mono text-foreground focus:outline-none focus:border-primary/50"
                placeholder="Enter input for your program (one line per input)..."
                value={stdin}
                onChange={(e) => setStdin(e.target.value)}
             />
          </div>
        )}
      </div>

      {/* Resize Handle */}
      {hasOutput && !outputCollapsed && (
        <div
            className={cn(
                "h-4 bg-transparent hover:bg-white/[0.05] cursor-row-resize transition-colors flex items-center justify-center relative border-t border-white/[0.04]",
                isResizing && "bg-white/[0.08]"
            )}
            onMouseDown={handleResizeStart}
        >
            <div className="absolute inset-x-4 top-1/2 h-px bg-white/[0.1]" />
            <DragHandleDots2Icon className="relative h-4 w-4 text-muted-foreground/40" />
        </div>
      )}

      {/* Output Panel */}
      <div 
        className={cn(
            "flex flex-col bg-background/95",
            !hasOutput && "h-auto flex-shrink-0 border-t border-white/[0.04]"
        )}
        style={hasOutput && !outputCollapsed ? { height: `${outputHeight}px`, flex: '0 0 auto' } : undefined}
      >
        {/* Output Header */}
        <div className="flex items-center justify-between px-3 py-2 border-t border-white/[0.04]">
            <span className="text-xs font-medium tracking-wide text-muted-foreground/60">OUTPUT</span>
            {hasOutput && (
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
            )}
        </div>

        {hasOutput && !outputCollapsed ? (
          <div className="flex-1 overflow-auto px-3 pb-3">
            {isInteractive ? (
              <TerminalSimulation output={error || output} />
            ) : (
              <pre className={cn(
                  "text-sm whitespace-pre-wrap font-mono",
                  error ? "text-red-400" : "text-foreground/80"
              )}>
                  {error || output}
              </pre>
            )}
          </div>
        ) : !hasOutput ? (
          <EmptyState
            icon={PlayIcon}
            title="Write code and hit Run"
            description="Your output will appear here when you run your code."
          />
        ) : null}
      </div>
    </div>
  );

}
