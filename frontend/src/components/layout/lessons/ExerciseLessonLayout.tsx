'use client';

import React, { useEffect, useState } from 'react';
import { CodeEditorContainer } from '@/components/layout/elements';
import { cn } from '@/lib/utils';
import { ChatMessage, Language, LessonSummary, Question } from '@/types';
import { AICoachPane } from './AICoachPane';
import { AIPanelDrawer } from './AIPanelDrawer';
import { ExerciseDescriptionPane, ExerciseTestCase } from './ExerciseDescriptionPane';
import { PanelResizer } from './PanelResizer';
import { useResizablePanels } from './useResizablePanels';
import { useWorkspaceMode } from './useWorkspaceMode';

interface ExerciseLessonLayoutProps {
  lesson: LessonSummary;
  storageKey: string;
  linkedQuestion: Question | null;
  testCases: ExerciseTestCase[];
  language: Language;
  currentCode: string;
  initialCode: string;
  isRunning: boolean;
  output: string;
  error: string;
  isInteractive: boolean;
  messages: ChatMessage[];
  isTyping: boolean;
  selectedQuestion: string;
  onSendMessage: (message: string, mode: string) => void;
  onCodeChange: (code: string) => void;
  onLanguageChange: (language: Language) => void;
  onRunCode: (stdin: string) => void;
  onSubmitCode: () => void;
}

export function ExerciseLessonLayout({
  lesson,
  storageKey,
  linkedQuestion,
  testCases,
  language,
  currentCode,
  initialCode,
  isRunning,
  output,
  error,
  isInteractive,
  messages,
  isTyping,
  selectedQuestion,
  onSendMessage,
  onCodeChange,
  onLanguageChange,
  onRunCode,
  onSubmitCode,
}: ExerciseLessonLayoutProps) {
  const {
    descriptionWidth,
    aiWidth,
    isAIOpen,
    isDragging,
    activeBoundary,
    workspaceRef,
    startDrag,
    resizeBy,
    openAI,
    closeAI,
  } = useResizablePanels({ storageKey });

  const { ref: modeRef, mode } = useWorkspaceMode();
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    if (mode === 'wide' && drawerOpen) {
      openAI();
      setDrawerOpen(false);
    }
  }, [mode, drawerOpen, openAI]);

  const isWide = mode === 'wide';
  const isStacked = mode === 'stacked';
  const showSideColumn = isWide && isAIOpen;
  const showDrawer = !isWide && drawerOpen;

  const coachPane = (onClose: () => void) => (
    <AICoachPane
      messages={messages}
      onSendMessage={onSendMessage}
      onClose={onClose}
      isTyping={isTyping}
      selectedQuestion={selectedQuestion}
      currentCode={currentCode}
      language={language}
    />
  );

  return (
    <div
      ref={(el) => {
        workspaceRef.current = el;
        modeRef(el);
      }}
      className={cn('flex-1 flex min-h-0 relative', isStacked && 'flex-col')}
      data-testid="exercise-layout-workspace"
    >
      {isDragging && (
        <div className="fixed inset-0 z-[9999] cursor-col-resize bg-transparent select-none" />
      )}

      {isStacked ? (
        <>
          <div
            data-testid="description-pane"
            className="h-[45%] min-h-0 overflow-y-auto p-6 flex-shrink-0"
          >
            <ExerciseDescriptionPane
              lesson={lesson}
              linkedQuestion={linkedQuestion}
              testCases={testCases}
            />
          </div>
          <div className="flex-1 min-h-0 flex flex-col">
            <CodeEditorContainer
              language={language}
              currentCode={currentCode}
              initialCode={initialCode}
              isRunning={isRunning}
              output={output}
              error={error}
              isInteractive={isInteractive}
              onCodeChange={onCodeChange}
              onLanguageChange={onLanguageChange}
              onRunCode={onRunCode}
              onSubmitCode={onSubmitCode}
            />
          </div>
        </>
      ) : (
        <>
          <div
            data-testid="description-pane"
            className="min-w-0 overflow-y-auto p-6 flex-shrink-0"
            style={{ width: `${descriptionWidth}%` }}
          >
            <ExerciseDescriptionPane
              lesson={lesson}
              linkedQuestion={linkedQuestion}
              testCases={testCases}
            />
          </div>

          <PanelResizer
            boundary="description"
            label="Resize lesson description"
            onMouseDown={startDrag('description')}
            onResizeBy={resizeBy}
            isActive={activeBoundary === 'description'}
          />

          <div className="flex-1 min-w-0 flex flex-col min-h-0">
            <CodeEditorContainer
              language={language}
              currentCode={currentCode}
              initialCode={initialCode}
              isRunning={isRunning}
              output={output}
              error={error}
              isInteractive={isInteractive}
              onCodeChange={onCodeChange}
              onLanguageChange={onLanguageChange}
              onRunCode={onRunCode}
              onSubmitCode={onSubmitCode}
            />
          </div>
        </>
      )}

      {showSideColumn ? (
        <>
          <PanelResizer
            boundary="ai"
            label="Resize AI coach panel"
            onMouseDown={startDrag('ai')}
            onResizeBy={resizeBy}
            isActive={activeBoundary === 'ai'}
          />
          <div
            data-testid="ai-pane"
            className="h-full flex-shrink-0 flex flex-col min-h-0"
            style={{ width: `${aiWidth}px` }}
          >
            {coachPane(closeAI)}
          </div>
        </>
      ) : (
        !showDrawer && (
          <div
            className={`flex flex-col items-center justify-center p-4 ${
              isStacked ? 'absolute bottom-4 right-4 z-30' : ''
            }`}
          >
            <button
              onClick={() => (isWide ? openAI() : setDrawerOpen(true))}
              className="p-3 bg-white/[0.05] hover:bg-white/[0.08] rounded-full transition-all"
              aria-label="Open AI Panel"
            >
              <div className="w-5 h-5 bg-primary/60 rounded-full" />
            </button>
          </div>
        )
      )}

      {showDrawer && (
        <AIPanelDrawer open onClose={() => setDrawerOpen(false)}>
          {coachPane(() => setDrawerOpen(false))}
        </AIPanelDrawer>
      )}
    </div>
  );
}
