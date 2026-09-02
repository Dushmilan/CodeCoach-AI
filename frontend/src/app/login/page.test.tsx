import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LoginPage from './page';

const mockUseAuth = vi.hoisted(() => vi.fn());
const mockSignInWithGoogle = vi.hoisted(() => vi.fn());
const mockPush = vi.hoisted(() => vi.fn());

vi.mock('@/providers/AuthProvider', () => ({ useAuth: mockUseAuth }));
vi.mock('@/features/auth/auth.service', () => ({
  signInWithGoogle: mockSignInWithGoogle,
}));
vi.mock('next/navigation', () => ({ useRouter: () => ({ push: mockPush }) }));
vi.mock('next/link', () => ({
  default: ({ children, ...props }: Record<string, unknown>) => (
    <a {...props}>{children as React.ReactNode}</a>
  ),
}));
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: Record<string, unknown>) => {
      // Strip animation-only props so React doesn't warn about DOM attributes.
      const { initial, animate, transition, ...rest } = props as Record<string, unknown>;
      return <div {...rest}>{children as React.ReactNode}</div>;
    },
  },
}));
vi.mock('@/components/header/Header', () => ({ Header: () => <header /> }));

describe('LoginPage', () => {
  beforeEach(() => {
    mockUseAuth.mockReset();
    mockUseAuth.mockReturnValue({
      login: vi.fn().mockResolvedValue({}),
    });
    mockSignInWithGoogle.mockReset();
    mockPush.mockReset();
  });

  it('renders a Continue with Google button', () => {
    render(<LoginPage />);
    expect(screen.getByRole('button', { name: /continue with google/i })).toBeInTheDocument();
  });

  it('starts the Supabase Google OAuth flow on click', async () => {
    mockSignInWithGoogle.mockResolvedValue(undefined);
    render(<LoginPage />);

    fireEvent.click(screen.getByRole('button', { name: /continue with google/i }));

    await waitFor(() => expect(mockSignInWithGoogle).toHaveBeenCalled());
  });

  it('shows an error when the Google flow fails', async () => {
    mockSignInWithGoogle.mockRejectedValue(new Error('provider not enabled'));
    render(<LoginPage />);

    fireEvent.click(screen.getByRole('button', { name: /continue with google/i }));

    expect(await screen.findByText('provider not enabled')).toBeInTheDocument();
  });

  it('redirects to /admin when admin user logs in', async () => {
    const adminResponse = { user: { role: 'admin' }, access_token: 'tok' };
    const mockLogin = vi.fn().mockResolvedValue(adminResponse);
    mockUseAuth.mockReturnValue({ login: mockLogin } as unknown as ReturnType<typeof mockUseAuth>);
    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'admin' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'admin123' } });
    fireEvent.click(screen.getByTestId('login-submit'));
    await waitFor(() => expect(mockLogin).toHaveBeenCalled());
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith('/admin'));
  });

  it('redirects to / when regular user logs in', async () => {
    const userResponse = { user: { role: 'user' }, access_token: 'tok' };
    const mockLogin = vi.fn().mockResolvedValue(userResponse);
    mockUseAuth.mockReturnValue({ login: mockLogin } as unknown as ReturnType<typeof mockUseAuth>);
    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'bob' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'bob12345' } });
    fireEvent.click(screen.getByTestId('login-submit'));
    await waitFor(() => expect(mockLogin).toHaveBeenCalled());
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith('/'));
  });

  it('redirects to /admin when super_admin user logs in', async () => {
    const superResponse = { user: { role: 'super_admin' }, access_token: 'tok' };
    const mockLogin = vi.fn().mockResolvedValue(superResponse);
    mockUseAuth.mockReturnValue({ login: mockLogin } as unknown as ReturnType<typeof mockUseAuth>);
    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'superadmin' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'superadmin123' } });
    fireEvent.click(screen.getByTestId('login-submit'));
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith('/admin'));
  });
});
