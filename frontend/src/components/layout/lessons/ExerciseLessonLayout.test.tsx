import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ExerciseLessonLayout } from './ExerciseLessonLayout';
import { LessonSummary, Question } from '@/types';

vi.mock('@/components/layout/elements', () => ({
  CodeEditorContainer: vi.fn(() => <div data-testid="mock-editor" />),
  AIChatPanelContainer: vi.fn(({ onClose }: { onClose: () => void }) => (
    <div data-testid="mock-ai-panel">
      <button onClick={onClose}>Close AI</button>
    </div>
  )),
}));

let mockMode: 'wide' | 'compact' | 'stacked' = 'wide';
vi.mock('./useWorkspaceMode', () => ({
  useWorkspaceMode: vi.fn(() => ({
    ref: vi.fn(),
    mode: mockMode,
    width: 0,
    isReady: true,
  })),
}));

const lesson: LessonSummary = {
  id: 'l1',
  course_id: 'c1',
  module_id: 'm1',
  title: 'Loops',
  type: 'exercise',
  content: 'Exercise lesson',
  order: 2,
  starter_code: 'print(1)',
  test_cases: [{ input: '1', expected_output: '1', description: 'basic' }],
  question_id: null,
  language: 'python',
};

const linkedQuestion: Question = {
  id: 'q1',
  title: 'Loops problem',
  difficulty: 'easy',
  category: 'loops',
  company_tags: [],
  description: 'Problem description',
  starter: {
    python: 'print(1)',
    javascript: '',
    java: '',
    cpp: '',
    c: '',
    go: '',
    rust: '',
    typescript: '',
    r: '',
    bash: '',
  },
  examples: [],
  test_cases: [],
  hints: [],
  solution: '',
  time_complexity: '',
  space_complexity: '',
};

const baseProps: React.ComponentProps<typeof ExerciseLessonLayout> = {
  lesson,
  storageKey: 'l1',
  linkedQuestion,
  testCases: lesson.test_cases || [],
  language: 'python',
  currentCode: 'print(1)',
  initialCode: 'print(1)',
  isRunning: false,
  output: '',
  error: '',
  isInteractive: false,
  messages: [],
  isTyping: false,
  selectedQuestion: lesson.title,
  onSendMessage: vi.fn(),
  onCodeChange: vi.fn(),
  onLanguageChange: vi.fn(),
  onRunCode: vi.fn(),
  onSubmitCode: vi.fn(),
};

describe('ExerciseLessonLayout', () => {
  beforeEach(() => {
    window.localStorage.clear();
    mockMode = 'wide';
  });

  it('renders description pane, editor and AI panel in wide mode', () => {
    render(<ExerciseLessonLayout {...baseProps} />);
    expect(screen.getByTestId('description-pane')).toBeInTheDocument();
    expect(screen.getByTestId('mock-editor')).toBeInTheDocument();
    expect(screen.getByTestId('mock-ai-panel')).toBeInTheDocument();
  });

  it('renders problem description and test cases', () => {
    render(<ExerciseLessonLayout {...baseProps} />);
    expect(screen.getByText(/Problem description/)).toBeInTheDocument();
    expect(screen.getByText('basic')).toBeInTheDocument();
  });

  it('closes AI panel and shows a reopen button in wide mode', () => {
    render(<ExerciseLessonLayout {...baseProps} />);
    fireEvent.click(screen.getByRole('button', { name: 'Close AI' }));
    expect(screen.queryByTestId('mock-ai-panel')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open AI Panel' })).toBeInTheDocument();
  });

  it('reopens AI panel from the toggle button in wide mode', () => {
    render(<ExerciseLessonLayout {...baseProps} />);
    fireEvent.click(screen.getByRole('button', { name: 'Close AI' }));
    fireEvent.click(screen.getByRole('button', { name: 'Open AI Panel' }));
    expect(screen.getByTestId('mock-ai-panel')).toBeInTheDocument();
  });

  it('applies persisted description width preference', () => {
    window.localStorage.setItem('codecoach:lesson:l1:desc-width', '50');
    render(<ExerciseLessonLayout {...baseProps} />);
    expect(screen.getByTestId('description-pane')).toHaveStyle({
      width: '50%',
    });
  });

  it('applies persisted ai width preference', () => {
    window.localStorage.setItem('codecoach:lesson:l1:ai-width', '480');
    render(<ExerciseLessonLayout {...baseProps} />);
    expect(screen.getByTestId('ai-pane')).toHaveStyle({ width: '480px' });
  });

  it('respects persisted closed AI panel state (global key)', () => {
    window.localStorage.setItem('codecoach:workspace:ai-open', '0');
    render(<ExerciseLessonLayout {...baseProps} />);
    expect(screen.queryByTestId('mock-ai-panel')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open AI Panel' })).toBeInTheDocument();
  });

  it('hides the side column and shows a drawer toggle in compact mode', () => {
    mockMode = 'compact';
    render(<ExerciseLessonLayout {...baseProps} />);
    expect(screen.queryByTestId('ai-pane')).not.toBeInTheDocument();
    expect(screen.getByTestId('mock-editor')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open AI Panel' })).toBeInTheDocument();
  });

  it('opens the AI drawer in compact mode', () => {
    mockMode = 'compact';
    render(<ExerciseLessonLayout {...baseProps} />);
    fireEvent.click(screen.getByRole('button', { name: 'Open AI Panel' }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByTestId('mock-ai-panel')).toBeInTheDocument();
  });

  it('closes the AI drawer via the panel close button', () => {
    mockMode = 'compact';
    render(<ExerciseLessonLayout {...baseProps} />);
    fireEvent.click(screen.getByRole('button', { name: 'Open AI Panel' }));
    fireEvent.click(screen.getByRole('button', { name: 'Close AI' }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('stacks description and editor vertically in stacked mode', () => {
    mockMode = 'stacked';
    render(<ExerciseLessonLayout {...baseProps} />);
    expect(screen.getByTestId('description-pane')).toBeInTheDocument();
    expect(screen.getByTestId('mock-editor')).toBeInTheDocument();
    expect(screen.queryByTestId('ai-pane')).not.toBeInTheDocument();
  });

  it('opens the AI drawer in stacked mode', () => {
    mockMode = 'stacked';
    render(<ExerciseLessonLayout {...baseProps} />);
    fireEvent.click(screen.getByRole('button', { name: 'Open AI Panel' }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });
});
