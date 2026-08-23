import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LoginPage from './page';

const mockUseAuth = vi.hoisted(() => vi.fn());
const mockSignInWithGoogle = vi.hoisted(() => vi.fn());

vi.mock('@/providers/AuthProvider', () => ({ useAuth: mockUseAuth }));
vi.mock('@/features/auth/auth.service', () => ({
  signInWithGoogle: mockSignInWithGoogle,
}));
vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn() }) }));
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
});
