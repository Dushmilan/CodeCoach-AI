'use client';

import { Header } from '@/components/header/Header';
import { AnimateLauncher } from '@/components/animate/AnimateLauncher';
import { AIChatPanelContainer } from '@/components/layout/elements/AIChatPanelContainer';
import { CodeEditorContainer } from '@/components/layout/elements/CodeEditorContainer';
import { AIPanelDrawer, useWorkspaceMode } from '@/components/layout/lessons';
import { RescueIntervention } from '@/components/rescue/RescueIntervention';
import { QuestionDescriptionPanel } from '@/components/sidebar/QuestionDescriptionPanel';
import { ResizablePanelGroup } from '@/components/ui/ResizablePanelGroup';
import { useCoaching } from '@/features/coaching/coaching.hook';
import { useWorkspace } from '@/features/workspace/use-workspace.hook';
import { CoachingMode } from '@/features/coaching/coaching.types';
import { questionService } from '@/features/question/question.service';
import { useCodeRunner } from '@/features/question/use-code-runner.hook';
import { useRescueContract } from '@/features/rescue/use-rescue-contract.hook';
import { buildRescueCheckpoints } from '@/features/rescue/rescue.checkpoints';
import { Language, Question } from '@/types';
import { ChevronLeft, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';

export default function ProblemWorkspacePage() {
  const params = useParams();
  const questionId = params.id as string;

  const [language, setLanguage] = useState<Language>('python');
  const [currentCode, setCurrentCode] = useState('');
  const [fullQuestion, setFullQuestion] = useState<Question | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!questionId) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    questionService
      .getQuestion(questionId)
      .then((data) => {
        if (!cancelled) setFullQuestion(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load question');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [questionId]);

  const {
    isRunning,
    output,
    testResults,
    executionError,
    lastSubmitResult,
    handleRunCode,
    handleSubmitCode,
    isAuthenticated,
  } = useCodeRunner({ fullQuestion, language, currentCode });

  const { messages, isTyping, sendMessage, hydrateMessages } = useCoaching() as ReturnType<typeof useCoaching> & { hydrateMessages: (msgs: import('@/types').ChatMessage[]) => void };
  const { ref: workspaceRef, mode } = useWorkspaceMode();
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    if (
      fullQuestion?.starter &&
      typeof fullQuestion.starter === 'object' &&
      language in fullQuestion.starter
    ) {
      const starter = fullQuestion.starter[language as keyof typeof fullQuestion.starter];
      setCurrentCode(typeof starter === 'string' ? starter : '');
    } else {
      setCurrentCode('');
    }
  }, [language, fullQuestion]);

  const starterCode =
    fullQuestion?.starter && typeof fullQuestion.starter === 'object'
      ? fullQuestion.starter[language as keyof typeof fullQuestion.starter] || ''
      : '';

  const { deleteDraft } = useWorkspace({
    questionId: questionId || null,
    language,
    currentCode,
    setCurrentCode,
    onHydrateChat: (msgs) => {
      // Convert persisted messages to ChatMessage
      const hydrated = msgs.map((m) => ({
        id: `${Date.now()}-${Math.random()}`,
        role: m.role as 'user' | 'assistant',
        content: m.content,
        structured: (m as unknown as { structured?: import('@/types').StructuredCoachingResponse }).structured ?? null,
        timestamp: new Date((m as unknown as { timestamp: string }).timestamp),
      }));
      if (hydrated.length) hydrateMessages(hydrated as import('@/types').ChatMessage[]);
    },
  });

  const handleEscalateToT2 = useCallback(() => {
    if (!fullQuestion) return;
    const checkpoints = buildRescueCheckpoints(
      fullQuestion.test_cases ?? [],
      lastSubmitResult,
    );
    const current = checkpoints.find((c) => c.state === 'current');
    const hintMsg = current
      ? `I'm stuck on "${current.label}"${current.detail ? ` — ${current.detail}` : ''}. Can you give me a targeted hint?`
      : "I'm stuck on the failing test — can you give me a targeted hint?";
    void sendMessage(
      hintMsg,
      'explain' as CoachingMode,
      fullQuestion.title,
      currentCode,
      language,
      undefined,
      fullQuestion.difficulty,
      starterCode,
      'questions',
      questionId,
    );
    if (mode !== 'wide') setDrawerOpen(true);
  }, [fullQuestion, lastSubmitResult, currentCode, language, starterCode, sendMessage, mode, questionId]);

  const handleEscalateToT3 = useCallback(() => {
    if (!fullQuestion) return;
    const checkpoints = buildRescueCheckpoints(
      fullQuestion.test_cases ?? [],
      lastSubmitResult,
    );
    const current = checkpoints.find((c) => c.state === 'current');
    const replanMsg = current
      ? `I've been stuck on "${current.label}" for a while. Can you re-plan my path with a smaller next step?`
      : "I've been stuck for a while. Can you re-plan my path with a smaller next step?";
    void sendMessage(
      replanMsg,
      'review' as CoachingMode,
      fullQuestion.title,
      currentCode,
      language,
      undefined,
      fullQuestion.difficulty,
      starterCode,
      'questions',
      questionId,
    );
    if (mode !== 'wide') setDrawerOpen(true);
  }, [fullQuestion, lastSubmitResult, currentCode, language, starterCode, sendMessage, mode, questionId]);

  const rescue = useRescueContract({
    questionId,
    questionTitle: fullQuestion?.title ?? '',
    testCases: fullQuestion?.test_cases ?? [],
    lastSubmitResult,
    onEscalateToT2: handleEscalateToT2,
    onEscalateToT3: handleEscalateToT3,
  });
  const { registerActivity: rescueActivity } = rescue;

  const handleSendMessage = useCallback(
    async (message: string, mode: CoachingMode) => {
      if (!fullQuestion) return;
      rescueActivity();
      await sendMessage(
        message,
        mode,
        fullQuestion.title,
        currentCode,
        language,
        undefined,
        undefined,
        starterCode,
        'questions',
        questionId,
      );
    },
    [fullQuestion, currentCode, language, sendMessage, rescueActivity, starterCode, questionId],
  );

  const handleRunCodeRescue = useCallback(
    (stdin: string) => {
      rescueActivity();
      handleRunCode(stdin);
    },
    [handleRunCode, rescueActivity],
  );

  const handleSubmitCodeRescue = useCallback(() => {
    rescueActivity();
    handleSubmitCode();
  }, [handleSubmitCode, rescueActivity]);

  const handleCodeChangeRescue = useCallback(
    (code: string) => {
      rescueActivity();
      setCurrentCode(code);
    },
    [rescueActivity],
  );

  const handleResetCode = useCallback(() => {
    rescueActivity();
    setCurrentCode(starterCode);
    void deleteDraft();
  }, [rescueActivity, starterCode, deleteDraft]);

  const handleLanguageChangeRescue = useCallback(
    (lang: Language) => {
      rescueActivity();
      setLanguage(lang);
    },
    [rescueActivity],
  );

  useEffect(() => {
    if (mode === 'wide' && drawerOpen) setDrawerOpen(false);
  }, [mode, drawerOpen]);

  // Open the AI chat drawer when the rescue escalates to T2+ so the learner
  // can take the targeted coach help / re-plan offer.
  useEffect(() => {
    if ((rescue.tier === 't2' || rescue.tier === 't3') && mode !== 'wide') {
      setDrawerOpen(true);
    }
  }, [rescue.tier, mode]);

  const requestCoachHelp = useCallback(() => {
    rescueActivity();
    if (mode !== 'wide') setDrawerOpen(true);
  }, [rescueActivity, mode]);

  const requestReplan = useCallback(() => {
    rescueActivity();
    if (mode !== 'wide') setDrawerOpen(true);
  }, [rescueActivity, mode]);

  if (loading) {
    return (
      <div className="min-h-[100dvh] bg-background text-foreground">
        <Header />
        <main className="flex items-center justify-center min-h-[60vh]">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground/40" />
            <span className="text-sm text-muted-foreground/60">Loading question...</span>
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-[100dvh] bg-background text-foreground">
        <Header />
        <main className="flex items-center justify-center min-h-[60vh]">
          <div className="flex flex-col items-center gap-4">
            <div className="text-sm text-red-400/80 bg-red-500/5 px-4 py-3 rounded-2xl ring-1 ring-red-500/10">
              {error}
            </div>
            <Link
              href="/problems"
              className="text-xs text-muted-foreground/60 hover:text-foreground transition-colors flex items-center gap-1"
            >
              <ChevronLeft className="h-3 w-3" />
              Back to problems
            </Link>
          </div>
        </main>
      </div>
    );
  }

  if (!fullQuestion) {
    return (
      <div className="min-h-[100dvh] bg-background text-foreground">
        <Header />
        <main className="flex items-center justify-center min-h-[60vh]">
          <div className="flex flex-col items-center gap-4">
            <p className="text-sm text-muted-foreground/60">Question not found</p>
            <Link
              href="/problems"
              className="text-xs text-muted-foreground/60 hover:text-foreground transition-colors flex items-center gap-1"
            >
              <ChevronLeft className="h-3 w-3" />
              Back to problems
            </Link>
          </div>
        </main>
      </div>
    );
  }

  const isWide = mode === 'wide';
  const isStacked = mode === 'stacked';

  const editorPanel = (
    <div className="h-full flex flex-col rounded-[1.5rem] bg-white/[0.03] ring-1 ring-white/5 p-1 mr-1">
      <div className="flex-1 flex flex-col rounded-[calc(1.5rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.06)] overflow-hidden">
        <CodeEditorContainer
          language={language}
          currentCode={currentCode}
          initialCode={starterCode}
          isRunning={isRunning}
          output={output}
          error={executionError || error || ''}
          testResults={testResults}
          isInteractive={fullQuestion.is_interactive || false}
          onCodeChange={handleCodeChangeRescue}
          onResetCode={handleResetCode}
          onLanguageChange={handleLanguageChangeRescue}
          onRunCode={handleRunCodeRescue}
          onSubmitCode={handleSubmitCodeRescue}
          isAuthenticated={isAuthenticated}
        />
      </div>
    </div>
  );

  const chatPanel = (
    <AIChatPanelContainer
      messages={messages}
      onSendMessage={handleSendMessage}
      onClose={() => setDrawerOpen(false)}
      isTyping={isTyping}
      selectedQuestion={fullQuestion.title}
      currentCode={currentCode}
      language={language}
    />
  );

  return (
    <div className="h-dvh bg-background text-foreground flex flex-col overflow-hidden">
      <Header />
      <div className="flex-1 flex flex-col min-h-0 px-4 pb-4">
        <div className="flex items-center gap-2 px-1 py-2">
          <Link
            href="/problems"
            className="flex items-center gap-1 px-3 py-1.5 text-xs text-muted-foreground/60 hover:text-foreground hover:bg-white/5 rounded-full transition-all"
          >
            <ChevronLeft className="h-3 w-3" />
            Problems
          </Link>
          <span className="text-xs text-muted-foreground/30">/</span>
          <span className="text-xs text-foreground/60 truncate max-w-[200px]">
            {fullQuestion.title}
          </span>
          <div className="flex-1" />
          <AnimateLauncher
            problem={fullQuestion.title}
            code={currentCode}
            language={language}
            difficulty={fullQuestion.difficulty}
            initialCode={starterCode}
            question={fullQuestion}
          />
        </div>

        <div ref={workspaceRef} data-testid="problem-workspace" className="flex-1 min-h-0 relative">
          {isWide ? (
            <ResizablePanelGroup
              panels={[
                {
                  id: 'description',
                  defaultSize: 28,
                  minSize: 280,
                  children: (
                    <div className="h-full flex flex-col rounded-[1.5rem] bg-white/[0.03] ring-1 ring-white/5 p-1 mr-1">
                      <div className="flex-1 flex flex-col rounded-[calc(1.5rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.06)] overflow-hidden">
                        <QuestionDescriptionPanel selectedQuestion={fullQuestion} />
                      </div>
                    </div>
                  ),
                },
                {
                  id: 'editor',
                  defaultSize: 44,
                  minSize: 400,
                  children: editorPanel,
                },
                {
                  id: 'chat',
                  defaultSize: 28,
                  minSize: 280,
                  children: (
                    <div className="h-full flex flex-col rounded-[1.5rem] bg-white/[0.03] ring-1 ring-white/5 p-1">
                      <div className="flex-1 flex flex-col rounded-[calc(1.5rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.06)] overflow-hidden">
                        {chatPanel}
                      </div>
                    </div>
                  ),
                },
              ]}
            />
          ) : (
            <>
              <ResizablePanelGroup
                direction={isStacked ? 'vertical' : 'horizontal'}
                panels={[
                  {
                    id: 'description',
                    defaultSize: isStacked ? 45 : 40,
                    minSize: isStacked ? 200 : 240,
                    children: (
                      <div className="h-full flex flex-col rounded-[1.5rem] bg-white/[0.03] ring-1 ring-white/5 p-1 mr-1">
                        <div className="flex-1 flex flex-col rounded-[calc(1.5rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.06)] overflow-hidden">
                          <QuestionDescriptionPanel selectedQuestion={fullQuestion} />
                        </div>
                      </div>
                    ),
                  },
                  {
                    id: 'editor',
                    defaultSize: isStacked ? 55 : 60,
                    minSize: isStacked ? 240 : 320,
                    children: editorPanel,
                  },
                ]}
              />
              {drawerOpen ? (
                <AIPanelDrawer open onClose={() => setDrawerOpen(false)}>
                  {chatPanel}
                </AIPanelDrawer>
              ) : (
                <div className="absolute bottom-4 right-4 z-30">
                  <button
                    onClick={() => setDrawerOpen(true)}
                    className="p-3 bg-white/[0.05] hover:bg-white/[0.08] rounded-full transition-all"
                    aria-label="Open AI Panel"
                  >
                    <div className="w-5 h-5 bg-primary/60 rounded-full" />
                  </button>
                </div>
              )}
            </>
          )}

          <RescueIntervention
            tier={rescue.tier}
            checkpoints={rescue.checkpoints}
            isSuppressed={rescue.isSuppressed}
            onLeaveMeAlone={rescue.leaveMeAlone}
            onResume={rescue.resume}
            onRequestCoachHelp={requestCoachHelp}
            onReplan={requestReplan}
            onContinue={rescueActivity}
          />
        </div>
      </div>
    </div>
  );
}
