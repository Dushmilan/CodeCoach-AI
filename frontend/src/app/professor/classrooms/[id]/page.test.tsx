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

import ProfessorClassroomDetailPage from './page';

describe('ProfessorClassroomDetailPage', () => {
  it('renders the classroom roster from the route id', async () => {
    render(<ProfessorClassroomDetailPage />);
    expect(await screen.findByText('CS101 · Section A')).toBeInTheDocument();
    expect(screen.getByTestId('roster-table')).toBeInTheDocument();
    // Issue #292 bans em dashes, so the heading is dash-free copy.
    expect(screen.getByText('Roster and enrollment')).toBeInTheDocument();
  });

  it('lays stats out as a varied bento and passes taste gates', async () => {
    const { container } = render(<ProfessorClassroomDetailPage />);
    await screen.findByText('CS101 · Section A');
    expect(container.querySelectorAll('[data-stat]')).toHaveLength(3);
    expectBentoStats(container);
    expectNoDash(container, 'professor classroom detail');
    expectEyebrowBudget(container, 'professor classroom detail');
    expectNoDuplicateCtas(container, 'professor classroom detail');
  });
});
