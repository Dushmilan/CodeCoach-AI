import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import ProblemsPage from './page';
import type { QuestionSummary } from '@/types';

let mockQuestions: QuestionSummary[] = [];
let mockProgress: Record<string, 'attempted' | 'solved'> = {};
let mockIsLoading = false;
let mockError: string | null = null;

const mockLoadQuestions = vi.fn();

vi.mock('@/features/question/question.hook', () => ({
  useQuestion: () => ({
    allQuestions: mockQuestions,
    loadQuestions: mockLoadQuestions,
    isLoading: mockIsLoading,
    error: mockError,
  }),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock('@/components/header/Header', () => ({
  Header: () => <div data-testid="header" />,
}));

vi.mock('@/features/skill-graph/RecommendedQuestions', () => ({
  RecommendedQuestions: () => <div data-testid="recommended-questions" />,
}));

vi.mock('@/hooks', () => ({
  useLocalStorage: () => [mockProgress, vi.fn()],
}));

vi.mock('@/features/workspace/workspace.service', () => ({
  workspaceService: {
    getLastVisited: vi.fn(() => Promise.resolve(null)),
  },
}));

vi.mock('@/lib/shuffle', () => ({
  seededShuffle: <T,>(arr: T[]) => [...arr],
  getDailySeed: () => '2026-01-01',
}));

const sample: QuestionSummary[] = [
  {
    id: '1',
    title: 'Two Sum',
    difficulty: 'easy',
    category: 'Arrays & Hashing',
    company_tags: ['Google', 'Amazon'],
  },
  {
    id: '2',
    title: 'Valid Parentheses',
    difficulty: 'easy',
    category: 'Stack & Queue',
    company_tags: ['Amazon'],
  },
  {
    id: '3',
    title: 'Merge k Sorted Lists',
    difficulty: 'hard',
    category: 'Linked Lists',
    company_tags: ['Google'],
  },
];

function queryInDesktopTable(text: string) {
  const table = document.querySelector('table') as HTMLElement | null;
  return table ? within(table).queryByText(text) : null;
}

function queryInMobileList(text: string) {
  const mobile = document.querySelector('.md\\:hidden') as HTMLElement | null;
  return mobile ? within(mobile).queryByText(text) : null;
}

beforeEach(() => {
  mockQuestions = sample;
  mockProgress = {};
  mockIsLoading = false;
  mockError = null;
  mockLoadQuestions.mockReset();
});

describe('ProblemsPage', () => {
  it('loads questions on mount', () => {
    render(<ProblemsPage />);
    expect(mockLoadQuestions).toHaveBeenCalledTimes(1);
  });

  it('renders the practice-next recommendations panel', () => {
    render(<ProblemsPage />);
    expect(screen.getByTestId('recommended-questions')).toBeInTheDocument();
  });

  it('renders all questions in the table with difficulty badges and categories', () => {
    render(<ProblemsPage />);
    expect(queryInDesktopTable('Two Sum')).toBeTruthy();
    expect(queryInDesktopTable('Valid Parentheses')).toBeTruthy();
    expect(queryInDesktopTable('Merge k Sorted Lists')).toBeTruthy();
    expect(queryInDesktopTable('Arrays & Hashing')).toBeTruthy();
    const table = document.querySelector('table') as HTMLElement;
    expect(within(table).getAllByText('easy')).toHaveLength(2);
    expect(within(table).getAllByText('hard')).toHaveLength(1);
  });

  it('shows the total question count', () => {
    render(<ProblemsPage />);
    expect(screen.getAllByText(/3 questions available/).length).toBeGreaterThan(0);
  });

  it('filters by search text', () => {
    render(<ProblemsPage />);
    const search = screen.getByLabelText('Search questions');
    fireEvent.change(search, { target: { value: 'two sum' } });
    expect(queryInDesktopTable('Two Sum')).toBeTruthy();
    expect(queryInDesktopTable('Valid Parentheses')).toBeNull();
    expect(queryInMobileList('Valid Parentheses')).toBeNull();
  });

  it('filters by difficulty', () => {
    render(<ProblemsPage />);
    const select = screen.getByLabelText('Filter by difficulty');
    fireEvent.change(select, { target: { value: 'hard' } });
    expect(queryInDesktopTable('Merge k Sorted Lists')).toBeTruthy();
    expect(queryInDesktopTable('Two Sum')).toBeNull();
    expect(queryInMobileList('Two Sum')).toBeNull();
  });

  it('filters by category', () => {
    render(<ProblemsPage />);
    const select = screen.getByLabelText('Filter by category');
    fireEvent.change(select, { target: { value: 'Stack & Queue' } });
    expect(queryInDesktopTable('Valid Parentheses')).toBeTruthy();
    expect(queryInDesktopTable('Two Sum')).toBeNull();
  });

  it('filters by company', () => {
    render(<ProblemsPage />);
    const select = screen.getByLabelText('Filter by company');
    fireEvent.change(select, { target: { value: 'Google' } });
    expect(queryInDesktopTable('Two Sum')).toBeTruthy();
    expect(queryInDesktopTable('Merge k Sorted Lists')).toBeTruthy();
    expect(queryInDesktopTable('Valid Parentheses')).toBeNull();
  });

  it('filters by progress status', () => {
    mockProgress = { '1': 'solved' };
    render(<ProblemsPage />);
    const select = screen.getByLabelText('Filter by progress');
    fireEvent.change(select, { target: { value: 'solved' } });
    expect(queryInDesktopTable('Two Sum')).toBeTruthy();
    expect(queryInDesktopTable('Valid Parentheses')).toBeNull();
  });

  it('sorts by title', () => {
    render(<ProblemsPage />);
    const select = screen.getByLabelText('Sort questions');
    fireEvent.change(select, { target: { value: 'title' } });
    const rows = document.querySelectorAll('tbody tr');
    expect(rows.length).toBe(3);
  });

  it('shows active filter chips and clears them', () => {
    render(<ProblemsPage />);
    const select = screen.getByLabelText('Filter by difficulty');
    fireEvent.change(select, { target: { value: 'hard' } });
    const clearAll = screen.getByText('Clear all');
    fireEvent.click(clearAll);
    expect(queryInDesktopTable('Two Sum')).toBeTruthy();
    expect(queryInDesktopTable('Valid Parentheses')).toBeTruthy();
  });

  it('shows an empty state when no questions match', () => {
    render(<ProblemsPage />);
    const search = screen.getByLabelText('Search questions');
    fireEvent.change(search, { target: { value: 'zzz-no-match' } });
    expect(screen.getByText('No questions match your filters')).toBeInTheDocument();
  });

  it('shows a loading state', () => {
    mockIsLoading = true;
    render(<ProblemsPage />);
    expect(screen.getByText('Loading questions...')).toBeInTheDocument();
  });

  it('shows an error state', () => {
    mockError = 'Failed to load questions';
    render(<ProblemsPage />);
    expect(screen.getByText('Failed to load questions')).toBeInTheDocument();
  });

  describe('continue banner on question-solved (#277)', () => {
    async function renderWithLastVisited(visitedId: string) {
      const { workspaceService } = await import('@/features/workspace/workspace.service');
      vi.mocked(workspaceService.getLastVisited).mockResolvedValue({
        question_id: visitedId,
        language: 'python',
        visited_at: '2026-09-22T00:00:00Z',
      });
      const { AuthContext } = await import('@/providers/AuthProvider');
      render(
        <AuthContext.Provider value={{ isAuthenticated: true } as never}>
          <ProblemsPage />
        </AuthContext.Provider>,
      );
      await screen.findByText(/Continue where you left off/);
    }

    it('advances past the solved question to the next unsolved one', async () => {
      await renderWithLastVisited('1');
      expect(screen.getByText(/Continue where you left off/).textContent).toContain('Two Sum');
      fireEvent(window, new CustomEvent('question-solved', { detail: { questionId: '1' } }));
      await waitFor(() => {
        expect(screen.getByText(/Continue where you left off/).textContent).toContain('Valid Parentheses');
      });
    });

    it('hides the banner when nothing is left unsolved', async () => {
      mockProgress = { '1': 'solved', '2': 'solved', '3': 'solved' };
      const { workspaceService } = await import('@/features/workspace/workspace.service');
      vi.mocked(workspaceService.getLastVisited).mockResolvedValue({
        question_id: '3',
        language: 'python',
        visited_at: '2026-09-22T00:00:00Z',
      });
      const { AuthContext } = await import('@/providers/AuthProvider');
      render(
        <AuthContext.Provider value={{ isAuthenticated: true } as never}>
          <ProblemsPage />
        </AuthContext.Provider>,
      );
      fireEvent(window, new CustomEvent('question-solved', { detail: { questionId: '3' } }));
      await waitFor(() => {
        expect(screen.queryByText(/Continue where you left off/)).toBeNull();
      });
    });

    it('leaves the banner alone when another question was solved', async () => {
      await renderWithLastVisited('1');
      fireEvent(window, new CustomEvent('question-solved', { detail: { questionId: '2' } }));
      await new Promise((r) => setTimeout(r, 50));
      expect(screen.getByText(/Continue where you left off/).textContent).toContain('Two Sum');
    });

    it('advances past an already-solved banner target on mount (#277)', async () => {
      mockProgress = { '1': 'solved' };
      await renderWithLastVisited('1');
      await waitFor(() => {
        expect(screen.getByText(/Continue where you left off/).textContent).toContain('Valid Parentheses');
      });
    });

    it('keeps the banner while the question list is still loading (#277)', async () => {
      // last-visited resolves before the catalog: the banner must not
      // collapse to hidden just because the next stop is unknowable yet.
      mockQuestions = [];
      mockProgress = { '1': 'solved' };
      const { workspaceService } = await import('@/features/workspace/workspace.service');
      vi.mocked(workspaceService.getLastVisited).mockResolvedValue({
        question_id: '1',
        language: 'python',
        visited_at: '2026-09-22T00:00:00Z',
      });
      const { AuthContext } = await import('@/providers/AuthProvider');
      const view = render(
        <AuthContext.Provider value={{ isAuthenticated: true } as never}>
          <ProblemsPage />
        </AuthContext.Provider>,
      );
      await waitFor(() => {
        expect(screen.getByText(/Continue where you left off/).textContent).toContain('1');
      });
      // Catalog arrives late: the banner then advances past the solved target.
      mockQuestions = sample;
      view.rerender(
        <AuthContext.Provider value={{ isAuthenticated: true } as never}>
          <ProblemsPage />
        </AuthContext.Provider>,
      );
      await waitFor(() => {
        expect(screen.getByText(/Continue where you left off/).textContent).toContain('Valid Parentheses');
      });
    });
  });
});
