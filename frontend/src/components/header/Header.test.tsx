import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const mockSetTheme = vi.fn();
const mockUseTheme = vi.hoisted(() => vi.fn());
const mockUseAuth = vi.hoisted(() =>
  vi.fn(() => ({
    user: null,
    isAuthenticated: false,
    isLoading: false,
    logout: vi.fn(),
  })),
);

vi.mock('next-themes', () => ({
  useTheme: mockUseTheme,
}));

vi.mock('@/providers', () => ({
  useAuth: mockUseAuth,
}));

vi.mock('@/components/settings/SettingsModal', () => ({
  SettingsModal: vi.fn(({ open }: { open: boolean }) =>
    open ? <div role="dialog">Settings Modal</div> : null,
  ),
}));

import { Header } from './Header';

describe('Header', () => {
  beforeEach(() => {
    mockUseTheme.mockReturnValue({
      theme: 'dark',
      setTheme: mockSetTheme,
      resolvedTheme: 'dark',
    });
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      logout: vi.fn(),
    });
    vi.clearAllMocks();
  });

  it('renders the title', () => {
    render(<Header />);
    expect(screen.getByText('CodeCoach AI')).toBeInTheDocument();
  });

  it('renders settings button', () => {
    render(<Header />);
    expect(screen.getByTitle('Settings')).toBeInTheDocument();
  });

  it("shows 'Light Mode' label when resolved theme is dark", async () => {
    render(<Header />);
    expect(await screen.findByText('Light Mode')).toBeInTheDocument();
  });

  it('toggles theme when theme button is clicked', async () => {
    const user = userEvent.setup();
    render(<Header />);
    const buttons = screen.getAllByRole('button');
    const themeButton = buttons.find((b) => b.getAttribute('aria-label') === 'Toggle theme')!;
    await user.click(themeButton);
    expect(mockSetTheme).toHaveBeenCalledWith('light');
  });

  it('opens settings modal when settings button is clicked', async () => {
    const user = userEvent.setup();
    render(<Header />);
    await user.click(screen.getByTitle('Settings'));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Settings Modal')).toBeInTheDocument();
  });

  it("shows 'Dark Mode' label when resolved theme is light", async () => {
    mockUseTheme.mockReturnValue({
      theme: 'light',
      setTheme: mockSetTheme,
      resolvedTheme: 'light',
    });
    render(<Header />);
    expect(await screen.findByText('Dark Mode')).toBeInTheDocument();
  });

  describe('admin dashboard link', () => {
    it('shows admin dashboard link for admin user', () => {
      mockUseAuth.mockReturnValue({
        user: { id: '1', username: 'admin', email: 'a@a.com', created_at: '', is_active: true, role: 'admin' },
        isAuthenticated: true,
        isHydrated: true,
        isLoading: false,
        logout: vi.fn(),
      } as unknown as ReturnType<typeof mockUseAuth>);
      render(<Header />);
      expect(screen.getByTestId('header-admin-link')).toBeInTheDocument();
      expect(screen.getByTestId('header-admin-link')).toHaveAttribute('href', '/admin');
    });

    it('shows admin dashboard link for super_admin user', () => {
      mockUseAuth.mockReturnValue({
        user: { id: '1', username: 'super', email: 's@a.com', created_at: '', is_active: true, role: 'super_admin' },
        isAuthenticated: true,
        isHydrated: true,
        isLoading: false,
        logout: vi.fn(),
      } as unknown as ReturnType<typeof mockUseAuth>);
      render(<Header />);
      expect(screen.getByTestId('header-admin-link')).toBeInTheDocument();
    });

    it('does not show admin link for regular user', () => {
      mockUseAuth.mockReturnValue({
        user: { id: '2', username: 'bob', email: 'b@a.com', created_at: '', is_active: true, role: 'user' },
        isAuthenticated: true,
        isHydrated: true,
        isLoading: false,
        logout: vi.fn(),
      } as unknown as ReturnType<typeof mockUseAuth>);
      render(<Header />);
      expect(screen.queryByTestId('header-admin-link')).not.toBeInTheDocument();
    });

    it('does not show admin link when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isAuthenticated: false,
        isHydrated: true,
        isLoading: false,
        logout: vi.fn(),
      } as unknown as ReturnType<typeof mockUseAuth>);
      render(<Header />);
      expect(screen.queryByTestId('header-admin-link')).not.toBeInTheDocument();
    });

    it('does not show admin link when not hydrated', () => {
      mockUseAuth.mockReturnValue({
        user: { id: '1', username: 'admin', email: 'a@a.com', created_at: '', is_active: true, role: 'admin' },
        isAuthenticated: true,
        isHydrated: false,
        isLoading: false,
        logout: vi.fn(),
      } as unknown as ReturnType<typeof mockUseAuth>);
      render(<Header />);
      expect(screen.queryByTestId('header-admin-link')).not.toBeInTheDocument();
    });
  });
});
