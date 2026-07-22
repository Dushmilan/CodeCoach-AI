"use client";

import { useState, useCallback, useEffect } from "react";
import { Header } from "@/components/header/Header";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { OnboardingTour } from "@/components/onboarding/OnboardingTour";
import { Question, QuestionSummary, Language } from "@/types";
import { useQuestion } from "@/features/question/question.hook";
import { useCodeRunner } from "@/features/question/use-code-runner.hook";
import { useCoaching } from "@/features/coaching/coaching.hook";
import {
  LoadingSkeleton,
  MainLayoutContainer,
  MainContentContainer,
  ContentLayoutContainer,
  QuestionContentSection,
  CodeEditorContainer,
  AIChatPanelContainer,
} from "@/components/layout/elements";

export function MainWorkspace() {
  const [language, setLanguage] = useState<Language>("python");
  const [currentCode, setCurrentCode] = useState<string>("");
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
      typeof fullQuestion.starter === "object" &&
      language in fullQuestion.starter
    ) {
      setCurrentCode(
        fullQuestion.starter[language as keyof typeof fullQuestion.starter] ||
          "",
      );
    } else {
      setCurrentCode("");
    }
  }, [language, fullQuestion]);

  const displayQuestion: Question | QuestionSummary | null =
    fullQuestion || selectedQuestion;

  const handleRunCodeWrapper = (stdin: string) => {
    handleRunCode(stdin);
  };

  const handleSendMessage = useCallback(
    async (message: string, mode: string) => {
      if (!displayQuestion) return;
      setIsAIChatOpen(true);
      await sendMessage(
        message,
        mode as any,
        displayQuestion.title,
        currentCode,
        language,
      );
    },
    [displayQuestion, currentCode, language, sendMessage],
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
              initialCode={
                fullQuestion && typeof fullQuestion.starter === "object"
                  ? fullQuestion.starter[
                      language as keyof typeof fullQuestion.starter
                    ] || ""
                  : ""
              }
              isRunning={isRunning}
              output={output}
              error={executionError || error || ""}
              isInteractive={fullQuestion?.is_interactive || false}
              onCodeChange={setCurrentCode}
              onLanguageChange={setLanguage}
              onRunCode={handleRunCodeWrapper}
              onSubmitCode={handleSubmitCode}
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
                selectedQuestion={displayQuestion?.title || ""}
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
