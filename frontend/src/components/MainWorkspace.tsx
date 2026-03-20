'use client';

import { useState, useCallback, useMemo, useEffect } from 'react';
import { Header } from '@/components/header/Header';
import { Sidebar } from '@/components/sidebar/Sidebar';
import { CodeEditor } from '@/components/editor/CodeEditor';
import { AIChatPanel } from '@/components/chat/AIChatPanel';
import { Question, QuestionSummary, Language } from '@/types';
import { useQuestion } from '@/features/question/question.hook';
import { useCodeExecution } from '@/features/code-execution/code-execution.hook';
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
  const [userProgress, setUserProgress] = useState<Record<string, 'attempted' | 'solved'>>({});
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
    isRunning,
    output,
    error: executionError,
    validateCode,
    runLocalJavaScript,
    clearOutput,
    clearError: clearExecutionError,
  } = useCodeExecution();

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

  const handleRunCode = useCallback(async () => {
    if (!fullQuestion) {
      return;
    }

    if (language === 'javascript') {
      try {
        await runLocalJavaScript(currentCode, fullQuestion);
      } catch (err) {
        console.error('JavaScript execution error:', err);
      }
      return;
    }

    try {
      const validation = await validateCode(language, currentCode, fullQuestion.test_cases);

      let outputText = '';
      outputText += `Test Results: ${validation.passed_tests}/${validation.total_tests} passed\n`;
      outputText += `Success Rate: ${(validation.success_rate * 100).toFixed(0)}%\n\n`;

      validation.results.forEach((r, index) => {
        const testCase = fullQuestion.test_cases[index];
        const status = r.passed ? 'Pass' : 'Fail';
        outputText += `${r.passed ? '✅' : '❌'} ${r.test_name || `Test ${index + 1}`}:\n`;
        outputText += `   Status: ${status}\n`;
        outputText += `   Input: ${testCase.input}\n`;
        outputText += `   Expected Output: ${testCase.expected_output}\n`;
        outputText += `   Actual Output: ${r.stdout || '(empty)'}\n`;
        if (r.error) {
          outputText += `   Error: ${r.error}\n`;
        }
        if (r.stderr) {
          outputText += `   Stderr: ${r.stderr}\n`;
        }
        outputText += '\n';
      });

      if (validation.passed_tests === validation.total_tests) {
        setUserProgress((prev) => ({ ...prev, [fullQuestion.id]: 'solved' }));
      } else {
        setUserProgress((prev) => ({ ...prev, [fullQuestion.id]: 'attempted' }));
      }
    } catch (error) {
      console.error('Code execution error:', error);
    }
  }, [fullQuestion, language, currentCode, validateCode, runLocalJavaScript]);

  const difficultyBadge = useMemo(() => {
    if (!displayQuestion) return '';

    const styles: Record<string, string> = {
      easy: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
      hard: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    };

    return styles[displayQuestion.difficulty] || styles.easy;
  }, [displayQuestion]);

  if (!isMounted || isLoading) {
    return <LoadingSkeleton />;
  }

  return (
    <MainLayoutContainer>
      <Sidebar
        questions={questions}
        selectedQuestion={selectedQuestion}
        fullQuestion={displayQuestion}
        onSelectQuestion={selectQuestion}
        userProgress={userProgress}
        difficultyBadge={difficultyBadge}
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
