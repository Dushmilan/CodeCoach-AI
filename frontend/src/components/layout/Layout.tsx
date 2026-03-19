'use client';

import { useState, useEffect } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { CodeEditor } from '@/components/editor/CodeEditor';
import { AIChatPanel } from '@/components/chat/AIChatPanel';
import { Question, ChatMessage, Language } from '@/types';
import { api } from '@/lib/api';

const sampleQuestions: Question[] = [
  {
    id: 'two-sum',
    title: 'Two Sum',
    difficulty: 'easy',
    category: 'Arrays',
    company_tags: ['Google', 'Amazon', 'Meta'],
    description: 'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.',
    starter: {
      python: 'def two_sum(nums, target):\n    # Your code here\n    pass',
      javascript: 'function twoSum(nums, target) {\n    // Your code here\n}',
      java: 'class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        // Your code here\n    }\n}'
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

export function Layout() {
  const [questions, setQuestions] = useState<Question[]>(sampleQuestions);
  const [selectedQuestion, setSelectedQuestion] = useState<Question>(sampleQuestions[0]);
  const [currentCode, setCurrentCode] = useState('');
  const [language, setLanguage] = useState<Language>('python');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [userProgress, setUserProgress] = useState<Record<string, 'attempted' | 'solved'>>({});

  useEffect(() => {
    // Load questions from API
    api.getQuestions()
      .then(setQuestions)
      .catch((error) => {
        console.error('Failed to load questions:', error);
        // Fallback to sample questions if API fails
        setQuestions(sampleQuestions);
      });
  }, []);

  useEffect(() => {
    // Initialize code with starter for selected language
    if (selectedQuestion) {
      setCurrentCode(selectedQuestion.starter[language]);
    }
  }, [selectedQuestion, language]);

  const handleQuestionSelect = (question: Question) => {
    setSelectedQuestion(question);
    setMessages([]); // Clear chat when switching questions
    setOutput('');
    setError('');
  };

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

            try {
              const parsed = JSON.parse(data);
              const content = parsed.choices?.[0]?.delta?.content || '';
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
    setIsRunning(true);
    setOutput('');
    setError('');

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

  return (
    <div className="flex h-screen bg-background">
      <Sidebar
        questions={questions}
        selectedQuestion={selectedQuestion}
        onSelectQuestion={handleQuestionSelect}
        userProgress={userProgress}
      />
      
      <div className="flex-1 flex flex-col">
        <Header />
        
        <div className="flex-1 flex overflow-hidden">
          <div className="flex-1 flex flex-col p-4">
            {selectedQuestion && (
              <div className="mb-4">
                <h2 className="text-2xl font-bold mb-2">{selectedQuestion.title}</h2>
                <div className="flex items-center space-x-2 mb-4">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    selectedQuestion.difficulty === 'easy' ? 'bg-green-500/10 text-green-500' :
                    selectedQuestion.difficulty === 'medium' ? 'bg-yellow-500/10 text-yellow-500' :
                    'bg-red-500/10 text-red-500'
                  }`}>
                    {selectedQuestion.difficulty}
                  </span>
                  <span className="text-sm text-muted-foreground">{selectedQuestion.category}</span>
                </div>
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <p>{selectedQuestion.description}</p>
                  {selectedQuestion.examples.map((example, index) => (
                    <div key={index} className="mt-2">
                      <strong>Example {index + 1}:</strong>
                      <div className="bg-secondary p-2 rounded mt-1">
                        <div><strong>Input:</strong> {example.input}</div>
                        <div><strong>Output:</strong> {example.output}</div>
                        {example.explanation && (
                          <div><strong>Explanation:</strong> {example.explanation}</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div className="flex-1">
              <CodeEditor
                language={language}
                code={currentCode}
                onCodeChange={setCurrentCode}
                onLanguageChange={setLanguage}
                onRunCode={handleRunCode}
                isRunning={isRunning}
                output={output}
                error={error}
              />
            </div>
          </div>
          
          <div className="w-96 p-4">
            <AIChatPanel
              messages={messages}
              onSendMessage={handleSendMessage}
              isTyping={isTyping}
              selectedQuestion={selectedQuestion?.title || ''}
              currentCode={currentCode}
              language={language}
            />
          </div>
        </div>
      </div>
    </div>
  );
}