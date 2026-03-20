'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { Header } from './Header';
import { Question, QuestionSummary, ChatMessage, Language } from '@/types';
import { api } from '@/lib/api';
import {
  LoadingSkeleton,
  MainLayoutContainer,
  SidebarContainer,
  MainContentContainer,
  ContentLayoutContainer,
  QuestionContentSection,
  CodeEditorContainer,
  AIChatPanelContainer,
} from './elements';

interface LayoutProps {
  questions: QuestionSummary[];
  userProgress?: Record<string, 'attempted' | 'solved'>;
  selectedQuestion?: QuestionSummary | null;
  onQuestionSelect?: (question: QuestionSummary) => void;
}

export function Layout({
  questions,
  userProgress: externalUserProgress,
  selectedQuestion: externalSelectedQuestion,
  onQuestionSelect: externalOnQuestionSelect
}: LayoutProps) {
  const [internalSelectedQuestion, setInternalSelectedQuestion] = useState<QuestionSummary | null>(null);
  const [fullQuestionData, setFullQuestionData] = useState<Question | null>(null);
  const [isLoadingQuestion, setIsLoadingQuestion] = useState(false);
  const [language, setLanguage] = useState<Language>('python');
  const [currentCode, setCurrentCode] = useState<string>('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [internalUserProgress, setInternalUserProgress] = useState<Record<string, 'attempted' | 'solved'>>({});
  const [isMounted, setIsMounted] = useState(false);

  // Use external props if provided, otherwise use internal state
  const selectedQuestion = externalSelectedQuestion ?? internalSelectedQuestion;
  // Use full question data if available, otherwise use the summary
  const displayQuestion: Question | QuestionSummary | null = fullQuestionData || selectedQuestion;
  const userProgress = externalUserProgress ?? internalUserProgress;
  const handleQuestionSelect = externalOnQuestionSelect ?? setInternalSelectedQuestion;

  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Fetch full question data when a question is selected
  useEffect(() => {
    if (selectedQuestion && selectedQuestion.id) {
      // Check if we already have the full data
      if (fullQuestionData?.id === selectedQuestion.id) {
        return;
      }
      
      setIsLoadingQuestion(true);
      api.getQuestion(selectedQuestion.id)
        .then((fullData) => {
          setFullQuestionData(fullData);
          setCurrentCode(fullData.starter?.[language] || '');
        })
        .catch((err) => {
          console.error('Failed to fetch full question data:', err);
        })
        .finally(() => {
          setIsLoadingQuestion(false);
        });
    }
  }, [selectedQuestion?.id, language]);

  // Update code when language changes
  useEffect(() => {
    if (fullQuestionData && fullQuestionData.starter) {
      setCurrentCode(fullQuestionData.starter[language] || '');
    }
  }, [language, fullQuestionData]);

  const handleQuestionSelection = useCallback((question: QuestionSummary) => {
    handleQuestionSelect(question);
    setFullQuestionData(null); // Reset full data when switching questions
    setMessages([]); // Clear chat when switching questions
    setOutput('');
    setError('');
  }, [handleQuestionSelect]);

  const handleSendMessage = async (message: string, mode: string) => {
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message || `${mode} requested`,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);

    try {
      const response = await api.getCoachResponse(
        displayQuestion!.title,
        language,
        currentCode,
        message,
        mode
      );

      const reader = response.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = '';

      const assistantMessageObj: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessageObj]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') continue;
            if (data.includes('"done": true')) continue;

            try {
              const parsed = JSON.parse(data);
              const content = parsed.chunk || parsed.choices?.[0]?.delta?.content || '';
              if (content) {
                assistantMessage += content;
                setMessages(prev =>  prev.map(msg =>
                  msg.id === assistantMessageObj.id
                    ? { ...msg, content: assistantMessage }
                    : msg
                ));
              }
            } catch (e) {
              // Handle non-JSON data
              if (data.trim() && !data.includes('"error"')) {
                assistantMessage += data;
                setMessages(prev =>  prev.map(msg =>
                  msg.id === assistantMessageObj.id
                    ? { ...msg, content: assistantMessage }
                    : msg
                ));
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Error getting coach response:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleRunCode = async () => {
    if (!displayQuestion) return;

    // Check if we have full question data
    if (!fullQuestionData) {
      setError('Question data is still loading. Please wait...');
      return;
    }

    setIsRunning(true);
    setOutput('');
    setError('');

    if (language === 'javascript') {
      const logs: string[] = [];
      const originalConsoleLog = console.log;
      const originalConsoleError = console.error;
      const originalConsoleWarn = console.warn;

      const captureLog = (...args: any[]) => {
        const formattedArgs = args.map(arg =>
          typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
        ).join(' ');
        logs.push(formattedArgs);
        originalConsoleLog(...args);
      };

      console.log = captureLog;
      console.error = captureLog;
      console.warn = captureLog;

      try {
        // Identify the function name from starter code
        const jsStarter = fullQuestionData.starter.javascript;
        const fnNameMatch = jsStarter.match(/function\s+(\w+)\s*\(/) ||
          jsStarter.match(/var\s+(\w+)\s*=\s*function/) ||
          jsStarter.match(/const\s+(\w+)\s*=\s*/);

        const fnName = fnNameMatch ? fnNameMatch[1] : null;

        if (!fnName) {
          throw new Error("Could not identify the target function name for testing.");
        }

        // Create a test runner
        const testRunner = new Function('testCases', `
          ${currentCode}

          if (typeof ${fnName} !== 'function') {
            throw new Error('Function "${fnName}" is not defined or is not a function.');
          }

          return testCases.map((tc, index) => {
            try {
              // Parse input string (format: "[1,2,3]\\narg2")
              const inputLines = tc.input.split('\\n');
              const parsedArgs = inputLines.map(line => JSON.parse(line));
              const result = ${fnName}(...parsedArgs);
              const expectedOutput = JSON.parse(tc.expected_output);
              const passed = JSON.stringify(result) === JSON.stringify(expectedOutput);
              return { index: index + 1, passed, input: tc.input, expected: tc.expected_output, actual: result };
            } catch (e) {
              return { index: index + 1, passed: false, error: e.message, input: tc.input };
            }
          });
        `);

        const results = testRunner(fullQuestionData.test_cases);

        let outputText = logs.length > 0 ? `Console Output:\n${logs.join('\n')}\n\n` : '';
        outputText += "Test Results:\n";

        let allPassed = true;
        results.forEach((r: any) => {
          if (r.error) {
            outputText += `❌ Test Case ${r.index}: Error - ${r.error}\n`;
            allPassed = false;
          } else if (r.passed) {
            outputText += `✅ Test Case ${r.index}: Passed\n`;
          } else {
            outputText += `❌ Test Case ${r.index}: Failed\n Input: ${r.input}\n Expected: ${r.expected}\n Actual: ${JSON.stringify(r.actual)}\n`;
            allPassed = false;
          }
        });

        setOutput(outputText);
        if (allPassed) {
          setInternalUserProgress(prev => ({ ...prev, [fullQuestionData.id]: 'solved' }));
        }
      } catch (err: any) {
        setError(err.message || 'An error occurred during execution');
      } finally {
        console.log = originalConsoleLog;
        console.error = originalConsoleError;
        console.warn = originalConsoleWarn;
        setIsRunning(false);
      }
      return;
    }

    try {
      const result = await api.runCode(language, currentCode);

      if (result.exit_code === 0) {
        setOutput(result.stdout);
      } else {
        setError(result.stderr || result.stdout);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      setError(`Failed to run code: ${errorMessage}`);
      console.error('Code execution error:', error);
    } finally {
      setIsRunning(false);
    }
  };

  // Memoize expensive computations
  const questionSummary = useMemo(() => {
    if (!displayQuestion) return null;

    const progress = userProgress[displayQuestion.id];
    const status = progress === 'solved' ? '✅ Solved' :
      progress === 'attempted' ? '🔄 Attempted' : '⏳ Not started';

    return `${displayQuestion.title} - ${status}`;
  }, [displayQuestion, userProgress]);

  // Memoize difficulty badge styles
  const difficultyBadge = useMemo(() => {
    if (!displayQuestion) return null;

    const styles = {
      easy: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
      hard: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
    };

    return styles[displayQuestion.difficulty] || styles.easy;
  }, [displayQuestion]);

  if (!isMounted) {
    return <LoadingSkeleton />;
  }

  return (
    <MainLayoutContainer>
      <SidebarContainer
        questions={questions}
        selectedQuestion={selectedQuestion}
        onSelectQuestion={handleQuestionSelection}
        userProgress={userProgress}
        difficultyBadge={difficultyBadge || ''}
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
              error={error}
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
