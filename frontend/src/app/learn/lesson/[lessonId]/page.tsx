'use client';

import { Header } from '@/components/header/Header';
import { AnimateLauncher } from '@/components/animate/AnimateLauncher';
import {
  ExerciseLessonLayout,
  LessonChrome,
  TheoryLessonLayout,
} from '@/components/layout/lessons';
import { HydrationGuard } from '@/components/ui/HydrationGuard';
import { showToast } from '@/components/ui/Toast';
import { useCoaching } from '@/features/coaching/coaching.hook';
import { CoachingMode } from '@/features/coaching/coaching.types';
import { useLesson } from '@/features/curriculum/use-curriculum.hook';
import { TestCaseResultView } from '@/features/code-execution/code-execution.types';
import { FetchClient, HttpError } from '@/lib/fetch-client';
import { useAuth } from '@/providers';
import { Language, LessonSummary, Question } from '@/types';
import { motion } from 'framer-motion';
import { useParams } from 'next/navigation';
import { useCallback, useEffect, useRef, useState } from 'react';

const api = new FetchClient();

function useAdjacentLessons(lesson: LessonSummary | null) {
  const [adjacent, setAdjacent] = useState<{
    prevId: string | null;
    nextId: string | null;
  }>({
    prevId: null,
    nextId: null,
  });

  useEffect(() => {
    if (!lesson) return;
    api
      .get<{ prev_id: string | null; next_id: string | null }>(
        `/api/courses/lessons/${lesson.id}/adjacent`,
      )
      .then((d) => setAdjacent({ prevId: d.prev_id, nextId: d.next_id }))
      .catch((err) => console.error('Failed to fetch adjacent lessons:', err));
  }, [lesson]);
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
  const [testResults, setTestResults] = useState<TestCaseResultView[] | null>(null);
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

  const { messages, isTyping, sendMessage } = useCoaching();

  // Load progress
  useEffect(() => {
    if (!lesson || !isAuthenticated) return;
    api
      .get<{ completed_lessons: string[] }>(`/api/progress/${lesson.course_id}`)
      .then((p) => setIsCompleted(p.completed_lessons?.includes(lesson.id) ?? false))
      .catch(() => setIsCompleted(false));
  }, [lesson, lesson?.course_id, isAuthenticated]);

  // Load linked question data
  useEffect(() => {
    if (lesson?.question_id) {
      api
        .get<Question>(`/api/questions/${lesson.question_id}`)
        .then(setLinkedQuestion)
        .catch(console.error);
    }
  }, [lesson?.question_id]);

  const resolvedStarterCode =
    (linkedQuestion?.starter as any)?.[language] || lesson?.starter_code || '';

  const handleSendMessage = useCallback(
    async (message: string, mode: CoachingMode) => {
      const lessonContext = lesson ? `${lesson.title}` : undefined;
      await sendMessage(
        message,
        mode,
        lesson?.title || 'Coding exercise',
        currentCode,
        language,
        lessonContext,
        linkedQuestion?.difficulty,
        resolvedStarterCode,
        'learn',
      );
    },
    [lesson, currentCode, language, sendMessage, linkedQuestion?.difficulty, resolvedStarterCode],
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
    setTestResults(null);
    try {
      const res = (await api.post('/api/run/', {
        language,
        code: currentCode,
        stdin: stdin,
      })) as { stdout: string; stderr: string };
      setOutput(res.stdout || '');
      setRunError(res.stderr || '');
    } catch (err) {
      if (err instanceof HttpError) {
        setRunError(`Execution failed (${err.status}): ${err.body || err.message}`);
      } else {
        setRunError(err instanceof Error ? err.message : 'Execution failed');
      }
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
          code: currentCode,
        })) as {
          passed: boolean;
          total: number;
          passed_count: number;
          results: Array<{
            index: number;
            passed: boolean;
            actual: string;
            input: string;
            expected: string;
            hidden?: boolean;
          }>;
        };

        setTestResults(
          submitRes.results.map((r) => ({
            index: r.index,
            passed: r.passed,
            testName: `Test ${r.index}`,
            input: r.hidden ? '' : r.input,
            expected: r.hidden ? '' : r.expected,
            actual: r.hidden ? '' : r.actual,
            hidden: r.hidden ?? false,
          })),
        );
        const results = submitRes.results.map(
          (r: any) =>
            `Test ${r.index}: ${r.passed ? 'PASSED' : 'FAILED'}${
              r.actual ? ` (Actual: ${r.actual})` : ''
            }`,
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
    const structuredResults: TestCaseResultView[] = [];

    for (let i = 0; i < lessonTestCases.length; i++) {
      const tc = lessonTestCases[i];
      try {
        const res = (await api.post('/api/run/', {
          language,
          code: currentCode,
          stdin: tc.input,
        })) as { stdout: string; stderr: string };

        const actual = (res.stdout || '').trim();
        const expected = tc.expected_output.trim();
        const passed = actual === expected;
        if (passed) passedCount++;
        resultLines.push(
          `Test ${i + 1}: ${passed ? 'PASSED' : 'FAILED'}\n  Input: ${
            tc.input
          }\n  Expected: ${expected}\n  Actual: ${actual}`,
        );
        structuredResults.push({
          index: i + 1,
          passed,
          testName: `Test ${i + 1}`,
          input: tc.input,
          expected,
          actual,
          hidden: false,
        });
      } catch (err) {
        resultLines.push(
          `Test ${i + 1}: ERROR - ${err instanceof Error ? err.message : 'Execution failed'}`,
        );
        structuredResults.push({
          index: i + 1,
          passed: false,
          testName: `Test ${i + 1}`,
          input: tc.input,
          expected: tc.expected_output,
          actual: '',
          error: err instanceof Error ? err.message : 'Execution failed',
          hidden: false,
        });
      }
    }

    setTestResults(structuredResults);

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
  }, [lesson?.id, linkedQuestion?.id]);

  useEffect(() => {
    const starter = (linkedQuestion?.starter as any)?.[language] || lesson?.starter_code || '';
    if (starter && !codeInitialized.current) {
      setCurrentCode(starter);
      codeInitialized.current = true;
    }
  }, [lesson?.id, linkedQuestion?.id, language, linkedQuestion?.starter, lesson?.starter_code]);

  if (isLoading) return <div>Loading...</div>;
  if (error || !lesson) return <div>Error</div>;

  const isExercise = lesson.type === 'exercise';
  const resolvedTestCases = linkedQuestion?.test_cases || lesson.test_cases || [];

  return (
    <HydrationGuard>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, ease: [0.32, 0.72, 0, 1] }}
        className="h-dvh bg-background text-foreground flex flex-col overflow-hidden"
      >
        <Header />

        <main className="flex-1 flex flex-col px-6 pt-6 pb-4 w-full min-h-0 overflow-hidden">
          <LessonChrome
            lesson={lesson}
            prevId={prevId}
            nextId={nextId}
            actions={
              <AnimateLauncher
                problem={lesson.title}
                code={currentCode}
                language={language}
                difficulty={linkedQuestion?.difficulty}
                lessonContext={lesson.title}
                initialCode={resolvedStarterCode}
                question={linkedQuestion}
              />
            }
          />

          {isExercise ? (
            <ExerciseLessonLayout
              storageKey={lesson.id}
              lesson={lesson}
              linkedQuestion={linkedQuestion}
              testCases={resolvedTestCases}
              language={language}
              currentCode={currentCode}
              initialCode={resolvedStarterCode}
              isRunning={isRunning}
              output={output}
              error={runError}
              testResults={testResults}
              isInteractive={linkedQuestion?.is_interactive ?? false}
              messages={messages}
              isTyping={isTyping}
              selectedQuestion={lesson.title}
              onSendMessage={handleSendMessage}
              onCodeChange={handleCodeChange}
              onLanguageChange={handleLanguageChange}
              onRunCode={handleRunCode}
              onSubmitCode={handleSubmitCode}
            />
          ) : (
            <TheoryLessonLayout
              storageKey={lesson.id}
              lesson={lesson}
              nextId={nextId}
              isAuthenticated={isAuthenticated}
              isCompleted={isCompleted}
              isMarkingComplete={isMarkingComplete}
              onMarkComplete={handleMarkComplete}
              messages={messages}
              isTyping={isTyping}
              selectedQuestion={lesson.title}
              currentCode={currentCode}
              language={language}
              onSendMessage={handleSendMessage}
            />
          )}
        </main>
      </motion.div>
    </HydrationGuard>
  );
}
