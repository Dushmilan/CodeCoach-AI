import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TheoryLessonLayout } from './TheoryLessonLayout';
import { LessonSummary } from '@/types';

vi.mock('@/components/layout/elements', () => ({
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
  title: 'Variables',
  type: 'theory',
  content: '# Variables\n\nIntro content',
  order: 1,
  starter_code: null,
  test_cases: null,
  question_id: null,
  language: 'python',
};

function renderTheory(overrides: Partial<React.ComponentProps<typeof TheoryLessonLayout>> = {}) {
  return render(
    <TheoryLessonLayout
      lesson={lesson}
      storageKey="l1"
      nextId={null}
      isAuthenticated={false}
      isCompleted={false}
      isMarkingComplete={false}
      onMarkComplete={vi.fn()}
      messages={[]}
      isTyping={false}
      selectedQuestion={lesson.title}
      currentCode=""
      language="python"
      onSendMessage={vi.fn()}
      {...overrides}
    />,
  );
}

describe('TheoryLessonLayout', () => {
  beforeEach(() => {
    window.localStorage.clear();
    mockMode = 'wide';
  });

  it('renders lesson content', () => {
    renderTheory();
    expect(screen.getByText(/Intro content/)).toBeInTheDocument();
  });

  it('renders reading pane with AI closed by default in wide mode', () => {
    renderTheory();
    expect(screen.getByTestId('reading-pane')).toBeInTheDocument();
    expect(screen.queryByTestId('mock-ai-panel')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open AI Panel' })).toBeInTheDocument();
  });

  it('opens the AI side column via the toggle in wide mode', () => {
    renderTheory();
    fireEvent.click(screen.getByRole('button', { name: 'Open AI Panel' }));
    expect(screen.getByTestId('mock-ai-panel')).toBeInTheDocument();
  });

  it('shows Next Lesson link when nextId provided', () => {
    renderTheory({ nextId: 'l2' });
    const link = screen.getByRole('link', { name: /Next Lesson/ });
    expect(link).toHaveAttribute('href', '/learn/lesson/l2');
  });

  it('shows Back to Course when no nextId', () => {
    renderTheory();
    const link = screen.getByRole('link', { name: /Back to Course/ });
    expect(link).toHaveAttribute('href', '/learn/c1');
  });

  it('calls onMarkComplete when Mark Complete clicked', () => {
    const onMarkComplete = vi.fn();
    renderTheory({ isAuthenticated: true, onMarkComplete });
    fireEvent.click(screen.getByRole('button', { name: /Mark Complete/ }));
    expect(onMarkComplete).toHaveBeenCalled();
  });

  it('disables button when already completed', () => {
    renderTheory({ isAuthenticated: true, isCompleted: true });
    expect(screen.getByRole('button', { name: /Completed/ })).toBeDisabled();
  });

  it('does not render Mark Complete when unauthenticated', () => {
    renderTheory({ isAuthenticated: false });
    expect(screen.queryByRole('button', { name: /Mark Complete/ })).not.toBeInTheDocument();
  });

  it('closes AI panel and shows a reopen button in wide mode', () => {
    renderTheory();
    fireEvent.click(screen.getByRole('button', { name: 'Open AI Panel' }));
    fireEvent.click(screen.getByRole('button', { name: 'Close AI' }));
    expect(screen.queryByTestId('mock-ai-panel')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open AI Panel' })).toBeInTheDocument();
  });

  it('reopens AI panel from the toggle button in wide mode', () => {
    renderTheory();
    fireEvent.click(screen.getByRole('button', { name: 'Open AI Panel' }));
    fireEvent.click(screen.getByRole('button', { name: 'Close AI' }));
    fireEvent.click(screen.getByRole('button', { name: 'Open AI Panel' }));
    expect(screen.getByTestId('mock-ai-panel')).toBeInTheDocument();
  });

  it('applies persisted reading width preference when the AI panel is open', () => {
    window.localStorage.setItem('codecoach:lesson:l1:desc-width', '70');
    renderTheory();
    fireEvent.click(screen.getByRole('button', { name: 'Open AI Panel' }));
    expect(screen.getByTestId('reading-pane')).toHaveStyle({ width: '70%' });
  });

  it('respects persisted open AI panel state (theory key)', () => {
    window.localStorage.setItem('codecoach:workspace:ai-open:theory', '1');
    renderTheory();
    expect(screen.getByTestId('mock-ai-panel')).toBeInTheDocument();
  });

  it('respects persisted closed AI panel state (theory key)', () => {
    window.localStorage.setItem('codecoach:workspace:ai-open:theory', '0');
    renderTheory();
    expect(screen.queryByTestId('mock-ai-panel')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open AI Panel' })).toBeInTheDocument();
  });

  it('fills the reading pane and shows a drawer toggle in compact mode', () => {
    mockMode = 'compact';
    renderTheory();
    expect(screen.queryByTestId('ai-pane')).not.toBeInTheDocument();
    expect(screen.getByTestId('reading-pane')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open AI Panel' })).toBeInTheDocument();
  });

  it('opens the AI drawer in compact mode', () => {
    mockMode = 'compact';
    renderTheory();
    fireEvent.click(screen.getByRole('button', { name: 'Open AI Panel' }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByTestId('mock-ai-panel')).toBeInTheDocument();
  });

  it('closes the AI drawer via the panel close button', () => {
    mockMode = 'compact';
    renderTheory();
    fireEvent.click(screen.getByRole('button', { name: 'Open AI Panel' }));
    fireEvent.click(screen.getByRole('button', { name: 'Close AI' }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('uses the drawer in stacked mode', () => {
    mockMode = 'stacked';
    renderTheory();
    fireEvent.click(screen.getByRole('button', { name: 'Open AI Panel' }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });
});
