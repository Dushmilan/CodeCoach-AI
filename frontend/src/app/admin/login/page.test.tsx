import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { HttpError } from '@/lib/fetch-client';
import AdminLogin from './page';

const mockUseAuth = vi.hoisted(() => vi.fn());
const mockPush = vi.hoisted(() => vi.fn());

vi.mock('@/providers', () => ({ useAuth: mockUseAuth }));
vi.mock('next/navigation', () => ({ useRouter: () => ({ push: mockPush }) }));
vi.mock('next/link', () => ({
  default: ({ children, ...props }: Record<string, unknown>) => (
    <a {...props}>{children as React.ReactNode}</a>
  ),
}));

describe('AdminLogin', () => {
  beforeEach(() => {
    mockUseAuth.mockReset();
    mockUseAuth.mockReturnValue({
      login: vi.fn().mockResolvedValue({}),
    });
    mockPush.mockReset();
  });

  it('renders server detail when login fails with 401 + detail body', async () => {
    const mockLogin = vi.fn().mockRejectedValue(
      new HttpError(
        'Request failed: 401 Unauthorized',
        401,
        JSON.stringify({ detail: 'Invalid username or password' }),
      ),
    );
    mockUseAuth.mockReturnValue({ login: mockLogin } as unknown as ReturnType<typeof mockUseAuth>);
    render(<AdminLogin />);
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'admin' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'wrongpassword' } });
    fireEvent.click(screen.getByTestId('admin-login-submit'));
    await waitFor(() => expect(mockLogin).toHaveBeenCalled());
    expect(await screen.findByText('Invalid username or password')).toBeTruthy();
  });
});
