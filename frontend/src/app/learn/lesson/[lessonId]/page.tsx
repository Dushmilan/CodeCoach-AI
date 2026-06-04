'use client';

import { motion } from 'framer-motion';
import {
  ArrowLeftIcon,
  ArrowRightIcon,
  CheckIcon,
  ReaderIcon,
  CodeIcon,
} from '@radix-ui/react-icons';
import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Header } from '@/components/header/Header';
import { MarkdownRenderer } from '@/components/learn/MarkdownRenderer';
import { CodeEditorContainer } from '@/components/layout/elements/CodeEditorContainer';
import { AIChatPanelContainer } from '@/components/layout/elements/AIChatPanelContainer';
import { HydrationGuard } from '@/components/ui/HydrationGuard';
import { useLesson } from '@/features/curriculum/use-curriculum.hook';
import { useCoaching } from '@/features/coaching/coaching.hook';
import { useAuth } from '@/providers';
import { FetchClient } from '@/lib/fetch-client';
import { Language, LessonSummary, CourseDetail, Question } from '@/types';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { showToast } from '@/components/ui/Toast';

const api = new FetchClient();

function useAdjacentLessons(lesson: LessonSummary | null) {
  const [adjacent, setAdjacent] = useState<{ prevId: string | null; nextId: string | null }>({
    prevId: null,
    nextId: null,
  });

  useEffect(() => {
    if (!lesson) return;
    api.get<{ prev_id: string | null; next_id: string | null }>(
      `/api/courses/lessons/${lesson.id}/adjacent`
    )
      .then((d) => setAdjacent({ prevId: d.prev_id, nextId: d.next_id }))
      .catch((err) => console.error('Failed to fetch adjacent lessons:', err));
  }, [lesson?.id]);
  return adjacent;
}

