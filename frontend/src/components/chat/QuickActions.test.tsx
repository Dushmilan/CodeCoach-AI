import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QuickActions } from './QuickActions';

describe('QuickActions', () => {
  it('renders all four action buttons', () => {
    render(<QuickActions onActionClick={vi.fn()} />);
    expect(screen.getByRole('button', { name: /hint/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /review/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /explain/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /debug/i })).toBeInTheDocument();
  });

  it('calls onActionClick with correct mode when clicked', async () => {
    const onActionClick = vi.fn();
    const user = userEvent.setup();
    render(<QuickActions onActionClick={onActionClick} />);

    await user.click(screen.getByRole('button', { name: /hint/i }));
    expect(onActionClick).toHaveBeenCalledWith('hint');

    await user.click(screen.getByRole('button', { name: /debug/i }));
    expect(onActionClick).toHaveBeenCalledWith('debug');
  });

  it('disables all buttons when disabled is true', () => {
    render(<QuickActions onActionClick={vi.fn()} disabled />);
    const buttons = screen.getAllByRole('button');
    buttons.forEach((button) => {
      expect(button).toBeDisabled();
    });
  });

  it('enables all buttons by default', () => {
    render(<QuickActions onActionClick={vi.fn()} />);
    const buttons = screen.getAllByRole('button');
    buttons.forEach((button) => {
      expect(button).toBeEnabled();
    });
  });
});
