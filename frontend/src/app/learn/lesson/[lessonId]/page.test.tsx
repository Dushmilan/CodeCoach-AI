import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { server } from '@/mocks/server';
import LessonLoading from './loading';
import LessonPage from './page';
import type { LessonSummary } from '@/types';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

vi.mock('next/navigation', () => ({
  useParams: () => ({ lessonId: 'test-lesson' }),
}));

vi.mock('@/providers', () => ({
  useAuth: () => ({ isAuthenticated: false, isHydrated: true }),
}));

vi.mock('@/features/coaching/coaching.hook', () => ({
  useCoaching: () => ({
    messages: [],
    isTyping: false,
    sendMessage: vi.fn(),
  }),
}));

const lesson: LessonSummary = {
  id: 'test-lesson',
  course_id: 'c1',
  module_id: 'm1',
  title: 'Test Lesson',
  type: 'theory',
  content: 'content',
  order: 1,
  starter_code: null,
  test_cases: null,
  question_id: null,
  language: 'python',
};

vi.mock('@/features/curriculum/use-curriculum.hook', () => ({
  useLesson: () => ({ lesson, isLoading: false, error: null }),
}));

describe('LessonPage layout width', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/courses/lessons/:lessonId/adjacent', () =>
        HttpResponse.json({ prev_id: null, next_id: null }),
      ),
    );
  });

  afterEach(() => {
    server.resetHandlers();
  });

  it('renders the main workspace container at full width (no max-w-7xl cap)', async () => {
    render(<LessonPage />);
    const main = await screen.findByRole('main');
    expect(main).toHaveClass('w-full');
    expect(main).not.toHaveClass('max-w-7xl');
  });
});

describe('LessonLoading layout width', () => {
  it('renders the content container at full width (no max-w-7xl cap)', () => {
    render(<LessonLoading />);
    const container = screen.getByTestId('lesson-content-container');
    expect(container).toBeInTheDocument();
    expect(container).toHaveClass('w-full');
    expect(container).not.toHaveClass('max-w-7xl');
  });
});
