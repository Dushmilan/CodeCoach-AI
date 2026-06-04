'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Question, Language } from '@/types';
import { questionService } from '@/features/question/question.service';
import { useCodeRunner } from '@/features/question/use-code-runner.hook';
import { useCoaching } from '@/features/coaching/coaching.hook';
import { ResizablePanelGroup } from '@/components/ui/ResizablePanelGroup';
import { QuestionDescriptionPanel } from '@/components/sidebar/QuestionDescriptionPanel';
import { CodeEditorContainer } from '@/components/layout/elements/CodeEditorContainer';
import { AIChatPanelContainer } from '@/components/layout/elements/AIChatPanelContainer';
import { Loader2Icon, RadixChevronLeft } from '@/components/ui/icons';
import { Header } from '@/components/header/Header';

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

  const { isRunning, output, executionError, handleRunCode, handleSubmitCode, isAuthenticated } =
    useCodeRunner({ fullQuestion, language, currentCode });

  const { messages, isTyping, sendMessage } = useCoaching();

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

  const handleSendMessage = useCallback(
    async (message: string, mode: string) => {
      if (!fullQuestion) return;
      await sendMessage(message, mode as any, fullQuestion.title, currentCode, language);
    },
    [fullQuestion, currentCode, language, sendMessage]
  );

  if (loading) {
    return (
      <div className="min-h-[100dvh] bg-background text-foreground">
        <Header />
        <main className="flex items-center justify-center min-h-[60vh]">
          <div className="flex flex-col items-center gap-3">
            <Loader2Icon className="h-6 w-6 animate-spin text-muted-foreground/40" />
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
              <RadixChevronLeft className="h-3 w-3" />
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
              <RadixChevronLeft className="h-3 w-3" />
              Back to problems
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="h-dvh bg-background text-foreground flex flex-col overflow-hidden">
      <Header />
      <div className="flex-1 flex flex-col min-h-0 px-4 pb-4">
      <div className="flex items-center gap-2 px-1 py-2">
        <Link
          href="/problems"
          className="flex items-center gap-1 px-3 py-1.5 text-xs text-muted-foreground/60 hover:text-foreground hover:bg-white/5 rounded-full transition-all"
        >
          <RadixChevronLeft className="h-3 w-3" />
          Problems
        </Link>
        <span className="text-xs text-muted-foreground/30">/</span>
        <span className="text-xs text-foreground/60 truncate max-w-[200px]">
          {fullQuestion.title}
        </span>
      </div>

      <div className="flex-1 min-h-0">
        <ResizablePanelGroup
          panels={[
            {
              id: 'description',
              defaultSize: 28,
              minSize: 280,
              children: (
                <div className="h-full flex flex-col rounded-[1.5rem] bg-white/[0.03] ring-1 ring-white/5 p-1 mr-1">
                  <div className="flex-1 flex flex-col rounded-[calc(1.5rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.06)] overflow-hidden">
                    <QuestionDescriptionPanel
                      selectedQuestion={fullQuestion}
                    />
                  </div>
                </div>
              ),
            },
            {
              id: 'editor',
              defaultSize: 44,
              minSize: 400,
              children: (
                <div className="h-full flex flex-col rounded-[1.5rem] bg-white/[0.03] ring-1 ring-white/5 p-1 mr-1">
                  <div className="flex-1 flex flex-col rounded-[calc(1.5rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.06)] overflow-hidden">
                    <CodeEditorContainer
                      language={language}
                      currentCode={currentCode}
                      initialCode={
                        fullQuestion.starter &&
                        typeof fullQuestion.starter === 'object'
                          ? (fullQuestion.starter[language as keyof typeof fullQuestion.starter] || '')
                          : ''
                      }
                      isRunning={isRunning}
                      output={output}
                      error={executionError || error || ''}
                      isInteractive={fullQuestion.is_interactive || false}
                      onCodeChange={setCurrentCode}
                      onLanguageChange={setLanguage}
                      onRunCode={handleRunCode}
                      onSubmitCode={handleSubmitCode}
                      isAuthenticated={isAuthenticated}
                    />
                  </div>
                </div>
              ),
            },
            {
              id: 'chat',
              defaultSize: 28,
              minSize: 280,
              children: (
                <div className="h-full flex flex-col rounded-[1.5rem] bg-white/[0.03] ring-1 ring-white/5 p-1">
                  <div className="flex-1 flex flex-col rounded-[calc(1.5rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.06)] overflow-hidden">
                    <AIChatPanelContainer
                      messages={messages}
                      onSendMessage={handleSendMessage}
                      isTyping={isTyping}
                      selectedQuestion={fullQuestion.title}
                      currentCode={currentCode}
                      language={language}
                    />
                  </div>
                </div>
              ),
            },
          ]}
        />
      </div>
      </div>
    </div>
  );
}
