import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ReviewsDueQueue } from './ReviewsDueQueue';
import { reviewService, ReviewCardItem } from './review.service';

vi.mock('./review.service', () => ({
  reviewService: {
    getDue: vi.fn(),
    grade: vi.fn(),
  },
}));

function makeCard(overrides: Partial<ReviewCardItem> = {}): ReviewCardItem {
  return {
    id: 'card-1',
    user_id: 'u1',
    question_id: 'two-sum',
    error_signature: "expected True, got False",
    state: 'scheduled',
    ease: 2.5,
    interval_days: 1,
    repetitions: 1,
    lapses: 0,
    due_at: '2026-08-24T09:00:00Z',
    last_reviewed_at: null,
    created_at: '2026-08-23T12:00:00Z',
    updated_at: '2026-08-23T12:00:00Z',
    ...overrides,
  };
}

describe('ReviewsDueQueue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing while there are no due reviews', async () => {
    vi.mocked(reviewService.getDue).mockResolvedValue({ cards: [], total: 0 });

    const { container } = render(<ReviewsDueQueue />);

    await waitFor(() => {
      expect(reviewService.getDue).toHaveBeenCalled();
    });
    expect(container).toBeEmptyDOMElement();
  });

  it('renders nothing when the API is unavailable', async () => {
    vi.mocked(reviewService.getDue).mockRejectedValue(new Error('down'));

    const { container } = render(<ReviewsDueQueue />);

    await waitFor(() => {
      expect(reviewService.getDue).toHaveBeenCalled();
    });
    expect(container).toBeEmptyDOMElement();
  });

  it('renders due cards with resolved titles under a review heading', async () => {
    vi.mocked(reviewService.getDue).mockResolvedValue({
      cards: [
        makeCard(),
        makeCard({ id: 'card-2', question_id: 'valid-parentheses' }),
      ],
      total: 2,
    });

    render(
      <ReviewsDueQueue resolveTitle={(id) =>
        id === 'two-sum' ? 'Two Sum' : 'Valid Parentheses'
      } />
    );

    await screen.findByRole('heading', { name: /review your past bugs/i });

    const links = screen.getAllByRole('link');
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAttribute('href', '/problems/two-sum');
    expect(links[0]).toHaveTextContent('Two Sum');
    expect(links[1]).toHaveTextContent('Valid Parentheses');

    // The recurring bug itself is shown so recall has context.
    expect(screen.getAllByText(/expected True, got False/)).toHaveLength(2);
  });

  it('falls back to the raw question id without a resolver', async () => {
    vi.mocked(reviewService.getDue).mockResolvedValue({
      cards: [makeCard()],
      total: 1,
    });

    render(<ReviewsDueQueue />);

    await screen.findByRole('link', { name: 'two-sum' });
  });

  it('grades "Got it" as quality 4 and removes the card', async () => {
    vi.mocked(reviewService.getDue).mockResolvedValue({
      cards: [makeCard()],
      total: 1,
    });
    vi.mocked(reviewService.grade).mockResolvedValue(
      makeCard({ interval_days: 6, repetitions: 2 })
    );
    const user = userEvent.setup();

    render(<ReviewsDueQueue resolveTitle={() => 'Two Sum'} />);
    await screen.findByRole('link', { name: 'Two Sum' });

    await user.click(screen.getByRole('button', { name: /got it/i }));

    await waitFor(() => {
      expect(reviewService.grade).toHaveBeenCalledWith('card-1', 4);
    });
    await waitFor(() => {
      expect(
        screen.queryByRole('link', { name: 'Two Sum' })
      ).not.toBeInTheDocument();
    });
  });

  it('grades "Forgot" as quality 2 and removes the card for re-solve', async () => {
    vi.mocked(reviewService.getDue).mockResolvedValue({
      cards: [makeCard()],
      total: 1,
    });
    vi.mocked(reviewService.grade).mockResolvedValue(makeCard({ state: 'active' }));
    const user = userEvent.setup();

    render(<ReviewsDueQueue resolveTitle={() => 'Two Sum'} />);
    await screen.findByRole('link', { name: 'Two Sum' });

    await user.click(screen.getByRole('button', { name: /forgot/i }));

    await waitFor(() => {
      expect(reviewService.grade).toHaveBeenCalledWith('card-1', 2);
    });
    await waitFor(() => {
      expect(screen.queryByRole('link')).not.toBeInTheDocument();
    });
  });

  it('re-syncs from the server when grading fails', async () => {
    vi.mocked(reviewService.getDue)
      .mockResolvedValueOnce({ cards: [makeCard()], total: 1 })
      .mockResolvedValueOnce({ cards: [makeCard()], total: 1 });
    vi.mocked(reviewService.grade).mockRejectedValue(new Error('offline'));
    const user = userEvent.setup();

    render(<ReviewsDueQueue resolveTitle={() => 'Two Sum'} />);
    await screen.findByRole('link', { name: 'Two Sum' });

    await user.click(screen.getByRole('button', { name: /got it/i }));

    await waitFor(() => {
      expect(reviewService.grade).toHaveBeenCalled();
    });
    // Recovery fetch restores server truth: the card is listed again.
    await waitFor(() => {
      expect(reviewService.getDue).toHaveBeenCalledTimes(2);
    });
    expect(screen.getByRole('link', { name: 'Two Sum' })).toBeInTheDocument();
  });
});
