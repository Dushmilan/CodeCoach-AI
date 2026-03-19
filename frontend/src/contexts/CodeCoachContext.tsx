'use client';

import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { CodeCoachState, Question, ChatMessage } from '@/types/question';
import { questionsApi } from '@/lib/api/questions';

interface CodeCoachContextType {
  state: CodeCoachState;
  dispatch: React.Dispatch<CodeCoachAction>;
  loadQuestions: () => Promise<Question[]>;
  loadQuestion: (id: string) => Promise<void>;
  executeCode: (code: string, language: string, stdin?: string) => Promise<void>;
  runTests: (code: string, language: string, testCases: any[]) => Promise<void>;
  getHint: (questionId: string, code: string, language: string) => Promise<string>;
  getReview: (questionId: string, code: string, language: string) => Promise<string>;
  chatWithCoach: (message: string, code?: string) => Promise<void>;
}

type CodeCoachAction =
  | { type: 'SET_QUESTION'; payload: Question }
  | { type: 'SET_CODE'; payload: string }
  | { type: 'SET_LANGUAGE'; payload: 'python' | 'javascript' | 'java' }
  | { type: 'SET_OUTPUT'; payload: string }
  | { type: 'SET_TEST_RESULTS'; payload: any[] }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'ADD_CHAT_MESSAGE'; payload: ChatMessage }
  | { type: 'SET_CHAT_MESSAGES'; payload: ChatMessage[] };

const initialState: CodeCoachState = {
  currentQuestion: null,
  code: '',
  language: 'python',
  output: '',
  testResults: [],
  isLoading: false,
  error: null,
};

function codeCoachReducer(state: CodeCoachState, action: CodeCoachAction): CodeCoachState {
  switch (action.type) {
    case 'SET_QUESTION':
      return {
        ...state,
        currentQuestion: action.payload,
        code: action.payload.starter.python,
        output: '',
        testResults: [],
        error: null,
      };
    case 'SET_CODE':
      return { ...state, code: action.payload };
    case 'SET_LANGUAGE':
      return {
        ...state,
        language: action.payload,
        code: state.currentQuestion?.starter[action.payload] || '',
      };
    case 'SET_OUTPUT':
      return { ...state, output: action.payload };
    case 'SET_TEST_RESULTS':
      return { ...state, testResults: action.payload };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'ADD_CHAT_MESSAGE':
      return { ...state };
    case 'SET_CHAT_MESSAGES':
      return { ...state };
    default:
      return state;
  }
}

const CodeCoachContext = createContext<CodeCoachContextType | undefined>(undefined);

export function CodeCoachProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(codeCoachReducer, initialState);

  const loadQuestions = async (): Promise<Question[]> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const questions = await questionsApi.getAllQuestions();
      if (questions.length > 0 && !state.currentQuestion) {
        dispatch({ type: 'SET_QUESTION', payload: questions[0] });
      }
      return questions;
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: (error as Error).message });
      return [];
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const loadQuestion = async (id: string) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const question = await questionsApi.getQuestionById(id);
      dispatch({ type: 'SET_QUESTION', payload: question });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: (error as Error).message });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const executeCode = async (code: string, language: string, stdin?: string) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      // TODO: Implement actual code execution API
      dispatch({ type: 'SET_OUTPUT', payload: 'Code execution not yet implemented' });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: (error as Error).message });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const runTests = async (code: string, language: string, testCases: any[]) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      // TODO: Implement actual test running API
      dispatch({ type: 'SET_TEST_RESULTS', payload: [] });
      dispatch({ type: 'SET_OUTPUT', payload: 'Test running not yet implemented' });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: (error as Error).message });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const getHint = async (questionId: string, code: string, language: string) => {
    try {
      // TODO: Implement actual hint API
      return 'Hint functionality not yet implemented';
    } catch (error) {
      throw new Error((error as Error).message);
    }
  };

  const getReview = async (questionId: string, code: string, language: string) => {
    try {
      // TODO: Implement actual review API
      return 'Review functionality not yet implemented';
    } catch (error) {
      throw new Error((error as Error).message);
    }
  };

  const chatWithCoach = async (message: string, code?: string) => {
    if (!state.currentQuestion) return;

    try {
      // TODO: Implement actual chat API
      console.log('Chat message:', message, 'with code:', code);
    } catch (error) {
      console.error('Chat error:', error);
    }
  };

  // Load questions on mount
  useEffect(() => {
    loadQuestions();
  }, []);

  const value: CodeCoachContextType = {
    state,
    dispatch,
    loadQuestions,
    loadQuestion,
    executeCode,
    runTests,
    getHint,
    getReview,
    chatWithCoach,
  };

  return (
    <CodeCoachContext.Provider value={value}>
      {children}
    </CodeCoachContext.Provider>
  );
}

export function useCodeCoach() {
  const context = useContext(CodeCoachContext);
  if (context === undefined) {
    throw new Error('useCodeCoach must be used within a CodeCoachProvider');
  }
  return context;
}

// Streaming utilities
export async function* streamResponse(response: Response): AsyncGenerator<string> {
  const reader = response.body?.getReader();
  if (!reader) return;

  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') return;
        yield data;
      }
    }
  }
}