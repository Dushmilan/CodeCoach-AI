'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Header } from '@/components/header/Header';
import { MarkdownRenderer } from '@/components/learn/MarkdownRenderer';
import { CodeEditorContainer } from '@/components/layout/elements/CodeEditorContainer';
import { AIChatPanelContainer } from '@/components/layout/elements/AIChatPanelContainer';
import { useLesson } from '@/features/curriculum/use-curriculum.hook';
import { useCoaching } from '@/features/coaching/coaching.hook';
import { FetchClient } from '@/lib/fetch-client';
import { Language, LessonSummary } from '@/types';
import { ArrowLeft, ArrowRight, CheckCircle2, Code2, BookOpen } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';

const api = new FetchClient();

function getAdjacentLessons(lesson: LessonSummary | null) {
  return { prevId: null, nextId: null };
}

export default function LessonPage() {
  const params = useParams();
  const router = useRouter();
  const lessonId = params.lessonId as string;
  const { lesson, isLoading, error } = useLesson(lessonId);

  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState('');
  const [runError, setRunError] = useState('');

  const [currentCode, setCurrentCode] = useState('');
  const [language, setLanguage] = useState<Language>('python');

  const {
    messages,
    isTyping,
    sendMessage,
    clearMessages,
  } = useCoaching();

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

  const handleRunCode = async () => {
    setIsRunning(true);
    setOutput('');
    setRunError('');
    try {
      const result = await api.post<{ stdout: string; stderr: string; exit_code: number }>('/api/run', {
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
        const result = await api.post<{ stdout: string; stderr: string; exit_code: number }>('/api/run', {
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
        setOutput('All tests passed! 🎉\n\n' + results.join('\n'));
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
        <main className="max-w-3xl mx-auto px-4 pt-16 pb-24">
          <div className="animate-pulse space-y-4">
            <div className="h-8 w-64 rounded-full bg-white/[0.03]" />
            <div className="h-4 w-48 rounded-full bg-white/[0.03]" />
            <div className="h-96 rounded-2xl bg-white/[0.03] ring-1 ring-white/5" />
          </div>
        </main>
      </div>
    );
  }

  if (error || !lesson) {
    return (
      <div className="min-h-[100dvh] bg-background text-foreground">
        <Header />
        <main className="max-w-3xl mx-auto px-4 pt-16 pb-24">
          <div className="rounded-2xl bg-red-500/10 ring-1 ring-red-500/20 p-6 text-sm text-red-400">
            {error || 'Lesson not found'}
          </div>
          <Link href="/learn" className="inline-flex items-center gap-2 text-sm text-primary/80 hover:text-primary mt-4 transition-colors">
            Back to learning paths
          </Link>
        </main>
      </div>
    );
  }

  const isExercise = lesson.type === 'exercise';

  return (
    <div className="min-h-[100dvh] bg-background text-foreground flex flex-col">
      <Header />

      <main className="flex-1 flex flex-col px-4 pt-6 pb-4 max-w-7xl mx-auto w-full">
        {/* Breadcrumb + Title */}
        <div className="mb-6">
          <Link
            href={`/learn/${lesson.course_id}`}
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground/60 hover:text-foreground/80 mb-3 transition-colors"
          >
            <ArrowLeft className="h-3 w-3" /> Back to course
          </Link>
          <div className="flex items-center gap-3">
            <div className={cn(
              'p-2 rounded-xl',
              isExercise ? 'bg-emerald-500/10' : 'bg-blue-500/10'
            )}>
              {isExercise ? (
                <Code2 className="h-4 w-4 text-emerald-500/70" strokeWidth={1.5} />
              ) : (
                <BookOpen className="h-4 w-4 text-blue-500/70" strokeWidth={1.5} />
              )}
            </div>
            <div>
              <h1 className="text-xl font-semibold tracking-tight text-foreground/90">{lesson.title}</h1>
              <span className={cn(
                'text-xs uppercase tracking-wider',
                isExercise ? 'text-emerald-500/60' : 'text-blue-500/60'
              )}>
                {isExercise ? 'Coding Exercise' : 'Theory Lesson'}
              </span>
            </div>
          </div>
        </div>

        {isExercise ? (
          <div className="flex-1 flex gap-4 min-h-0">
            {/* Left: Lesson instructions */}
            <div className="w-[40%] min-w-0 overflow-y-auto rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-6">
              <MarkdownRenderer content={lesson.content} />
              {lesson.test_cases && lesson.test_cases.length > 0 && (
                <div className="mt-6 pt-4 border-t border-white/5">
                  <h3 className="text-sm font-semibold text-foreground/80 mb-3">Test Cases</h3>
                  <div className="space-y-2">
                    {lesson.test_cases.map((tc, i) => (
                      <div key={i} className="text-xs text-muted-foreground/60 bg-white/[0.02] rounded-xl px-3 py-2">
                        <span className="text-foreground/70">{tc.description}</span>
                        <div className="mt-1 font-mono">
                          Input: &ldquo;{tc.input}&rdquo; → Expected: &ldquo;{tc.expected_output}&rdquo;
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Right: Code editor + AI Coach */}
            <div className="flex-[2] flex gap-4 min-w-0">
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
        ) : (
          /* Theory: scrollable content */
          <div className="flex-1 overflow-y-auto max-w-3xl mx-auto w-full">
            <div className="rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-8">
              <MarkdownRenderer content={lesson.content} />
            </div>

            <div className="flex items-center justify-between mt-6">
              <div />
              <Link
                href={`/learn/${lesson.course_id}`}
                className="inline-flex items-center gap-2 text-sm text-primary/80 hover:text-primary px-4 py-2 rounded-full bg-white/[0.03] ring-1 ring-white/5 hover:bg-white/[0.06] transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"
              >
                Continue <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
