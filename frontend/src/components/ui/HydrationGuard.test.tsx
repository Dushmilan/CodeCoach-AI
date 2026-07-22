import { render, screen, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { HydrationGuard } from './HydrationGuard';

describe('HydrationGuard', () => {
  it('renders fallback initially', () => {
    render(
      <HydrationGuard fallback={<div data-testid="fallback">Loading</div>}>
        <div data-testid="content">Content</div>
      </HydrationGuard>,
    );
    expect(screen.getByTestId('fallback')).toBeInTheDocument();
    expect(screen.queryByTestId('content')).not.toBeInTheDocument();
  });

  it('renders children after mount', () => {
    render(
      <HydrationGuard fallback={<div data-testid="fallback">Loading</div>}>
        <div data-testid="content">Content</div>
      </HydrationGuard>,
    );
    act(() => {
      vi.runAllTimers();
    });
  });

  it('renders children without fallback prop', () => {
    render(
      <HydrationGuard>
        <div data-testid="content">Content</div>
      </HydrationGuard>,
    );
    expect(screen.queryByTestId('content')).not.toBeInTheDocument();
  });

  it('shows children after hydration effect runs', async () => {
    render(
      <HydrationGuard>
        <div data-testid="content">Content</div>
      </HydrationGuard>,
    );
    await act(async () => {});
    expect(screen.getByTestId('content')).toBeInTheDocument();
  });
});
