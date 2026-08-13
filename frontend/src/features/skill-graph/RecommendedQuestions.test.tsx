import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RecommendedQuestions } from './RecommendedQuestions';
import { RecommendedQuestion } from '@/types';

const state = vi.hoisted(() => ({
  recommendations: [] as RecommendedQuestion[],
  loading: false,
  error: null as string | null,
  authenticated: true,
  hydrated: true,
  refresh: vi.fn(),
}));

vi.mock('./use-recommended-questions.hook', () => ({
  useRecommendedQuestions: () => ({
    recommendations: state.recommendations,
    isLoading: state.loading,
    error: state.error,
    loadRecommendations: vi.fn(),
    refresh: state.refresh,
  }),
}));

vi.mock('@/providers', () => ({
  useAuth: () => ({
    isAuthenticated: state.authenticated,
    isHydrated: state.hydrated,
  }),
}));

const sampleRecommendation: RecommendedQuestion = {
  skill_slug: 'arrays',
  skill_name: 'Arrays',
  reason: 'weak_skill',
  reason_text: 'Arrays needs practice to become a strength.',
  question: {
    id: 'two-sum',
    title: 'Two Sum',
    difficulty: 'easy',
    category: 'arrays',
    company_tags: ['Google'],
    description: 'Find two numbers that add up to target',
    starter: {
      python: 'def two_sum(nums, target):',
      javascript: 'function twoSum(nums, target) {}',
      java: 'class Solution {}',
      cpp: '',
      c: '',
      go: '',
      rust: '',
      typescript: '',
    },
    examples: [{ input: '[2,7,11,15], 9', output: '[0,1]' }],
    test_cases: [{ input: '[2,7], 9', expected_output: '[0,1]' }],
    hints: ['Use a hash map'],
    solution: 'def two_sum(nums, target): return [0, 1]',
    time_complexity: 'O(n)',
    space_complexity: 'O(n)',
  },
};

function setState(
  partial: Partial<typeof state> & {
    recommendations?: RecommendedQuestion[];
  } = {},
) {
  Object.assign(state, partial);
}

beforeEach(() => {
  state.recommendations = [];
  state.loading = false;
  state.error = null;
  state.authenticated = true;
  state.hydrated = true;
  state.refresh.mockReset();
});

describe('RecommendedQuestions', () => {
  it('renders nothing before auth hydration', () => {
    setState({ hydrated: false });
    const { container } = render(<RecommendedQuestions />);
    expect(container).toBeEmptyDOMElement();
  });

  it('shows a sign-in CTA for anonymous users', () => {
    setState({ authenticated: false });
    render(<RecommendedQuestions />);
    expect(
      screen.getByText(/sign in to get personalized practice/i),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /sign in/i })).toHaveAttribute(
      'href',
      '/login',
    );
  });

  it('shows loading skeletons while fetching', () => {
    setState({ loading: true, recommendations: [] });
    render(<RecommendedQuestions />);
    expect(screen.getByTestId('recommendations-loading')).toBeInTheDocument();
  });

  it('renders recommendation cards with question details', () => {
    setState({ recommendations: [sampleRecommendation] });
    render(<RecommendedQuestions />);
    expect(screen.getByText('Two Sum')).toBeInTheDocument();
    expect(screen.getByText('easy')).toBeInTheDocument();
    expect(screen.getByText('arrays')).toBeInTheDocument();
    expect(screen.getByText('Arrays')).toBeInTheDocument();
    expect(
      screen.getByText('Arrays needs practice to become a strength.'),
    ).toBeInTheDocument();
  });

  it('links each recommendation to the problem page', () => {
    setState({ recommendations: [sampleRecommendation] });
    render(<RecommendedQuestions />);
    expect(screen.getByRole('link', { name: /two sum/i })).toHaveAttribute(
      'href',
      '/problems/two-sum',
    );
  });

  it('shows the empty state when there are no recommendations', () => {
    setState({ recommendations: [] });
    render(<RecommendedQuestions />);
    expect(screen.getByText(/no recommendations yet/i)).toBeInTheDocument();
  });

  it('shows an error state with a retry button that reloads', async () => {
    const user = userEvent.setup();
    setState({ error: 'Server error', recommendations: [] });
    render(<RecommendedQuestions />);
    expect(screen.getByText('Server error')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /retry/i }));
    expect(state.refresh).toHaveBeenCalledTimes(1);
  });
});
