import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from './button';

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('renders as a button element', () => {
    render(<Button />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('applies default variant and size classes', () => {
    render(<Button>Default</Button>);
    const button = screen.getByRole('button');
    expect(button.className).toContain('bg-primary');
    expect(button.className).toContain('h-10');
  });

  it.each([
    'default', 'destructive', 'outline', 'secondary', 'ghost', 'link',
  ] as const)('renders %s variant', (variant) => {
    render(<Button variant={variant}>{variant}</Button>);
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
  });

  it.each([
    'default', 'sm', 'lg', 'icon',
  ] as const)('renders %s size', (size) => {
    render(<Button size={size}>{size}</Button>);
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
  });

  it('handles click events', async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(<Button onClick={onClick}>Click</Button>);
    await user.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it('is disabled when disabled prop is set', () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('applies custom className', () => {
    render(<Button className="custom-class">Styled</Button>);
    expect(screen.getByRole('button').className).toContain('custom-class');
  });

  it('forwards ref to the button element', () => {
    const ref = { current: null };
    render(<Button ref={ref} />);
    expect(ref.current).toBeInstanceOf(HTMLButtonElement);
  });
});
