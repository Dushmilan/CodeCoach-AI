import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
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

vi.mock('@/hooks', () => ({
  useLocalStorage: () => [mockProgress, vi.fn()],
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
});
