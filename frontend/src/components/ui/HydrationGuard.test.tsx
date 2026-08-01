import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { HydrationGuard } from './HydrationGuard';

describe('HydrationGuard', () => {
  it('renders children after mount when fallback is provided', () => {
    render(
      <HydrationGuard fallback={<div data-testid="fallback">Loading</div>}>
        <div data-testid="content">Content</div>
      </HydrationGuard>,
    );
    expect(screen.getByTestId('content')).toBeInTheDocument();
    expect(screen.queryByTestId('fallback')).not.toBeInTheDocument();
  });

  it('renders children after mount without a fallback prop', () => {
    render(
      <HydrationGuard>
        <div data-testid="content">Content</div>
      </HydrationGuard>,
    );
    expect(screen.getByTestId('content')).toBeInTheDocument();
  });

  it('shows children after the hydration effect runs', async () => {
    render(
      <HydrationGuard>
        <div data-testid="content">Content</div>
      </HydrationGuard>,
    );
    await screen.findByTestId('content');
    expect(screen.getByTestId('content')).toBeInTheDocument();
  });
});
