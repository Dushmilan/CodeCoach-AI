import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QuestionItem } from './QuestionItem';
import { QuestionSummary } from '@/types';

const baseQuestion: QuestionSummary = {
  id: '1',
  title: 'Two Sum',
  difficulty: 'easy',
  category: 'arrays',
  company_tags: [],
};

describe('QuestionItem', () => {
  it('renders the question title', () => {
    render(
      <QuestionItem
        question={baseQuestion}
        isSelected={false}
        isCurrentIndex={false}
        onClick={vi.fn()}
      />
    );
    expect(screen.getByText('Two Sum')).toBeInTheDocument();
  });

  it('renders difficulty and category', () => {
    render(
      <QuestionItem
        question={baseQuestion}
        isSelected={false}
        isCurrentIndex={false}
        onClick={vi.fn()}
      />
    );
    expect(screen.getByText(/easy/i)).toBeInTheDocument();
    expect(screen.getByText('arrays')).toBeInTheDocument();
  });

  it('shows solved checkmark when progress is solved', () => {
    const { container } = render(
      <QuestionItem
        question={baseQuestion}
        isSelected={false}
        isCurrentIndex={false}
        progress="solved"
        onClick={vi.fn()}
      />
    );
    expect(screen.getByText('Two Sum')).toBeInTheDocument();
    expect(container.querySelector('.lucide-circle-check-big')).toBeInTheDocument();
  });

  it('shows attempted icon when progress is attempted', () => {
    const { container } = render(
      <QuestionItem
        question={baseQuestion}
        isSelected={false}
        isCurrentIndex={false}
        progress="attempted"
        onClick={vi.fn()}
      />
    );
    expect(container.querySelector('.lucide-circle-alert')).toBeInTheDocument();
  });

  it('shows no progress icon when progress is undefined', () => {
    const { container } = render(
      <QuestionItem
        question={baseQuestion}
        isSelected={false}
        isCurrentIndex={false}
        onClick={vi.fn()}
      />
    );
    expect(container.querySelector('.lucide-circle-check-big')).not.toBeInTheDocument();
    expect(container.querySelector('.lucide-circle-alert')).not.toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(
      <QuestionItem
        question={baseQuestion}
        isSelected={false}
        isCurrentIndex={false}
        onClick={onClick}
      />
    );
    await user.click(screen.getByText('Two Sum'));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it('applies selected styles', () => {
    const { container } = render(
      <QuestionItem
        question={baseQuestion}
        isSelected
        isCurrentIndex={false}
        onClick={vi.fn()}
      />
    );
    const outerDiv = container.firstChild as HTMLElement;
    expect(outerDiv.className).toContain('bg-secondary');
  });

  it('applies current index styles', () => {
    const { container } = render(
      <QuestionItem
        question={baseQuestion}
        isSelected={false}
        isCurrentIndex
        onClick={vi.fn()}
      />
    );
    const outerDiv = container.firstChild as HTMLElement;
    expect(outerDiv.className).toContain('bg-secondary/30');
  });

  it.each([
    ['easy' as const, 'green'],
    ['medium' as const, 'yellow'],
    ['hard' as const, 'red'],
  ])('shows correct color for %s difficulty', (difficulty, color) => {
    render(
      <QuestionItem
        question={{ ...baseQuestion, difficulty }}
        isSelected={false}
        isCurrentIndex={false}
        onClick={vi.fn()}
      />
    );
    const badge = screen.getByText(new RegExp(difficulty, 'i'));
    expect(badge.className).toContain(color);
  });
});
