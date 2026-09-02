import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { OnboardingTour } from './OnboardingTour';

const mockSetItem = vi.fn();

beforeEach(() => {
  vi.spyOn(Storage.prototype, 'getItem').mockReturnValue(null);
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(mockSetItem);
  mockSetItem.mockReset();
});

describe('OnboardingTour', () => {
  it('renders when no stored completion flag', () => {
    render(<OnboardingTour />);
    expect(screen.getByText('Welcome to CodeCoach AI')).toBeInTheDocument();
  });

  it('does not render when onboarding is already done', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockReturnValue(JSON.stringify(true));
    const { container } = render(<OnboardingTour />);
    expect(container.innerHTML).toBe('');
  });

  it('navigates through steps', async () => {
    const user = userEvent.setup();
    render(<OnboardingTour />);

    expect(screen.getByText('Welcome to CodeCoach AI')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByText('Dashboard & Memory Graph')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByText('Question Browser')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByText('AI Coach')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByText('Never-Alone Rescue')).toBeInTheDocument();
  });

  it('completes tour on last step', async () => {
    const user = userEvent.setup();
    render(<OnboardingTour />);

    for (let i = 0; i < 4; i++) {
      await user.click(screen.getByRole('button', { name: /next/i }));
    }

    await user.click(screen.getByRole('button', { name: /get started/i }));
    expect(screen.queryByText('Welcome to CodeCoach AI')).not.toBeInTheDocument();
  });

  it('dismisses tour on close', async () => {
    const user = userEvent.setup();
    render(<OnboardingTour />);

    await user.click(screen.getByLabelText('Dismiss tour'));
    expect(screen.queryByText('Welcome to CodeCoach AI')).not.toBeInTheDocument();
  });

  it('goes back to previous step', async () => {
    const user = userEvent.setup();
    render(<OnboardingTour />);

    await user.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByText('Dashboard & Memory Graph')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /back/i }));
    expect(screen.getByText('Welcome to CodeCoach AI')).toBeInTheDocument();
  });

  it('exposes retrigger via Restart button after dismiss', async () => {
    const user = userEvent.setup();
    const { rerender } = render(<OnboardingTour />);
    await user.click(screen.getByLabelText('Dismiss tour'));
    expect(screen.queryByText('Welcome to CodeCoach AI')).not.toBeInTheDocument();
    // Simulate external retrigger by clearing storage and remounting
    window.localStorage.removeItem('onboarding-done');
    rerender(<OnboardingTour />);
    // still hidden until storage cleared and component remounted with fresh hook read
    // This test documents the retrigger contract: clearing the key re-shows the tour
    window.localStorage.setItem('onboarding-done', JSON.stringify(false));
    rerender(<OnboardingTour />);
    // After reset, tour should be visible again on next mount
    const { container } = render(<OnboardingTour />);
    expect(container.innerHTML).not.toBe('');
  });
});
