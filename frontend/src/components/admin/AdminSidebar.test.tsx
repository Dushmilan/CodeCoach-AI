import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
  useTheme: vi.fn(),
  usePathname: vi.fn(),
}));

vi.mock('@/providers', () => ({ useAuth: mocks.useAuth }));
vi.mock('next-themes', () => ({ useTheme: mocks.useTheme }));
vi.mock('next/navigation', () => ({ usePathname: mocks.usePathname }));

import AdminSidebar from './AdminSidebar';

describe('AdminSidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.useAuth.mockReturnValue({
      user: { username: 'admin', role: 'admin' },
      isAuthenticated: true,
      isLoading: false,
      logout: vi.fn(),
    });
    mocks.useTheme.mockReturnValue({
      theme: 'dark',
      setTheme: vi.fn(),
      resolvedTheme: 'dark',
    });
    mocks.usePathname.mockReturnValue('/admin');
  });

  it('renders the core admin nav items', () => {
    render(<AdminSidebar open={false} onClose={vi.fn()} />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Users')).toBeInTheDocument();
    expect(screen.getByText('Questions')).toBeInTheDocument();
    expect(screen.getByText('Curriculum')).toBeInTheDocument();
  });

  it('does not render removed Analytics nav item', () => {
    render(<AdminSidebar open={false} onClose={vi.fn()} />);
    expect(screen.queryByText('Analytics')).not.toBeInTheDocument();
  });

  it('does not render removed Settings nav item', () => {
    render(<AdminSidebar open={false} onClose={vi.fn()} />);
    expect(screen.queryByText('Settings')).not.toBeInTheDocument();
  });
});
