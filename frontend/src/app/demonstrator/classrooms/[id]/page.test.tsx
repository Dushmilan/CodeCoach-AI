import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  expectBentoStats,
  expectEyebrowBudget,
  expectNoDash,
  expectNoDuplicateCtas,
} from '@/test-helpers/taste';

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

  it('lays stats out as a varied bento and passes taste gates', async () => {
    const { container } = render(<DemonstratorClassroomDetailPage />);
    await screen.findByText('CS101 · Section A');
    expect(container.querySelectorAll('[data-stat]')).toHaveLength(3);
    expectBentoStats(container);
    expectNoDash(container, 'demonstrator classroom detail');
    expectEyebrowBudget(container, 'demonstrator classroom detail');
    expectNoDuplicateCtas(container, 'demonstrator classroom detail');
  });
});
