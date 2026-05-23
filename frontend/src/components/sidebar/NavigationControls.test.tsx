import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NavigationControls } from './NavigationControls';

describe('NavigationControls', () => {
  it('renders Prev and Next buttons', () => {
    render(<NavigationControls onPrevious={vi.fn()} onNext={vi.fn()} />);
    expect(screen.getByRole('button', { name: /prev/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
  });

  it('calls onPrevious when Prev is clicked', async () => {
    const onPrevious = vi.fn();
    const user = userEvent.setup();
    render(<NavigationControls onPrevious={onPrevious} onNext={vi.fn()} />);
    await user.click(screen.getByRole('button', { name: /prev/i }));
    expect(onPrevious).toHaveBeenCalledOnce();
  });

  it('calls onNext when Next is clicked', async () => {
    const onNext = vi.fn();
    const user = userEvent.setup();
    render(<NavigationControls onPrevious={vi.fn()} onNext={onNext} />);
    await user.click(screen.getByRole('button', { name: /next/i }));
    expect(onNext).toHaveBeenCalledOnce();
  });

  it('disables buttons when disabled is true', () => {
    render(<NavigationControls onPrevious={vi.fn()} onNext={vi.fn()} disabled />);
    expect(screen.getByRole('button', { name: /prev/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /next/i })).toBeDisabled();
  });

  it('enables buttons by default', () => {
    render(<NavigationControls onPrevious={vi.fn()} onNext={vi.fn()} />);
    expect(screen.getByRole('button', { name: /prev/i })).toBeEnabled();
    expect(screen.getByRole('button', { name: /next/i })).toBeEnabled();
  });

  it('hides content when collapsed', () => {
    const { container } = render(
      <NavigationControls onPrevious={vi.fn()} onNext={vi.fn()} isCollapsed />
    );
    const outerDiv = container.firstChild as HTMLElement;
    expect(outerDiv.className).toContain('opacity-0');
    expect(outerDiv.className).toContain('h-0');
  });
});
