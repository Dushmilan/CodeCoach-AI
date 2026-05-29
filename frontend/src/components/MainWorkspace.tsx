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
  const [isAIChatOpen, setIsAIChatOpen] = useState(true);

  const {
// ... existing hook code ...
  const handleSendMessage = useCallback(
    async (message: string, mode: string) => {
      if (!displayQuestion) return;
      setIsAIChatOpen(true);
      await sendMessage(message, mode as any, displayQuestion.title, currentCode, language);
    },
    [displayQuestion, currentCode, language, sendMessage]
  );

  if (!isMounted || isLoading) {
// ... existing return code ...
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
              initialCode={fullQuestion?.starter?.[language] || ''}
              isRunning={isRunning}
              output={output}
              error={executionError || questionError || ''}
              onCodeChange={setCurrentCode}
              onLanguageChange={setLanguage}
              onRunCode={handleRunCode}
              onSubmitCode={handleSubmitCode}
            />
          </QuestionContentSection>
          {isAIChatOpen && (
            <div className="flex-[0_0_35%] min-w-[350px] max-w-[450px]">
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
                className="p-3 bg-white/[0.05] hover:bg-white/[0.08] rounded-full transition-all"
                aria-label="Open AI Panel"
              >
                <div className="w-5 h-5 bg-primary/60 rounded-full" />
              </button>
            </div>
          )}
        </ContentLayoutContainer>
      </MainContentContainer>
    </MainLayoutContainer>
  );
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
              initialCode={fullQuestion?.starter?.[language] || ''}
              isRunning={isRunning}
              output={output}
              error={executionError || questionError || ''}
              onCodeChange={setCurrentCode}
              onLanguageChange={setLanguage}
              onRunCode={handleRunCode}
              onSubmitCode={handleSubmitCode}
            />
          </QuestionContentSection>
          <div className="w-[400px] flex-shrink-0">
            <AIChatPanelContainer
              messages={messages}
              onSendMessage={handleSendMessage}
              isTyping={isTyping}
              selectedQuestion={displayQuestion?.title || ''}
              currentCode={currentCode}
              language={language}
            />
          </div>
        </ContentLayoutContainer>
      </MainContentContainer>
    </MainLayoutContainer>
  );
}