export default function LessonPage() {
  const params = useParams();
  const lessonId = params.lessonId as string;
  const { lesson, isLoading, error } = useLesson(lessonId);
  const { isAuthenticated, isHydrated } = useAuth();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const { prevId, nextId } = useAdjacentLessons(lesson);

  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState('');
  const [runError, setRunError] = useState('');
  const [currentCode, setCurrentCode] = useState('');
  const [language, setLanguage] = useState<Language>((lesson?.language as Language) || 'python');

  // Sync language when lesson changes
  useEffect(() => {
    if (lesson?.language) {
      setLanguage(lesson.language as Language);
    }
  }, [lesson?.language]);

  const [isCompleted, setIsCompleted] = useState(false);
  const [isMarkingComplete, setIsMarkingComplete] = useState(false);
  const [linkedQuestion, setLinkedQuestion] = useState<Question | null>(null);
  const [isAIChatOpen, setIsAIChatOpen] = useState(true);

  const { messages, isTyping, sendMessage } = useCoaching();

  // Load progress
  useEffect(() => {
    if (!lesson || !isAuthenticated) return;
    api.get<{ completed_lessons: string[] }>(`/api/progress/${lesson.course_id}`)
      .then((p) => setIsCompleted(p.completed_lessons?.includes(lesson.id) ?? false))
      .catch(() => setIsCompleted(false));
  }, [lesson?.id, lesson?.course_id, isAuthenticated]);

  // Load linked question data
  useEffect(() => {
    if (lesson?.question_id) {
        api.get<Question>(`/api/questions/${lesson.question_id}`).then(setLinkedQuestion).catch(console.error);
    }
  }, [lesson?.question_id]);

  const handleSendMessage = useCallback(
    async (message: string, mode: string) => {
      setIsAIChatOpen(true);
      const lessonContext = lesson ? `${lesson.title}` : undefined;
      await sendMessage(
        message,
        mode as any,
        lesson?.title || 'Coding exercise',
        currentCode,
        language,
        lessonContext
      );
    },
    [lesson, currentCode, language, sendMessage]
  );

  const handleMarkComplete = async () => {
    if (!lesson || !isAuthenticated) return;
    setIsMarkingComplete(true);
    try {
      await api.post(`/api/progress/${lesson.id}/complete?course_id=${lesson.course_id}`);
      setIsCompleted(true);
      showToast('Lesson marked as complete!');
    } catch (err) {
      showToast('Failed to mark complete');
    } finally {
      setIsMarkingComplete(false);
    }
  };

  const handleRunCode = async (stdin: string) => {
    setIsRunning(true);
    setRunError('');
    try {
      const res = (await api.post('/api/run/', {
        language,
        code: currentCode,
        stdin: stdin
      })) as { stdout: string; stderr: string };
      setOutput(res.stdout || '');
      setRunError(res.stderr || '');
    } catch (err) {
      setRunError('Execution failed');
    } finally {
      setIsRunning(false);
    }
  };

  const handleSubmitCode = async () => {
    if (!lesson) return;
    setIsRunning(true);
    setRunError('');

    if (linkedQuestion) {
      try {
        const submitRes = (await api.post('/api/submit/', {
          question_id: linkedQuestion.id,
          language,
          code: currentCode
        })) as { passed: boolean; total: number; passed_count: number; results: Array<{ index: number; passed: boolean; actual: string }> };

        const results = submitRes.results.map((r: any) =>
          `Test ${r.index}: ${r.passed ? 'PASSED' : 'FAILED'}${r.actual ? ` (Actual: ${r.actual})` : ''}`
        );
        if (submitRes.passed) {
          setOutput('All tests passed!\n\n' + results.join('\n'));
          if (isAuthenticated && !isCompleted) {
            await handleMarkComplete();
          }
        } else {
          setOutput(results.join('\n'));
        }
      } catch (err) {
        setRunError(err instanceof Error ? err.message : 'Submission failed');
      } finally {
        setIsRunning(false);
      }
      return;
    }

    const lessonTestCases = lesson.test_cases;
    if (!lessonTestCases || lessonTestCases.length === 0) {
      setIsRunning(false);
      return;
    }

    let passedCount = 0;
    const resultLines: string[] = [];

    for (let i = 0; i < lessonTestCases.length; i++) {
      const tc = lessonTestCases[i];
      try {
        const res = (await api.post('/api/run/', {
          language,
          code: currentCode,
          stdin: tc.input
        })) as { stdout: string; stderr: string };

        const actual = (res.stdout || '').trim();
        const expected = tc.expected_output.trim();
        const passed = actual === expected;
        if (passed) passedCount++;
        resultLines.push(
          `Test ${i + 1}: ${passed ? 'PASSED' : 'FAILED'}\n  Input: ${tc.input}\n  Expected: ${expected}\n  Actual: ${actual}`
        );
      } catch (err) {
        resultLines.push(`Test ${i + 1}: ERROR - ${err instanceof Error ? err.message : 'Execution failed'}`);
      }
    }

    const allPassed = passedCount === lessonTestCases.length;
    if (allPassed) {
      setOutput('All tests passed!\n\n' + resultLines.join('\n'));
      if (isAuthenticated && !isCompleted) {
        await handleMarkComplete();
      }
    } else {
      setOutput(`Passed ${passedCount}/${lessonTestCases.length}\n\n` + resultLines.join('\n'));
    }
    setIsRunning(false);
  };

  const handleCodeChange = (code: string) => {
    setCurrentCode(code);
  };

  const handleLanguageChange = (lang: Language) => {
    setLanguage(lang);
  };

  const codeInitialized = useRef(false);

  useEffect(() => {
    codeInitialized.current = false;
  }, [lesson?.id]);

  useEffect(() => {
    const starter = (linkedQuestion?.starter as any)?.[language] || lesson?.starter_code || '';
    if (starter && !codeInitialized.current) {
      setCurrentCode(starter);
      codeInitialized.current = true;
    }
  }, [lesson?.id, linkedQuestion?.id, language]);

  if (isLoading) return <div>Loading...</div>;
  if (error || !lesson) return <div>Error</div>;

  const isExercise = lesson.type === 'exercise';
  const resolvedTestCases = linkedQuestion?.test_cases || lesson.test_cases || [];
  const resolvedStarterCode = (linkedQuestion?.starter as any)?.[language] || lesson.starter_code || '';

  return (
    <HydrationGuard>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, ease: [0.32, 0.72, 0, 1] }}
        className="h-dvh bg-background text-foreground flex flex-col overflow-hidden"
      >
        <Header />

        <main className="flex-1 flex flex-col px-6 pt-6 pb-4 max-w-7xl mx-auto w-full min-h-0 overflow-hidden">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <Link
                href={`/learn/${lesson.course_id}`}
                className="flex items-center gap-1.5 text-xs text-muted-foreground/40 hover:text-foreground/60 transition-colors"
              >
                <ArrowLeftIcon width={12} height={12} /> Back
              </Link>
              <span className="text-muted-foreground/15">/</span>
              <div className="flex items-center gap-2.5">
                <span className={cn(
                  'flex h-7 w-7 items-center justify-center rounded-lg',
                  isExercise ? 'bg-emerald-500/8' : 'bg-white/[0.04]'
                )}>
                  {isExercise ? (
                    <CodeIcon width={14} height={14} className="text-emerald-500/60" />
                  ) : (
                    <ReaderIcon width={14} height={14} className="text-muted-foreground/40" />
                  )}
                </span>
                <div>
                  <h1 className="text-sm font-medium tracking-tight text-foreground/80">
                    {lesson.title}
                  </h1>
                  <span className={cn(
                    'text-[10px] uppercase tracking-widest',
                    isExercise ? 'text-emerald-500/50' : 'text-muted-foreground/30'
                  )}>
                    {isExercise ? 'Coding Exercise' : 'Theory Lesson'}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-1">
              {prevId && (
                <Link
                  href={`/learn/lesson/${prevId}`}
                  className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/[0.06] hover:bg-white/[0.04] transition-all"
                >
                  <ArrowLeftIcon width={14} height={14} className="text-muted-foreground/40" />
                </Link>
              )}
              {nextId && (
                <Link
                  href={`/learn/lesson/${nextId}`}
                  className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/[0.06] hover:bg-white/[0.04] transition-all"
                >
                  <ArrowRightIcon width={14} height={14} className="text-muted-foreground/40" />
                </Link>
              )}
            </div>
          </div>

          {isExercise ? (
            <div className="flex-1 grid grid-cols-[35%_1fr] min-h-0 divide-x divide-white/[0.04]">
              <div className="min-w-0 overflow-y-auto p-6">
                <MarkdownRenderer content={lesson.content} />
                {resolvedTestCases.length > 0 && (
                  <div className="mt-6 pt-5 border-t border-white/[0.04]">
                    <h3 className="text-[11px] uppercase tracking-widest text-muted-foreground/40 mb-3 font-mono">
                      Test Cases
                    </h3>
                    <div className="space-y-2">
                      {resolvedTestCases.map((tc, i) => (
                        <div key={i} className="border border-white/[0.04] rounded-lg px-3 py-2">
                          <p className="text-xs text-foreground/70 font-medium">{tc.description}</p>
                          <p className="text-[11px] font-mono text-muted-foreground/40 mt-1 tabular-nums">
                            input: &ldquo;{tc.input}&rdquo; &rarr; expected: &ldquo;{tc.expected_output}&rdquo;
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="h-full grid grid-cols-[1fr_auto] min-w-0 min-h-0 divide-x divide-white/[0.04]">
                <div className="min-w-0 flex flex-col min-h-0">
                    <CodeEditorContainer
                      language={language}
                      currentCode={currentCode}
                      initialCode={resolvedStarterCode}
                      isRunning={isRunning}
                      output={output}
                      error={runError}
                      isInteractive={linkedQuestion?.is_interactive}
                      onCodeChange={handleCodeChange}
                      onLanguageChange={handleLanguageChange}
                      onRunCode={handleRunCode}
                      onSubmitCode={handleSubmitCode}
                    />
                </div>
                {isAIChatOpen && (
                  <div className="w-[400px] flex-shrink-0 h-full flex flex-col min-h-0">
                    <AIChatPanelContainer
                      messages={messages}
                      onSendMessage={handleSendMessage}
                      onClose={() => setIsAIChatOpen(false)}
                      isTyping={isTyping}
                      selectedQuestion={lesson.title}
                      currentCode={currentCode}
                      language={language}
                    />
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex-1 flex min-h-0">
              <div className="flex-1 overflow-y-auto max-w-3xl">
                <div className="border border-white/[0.04] rounded-2xl p-8">
                  <MarkdownRenderer content={lesson.content} />
                </div>

                <div className="flex items-center justify-between mt-6 pb-8">
                  {isAuthenticated && (
                    <button
                      onClick={handleMarkComplete}
                      disabled={isCompleted || isMarkingComplete}
                      className="inline-flex items-center gap-2 text-xs px-4 py-2 rounded-full border border-primary/15 text-primary/70 hover:bg-primary/5 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      <CheckIcon width={12} height={12} />
                      {isCompleted ? 'Completed' : isMarkingComplete ? 'Marking...' : 'Mark Complete'}
                    </button>
                  )}
                  <Link
                    href={nextId ? `/learn/lesson/${nextId}` : `/learn/${lesson.course_id}`}
                    className="inline-flex items-center gap-2 text-xs text-foreground/50 hover:text-foreground/70 px-4 py-2 rounded-full border border-white/[0.06] hover:border-white/[0.12] transition-all"
                  >
                    {nextId ? 'Next Lesson' : 'Back to Course'}
                    <ArrowRightIcon width={12} height={12} />
                  </Link>
                </div>
              </div>
            </div>
          )}
        </main>
      </motion.div>
    </HydrationGuard>
  );
}
