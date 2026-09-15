import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('next/navigation', () => ({
  useParams: () => ({ id: 'class-cs101-a' }),
  notFound: () => {
    throw new Error('NEXT_NOT_FOUND');
  },
}));
vi.mock('next/link', () => ({
  default: ({ children, ...props }: Record<string, unknown>) => (
    <a {...props}>{children as React.ReactNode}</a>
  ),
}));

import DemonstratorClassroomDetailPage from './page';

describe('DemonstratorClassroomDetailPage', () => {
  it('renders the read-only classroom roster from the route id', async () => {
    render(<DemonstratorClassroomDetailPage />);
    expect(await screen.findByText('CS101 · Section A')).toBeInTheDocument();
    expect(screen.getByTestId('roster-table')).toBeInTheDocument();
    expect(screen.getByText('Roster (read-only)')).toBeInTheDocument();
  });
});
