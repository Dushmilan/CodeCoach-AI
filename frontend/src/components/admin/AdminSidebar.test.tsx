import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
  usePathname: vi.fn(),
}));

vi.mock('@/providers', () => ({ useAuth: mocks.useAuth }));
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
    mocks.usePathname.mockReturnValue('/admin');
  });

  it('renders the core admin nav items', () => {
    render(<AdminSidebar open={false} onClose={vi.fn()} />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Users')).toBeInTheDocument();
    expect(screen.getByText('Professors')).toBeInTheDocument();
    expect(screen.getByText('Questions')).toBeInTheDocument();
    expect(screen.getByText('Curriculum')).toBeInTheDocument();
  });

  it('shows Curriculum to professors but hides admin-only nav items', () => {
    mocks.useAuth.mockReturnValue({
      user: { username: 'prof', role: 'professor' },
      isAuthenticated: true,
      isLoading: false,
      logout: vi.fn(),
    });
    render(<AdminSidebar open={false} onClose={vi.fn()} />);
    expect(screen.getByText('Curriculum')).toBeInTheDocument();
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
    expect(screen.queryByText('Users')).not.toBeInTheDocument();
    expect(screen.queryByText('Questions')).not.toBeInTheDocument();
  });

  it('links Professors to the admin hierarchy roster', () => {
    render(<AdminSidebar open={false} onClose={vi.fn()} />);
    expect(screen.getByText('Professors').closest('a')).toHaveAttribute(
      'href',
      '/admin/professors',
    );
  });

  it('does not render removed Analytics nav item', () => {
    render(<AdminSidebar open={false} onClose={vi.fn()} />);
    expect(screen.queryByText('Analytics')).not.toBeInTheDocument();
  });

  it('does not render removed Settings nav item', () => {
    render(<AdminSidebar open={false} onClose={vi.fn()} />);
    expect(screen.queryByText('Settings')).not.toBeInTheDocument();
  });

  it('marks only the deepest matching nav item as an active pill', () => {
    mocks.usePathname.mockReturnValue('/admin/users');
    render(<AdminSidebar open={false} onClose={vi.fn()} />);
    const current = document.querySelectorAll('[aria-current="page"]');
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent('Users');
    expect(current[0].className).toMatch(/rounded-full/);
    expect(current[0].className).toMatch(/bg-brand\b/);
  });

  it('shows the signed-in user as an avatar chip', () => {
    render(<AdminSidebar open={false} onClose={vi.fn()} />);
    expect(screen.getByTestId('admin-sidebar-avatar')).toBeInTheDocument();
    // Username and role both render "admin" in this fixture.
    expect(screen.getAllByText('admin').length).toBeGreaterThanOrEqual(1);
  });
});
