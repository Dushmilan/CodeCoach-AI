import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { server } from '@/mocks/server';
import LessonPage from './page';
import type { LessonSummary } from '@/types';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

vi.mock('next/navigation', () => ({
  useParams: () => ({ lessonId: 'ex-1' }),
}));

vi.mock('@/providers', () => ({
  useAuth: () => ({
    isAuthenticated: true,
    isHydrated: true,
    user: { id: 'u1', username: 'stu' },
  }),
}));

vi.mock('@/features/coaching/coaching.hook', () => ({
  useCoaching: () => ({ messages: [], isTyping: false, sendMessage: vi.fn() }),
}));

vi.mock('@/features/animation/animation.service', () => ({
  animationService: { generateAnimation: vi.fn() },
  buildAnimateQuestion: vi.fn((q: unknown) => q),
}));

vi.mock('@/components/layout/lessons', () => ({
  LessonChrome: ({ actions }: any) => (
    <div data-testid="chrome">{actions}</div>
  ),
  ExerciseLessonLayout: (props: any) => (
    <div>
      <button onClick={() => props.onRunCode('')}>Run</button>
      {props.error ? (
        <div data-testid="run-error">{props.error}</div>
      ) : null}
    </div>
  ),
  TheoryLessonLayout: () => null,
}));

const mockUseLesson = vi.hoisted(() => vi.fn());

vi.mock('@/features/curriculum/use-curriculum.hook', () => ({
  useLesson: mockUseLesson,
}));

const lesson: LessonSummary = {
  id: 'ex-1',
  course_id: 'c1',
  module_id: 'm1',
  title: 'Exercise',
  type: 'exercise',
  content: 'content',
  order: 1,
  starter_code: 'print(1)',
  test_cases: null,
  question_id: null,
  language: 'python',
};

describe('LessonPage run errors (Issue #225)', () => {
  beforeEach(() => {
    mockUseLesson.mockReturnValue({ lesson, isLoading: false, error: null });
    server.use(
      http.get('/api/courses/lessons/:lessonId/adjacent', () =>
        HttpResponse.json({ prev_id: null, next_id: null }),
      ),
      http.get('/api/progress/:courseId', () =>
        HttpResponse.json({ completed_lessons: [] }),
      ),
    );
  });

  it('shows the server detail when code execution fails', async () => {
    server.use(
      http.post('/api/run/', () =>
        HttpResponse.json(
          { detail: 'Container overloaded' },
          { status: 500 },
        ),
      ),
    );
    render(<LessonPage />);
    fireEvent.click(await screen.findByRole('button', { name: 'Run' }));
    const err = await screen.findByTestId('run-error');
    expect(err.textContent).toBe(
      'Execution failed (500): Container overloaded',
    );
  });

  it('falls back to the status text when the failure has no detail', async () => {
    server.use(
      http.post('/api/run/', () =>
        HttpResponse.json({}, { status: 500 }),
      ),
    );
    render(<LessonPage />);
    fireEvent.click(await screen.findByRole('button', { name: 'Run' }));
    const err = await screen.findByTestId('run-error');
    expect(err.textContent).toMatch(/^Execution failed \(500\): /);
    expect(err.textContent).not.toContain('{}');
  });
});
