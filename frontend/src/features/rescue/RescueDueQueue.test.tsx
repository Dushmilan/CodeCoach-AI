import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RescueDueQueue } from './RescueDueQueue';
import { rescueService, RescueQueueItem } from './rescue.service';

vi.mock('./rescue.service', () => ({
  rescueService: {
    getDue: vi.fn(),
    dismiss: vi.fn(),
    abandon: vi.fn(),
    complete: vi.fn(),
  },
}));

function makeItem(overrides: Partial<RescueQueueItem> = {}): RescueQueueItem {
  return {
    id: 'row-1',
    user_id: 'u1',
    question_id: 'two-sum',
    status: 'abandoned',
    first_abandoned_at: '2026-08-23T12:00:00Z',
    due_at: '2026-08-24T09:00:00Z',
    resurface_count: 0,
    last_intervention_at: null,
    created_at: '2026-08-23T12:00:00Z',
    updated_at: '2026-08-23T12:00:00Z',
    ...overrides,
  };
}

describe('RescueDueQueue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing while the queue is empty', async () => {
    vi.mocked(rescueService.getDue).mockResolvedValue({ items: [], total: 0 });

    const { container } = render(<RescueDueQueue />);

    await waitFor(() => {
      expect(rescueService.getDue).toHaveBeenCalled();
    });
    expect(container).toBeEmptyDOMElement();
  });

  it('renders due items with resolved titles under a "Back tomorrow" heading', async () => {
    vi.mocked(rescueService.getDue).mockResolvedValue({
      items: [
        makeItem(),
        makeItem({
          id: 'row-2',
          question_id: 'valid-parentheses',
          resurface_count: 2,
        }),
      ],
      total: 2,
    });

    render(
      <RescueDueQueue
        resolveTitle={(id) =>
          id === 'two-sum' ? 'Two Sum' : 'Valid Parentheses'
        }
      />,
    );

    expect(await screen.findByText('Back tomorrow')).toBeInTheDocument();
    expect(screen.getByText('Two Sum')).toBeInTheDocument();
    expect(screen.getByText('Valid Parentheses')).toBeInTheDocument();
    // Repeat abandonments are visible so the nudge feels honest.
    expect(screen.getByText(/seen 3 times/i)).toBeInTheDocument();
  });

  it('links each item to its problem workspace', async () => {
    vi.mocked(rescueService.getDue).mockResolvedValue({
      items: [makeItem()],
      total: 1,
    });

    render(<RescueDueQueue resolveTitle={() => 'Two Sum'} />);

    const link = await screen.findByRole('link', { name: /two sum/i });
    expect(link).toHaveAttribute('href', '/problems/two-sum');
  });

  it('dismiss removes the item permanently', async () => {
    vi.mocked(rescueService.getDue).mockResolvedValue({
      items: [makeItem()],
      total: 1,
    });
    vi.mocked(rescueService.dismiss).mockResolvedValue(null);

    const user = userEvent.setup();
    render(<RescueDueQueue />);

    await user.click(await screen.findByRole('button', { name: /dismiss/i }));

    await waitFor(() => {
      expect(rescueService.dismiss).toHaveBeenCalledWith('two-sum');
    });
    await waitFor(() => {
      expect(screen.queryByRole('link', { name: /two sum/i })).toBeNull();
    });
  });

  it('falls back to the raw question id when no title resolver matches', async () => {
    vi.mocked(rescueService.getDue).mockResolvedValue({
      items: [makeItem({ question_id: 'obscure-q' })],
      total: 1,
    });

    render(<RescueDueQueue resolveTitle={() => undefined} />);

    expect(await screen.findByText('obscure-q')).toBeInTheDocument();
  });
});
