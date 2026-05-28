'use client';

import { motion } from 'framer-motion';
import {
  ArrowLeftIcon,
  ArrowRightIcon,
  CheckIcon,
  ReaderIcon,
  CodeIcon,
} from '@radix-ui/react-icons';
import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Header } from '@/components/header/Header';
import { MarkdownRenderer } from '@/components/learn/MarkdownRenderer';
import { CodeEditorContainer } from '@/components/layout/elements/CodeEditorContainer';
import { AIChatPanelContainer } from '@/components/layout/elements/AIChatPanelContainer';
import { useLesson } from '@/features/curriculum/use-curriculum.hook';
import { useCoaching } from '@/features/coaching/coaching.hook';
import { useAuth } from '@/providers';
import { FetchClient } from '@/lib/fetch-client';
import { Language, LessonSummary, CourseDetail } from '@/types';
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
    const fetchAdjacent = async () => {
      try {
        const course = await api.get<CourseDetail>(`/api/courses/${lesson.course_id}`);
        const allLessons = course.modules.flatMap(m => m.lessons);
        const currentIndex = allLessons.findIndex(l => l.id === lesson.id);
        setAdjacent({
          prevId: currentIndex > 0 ? allLessons[currentIndex - 1].id : null,
          nextId: currentIndex < allLessons.length - 1 ? allLessons[currentIndex + 1].id : null,
        });
      } catch (err) {
        console.error('Failed to fetch adjacent lessons:', err);
      }
    };
    fetchAdjacent();
  }, [lesson]);
  return adjacent;
}

