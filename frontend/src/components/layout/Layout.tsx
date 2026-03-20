'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { Header } from './Header';
import { Question, ChatMessage, Language } from '@/types';
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
  questions: Question[];
  userProgress?: Record<string, 'attempted' | 'solved'>;
  selectedQuestion?: Question | null;
  onQuestionSelect?: (question: Question) => void;
}

const sampleQuestions: Question[] = [
  {
    id: 'two-sum',
    title: 'Two Sum',
    difficulty: 'easy',
    category: 'Arrays',
    company_tags: ['Google', 'Amazon', 'Meta'],
    description: 'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.',
    starter: {
      python: 'def two_sum(nums, target):\n # Your code here\n pass',
      javascript: 'function twoSum(nums, target) {\n // Your code here\n}',
      java: 'class Solution {\n public int[] twoSum(int[] nums, int target) {\n // Your code here\n }\n}'
    },
    examples: [
      { input: 'nums = [2,7,11,15], target = 9', output: '[0,1]' },
      { input: 'nums = [3,2,4], target = 6', output: '[1,2]' }
    ],
    test_cases: [
      { input: [[2, 7, 11, 15], 9], expected: [0, 1] },
      { input: [[3, 2, 4], 6], expected: [1, 2] }
    ],
    hints: [
      'Try using a hash map to store the complement of each number',
      'Iterate through the array and check if the complement exists in the hash map'
    ],
    solution: 'Use a hash map to store the complement of each number as you iterate through the array.',
    time_complexity: 'O(n)',
    space_complexity: 'O(n)'
  }
];

export function Layout({
  questions,
  userProgress: externalUserProgress,
  selectedQuestion: externalSelectedQuestion,
  onQuestionSelect: externalOnQuestionSelect
}: LayoutProps) {
  const [internalSelectedQuestion, setInternalSelectedQuestion] = useState<Question>(questions[0] || sampleQuestions[0]);
    const [language, setLanguage] = useState<Language>('python');
    // Initialize code with starter for the default question and language
    const [currentCode, setCurrentCode] = useState<string>(() => {
      const defaultQuestion = questions[0] || sampleQuestions[0];
      return defaultQuestion?.starter?.['python'] || '';
    });
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [internalUserProgress, setInternalUserProgress] = useState<Record<string, 'attempted' | 'solved'>>({});
  const [isMounted, setIsMounted] = useState(false);

  // Use external props if provided, otherwise use internal state
  const selectedQuestion = externalSelectedQuestion ?? internalSelectedQuestion;
  const userProgress = externalUserProgress ?? internalUserProgress;
  const handleQuestionSelect = externalOnQuestionSelect ?? setInternalSelectedQuestion;

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    // Initialize code with starter for selected language
    if (selectedQuestion && selectedQuestion.starter) {
      setCurrentCode(selectedQuestion.starter[language] || '');
    }
  }, [selectedQuestion, language]);

  const handleQuestionSelection = useCallback((question: Question) => {
    handleQuestionSelect(question);
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
        selectedQuestion.title,
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
                setMessages(prev =>
                  prev.map(msg =>
                    msg.id === assistantMessageObj.id
                      ? { ...msg, content: assistantMessage }
                      : msg
                  )
                );
              }
            } catch (e) {
              // Handle non-JSON data
              if (data.trim() && !data.includes('"error"')) {
                assistantMessage += data;
                setMessages(prev =>
                  prev.map(msg =>
                    msg.id === assistantMessageObj.id
                      ? { ...msg, content: assistantMessage }
                      : msg
                  )
                );
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
    if (!selectedQuestion) return;

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
        const jsStarter = selectedQuestion.starter.javascript;
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
              // Deep clone input to prevent modification from affecting subsequent tests
              const input = JSON.parse(JSON.stringify(tc.input));
              const result = ${fnName}(...input);
              const passed = JSON.stringify(result) === JSON.stringify(tc.expected);
              return { index: index + 1, passed, input: tc.input, expected: tc.expected, actual: result };
            } catch (e) {
              return { index: index + 1, passed: false, error: e.message, input: tc.input };
            }
          });
        `);

        const results = testRunner(selectedQuestion.test_cases);

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
            outputText += `❌ Test Case ${r.index}: Failed\n Input: ${JSON.stringify(r.input)}\n Expected: ${JSON.stringify(r.expected)}\n Actual: ${JSON.stringify(r.actual)}\n`;
            allPassed = false;
          }
        });

        setOutput(outputText);
        if (allPassed) {
          setInternalUserProgress(prev => ({ ...prev, [selectedQuestion.id]: 'solved' }));
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
    if (!selectedQuestion) return null;

    const progress = userProgress[selectedQuestion.id];
    const status = progress === 'solved' ? '✅ Solved' :
      progress === 'attempted' ? '🔄 Attempted' : '⏳ Not started';

    return `${selectedQuestion.title} - ${status}`;
  }, [selectedQuestion, userProgress]);

  // Memoize difficulty badge styles
  const difficultyBadge = useMemo(() => {
    if (!selectedQuestion) return null;

    const styles = {
      easy: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
      hard: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
    };

    return styles[selectedQuestion.difficulty] || styles.easy;
  }, [selectedQuestion]);

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
            selectedQuestion={selectedQuestion?.title || ''}
            currentCode={currentCode}
            language={language}
          />
        </ContentLayoutContainer>
      </MainContentContainer>
    </MainLayoutContainer>
  );
}