'use client';

import { useState, useCallback, useEffect } from 'react';
import { Header } from '@/components/header/Header';
import { Sidebar } from '@/components/sidebar/Sidebar';
import { OnboardingTour } from '@/components/onboarding/OnboardingTour';
import { Question, QuestionSummary, Language } from '@/types';
import { useQuestion } from '@/features/question/question.hook';
import { useCodeRunner } from '@/features/question/use-code-runner.hook';
import { useCoaching } from '@/features/coaching/coaching.hook';
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

  const {
    questions,
    selectedQuestion,
    fullQuestion,
    isLoading,
    isLoadingQuestion,
    error: questionError,
    loadQuestions,
    selectQuestion,
    clearError,
  } = useQuestion();

  const {
    userProgress,
    handleRunCode,
    handleSubmitCode,
    isRunning,
    output,
    executionError,
    clearOutput,
    clearExecutionError,
  } = useCodeRunner({ fullQuestion, language, currentCode });

  const {
    messages,
    isTyping,
    error: coachingError,
    sendMessage,
    clearMessages,
    clearError: clearCoachingError,
  } = useCoaching();

  useEffect(() => {
    setIsMounted(true);
    loadQuestions();
  }, [loadQuestions]);

  useEffect(() => {
    if (fullQuestion && fullQuestion.starter) {
      setCurrentCode(fullQuestion.starter[language] || '');
    }
  }, [language, fullQuestion]);

  const displayQuestion: Question | QuestionSummary | null = fullQuestion || selectedQuestion;

  const handleSendMessage = useCallback(
    async (message: string, mode: string) => {
      if (!displayQuestion) return;
      await sendMessage(message, mode as any, displayQuestion.title, currentCode, language);
    },
    [displayQuestion, currentCode, language, sendMessage]
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
        fullQuestion={displayQuestion}
        onSelectQuestion={selectQuestion}
        userProgress={userProgress}
      />

      <MainContentContainer>
        <Header />
        <ContentLayoutContainer>
          <QuestionContentSection>
            <CodeEditorContainer
              language={language}
              currentCode={currentCode}
              isRunning={isRunning}
              output={output}
              error={executionError || questionError || ''}
              onCodeChange={setCurrentCode}
              onLanguageChange={setLanguage}
              onRunCode={handleRunCode}
              onSubmitCode={handleSubmitCode}
            />
          </QuestionContentSection>
          <AIChatPanelContainer
            messages={messages}
            onSendMessage={handleSendMessage}
            isTyping={isTyping}
            selectedQuestion={displayQuestion?.title || ''}
            currentCode={currentCode}
            language={language}
          />
        </ContentLayoutContainer>
      </MainContentContainer>
    </MainLayoutContainer>
  );
}
