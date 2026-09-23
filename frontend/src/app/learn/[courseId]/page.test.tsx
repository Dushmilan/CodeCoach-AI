import { act, render, screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { server } from '@/mocks/server';
import CoursePage from './page';
import type { CourseDetail } from '@/types';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    aside: ({ children, ...props }: any) => <aside {...props}>{children}</aside>,
    section: ({ children, ...props }: any) => <section {...props}>{children}</section>,
  },
}));

const mockParams = vi.hoisted(() => ({ courseId: 'c1' }));

vi.mock('next/navigation', () => ({
  useParams: () => ({ courseId: mockParams.courseId }),
}));

vi.mock('@/providers', () => ({
  useAuth: () => ({
    isAuthenticated: true,
    isHydrated: true,
    user: { id: 'u1', username: 'testuser' },
  }),
}));

const mockUseCourse = vi.hoisted(() => vi.fn());

vi.mock('@/features/curriculum/use-curriculum.hook', () => ({
  useCourse: mockUseCourse,
}));

function courseFixture(id: string): CourseDetail {
  return {
    id,
    title: `Course ${id}`,
    description: 'A course',
    language: 'python',
    icon: 'book',
    order: 1,
    modules: [
      {
        id: `${id}-m1`,
        course_id: id,
        title: 'Module 1',
        description: 'Module',
        order: 1,
        lessons: [
          {
            id: 'l1',
            course_id: id,
            module_id: `${id}-m1`,
            title: 'Lesson One',
            type: 'theory',
            content: 'content',
            order: 1,
            starter_code: null,
            test_cases: null,
            question_id: null,
            language: 'python',
          },
          {
            id: 'l2',
            course_id: id,
            module_id: `${id}-m1`,
            title: 'Lesson Two',
            type: 'exercise',
            content: 'content',
            order: 2,
            starter_code: null,
            test_cases: null,
            question_id: null,
            language: 'python',
          },
        ],
      },
    ],
  };
}

function deferredResponse() {
  let resolve!: (response: Response) => void;
  const promise = new Promise<Response>((res) => {
    resolve = res;
  });
  return { promise, resolve };
}

async function flushAsyncWork() {
  // Let the full MSW → fetch → effect-callback chain settle and React render.
  // 4 × 25ms of margin so slow CI runners can never observe a stale callback
  // later than the assertion (vacuous pass).
  await act(async () => {
    for (let i = 0; i < 4; i++) {
      await new Promise((resolve) => setTimeout(resolve, 25));
    }
  });
}

describe('CoursePage progress loader cleanup guard (issue #308)', () => {
  beforeEach(() => {
    mockParams.courseId = 'c1';
    mockUseCourse.mockReturnValue({
      course: courseFixture('c1'),
      isLoading: false,
      error: null,
    });
  });

  it('ignores a stale progress response after the course changes (issue #308)', async () => {
    const staleProgress = deferredResponse();
    server.use(
      http.get('/api/progress/:courseId', ({ params }) =>
        params.courseId === 'c1'
          ? staleProgress.promise
          : HttpResponse.json({ completed_lessons: [] }),
      ),
    );

    const { rerender } = render(<CoursePage />);
    // Two lessons, none completed yet.
    await screen.findByText('0/2');

    // Navigate to another course while the c1 progress request is in flight.
    mockParams.courseId = 'c2';
    mockUseCourse.mockReturnValue({
      course: courseFixture('c2'),
      isLoading: false,
      error: null,
    });
    rerender(<CoursePage />);
    await flushAsyncWork();

    // The stale c1 response arrives after its effect run was cleaned up; it
    // must not replace the c2 progress state.
    staleProgress.resolve(HttpResponse.json({ completed_lessons: ['l1'] }));
    await flushAsyncWork();

    expect(screen.getByText('0/2')).toBeInTheDocument();
    expect(screen.queryByText('1/2')).not.toBeInTheDocument();
  });
});
