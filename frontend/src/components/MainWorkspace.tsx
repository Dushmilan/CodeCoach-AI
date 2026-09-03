'use client';

import { useState, useCallback, useEffect } from 'react';
import { Sparkles } from 'lucide-react';
import { Header } from '@/components/header/Header';
import { Sidebar } from '@/components/sidebar/Sidebar';
import { OnboardingTour } from '@/components/onboarding/OnboardingTour';
import { Question, QuestionSummary, Language } from '@/types';
import { useQuestion } from '@/features/question/question.hook';
import { useCodeRunner } from '@/features/question/use-code-runner.hook';
import { useCoaching } from '@/features/coaching/coaching.hook';
import { CoachingMode } from '@/features/coaching/coaching.types';
import {
  LoadingSkeleton,
  MainLayoutContainer,
  MainContentContainer,
  ContentLayoutContainer,
  QuestionContentSection,
  CodeEditorContainer,
  AIChatPanelContainer,
} from '@/components/layout/elements';

export function MainWorkspace() {
  const [language, setLanguage] = useState<Language>('python');
  const [currentCode, setCurrentCode] = useState<string>('');
  const [isMounted, setIsMounted] = useState(false);
  const [isAIChatOpen, setIsAIChatOpen] = useState(true);

  const {
    questions,
    selectedQuestion,
    fullQuestion,
    selectQuestion,
    loadQuestions,
    isLoading,
    error,
  } = useQuestion();

  useEffect(() => {
    loadQuestions();
  }, [loadQuestions]);

  const {
    isRunning,
    output,
    testResults,
    executionError,
    handleRunCode,
    handleSubmitCode,
    isAuthenticated,
  } = useCodeRunner({ currentCode, language, fullQuestion });

  const { messages, isTyping, sendMessage } = useCoaching();

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (
      fullQuestion?.starter &&
      typeof fullQuestion.starter === 'object' &&
      language in fullQuestion.starter
    ) {
      setCurrentCode(fullQuestion.starter[language as keyof typeof fullQuestion.starter] || '');
    } else {
      setCurrentCode('');
    }
  }, [language, fullQuestion]);

  const displayQuestion: Question | QuestionSummary | null = fullQuestion || selectedQuestion;

  const initialCode =
    fullQuestion && typeof fullQuestion.starter === 'object'
      ? fullQuestion.starter[language as keyof typeof fullQuestion.starter] || ''
      : '';

  const handleRunCodeWrapper = (stdin: string) => {
    handleRunCode(stdin);
  };

  const handleSubmitWrapper = useCallback(async () => {
    await handleSubmitCode();
    if (typeof window !== "undefined") {
      window.dispatchEvent(new Event("learner-context-invalidated"));
    }
  }, [handleSubmitCode]);

  const buildProblemContext = useCallback(() => {
    if (!displayQuestion) return "";
    const base = displayQuestion.title || "";
    if (fullQuestion) {
      const desc = typeof fullQuestion.description === "string" ? fullQuestion.description : JSON.stringify(fullQuestion.description);
      const examples = (fullQuestion.examples || []).map((e: any) => `Input: ${e.input} -> Output: ${e.output}`).join("\n");
      const constraints = (fullQuestion.constraints || []).join("; ");
      const category = fullQuestion.category || "";
      const difficulty = fullQuestion.difficulty || "";
      return [base, `Category: ${category}`, `Difficulty: ${difficulty}`, `Description: ${desc}`, examples ? `Examples:\n${examples}` : "", constraints ? `Constraints: ${constraints}` : ""].filter(Boolean).join("\n\n");
    }
    return base;
  }, [displayQuestion, fullQuestion]);

  const handleSendMessage = useCallback(
    async (message: string, mode: CoachingMode) => {
      if (!displayQuestion) return;
      setIsAIChatOpen(true);
      const problemContext = buildProblemContext();
      await sendMessage(
        message,
        mode,
        problemContext,
        currentCode,
        language,
        undefined,
        (displayQuestion as any)?.difficulty || undefined,
        initialCode,
        'questions',
      );
      // Silent Practice Next refresh is handled via learner invalidation event dispathed by backend cache; also trigger frontend refresh
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event("learner-context-invalidated"));
      }
    },
    [displayQuestion, currentCode, language, sendMessage, initialCode, buildProblemContext],
  );

  if (!isMounted || isLoading) {
    return <LoadingSkeleton />;
  }

  return (
    <MainLayoutContainer>
      <OnboardingTour />
      <Sidebar
        questions={questions}
        selectedQuestion={selectedQuestion}
        fullQuestion={fullQuestion}
        onSelectQuestion={selectQuestion}
        userProgress={{}}
      />

      <MainContentContainer>
        <Header />
        <ContentLayoutContainer>
          <QuestionContentSection>
            <CodeEditorContainer
              language={language}
              currentCode={currentCode}
              initialCode={initialCode}
              isRunning={isRunning}
              output={output}
              error={executionError || error || ''}
              testResults={testResults}
              isInteractive={fullQuestion?.is_interactive || false}
              onCodeChange={setCurrentCode}
              onLanguageChange={setLanguage}
              onRunCode={handleRunCodeWrapper}
              onSubmitCode={handleSubmitWrapper}
              isAuthenticated={isAuthenticated}
            />
          </QuestionContentSection>
          {isAIChatOpen && (
            <div className="flex-[0_0_35%] min-w-[350px] max-w-[450px] h-full flex flex-col">
              <AIChatPanelContainer
                messages={messages}
                onSendMessage={handleSendMessage}
                onClose={() => setIsAIChatOpen(false)}
                isTyping={isTyping}
                selectedQuestion={displayQuestion?.title || ''}
                currentCode={currentCode}
                language={language}
              />
            </div>
          )}
          {!isAIChatOpen && (
            <div className="flex flex-col items-center justify-center p-4">
              <button
                onClick={() => setIsAIChatOpen(true)}
                aria-label="Open AI Panel"
                className="inline-flex items-center gap-2 rounded-full bg-white/[0.05] hover:bg-white/[0.08] px-4 py-2 text-xs font-medium text-muted-foreground/70 hover:text-foreground ring-1 ring-white/[0.06] transition-all active:scale-[0.97]"
              >
                <Sparkles className="h-3.5 w-3.5 text-primary/70" />
                Ask Coach
              </button>
            </div>
          )}
        </ContentLayoutContainer>
      </MainContentContainer>
    </MainLayoutContainer>
  );
}