export default function LessonPage() {
  const params = useParams();
  const router = useRouter();
  const lessonId = params.lessonId as string;
  const { lesson, isLoading, error } = useLesson(lessonId);
  const { isAuthenticated } = useAuth();
  const { prevId, nextId } = useAdjacentLessons(lesson);

  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState('');
  const [runError, setRunError] = useState('');
  const [currentCode, setCurrentCode] = useState('');
  const [language, setLanguage] = useState<Language>('python');
  const [isCompleted, setIsCompleted] = useState(false);
  const [isMarkingComplete, setIsMarkingComplete] = useState(false);

  const { messages, isTyping, sendMessage, clearMessages } = useCoaching();

  useEffect(() => {
    if (lesson?.starter_code) {
      setCurrentCode(lesson.starter_code);
    } else {
      setCurrentCode('');
    }
    if (lesson?.language) {
      setLanguage(lesson.language as Language);
    }
  }, [lesson]);

  useEffect(() => {
    if (lesson && isAuthenticated) {
      api.post(`/api/progress/${lesson.id}/access?course_id=${lesson.course_id}`).catch(() => {});
    }
  }, [lesson, isAuthenticated]);

  const handleMarkComplete = useCallback(async () => {
    if (!lesson || !isAuthenticated) return;
    setIsMarkingComplete(true);
    try {
      await api.post(`/api/progress/${lesson.id}/complete?course_id=${lesson.course_id}`);
      setIsCompleted(true);
      showToast('Lesson marked as complete!', 'success');
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to mark complete', 'error');
    } finally {
      setIsMarkingComplete(false);
    }
  }, [lesson, isAuthenticated]);

  const handleRunCode = async () => {
    setIsRunning(true);
    setOutput('');
    setRunError('');
    try {
      const result = await api.post<{ stdout: string; stderr: string; exit_code: number }>('/api/run/', {
        language,
        code: currentCode,
        stdin: '',
      });
      if (result.exit_code !== 0) {
        setRunError(result.stderr || `Exit code: ${result.exit_code}`);
      } else {
        setOutput(result.stdout);
      }
    } catch (err) {
      setRunError(err instanceof Error ? err.message : 'Run failed');
    } finally {
      setIsRunning(false);
    }
  };

  const handleSubmitCode = async () => {
    if (!lesson?.test_cases?.length) {
      await handleRunCode();
      return;
    }
    setIsRunning(true);
    setOutput('');
    setRunError('');
    try {
      const results: string[] = [];
      let allPassed = true;
      for (const tc of lesson.test_cases) {
        const result = await api.post<{ stdout: string; stderr: string; exit_code: number }>('/api/run/', {
          language,
          code: currentCode,
          stdin: tc.input,
        });
        const passed = result.exit_code === 0 && result.stdout.trim() === tc.expected_output.trim();
        if (!passed) allPassed = false;
        results.push(
          `${passed ? '✓' : '✗'} ${tc.description}\n` +
          `  Input:    "${tc.input}"\n` +
          `  Expected: "${tc.expected_output}"\n` +
          `  Got:      "${result.stdout.trim()}"\n`
        );
      }
      if (allPassed) {
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
  };

  const handleCodeChange = (code: string) => {
    setCurrentCode(code);
  };

  const handleLanguageChange = (lang: Language) => {
    setLanguage(lang);
  };

  const handleSendMessage = useCallback(
    async (message: string, mode: string) => {
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

  if (isLoading) {
    return (
      <div className="min-h-[100dvh] bg-background text-foreground">
        <Header />
        <main className="max-w-5xl mx-auto px-6 pt-20 pb-24">
          <div className="animate-pulse space-y-4">
            <div className="h-5 w-32 rounded-full bg-white/[0.03]" />
            <div className="h-4 w-64 rounded-full bg-white/[0.02]" />
            <div className="h-[32rem] rounded-2xl border border-white/[0.04] bg-white/[0.01]" />
          </div>
        </main>
      </div>
    );
  }

  if (error || !lesson) {
    return (
      <div className="min-h-[100dvh] bg-background text-foreground">
        <Header />
        <main className="max-w-5xl mx-auto px-6 pt-20 pb-24">
          <div className="rounded-2xl bg-red-500/5 border border-red-500/10 p-6">
            <p className="text-sm text-red-400/80">{error || 'Lesson not found'}</p>
          </div>
          <Link href="/learn" className="inline-flex items-center gap-1.5 text-xs text-muted-foreground/50 hover:text-foreground/70 mt-4 transition-colors">
            <ArrowLeftIcon /> Back to learning paths
          </Link>
        </main>
      </div>
    );
  }

  const isExercise = lesson.type === 'exercise';

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5, ease: [0.32, 0.72, 0, 1] }}
      className="min-h-[100dvh] bg-background text-foreground flex flex-col"
    >
      <Header />

      <main className="flex-1 flex flex-col px-6 pt-6 pb-4 max-w-7xl mx-auto w-full">
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
          <div className="flex-1 flex min-h-0 divide-x divide-white/[0.04]">
            <div className="w-[35%] min-w-0 overflow-y-auto p-6">
              <MarkdownRenderer content={lesson.content} />
              {lesson.test_cases && lesson.test_cases.length > 0 && (
                <div className="mt-6 pt-5 border-t border-white/[0.04]">
                  <h3 className="text-[11px] uppercase tracking-widest text-muted-foreground/40 mb-3 font-mono">
                    Test Cases
                  </h3>
                  <div className="space-y-2">
                    {lesson.test_cases.map((tc, i) => (
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
              {isCompleted && (
                <div className="mt-4 pt-4 border-t border-white/[0.04]">
                  <span className="inline-flex items-center gap-1.5 text-xs text-primary/70">
                    <CheckIcon width={12} height={12} /> Completed
                  </span>
                </div>
              )}
            </div>

            <div className="flex-[2] flex min-w-0 divide-x divide-white/[0.04]">
              <div className="flex-1 min-w-0 flex flex-col">
                <CodeEditorContainer
                  language={language}
                  currentCode={currentCode}
                  isRunning={isRunning}
                  output={output}
                  error={runError}
                  onCodeChange={handleCodeChange}
                  onLanguageChange={handleLanguageChange}
                  onRunCode={handleRunCode}
                  onSubmitCode={handleSubmitCode}
                />
              </div>
              <div className="w-80 flex-shrink-0">
                <AIChatPanelContainer
                  messages={messages}
                  onSendMessage={handleSendMessage}
                  isTyping={isTyping}
                  selectedQuestion={lesson.title}
                  currentCode={currentCode}
                  language={language}
                />
              </div>
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
                {!isAuthenticated && <div />}
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
  );
}
