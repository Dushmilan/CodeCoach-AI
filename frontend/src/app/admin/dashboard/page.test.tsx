import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
}));

vi.mock('@/providers', () => ({ useAuth: mocks.useAuth }));

import AdminDashboard from './page';

const TREE = {
  professors: [
    {
      id: 'p-ada',
      username: 'professor.ada',
      courses: [{ id: 'c-py', title: 'Python Fundamentals', lessons: 36 }],
      classrooms: [
        {
          id: 'r-cs101',
          name: 'CS101 · Section A',
          invite_code: 'CS101-A-2026',
          tas: ['demonstrator.turing'],
          students: 5,
          avg_completion: 61,
        },
      ],
    },
  ],
};

describe('AdminDashboard hierarchy section', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.useAuth.mockReturnValue({
      user: { username: 'admin', role: 'admin' },
      token: 'test-token',
    });
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        if (String(url).includes('/api/admin/hierarchy')) {
          return { ok: true, json: async () => TREE } as Response;
        }
        return { ok: true, json: async () => ({}) } as Response;
      }),
    );
  });

  it('lists each professor with courses and classroom analytics', async () => {
    render(<AdminDashboard />);
    await waitFor(() =>
      expect(screen.getByText('professor.ada')).toBeInTheDocument(),
    );
    expect(screen.getByText('Python Fundamentals')).toBeInTheDocument();
    expect(screen.getByText(/36 lessons/)).toBeInTheDocument();
    expect(screen.getByText('CS101 · Section A')).toBeInTheDocument();
    expect(screen.getByText('CS101-A-2026')).toBeInTheDocument();
    expect(screen.getByText('demonstrator.turing')).toBeInTheDocument();
    expect(screen.getByText(/5 students/)).toBeInTheDocument();
    expect(screen.getByText(/61% avg completion/)).toBeInTheDocument();
  });

  it('shows an empty state when no professors exist', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        if (String(url).includes('/api/admin/hierarchy')) {
          return { ok: true, json: async () => ({ professors: [] }) } as Response;
        }
        return { ok: true, json: async () => ({}) } as Response;
      }),
    );
    render(<AdminDashboard />);
    await waitFor(() =>
      expect(screen.getByText(/no professors/i)).toBeInTheDocument(),
    );
  });
});
