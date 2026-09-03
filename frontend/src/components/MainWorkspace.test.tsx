import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QuestionSummary, Question } from '@/types';

const mockLoadQuestions = vi.fn();
const mockSelectQuestion = vi.fn();
const mockSendMessage = vi.fn();
const mockClearError = vi.fn();
const mockClearMessages = vi.fn();
const mockClearCoachingError = vi.fn();
const mockSetUserProgress = vi.fn();
const mockValidateCode = vi.fn();
const mockSubmitCode = vi.fn();
const mockRunLocalJavaScript = vi.fn();
const mockClearExecutionError = vi.fn();
const mockClearOutput = vi.fn();

const mockUseQuestion = vi.hoisted(() =>
  vi.fn<
    (...args: unknown[]) => {
      questions: QuestionSummary[];
      selectedQuestion: QuestionSummary | null;
      fullQuestion: Question | null;
      isLoading: boolean;
      isLoadingQuestion: boolean;
      error: string | null;
      loadQuestions: () => void;
      selectQuestion: (q: QuestionSummary) => void;
      clearError: () => void;
    }
  >(() => ({
    questions: [] as QuestionSummary[],
    selectedQuestion: null,
    fullQuestion: null,
    isLoading: false,
    isLoadingQuestion: false,
    error: null,
    loadQuestions: mockLoadQuestions,
    selectQuestion: mockSelectQuestion,
    clearError: mockClearError,
  })),
);

const mockUseCodeRunner = vi.hoisted(() =>
  vi.fn<
    (...args: unknown[]) => {
      userProgress: Record<string, 'attempted' | 'solved'>;
      setUserProgress: (
        updater: (
          prev: Record<string, 'attempted' | 'solved'>,
        ) => Record<string, 'attempted' | 'solved'>,
      ) => void;
      handleRunCode: () => void;
      handleSubmitCode: () => void;
      isRunning: boolean;
      output: string;
      executionError: string | null;
      clearOutput: () => void;
      clearExecutionError: () => void;
    }
  >(() => ({
    userProgress: {},
    setUserProgress: vi.fn(),
    handleRunCode: mockValidateCode,
    handleSubmitCode: mockSubmitCode,
    isRunning: false,
    output: '',
    executionError: null,
    clearOutput: mockClearOutput,
    clearExecutionError: mockClearExecutionError,
  })),
);

const mockUseCoaching = vi.hoisted(() =>
  vi.fn<
    (...args: unknown[]) => {
      messages: {
        id: string;
        role: string;
        content: string;
        timestamp: Date;
      }[];
      isTyping: boolean;
      error: string | null;
      sendMessage: (...args: unknown[]) => Promise<void>;
      clearMessages: () => void;
      clearError: () => void;
    }
  >(() => ({
    messages: [],
    isTyping: false,
    error: null,
    sendMessage: mockSendMessage,
    clearMessages: mockClearMessages,
    clearError: mockClearCoachingError,
  })),
);

vi.mock('@/features/question/question.hook', () => ({
  useQuestion: mockUseQuestion,
}));

vi.mock('@/features/question/use-code-runner.hook', () => ({
  useCodeRunner: mockUseCodeRunner,
}));

vi.mock('@/features/coaching/coaching.hook', () => ({
  useCoaching: mockUseCoaching,
}));

vi.mock('@/hooks', () => ({
  useLocalStorage: vi.fn((key: string, initial: Record<string, string>) => [
    initial,
    mockSetUserProgress,
  ]),
  useTheme: vi.fn(() => ({ theme: 'dark', setTheme: vi.fn() })),
}));

vi.mock('@/components/header/Header', () => ({
  Header: vi.fn(() => <div>CodeCoach AI</div>),
}));

