import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { HttpError } from '@/lib/fetch-client';
import RegisterPage from './page';

const mockUseAuth = vi.hoisted(() => vi.fn());
const mockPush = vi.hoisted(() => vi.fn());

vi.mock('@/providers/AuthProvider', () => ({ useAuth: mockUseAuth }));
vi.mock('next/navigation', () => ({ useRouter: () => ({ push: mockPush }) }));
vi.mock('next/link', () => ({
  default: ({ children, ...props }: Record<string, unknown>) => (
    <a {...props}>{children as React.ReactNode}</a>
  ),
}));
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: Record<string, unknown>) => {
      const { initial, animate, transition, ...rest } = props as Record<string, unknown>;
      return <div {...rest}>{children as React.ReactNode}</div>;
    },
  },
}));
vi.mock('@/components/header/Header', () => ({ Header: () => <header /> }));

describe('RegisterPage', () => {
  beforeEach(() => {
    mockUseAuth.mockReset();
    mockUseAuth.mockReturnValue({
      register: vi.fn().mockResolvedValue({}),
    });
    mockPush.mockReset();
  });

  it('renders server detail when register fails with 409 + detail body', async () => {
    const mockRegister = vi.fn().mockRejectedValue(
      new HttpError(
        'Request failed: 409 Conflict',
        409,
        JSON.stringify({ detail: 'Username already taken' }),
      ),
    );
    mockUseAuth.mockReturnValue({ register: mockRegister } as unknown as ReturnType<typeof mockUseAuth>);
    render(<RegisterPage />);
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'takenname' } });
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'taken@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'secret123' } });
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));
    await waitFor(() => expect(mockRegister).toHaveBeenCalled());
    expect(await screen.findByText('Username already taken')).toBeTruthy();
  });
});
