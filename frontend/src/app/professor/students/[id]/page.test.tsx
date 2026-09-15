import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('next/navigation', () => ({
  useParams: () => ({ id: 'stu-mia-01' }),
  notFound: () => {
    throw new Error('NEXT_NOT_FOUND');
  },
}));
vi.mock('next/link', () => ({
  default: ({ children, ...props }: Record<string, unknown>) => (
    <a {...props}>{children as React.ReactNode}</a>
  ),
}));

import ProfessorStudentDetailPage from './page';

describe('ProfessorStudentDetailPage', () => {
  it('renders the student progress from the route id', () => {
    render(<ProfessorStudentDetailPage />);
    expect(screen.getByText('Mia Chen')).toBeInTheDocument();
    expect(screen.getByTestId('student-progress')).toBeInTheDocument();
  });
});