vi.mock('@/components/sidebar/Sidebar', () => ({
  Sidebar: vi.fn(
    ({
      questions,
      selectedQuestion,
      onSelectQuestion,
    }: {
      questions: QuestionSummary[];
      selectedQuestion: QuestionSummary | null;
      onSelectQuestion: (q: QuestionSummary) => void;
    }) => (
      <div
        data-testid="mock-sidebar"
        data-question-count={questions.length}
        data-has-selected={String(!!selectedQuestion)}
      >
        <button
          onClick={() =>
            onSelectQuestion({
              id: '1',
              title: 'Two Sum',
              difficulty: 'easy',
              category: 'arrays',
              company_tags: [],
            })
          }
        >
          Select Question
        </button>
      </div>
    ),
  ),
}));

vi.mock('@/components/layout/elements', () => ({
  LoadingSkeleton: vi.fn(() => <div data-testid="loading-skeleton">Loading...</div>),
  MainLayoutContainer: vi.fn(({ children }: { children: React.ReactNode }) => (
    <div data-testid="main-layout">{children}</div>
  )),
  MainContentContainer: vi.fn(({ children }: { children: React.ReactNode }) => (
    <div data-testid="main-content">{children}</div>
  )),
  ContentLayoutContainer: vi.fn(({ children }: { children: React.ReactNode }) => (
    <div data-testid="content-layout">{children}</div>
  )),
  QuestionContentSection: vi.fn(({ children }: { children: React.ReactNode }) => (
    <div data-testid="question-section">{children}</div>
  )),
  CodeEditorContainer: vi.fn(
    ({
      onRunCode,
      onSubmitCode,
      onCodeChange,
    }: {
      onRunCode: () => void;
      onSubmitCode: () => void;
      onCodeChange: (c: string) => void;
    }) => (
      <div data-testid="mock-editor-container">
        <button onClick={onRunCode}>Run Code</button>
        <button onClick={onSubmitCode}>Submit Code</button>
        <button onClick={() => onCodeChange('new code')}>Change Code</button>
      </div>
    ),
  ),
  AIChatPanelContainer: vi.fn(
    ({
      onSendMessage,
      isTyping,
    }: {
      onSendMessage: (msg: string, mode: string) => void;
      isTyping: boolean;
    }) => (
      <div data-testid="mock-chat-panel" data-typing={String(isTyping)}>
        <button onClick={() => onSendMessage('hello', 'freeform')}>Send Message</button>
      </div>
    ),
  ),
}));

import { MainWorkspace } from './MainWorkspace';

const questions: QuestionSummary[] = [
  {
    id: '1',
    title: 'Two Sum',
    difficulty: 'easy',
    category: 'arrays',
    company_tags: [],
  },
  {
    id: '2',
    title: 'Add Two Numbers',
    difficulty: 'medium',
    category: 'linked-list',
    company_tags: [],
  },
];

