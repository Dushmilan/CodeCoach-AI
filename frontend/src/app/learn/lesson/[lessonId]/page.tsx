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
  const [linkedQuestion, setLinkedQuestion] = useState<Question | null>(null);
  const [isAIChatOpen, setIsAIChatOpen] = useState(true);

  const { messages, isTyping, sendMessage } = useCoaching();

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
      await api.post(`/api/progress/complete`, { lesson_id: lesson.id });
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
      const res = await api.post('/api/run/', {
        language,
        code: currentCode,
        stdin: stdin
      }) as { stdout: string; stderr: string };
      setOutput(res.stdout || '');
      setRunError(res.stderr || '');
    } catch (err) {
      setRunError('Execution failed');
    } finally {
      setIsRunning(false);
    }
  };

  const handleSubmitCode = async () => {
    if (!linkedQuestion) return;
    setIsRunning(true);
    setRunError('');
    try {
      const submitRes = await api.post('/api/submit/', {
        question_id: linkedQuestion.id,
        language,
        code: currentCode
      }) as { passed: boolean; total: number; passed_count: number; results: Array<{ index: number; passed: boolean; actual: string }> };
      
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
  };

  const handleCodeChange = (code: string) => {
    setCurrentCode(code);
  };

  const handleLanguageChange = (lang: Language) => {
    setLanguage(lang);
  };

  if (isLoading) return <div>Loading...</div>;
  if (error || !lesson) return <div>Error</div>;

  const isExercise = lesson.type === 'exercise';
  const resolvedTestCases = linkedQuestion?.test_cases || [];
  const resolvedStarterCode = linkedQuestion?.starter[language as keyof typeof linkedQuestion.starter] || lesson.starter_code || '';

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5, ease: [0.32, 0.72, 0, 1] }}
      className="min-h-[100dvh] bg-background text-foreground flex flex-col"
    >
      <Header />

      <main className="flex-1 flex flex-col px-6 pt-6 pb-4 max-w-7xl mx-auto w-full">
        {/* ... header content omitted for brevity, keeping logic ... */}
        
        {isExercise ? (
          <div className="flex-1 grid grid-cols-[35%_1fr] min-h-0 divide-x divide-white/[0.04]">
            <div className="min-w-0 overflow-y-auto p-6">
              <MarkdownRenderer content={lesson.content} />
            </div>

            <div className="grid grid-cols-[1fr_auto] min-w-0 divide-x divide-white/[0.04]">
              <div className="min-w-0 flex flex-col">
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
                <div className="w-[400px] flex-shrink-0">
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
          <div>Theory lesson content</div>
        )}
      </main>
    </motion.div>
  );
}
