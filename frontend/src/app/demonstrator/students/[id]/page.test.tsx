import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  expectEyebrowBudget,
  expectNoDash,
  expectNoDuplicateCtas,
} from '@/test-helpers/taste';

vi.mock('next/navigation', () => ({
  useParams: () => ({ id: 'stu-mia-01' }),
  notFound: () => {
    throw new Error('NEXT_NOT_FOUND');
  },
}));

import DemonstratorStudentDetailPage from './page';

describe('DemonstratorStudentDetailPage', () => {
  it('renders the student progress from the route id', () => {
    render(<DemonstratorStudentDetailPage />);
    expect(screen.getByText('Mia Chen')).toBeInTheDocument();
    expect(screen.getByTestId('ta-student-progress')).toBeInTheDocument();
  });

  it('passes rendered taste gates (dash-free coaching copy)', () => {
    const { container } = render(<DemonstratorStudentDetailPage />);
    expectNoDash(container, 'demonstrator student detail');
    expectEyebrowBudget(container, 'demonstrator student detail');
    expectNoDuplicateCtas(container, 'demonstrator student detail');
  });
});
