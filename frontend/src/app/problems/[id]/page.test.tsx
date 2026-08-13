import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import ProblemWorkspacePage from './page';
import { Question } from '@/types';

const mockAnimateLauncher = vi.hoisted(() => vi.fn());
const mockGetQuestion = vi.hoisted(() => vi.fn());

vi.mock('@/components/animate/AnimateLauncher', () => ({
  AnimateLauncher: (props: unknown) => {
    mockAnimateLauncher(props);
    return <div data-testid="animate-launcher" />;
  },
}));

vi.mock('next/navigation', () => ({
  useParams: () => ({ id: 'lcp' }),
}));

vi.mock('@/components/header/Header', () => ({
  Header: () => <header>Header</header>,
}));

vi.mock('@/components/layout/elements/AIChatPanelContainer', () => ({
  AIChatPanelContainer: () => <div>Chat</div>,
}));

vi.mock('@/components/layout/elements/CodeEditorContainer', () => ({
  CodeEditorContainer: () => <div>Editor</div>,
}));

vi.mock('@/components/layout/lessons', () => ({
  useWorkspaceMode: () => ({ ref: undefined, mode: 'wide' }),
  AIPanelDrawer: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/rescue/RescueIntervention', () => ({
  RescueIntervention: () => <div>Rescue</div>,
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
    handleSubmitCode: vi.fn(),
    isAuthenticated: true,
  }),
}));

vi.mock('@/features/rescue/use-rescue-contract.hook', () => ({
  useRescueContract: () => ({
    registerActivity: vi.fn(),
    tier: 'none',
    checkpoints: [],
    isSuppressed: false,
    leaveMeAlone: vi.fn(),
    resume: vi.fn(),
  }),
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
});
