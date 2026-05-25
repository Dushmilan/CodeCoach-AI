import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QuestionSummary } from '@/types';

vi.mock('./QuestionList', () => ({
  QuestionList: vi.fn(({ questions, onSelectQuestion }: {
    questions: QuestionSummary[]; onSelectQuestion: (q: QuestionSummary, i: number) => void;
  }) => (
    <div data-testid="mock-question-list">
      {questions.map((q) => (
        <button key={q.id} onClick={() => onSelectQuestion(q, 0)}>
          {q.title}
        </button>
      ))}
    </div>
  )),
}));

vi.mock('./FilterBar', () => ({
  FilterBar: vi.fn(({ onAll, onRandom, onFilterChange, isCollapsed }: {
    onAll: () => void; onRandom: () => void;
    onFilterChange: (f: string) => void; isCollapsed: boolean;
  }) => (
    <div data-testid="mock-filter-bar" data-collapsed={String(isCollapsed)}>
      <button onClick={onAll}>All</button>
      <button onClick={onRandom}>Random</button>
      <button onClick={() => onFilterChange('easy')}>Easy</button>
    </div>
  )),
}));

vi.mock('./NavigationControls', () => ({
  NavigationControls: vi.fn(({ onPrevious, onNext, disabled, isCollapsed }: {
    onPrevious: () => void; onNext: () => void; disabled: boolean; isCollapsed: boolean;
  }) => (
    <div data-testid="mock-nav-controls" data-disabled={String(disabled)} data-collapsed={String(isCollapsed)}>
      <button onClick={onPrevious}>Previous</button>
      <button onClick={onNext}>Next</button>
    </div>
  )),
}));

vi.mock('./QuestionDescriptionPanel', () => ({
  QuestionDescriptionPanel: vi.fn(({ selectedQuestion, onToggleView }: {
    selectedQuestion: QuestionSummary; onToggleView: () => void;
  }) => (
    <div data-testid="mock-question-description">
      {selectedQuestion.title}
      <button onClick={onToggleView}>Back to list</button>
    </div>
  )),
}));

import { Sidebar } from './Sidebar';

const questions: QuestionSummary[] = [
  { id: '1', title: 'Two Sum', difficulty: 'easy', category: 'arrays', company_tags: [] },
  { id: '2', title: 'Add Two Numbers', difficulty: 'medium', category: 'linked-list', company_tags: [] },
];

describe('Sidebar', () => {
  const defaultProps = {
    questions,
    selectedQuestion: null,
    fullQuestion: null,
    onSelectQuestion: vi.fn(),
    userProgress: {},
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders Problems header', async () => {
    render(<Sidebar {...defaultProps} />);
    expect(await screen.findByText('PROBLEMS')).toBeInTheDocument();
  });

  it('renders collapse toggle button', async () => {
    render(<Sidebar {...defaultProps} />);
    expect(await screen.findByLabelText('Collapse sidebar')).toBeInTheDocument();
  });

  it('renders view mode toggle button', async () => {
    render(<Sidebar {...defaultProps} />);
    expect(await screen.findByText('Show Active Question')).toBeInTheDocument();
  });

  it('shows question list in default list mode', async () => {
    render(<Sidebar {...defaultProps} />);
    expect(await screen.findByTestId('mock-question-list')).toBeInTheDocument();
    expect(await screen.findByText('Two Sum')).toBeInTheDocument();
  });

  it('renders FilterBar and NavigationControls in list mode', async () => {
    render(<Sidebar {...defaultProps} />);
    expect(await screen.findByTestId('mock-filter-bar')).toBeInTheDocument();
    expect(await screen.findByTestId('mock-nav-controls')).toBeInTheDocument();
  });

  it('switches to description mode when view mode toggle is clicked', async () => {
    const fullQuestion = { ...questions[0], description: 'test', examples: [], hints: [] };
    const user = userEvent.setup();
    render(<Sidebar {...defaultProps} fullQuestion={fullQuestion} />);

    await user.click(await screen.findByText('Show Active Question'));
    expect(await screen.findByTestId('mock-question-description')).toBeInTheDocument();
    expect(screen.queryByTestId('mock-question-list')).not.toBeInTheDocument();
    expect(await screen.findByText('Show All Questions')).toBeInTheDocument();
  });

  it('shows question description panel in description mode', async () => {
    const fullQuestion = { ...questions[0], description: 'test', examples: [], hints: [] };
    const user = userEvent.setup();
    render(<Sidebar {...defaultProps} fullQuestion={fullQuestion} />);

    await user.click(await screen.findByText('Show Active Question'));
    expect(await screen.findByText('Two Sum')).toBeInTheDocument();
    expect(await screen.findByText('Back to list')).toBeInTheDocument();
  });

  it('switches back to list mode when Back to list is clicked in description mode', async () => {
    const fullQuestion = { ...questions[0], description: 'test', examples: [], hints: [] };
    const user = userEvent.setup();
    render(<Sidebar {...defaultProps} fullQuestion={fullQuestion} />);

    await user.click(await screen.findByText('Show Active Question'));
    await user.click(await screen.findByText('Back to list'));

    expect(await screen.findByTestId('mock-question-list')).toBeInTheDocument();
    expect(screen.queryByTestId('mock-question-description')).not.toBeInTheDocument();
  });

  it('shows no content when switching to description mode without fullQuestion', async () => {
    const user = userEvent.setup();
    render(<Sidebar {...defaultProps} fullQuestion={null} />);

    await user.click(await screen.findByText('Show Active Question'));
    expect(screen.queryByTestId('mock-question-description')).not.toBeInTheDocument();
    expect(screen.queryByTestId('mock-question-list')).not.toBeInTheDocument();
  });

  it('calls onSelectQuestion when a question is clicked', async () => {
    const onSelectQuestion = vi.fn();
    const user = userEvent.setup();
    render(<Sidebar {...defaultProps} onSelectQuestion={onSelectQuestion} />);

    await user.click(await screen.findByText('Two Sum'));
    expect(onSelectQuestion).toHaveBeenCalledWith(questions[0]);
  });

  it('shows solved count in progress summary', async () => {
    render(<Sidebar {...defaultProps} userProgress={{ '1': 'solved' }} />);
    expect(await screen.findByText(/solved:/i)).toBeInTheDocument();
  });

  it('shows total count in progress summary', async () => {
    render(<Sidebar {...defaultProps} />);
    expect(await screen.findByText(/total:/i)).toBeInTheDocument();
  });

  it('collapses sidebar when collapse button is clicked', async () => {
    const user = userEvent.setup();
    render(<Sidebar {...defaultProps} />);

    await user.click(await screen.findByLabelText('Collapse sidebar'));
    expect(await screen.findByLabelText('Expand sidebar')).toBeInTheDocument();
  });

  it('passes isCollapsed to child components', async () => {
    const user = userEvent.setup();
    render(<Sidebar {...defaultProps} />);

    await user.click(await screen.findByLabelText('Collapse sidebar'));

    const filterBar = await screen.findByTestId('mock-filter-bar');
    expect(filterBar).toHaveAttribute('data-collapsed', 'true');

    const navControls = await screen.findByTestId('mock-nav-controls');
    expect(navControls).toHaveAttribute('data-collapsed', 'true');
  });
});
