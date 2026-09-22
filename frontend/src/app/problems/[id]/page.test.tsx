import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ReactNode } from 'react';
import { HttpError } from '@/lib/fetch-client';
import ProblemWorkspacePage from './page';
import { Question } from '@/types';

const mockAnimateLauncher = vi.hoisted(() => vi.fn());
const mockGetQuestion = vi.hoisted(() => vi.fn());
const mockHandleSubmitCode = vi.hoisted(() => vi.fn(() => Promise.resolve()));

vi.mock('@/components/animate/AnimateLauncher', () => ({
  AnimateLauncher: (props: unknown) => {
    mockAnimateLauncher(props);
    return <div data-testid="animate-launcher" />;
  },
}));

vi.mock('next/navigation', () => ({
  useParams: () => ({ id: 'lcp' }),
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock('@/components/header/Header', () => ({
  Header: () => <header>Header</header>,
}));

vi.mock('@/components/layout/elements/AIChatPanelContainer', () => ({
  AIChatPanelContainer: () => <div>Chat</div>,
}));

vi.mock('@/components/layout/elements/CodeEditorContainer', () => ({
  CodeEditorContainer: ({ onSubmitCode }: { onSubmitCode: () => void }) => (
    <div>
      Editor
      <button data-testid="mock-submit" onClick={() => void onSubmitCode()}>
        Submit
      </button>
    </div>
  ),
}));

vi.mock('@/components/layout/lessons', () => ({
  useWorkspaceMode: () => ({ ref: undefined, mode: 'wide' }),
  AIPanelDrawer: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/sidebar/QuestionDescriptionPanel', () => ({
  QuestionDescriptionPanel: () => <div>Description</div>,
}));

vi.mock('@/components/ui/ResizablePanelGroup', () => ({
  ResizablePanelGroup: ({ panels }: { panels: Array<{ children: ReactNode }> }) => (
    <div>{panels.map((p, i) => <div key={i}>{p.children}</div>)}</div>
  ),
}));

vi.mock('@/features/coaching/coaching.hook', () => ({
  useCoaching: () => ({
    messages: [],
    isTyping: false,
    sendMessage: vi.fn(),
  }),
}));

vi.mock('@/features/question/question.service', () => ({
  questionService: { getQuestion: mockGetQuestion },
}));

vi.mock('@/features/question/use-code-runner.hook', () => ({
  useCodeRunner: () => ({
    isRunning: false,
    output: '',
    testResults: [],
    executionError: null,
    lastSubmitResult: null,
    handleRunCode: vi.fn(),
    handleSubmitCode: mockHandleSubmitCode,
    isAuthenticated: true,
  }),
}));

vi.mock('@/features/coaching/use-coach-warm.hook', () => ({
  useCoachWarm: () => {},
}));

const lcpQuestion: Question = {
  id: 'lcp',
  title: 'Longest Common Prefix',
  difficulty: 'easy',
  category: 'Strings',
  company_tags: [],
  description: 'Write a function to find the longest common prefix string amongst an array of strings.',
  starter: {
    python: 'class Solution:\n    def longestCommonPrefix(self, strs):\n        pass\n',
    javascript: '',
    java: '',
    cpp: '',
    c: '',
    go: '',
    rust: '',
    typescript: '',
  },
  examples: [
    { input: 'strs = ["flower","flow","flight"]', output: '"fl"', explanation: 'flower, flow and flight share the prefix "fl".' },
  ],
  test_cases: [
    { input: 'strs = ["dog","racecar","car"]', expected_output: '""' },
  ],
  hints: [],
  solution: '',
  time_complexity: 'O(S)',
  space_complexity: 'O(1)',
};

describe('ProblemWorkspacePage Animate wiring', () => {
  beforeEach(() => {
    mockAnimateLauncher.mockClear();
    mockGetQuestion.mockReset();
    mockGetQuestion.mockResolvedValue(lcpQuestion);
  });

  it('passes the loaded question context to the Animate launcher', async () => {
    render(<ProblemWorkspacePage />);

    await screen.findByTestId('animate-launcher');

    expect(mockAnimateLauncher).toHaveBeenCalled();
    const lastCall = mockAnimateLauncher.mock.calls.at(-1)![0] as {
      problem: string;
      question: unknown;
      difficulty: string;
      initialCode: string;
    };
    const props = lastCall;
    expect(props.problem).toBe('Longest Common Prefix');
    expect(props.difficulty).toBe('easy');
    expect(props.initialCode).toBe(lcpQuestion.starter.python);
    expect(props.question).toEqual(lcpQuestion);
  });

  describe('error display', () => {
    it('renders server detail when question load fails with 404 + detail body', async () => {
      mockGetQuestion.mockRejectedValue(
        new HttpError(
          'Request failed: 404 Not Found',
          404,
          JSON.stringify({ detail: 'Question not found' }),
        ),
      );
      render(<ProblemWorkspacePage />);

      expect(await screen.findByText('Question not found')).toBeTruthy();
    });
  });

  describe('submit wiring', () => {
    it('dispatches learner-context-invalidated after submit so moat UI refreshes', async () => {
      mockHandleSubmitCode.mockClear();
      const user = userEvent.setup();
      const spy = vi.fn();
      window.addEventListener('learner-context-invalidated', spy);
      try {
        render(<ProblemWorkspacePage />);

        await user.click(await screen.findByTestId('mock-submit'));
        await waitFor(() => expect(mockHandleSubmitCode).toHaveBeenCalled());
        await waitFor(() => expect(spy).toHaveBeenCalledTimes(1));
      } finally {
        window.removeEventListener('learner-context-invalidated', spy);
      }
    });
  });
});
