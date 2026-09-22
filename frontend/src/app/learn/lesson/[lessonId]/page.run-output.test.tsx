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
  LessonChrome: () => null,
  ExerciseLessonLayout: (props: any) => (
    <div>
      <button onClick={() => props.onRunCode('')}>Run</button>
      {props.output ? <div data-testid="run-output">{props.output}</div> : null}
      {props.error ? <div data-testid="run-error">{props.error}</div> : null}
      {props.testResults ? (
        <div data-testid="test-results">{props.testResults.length}</div>
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
  starter_code: 'def solve():\n    pass',
  test_cases: null,
  question_id: 'q1',
  language: 'python',
};

const linkedQuestion = {
  id: 'q1',
  title: 'Echo',
  difficulty: 'easy',
  category: 'basics',
  description: 'Echo input',
  starter: { python: 'def solve():\n    pass', javascript: '', java: '' },
  examples: [],
  test_cases: [{ input: 'hello', expected_output: 'hello' }],
  hints: [],
  constraints: [],
  is_interactive: false,
};

describe('LessonPage exercise Run output (Issue #263)', () => {
  beforeEach(() => {
    mockUseLesson.mockReturnValue({ lesson, isLoading: false, error: null });
    server.use(
      http.get('/api/courses/lessons/:lessonId/adjacent', () =>
        HttpResponse.json({ prev_id: null, next_id: null }),
      ),
      http.get('/api/progress/:courseId', () =>
        HttpResponse.json({ completed_lessons: [] }),
      ),
      http.get('/api/questions/:id', () => HttpResponse.json(linkedQuestion)),
      // Echo stdin back as stdout: a raw empty-stdin run returns empty,
      // per-test-case runs return matching output.
      http.post('/api/run/', async ({ request }) => {
        const body = (await request.json()) as { stdin?: string };
        const stdin = body.stdin ?? '';
        return HttpResponse.json({
          stdout: stdin,
          stderr: '',
          exit_code: 0,
          language: 'python',
          version: '3.10.0',
        });
      }),
    );
  });

  it('shows test-case results instead of an empty panel for linked exercises', async () => {
    render(<LessonPage />);
    fireEvent.click(await screen.findByRole('button', { name: 'Run' }));
    const output = await screen.findByTestId('run-output');
    expect(output.textContent).toMatch(/PASSED/i);
    const results = await screen.findByTestId('test-results');
    expect(results.textContent).toBe('1');
  });
});