describe('MainWorkspace', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseQuestion.mockImplementation(() => ({
      questions: [],
      selectedQuestion: null,
      fullQuestion: null,
      isLoading: false,
      isLoadingQuestion: false,
      error: null,
      loadQuestions: mockLoadQuestions,
      selectQuestion: mockSelectQuestion,
      clearError: mockClearError,
    }));
    mockUseCodeRunner.mockImplementation(() => ({
      userProgress: {},
      setUserProgress: vi.fn(),
      handleRunCode: mockValidateCode,
      handleSubmitCode: mockSubmitCode,
      isRunning: false,
      output: '',
      executionError: null,
      clearOutput: mockClearOutput,
      clearExecutionError: mockClearExecutionError,
    }));
    mockUseCoaching.mockImplementation(() => ({
      messages: [],
      isTyping: false,
      error: null,
      sendMessage: mockSendMessage,
      clearMessages: mockClearMessages,
      clearError: mockClearCoachingError,
    }));
  });

  it('shows loading skeleton when isLoading is true', () => {
    mockUseQuestion.mockImplementation(() => ({
      questions: [],
      selectedQuestion: null,
      fullQuestion: null,
      isLoading: true,
      isLoadingQuestion: false,
      error: null,
      loadQuestions: mockLoadQuestions,
      selectQuestion: mockSelectQuestion,
      clearError: mockClearError,
    }));

    act(() => {
      render(<MainWorkspace />);
    });
    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
  });

  it('renders main layout when mounted', () => {
    act(() => {
      render(<MainWorkspace />);
    });
    expect(screen.getByTestId('main-layout')).toBeInTheDocument();
  });

  it('renders Sidebar with questions', () => {
    mockUseQuestion.mockImplementation(() => ({
      questions,
      selectedQuestion: null,
      fullQuestion: null,
      isLoading: false,
      isLoadingQuestion: false,
      error: null,
      loadQuestions: mockLoadQuestions,
      selectQuestion: mockSelectQuestion,
      clearError: mockClearError,
    }));

    act(() => {
      render(<MainWorkspace />);
    });
    const sidebar = screen.getByTestId('mock-sidebar');
    expect(sidebar).toHaveAttribute('data-question-count', '2');
  });

  it('renders CodeEditorContainer', () => {
    act(() => {
      render(<MainWorkspace />);
    });
    expect(screen.getByTestId('mock-editor-container')).toBeInTheDocument();
  });

  it('renders AIChatPanelContainer', () => {
    act(() => {
      render(<MainWorkspace />);
    });
    expect(screen.getByTestId('mock-chat-panel')).toBeInTheDocument();
  });

  it('renders Header', () => {
    act(() => {
      render(<MainWorkspace />);
    });
    expect(screen.getByText('CodeCoach AI')).toBeInTheDocument();
  });

  it('calls loadQuestions on mount', () => {
    act(() => {
      render(<MainWorkspace />);
    });
    expect(mockLoadQuestions).toHaveBeenCalledTimes(1);
  });

  it('does not send message when no question is selected', async () => {
    act(() => {
      render(<MainWorkspace />);
    });
    const user = userEvent.setup();
    await user.click(screen.getByText('Send Message'));
    expect(mockSendMessage).not.toHaveBeenCalled();
  });

  it('calls sendMessage when question is selected', async () => {
    mockUseQuestion.mockImplementation(() => ({
      questions,
      selectedQuestion: questions[0],
      fullQuestion: null,
      isLoading: false,
      isLoadingQuestion: false,
      error: null,
      loadQuestions: mockLoadQuestions,
      selectQuestion: mockSelectQuestion,
      clearError: mockClearError,
    }));

    act(() => {
      render(<MainWorkspace />);
    });
    const user = userEvent.setup();
    await user.click(screen.getByText('Send Message'));
    expect(mockSendMessage).toHaveBeenCalledWith(
      'hello',
      'freeform',
      expect.stringContaining(questions[0].title),
      '',
      'python',
      undefined,
      'easy',
      '',
      'questions',
    );
  });

  it('passes the starter code as initialCode when a full question is loaded', async () => {
    const fullQuestion: Question = {
      id: '1',
      title: 'Two Sum',
      difficulty: 'easy',
      category: 'arrays',
      company_tags: [],
      description: 'test',
      examples: [],
      hints: [],
      starter: {
        python: 'def two_sum(nums, target):\n    pass',
        javascript: '',
        java: '',
        cpp: '',
        c: '',
        go: '',
        rust: '',
        typescript: '',
      },
      solution: '',
      time_complexity: '',
      space_complexity: '',
      test_cases: [],
    };
    mockUseQuestion.mockImplementation(() => ({
      questions,
      selectedQuestion: questions[0],
      fullQuestion,
      isLoading: false,
      isLoadingQuestion: false,
      error: null,
      loadQuestions: mockLoadQuestions,
      selectQuestion: mockSelectQuestion,
      clearError: mockClearError,
    }));

    act(() => {
      render(<MainWorkspace />);
    });
    const user = userEvent.setup();
    await user.click(screen.getByText('Change Code'));
    await user.click(screen.getByText('Send Message'));
    expect(mockSendMessage).toHaveBeenCalledWith(
      'hello',
      'freeform',
      expect.stringContaining('Two Sum'),
      'new code',
      'python',
      undefined,
      'easy',
      'def two_sum(nums, target):\n    pass',
      'questions',
    );
  });

  it('disables chat inputs when isTyping', () => {
    mockUseCoaching.mockImplementation(() => ({
      messages: [],
      isTyping: true,
      error: null,
      sendMessage: mockSendMessage,
      clearMessages: mockClearMessages,
      clearError: mockClearCoachingError,
    }));

    act(() => {
      render(<MainWorkspace />);
    });
    const chatPanel = screen.getByTestId('mock-chat-panel');
    expect(chatPanel).toHaveAttribute('data-typing', 'true');
  });

  it('calls validateCode when Run Code is clicked with fullQuestion', async () => {
    const fullQuestion: Question = {
      id: '1',
      title: 'Two Sum',
      difficulty: 'easy',
      category: 'arrays',
      company_tags: [],
      description: 'test',
      examples: [],
      hints: [],
      starter: {
        python: '',
        javascript: '',
        java: '',
        cpp: '',
        c: '',
        go: '',
        rust: '',
        typescript: '',
      },
      solution: '',
      time_complexity: '',
      space_complexity: '',
      test_cases: [],
    };
    mockUseQuestion.mockImplementation(() => ({
      questions,
      selectedQuestion: questions[0],
      fullQuestion,
      isLoading: false,
      isLoadingQuestion: false,
      error: null,
      loadQuestions: mockLoadQuestions,
      selectQuestion: mockSelectQuestion,
      clearError: mockClearError,
    }));

    act(() => {
      render(<MainWorkspace />);
    });
    const user = userEvent.setup();
    await user.click(screen.getByText('Run Code'));
    expect(mockValidateCode).toHaveBeenCalled();
  });

  it('calls submitCode when Submit Code is clicked with fullQuestion', async () => {
    const fullQuestion: Question = {
      id: '1',
      title: 'Two Sum',
      difficulty: 'easy',
      category: 'arrays',
      company_tags: [],
      description: 'test',
      examples: [],
      hints: [],
      starter: {
        python: '',
        javascript: '',
        java: '',
        cpp: '',
        c: '',
        go: '',
        rust: '',
        typescript: '',
      },
      solution: '',
      time_complexity: '',
      space_complexity: '',
      test_cases: [],
    };
    mockUseQuestion.mockImplementation(() => ({
      questions,
      selectedQuestion: questions[0],
      fullQuestion,
      isLoading: false,
      isLoadingQuestion: false,
      error: null,
      loadQuestions: mockLoadQuestions,
      selectQuestion: mockSelectQuestion,
      clearError: mockClearError,
    }));

    act(() => {
      render(<MainWorkspace />);
    });
    const user = userEvent.setup();
    await user.click(screen.getByText('Submit Code'));
    expect(mockSubmitCode).toHaveBeenCalled();
  });

  it('calls selectQuestion when question is selected in sidebar', async () => {
    act(() => {
      render(<MainWorkspace />);
    });
    const user = userEvent.setup();
    await user.click(screen.getByText('Select Question'));
    expect(mockSelectQuestion).toHaveBeenCalled();
  });

  it('dispatches learner-context-invalidated on submit', async () => {
    const fullQuestion: Question = {
      id: '1',
      title: 'Two Sum',
      difficulty: 'easy',
      category: 'arrays',
      company_tags: [],
      description: 'test',
      examples: [],
      hints: [],
      starter: { python: '', javascript: '', java: '', cpp: '', c: '', go: '', rust: '', typescript: '' },
      solution: '',
      time_complexity: '',
      space_complexity: '',
      test_cases: [],
    };
    mockUseQuestion.mockImplementation(() => ({
      questions,
      selectedQuestion: questions[0],
      fullQuestion,
      isLoading: false,
      isLoadingQuestion: false,
      error: null,
      loadQuestions: mockLoadQuestions,
      selectQuestion: mockSelectQuestion,
      clearError: mockClearError,
    }));
    const spy = vi.spyOn(window, 'dispatchEvent');
    act(() => {
      render(<MainWorkspace />);
    });
    const user = userEvent.setup();
    await user.click(screen.getByText('Submit Code'));
    expect(spy).toHaveBeenCalledWith(expect.objectContaining({ type: 'learner-context-invalidated' }));
    spy.mockRestore();
  });
});
