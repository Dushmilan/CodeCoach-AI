'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowRight, Check } from 'lucide-react';
import { MarkdownRenderer } from '@/components/learn/MarkdownRenderer';
import { cn } from '@/lib/utils';
import { ChatMessage, Language, LessonSummary } from '@/types';
import { CoachingMode } from '@/features/coaching/coaching.types';
import { AICoachPane } from './AICoachPane';
import { AIPanelDrawer } from './AIPanelDrawer';
import { PanelResizer } from './PanelResizer';
import { useResizablePanels } from './useResizablePanels';
import { useWorkspaceMode } from './useWorkspaceMode';

interface TheoryLessonLayoutProps {
  lesson: LessonSummary;
  storageKey: string;
  nextId: string | null;
  isAuthenticated: boolean;
  isCompleted: boolean;
  isMarkingComplete: boolean;
  onMarkComplete: () => void;
  messages: ChatMessage[];
  isTyping: boolean;
  selectedQuestion: string;
  currentCode: string;
  language: Language;
  onSendMessage: (message: string, mode: CoachingMode) => void;
}

export function TheoryLessonLayout({
  lesson,
  storageKey,
  nextId,
  isAuthenticated,
  isCompleted,
  isMarkingComplete,
  onMarkComplete,
  messages,
  isTyping,
  selectedQuestion,
  currentCode,
  language,
  onSendMessage,
}: TheoryLessonLayoutProps) {
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
  } = useResizablePanels({
    storageKey,
    percentageBoundary: 'reading',
    aiOpenStorageKey: 'codecoach:workspace:ai-open:theory',
    defaults: { descriptionWidth: 60, isAIOpen: false },
  });

  const { ref: modeRef, mode } = useWorkspaceMode();
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    if (mode === 'wide' && drawerOpen) {
      openAI();
      setDrawerOpen(false);
    }
  }, [mode, drawerOpen, openAI]);

  const isWide = mode === 'wide';
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
      className="flex-1 flex min-h-0 relative"
      data-testid="theory-layout-workspace"
    >
      {isDragging && (
        <div className="fixed inset-0 z-[9999] cursor-col-resize bg-transparent select-none" />
      )}

      <div
        data-testid="reading-pane"
        className={cn('min-w-0 overflow-y-auto p-6', showSideColumn ? 'flex-shrink-0' : 'flex-1')}
        style={showSideColumn ? { width: `${descriptionWidth}%` } : undefined}
      >
        <div className="border border-white/[0.04] rounded-2xl p-8">
          <MarkdownRenderer content={lesson.content} />
        </div>

        <div className="flex items-center justify-between mt-6 pb-8">
          {isAuthenticated && (
            <button
              onClick={onMarkComplete}
              disabled={isCompleted || isMarkingComplete}
              className="inline-flex items-center gap-2 text-xs px-4 py-2 rounded-full border border-primary/15 text-primary/70 hover:bg-primary/5 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <Check width={12} height={12} />
              {isCompleted ? 'Completed' : isMarkingComplete ? 'Marking...' : 'Mark Complete'}
            </button>
          )}
          <Link
            href={nextId ? `/learn/lesson/${nextId}` : `/learn/${lesson.course_id}`}
            className="inline-flex items-center gap-2 text-xs text-foreground/50 hover:text-foreground/70 px-4 py-2 rounded-full border border-white/[0.06] hover:border-white/[0.12] transition-all"
          >
            {nextId ? 'Next Lesson' : 'Back to Course'}
            <ArrowRight width={12} height={12} />
          </Link>
        </div>
      </div>

      {showSideColumn && (
        <>
          <PanelResizer
            boundary="reading"
            label="Resize lesson text"
            onMouseDown={startDrag('reading')}
            onResizeBy={resizeBy}
            isActive={activeBoundary === 'reading'}
          />
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
      )}

      {!showSideColumn && !showDrawer && (
        <div className="flex flex-col items-center justify-center p-4">
          <button
            onClick={() => (isWide ? openAI() : setDrawerOpen(true))}
            className="p-3 bg-white/[0.05] hover:bg-white/[0.08] rounded-full transition-all"
            aria-label="Open AI Panel"
          >
            <div className="w-5 h-5 bg-primary/60 rounded-full" />
          </button>
        </div>
      )}

      {showDrawer && (
        <AIPanelDrawer open onClose={() => setDrawerOpen(false)}>
          {coachPane(() => setDrawerOpen(false))}
        </AIPanelDrawer>
      )}
    </div>
  );
}
