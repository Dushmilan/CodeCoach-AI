import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QuestionDescriptionPanel } from './QuestionDescriptionPanel';
import { Question, QuestionSummary } from '@/types';

const summary: QuestionSummary = {
  id: '1',
  title: 'Two Sum',
  difficulty: 'easy',
  category: 'arrays',
  company_tags: [],
};

const fullQuestion: Question = {
  ...summary,
  description: 'Find two numbers that add up to target.',
  starter: { python: '', javascript: '', java: '' },
  examples: [
    { input: '[2,7,11,15], 9', output: '[0,1]' },
  ],
  test_cases: [{ input: '[2,7], 9', expected_output: '[0,1]' }],
  hints: ['Use a hash map', 'Check complement'],
  solution: '',
  time_complexity: 'O(n)',
  space_complexity: 'O(n)',
};

describe('QuestionDescriptionPanel', () => {
  it('returns null when no question is selected', () => {
    const { container } = render(
      <QuestionDescriptionPanel selectedQuestion={null} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders question title', () => {
    render(
      <QuestionDescriptionPanel selectedQuestion={summary} />
    );
    expect(screen.getByText('Two Sum')).toBeInTheDocument();
  });

  it('renders difficulty and category', () => {
    render(
      <QuestionDescriptionPanel selectedQuestion={summary} />
    );
    expect(screen.getByText('easy')).toBeInTheDocument();
    expect(screen.getByText('arrays')).toBeInTheDocument();
  });

  it('shows loading spinner when only summary data is available', () => {
    render(
      <QuestionDescriptionPanel selectedQuestion={summary} />
    );
    expect(screen.getByText('Loading description...')).toBeInTheDocument();
  });

  it('renders description when full question data is available', () => {
    render(
      <QuestionDescriptionPanel selectedQuestion={fullQuestion} />
    );
    expect(screen.getByText('Find two numbers that add up to target.')).toBeInTheDocument();
  });

  it('renders examples', () => {
    render(
      <QuestionDescriptionPanel selectedQuestion={fullQuestion} />
    );
    expect(screen.getByText(/Example 1/)).toBeInTheDocument();
    expect(screen.getByText(/\[0,1\]/)).toBeInTheDocument();
  });

  it('renders hints section', () => {
    render(
      <QuestionDescriptionPanel selectedQuestion={fullQuestion} />
    );
    expect(screen.getByText('Hints')).toBeInTheDocument();
  });

  it('toggles hints visibility on click', async () => {
    const user = userEvent.setup();
    render(
      <QuestionDescriptionPanel selectedQuestion={fullQuestion} />
    );

    expect(screen.queryByText('Use a hash map')).not.toBeInTheDocument();

    await user.click(screen.getByText('Hints'));
    expect(screen.getByText('Use a hash map')).toBeInTheDocument();
    expect(screen.getByText('Check complement')).toBeInTheDocument();

    await user.click(screen.getByText('Hints'));
    expect(screen.queryByText('Use a hash map')).not.toBeInTheDocument();
  });
});
