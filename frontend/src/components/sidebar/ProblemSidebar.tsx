'use client';

import { useState, useEffect } from 'react';
import { useCodeCoach } from '@/contexts/CodeCoachContext';
import { Question } from '@/types/question';

interface ProblemSidebarProps {
  className?: string;
}

export function ProblemSidebar({ className = '' }: ProblemSidebarProps) {
  const { state, loadQuestions, loadQuestion } = useCodeCoach();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchQuestions = async () => {
      try {
        setLoading(true);
        const questions = await api.getQuestions();
        setQuestions(questions as Question[]);
      } catch (error) {
        console.error('Failed to load questions:', error);
        setQuestions([]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchQuestions();
  }, []);

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy':
        return 'text-green-400 bg-green-900/20';
      case 'medium':
        return 'text-yellow-400 bg-yellow-900/20';
      case 'hard':
        return 'text-red-400 bg-red-900/20';
      default:
        return 'text-gray-400 bg-gray-900/20';
    }
  };

  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      'Strings': 'text-blue-400',
      'Arrays': 'text-purple-400',
      'Stacks': 'text-orange-400',
      'Dynamic Programming': 'text-pink-400',
      'Hash Tables': 'text-indigo-400',
    };
    return colors[category] || 'text-gray-400';
  };

  if (loading) {
    return (
      <div className={`flex flex-col h-full bg-gray-900 border-r border-gray-700 ${className}`}>
        <div className="p-4 border-b border-gray-700">
          <h2 className="text-lg font-semibold text-white">Problems</h2>
        </div>
        <div className="flex-1 p-4">
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="animate-pulse">
                <div className="h-4 bg-gray-700 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-700 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full bg-gray-900 border-r border-gray-700 ${className}`}>
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-white">Problems</h2>
        <p className="text-sm text-gray-400 mt-1">
          {questions.length} problems available
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="p-4 space-y-3">
          {questions.map((question) => (
            <div
              key={question.id}
              onClick={() => loadQuestion(question.id)}
              className={`p-4 rounded-lg cursor-pointer transition-all ${
                state.currentQuestion?.id === question.id
                  ? 'bg-blue-900/30 border border-blue-500'
                  : 'bg-gray-800 hover:bg-gray-700 border border-transparent'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <h3 className="text-sm font-medium text-white line-clamp-2">
                  {question.title}
                </h3>
                <span
                  className={`px-2 py-1 text-xs font-medium rounded ${getDifficultyColor(
                    question.difficulty
                  )}`}
                >
                  {question.difficulty}
                </span>
              </div>
              
              <p className="text-xs text-gray-400 mb-2 line-clamp-2">
                {question.description.substring(0, 100)}...
              </p>
              
              <div className="flex items-center space-x-2">
                <span className={`text-xs ${getCategoryColor(question.category)}`}>
                  {question.category}
                </span>
                <span className="text-xs text-gray-500">
                  • {question.testCases.length} test cases
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="p-4 border-t border-gray-700">
        <div className="text-xs text-gray-400">
          <p>Click on any problem to start coding!</p>
        </div>
      </div>
    </div>
  );
}

// Mock API for now until backend is ready
const api = {
  getQuestions: async () => [
    {
      id: 'reverse-string',
      title: 'Reverse String',
      difficulty: 'easy',
      category: 'Strings',
      description: 'Write a function that reverses a string. The input string is given as an array of characters.',
      starter: {
        python: 'def reverse_string(s):\n    pass',
        javascript: 'var reverseString = function(s) {\n    \n};',
        java: 'class Solution {\n    public void reverseString(char[] s) {\n        \n    }\n}'
      },
      testCases: [
        {
          input: [["h","e","l","l","o"]],
          expected: ["o","l","l","e","h"],
          functionName: 'reverseString',
          pythonFunctionName: 'reverse_string',
          javaFunctionName: 'reverseString',
          inPlace: true
        }
      ],
      examples: [
        { input: 's = ["h","e","l","l","o"]', output: '["o","l","l","e","h"]' }
      ],
      hints: ['Use two pointers approach'],
      solution: 'Use two pointers to swap elements',
      timeComplexity: 'O(n)',
      spaceComplexity: 'O(1)'
    }
  ]
};