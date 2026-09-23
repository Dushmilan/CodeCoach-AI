import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '@/mocks/server';
import { useCoaching } from '@/features/coaching/coaching.hook';
import { useLesson } from '@/features/curriculum/use-curriculum.hook';
import LessonLoading from './loading';
import LessonPage from './page';
import type { LessonSummary, Question } from '@/types';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

// Exercise lessons render the code editor container; stub it so the page test
// never loads Monaco from a CDN (mirrors ExerciseLessonLayout.test.tsx).
vi.mock('@/components/layout/elements', () => ({
  CodeEditorContainer: () => <div data-testid="mock-editor" />,
  AIChatPanelContainer: () => <div data-testid="mock-ai-panel" />,
}));

vi.mock('next/navigation', () => ({
  useParams: () => ({ lessonId: 'test-lesson' }),
}));

vi.mock('@/providers', () => ({
  useAuth: () => ({
    isAuthenticated: true,
    isHydrated: true,
    user: {
      id: 'test-id',
      username: 'testuser',
      email: 'test@example.com',
      created_at: '2025-01-01T00:00:00Z',
      is_active: true,
    },
  }),
}));

const mockSendMessage = vi.hoisted(() => vi.fn());
const mockGenerateAnimation = vi.hoisted(() => vi.fn());

vi.mock('@/features/coaching/coaching.hook', () => ({
  useCoaching: () => ({
    messages: [],
    isTyping: false,
    sendMessage: mockSendMessage,
  }),
}));

vi.mock('@/features/animation/animation.service', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/features/animation/animation.service')>();
  return {
    ...actual,
    animationService: { generateAnimation: mockGenerateAnimation },
  };
});

const mockUseLesson = vi.hoisted(() => vi.fn());

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
  useLesson: mockUseLesson,
}));

describe('LessonPage AI coaching wiring', () => {
  beforeEach(() => {
    mockSendMessage.mockClear();
    mockGenerateAnimation.mockReset();
    mockGenerateAnimation.mockResolvedValue({
      title: 'Searching for 4',
      data: { values: [5, 1, 2, 3, 4, 6], target: 4 },
      steps: [
        {
          narration: '5 is not the target.',
          shapes: [
            {
              id: 'cell_0',
              type: 'rect',
              x: -240,
              y: 0,
              width: 88,
              height: 88,
              fill: '#1e293b',
            },
          ],
          motion: [{ target: 'cell_0', op: 'appear', duration: 0.3 }],
        },
        {
          narration: 'Moving on.',
          motion: [{ target: 'cell_0', op: 'move', to: [0, 0], duration: 0.3 }],
        },
        {
          narration: 'Found 4!',
          shapes: [
            {
              id: 'ptr',
              type: 'polygon',
              x: 0,
              y: -80,
              points: [
                [-12, -30],
                [0, -60],
                [12, -30],
              ],
              fill: '#facc15',
            },
          ],
          motion: [{ target: 'ptr', op: 'appear', duration: 0.3 }],
        },
      ],
    });
    mockUseLesson.mockReturnValue({
      lesson: { ...lesson, starter_code: 'print(1)' },
      isLoading: false,
      error: null,
    });
    server.use(
      http.get('/api/courses/lessons/:lessonId/adjacent', () =>
        HttpResponse.json({ prev_id: null, next_id: null }),
      ),
    );
  });

  it('renders the Animate launcher outside the chat panel', async () => {
    localStorage.setItem('codecoach:workspace:ai-open:theory', '1');
    render(<LessonPage />);
    const animate = await screen.findByRole('button', { name: /animate solution/i });
    expect(animate).toBeInTheDocument();
  });

  it('opens the animation viewer modal and posts the generated animation', async () => {
    localStorage.setItem('codecoach:workspace:ai-open:theory', '1');
    const openSpy = vi.spyOn(window, 'open');

    const { unmount } = render(<LessonPage />);
    const animate = await screen.findByRole('button', { name: /animate solution/i });
    await userEvent.click(animate);

    // An in-app modal opens (no popup window) with a tokenised viewer iframe.
    const dialog = await screen.findByRole('dialog');
    expect(openSpy).not.toHaveBeenCalled();
    const iframe = within(dialog).getByTitle(
      'Animation viewer',
    ) as HTMLIFrameElement;
    const src = iframe.getAttribute('src');
    expect(src).toMatch(/viewer\.html\?token=/);
    const token = new URL(src!).searchParams.get('token');
    expect(token).toBeTruthy();

    const postMessage = vi
      .spyOn(iframe.contentWindow!, 'postMessage')
      .mockImplementation(() => {});
    fireEvent.load(iframe);

    await vi.waitFor(() => {
      expect(postMessage).toHaveBeenCalledTimes(1);
    });
    const [payload, targetOrigin] = postMessage.mock.calls[0];
    expect(payload.type).toBe('CODECOACH_ANIMATION');
    expect(payload.token).toBe(token);
    expect(payload.animation.title).toBe('Searching for 4');
    expect(payload.animation.data.target).toBe(4);
    expect(targetOrigin).toBe('http://localhost:9000');

    // The chat must never receive the animate request.
    expect(mockSendMessage).not.toHaveBeenCalled();
    openSpy.mockRestore();
    // Tear down the phase-tick interval synchronously so it cannot flush a
    // state update into a later test (intermittent act() unhandled error).
    unmount();
  });
});

describe('LessonPage layout width', () => {
  beforeEach(() => {
    mockUseLesson.mockReturnValue({
      lesson,
      isLoading: false,
      error: null,
    });
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

// --- Issue #308: loader cleanup guards --------------------------------------
// The progress / linked-question / adjacent-lessons effects used to dispatch
// state from promise callbacks with no cancelled/cleanup guard. When a promise
// settled after the effect was cleaned up (dependency change or unmount) the
// stale response was applied to the wrong lesson — and, after vitest tears the
// jsdom environment down, react-dom dev read the destroyed `window`
// (getCurrentEventPriority) and the ReferenceError escaped as an unhandled
// rejection, failing CI with every test green.

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

const exerciseLesson: LessonSummary = {
  ...lesson,
  id: 'ex-1',
  type: 'exercise',
  starter_code: 'print(1)',
  question_id: 'q1',
};

function linkedQuestionFixture(id: string, description: string): Question {
  return {
    id,
    title: `Question ${id}`,
    difficulty: 'easy',
    category: 'basics',
    company_tags: [],
    description,
    starter: {
      python: 'print(1)',
      javascript: '',
      java: '',
      cpp: '',
      c: '',
      go: '',
      rust: '',
      typescript: '',
    },
    examples: [],
    test_cases: [],
    hints: [],
    solution: '',
    time_complexity: '',
    space_complexity: '',
  };
}

describe('LessonPage loader cleanup guards (issue #308)', () => {
  beforeEach(() => {
    localStorage.removeItem('codecoach:workspace:ai-open:theory');
    mockUseLesson.mockReturnValue({
      lesson,
      isLoading: false,
      error: null,
    });
    server.use(
      http.get('/api/courses/lessons/:lessonId/adjacent', () =>
        HttpResponse.json({ prev_id: null, next_id: null }),
      ),
    );
  });

  it('ignores a stale progress response for a course the effect has left', async () => {
    const staleProgress = deferredResponse();
    server.use(
      http.get('/api/progress/:courseId', ({ params }) =>
        params.courseId === 'c1'
          ? staleProgress.promise
          : HttpResponse.json({ completed_lessons: [] }),
      ),
    );

    const { rerender } = render(<LessonPage />);
    await screen.findByRole('button', { name: /mark complete/i });

    // The lesson moves to another course while the c1 request is in flight.
    mockUseLesson.mockReturnValue({
      lesson: { ...lesson, course_id: 'c2' },
      isLoading: false,
      error: null,
    });
    rerender(<LessonPage />);
    await flushAsyncWork();

    // The stale c1 response arrives after its effect run was cleaned up.
    staleProgress.resolve(HttpResponse.json({ completed_lessons: ['test-lesson'] }));
    await flushAsyncWork();

    // It must not mark this lesson complete.
    expect(screen.queryByRole('button', { name: /^completed$/i })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /mark complete|completed/i })).toHaveTextContent(
      'Mark Complete',
    );
  });

  it('keeps the completed state when a stale progress request fails', async () => {
    const staleProgress = deferredResponse();
    server.use(
      http.get('/api/progress/:courseId', ({ params }) =>
        params.courseId === 'c1'
          ? staleProgress.promise
          : HttpResponse.json({ completed_lessons: ['test-lesson'] }),
      ),
    );

    const { rerender } = render(<LessonPage />);
    await screen.findByRole('button', { name: /mark complete/i });

    // Move to a course whose progress marks this lesson complete.
    mockUseLesson.mockReturnValue({
      lesson: { ...lesson, course_id: 'c2' },
      isLoading: false,
      error: null,
    });
    rerender(<LessonPage />);
    await screen.findByRole('button', { name: /^completed$/i });

    // The stale c1 request fails — this is the page.tsx:96
    // `.catch(() => setIsCompleted(false))` branch from the CI stack trace.
    staleProgress.resolve(HttpResponse.json({ detail: 'boom' }, { status: 500 }));
    await flushAsyncWork();

    expect(screen.getByRole('button', { name: /^completed$/i })).toBeInTheDocument();
  });

  it('dispatches nothing after unmount when the response settles past jsdom teardown', async () => {
    const progress = deferredResponse();
    server.use(http.get('/api/progress/:courseId', () => progress.promise));

    const { unmount } = render(<LessonPage />);
    await screen.findByRole('button', { name: /mark complete/i });
    unmount();

    const escaped: unknown[] = [];
    const track = (reason: unknown) => escaped.push(reason);
    process.on('unhandledRejection', track);
    // Emulate vitest tearing down the jsdom environment (window gone) before
    // the in-flight /api/progress request settles — the exact CI failure mode:
    // a post-cleanup dispatch makes react-dom dev read `window`, and the
    // resulting error escapes the promise chain as an unhandled rejection.
    vi.stubGlobal('window', undefined);
    try {
      progress.resolve(HttpResponse.json({ detail: 'boom' }, { status: 500 }));
      await new Promise((resolve) => setTimeout(resolve, 100));
      expect(escaped).toEqual([]);
    } finally {
      vi.unstubAllGlobals();
      process.off('unhandledRejection', track);
    }
  });

  it('ignores a stale linked-question response after the lesson changes', async () => {
    const staleQuestion = deferredResponse();
    server.use(
      http.get('/api/questions/:questionId', ({ params }) =>
        params.questionId === 'q1'
          ? staleQuestion.promise
          : HttpResponse.json(linkedQuestionFixture('q2', 'Fresh problem body')),
      ),
      http.get('/api/progress/:courseId', () =>
        HttpResponse.json({ completed_lessons: [] }),
      ),
    );

    mockUseLesson.mockReturnValue({
      lesson: exerciseLesson,
      isLoading: false,
      error: null,
    });
    const { rerender } = render(<LessonPage />);
    await screen.findByText('Coding Exercise');

    // The lesson switches to a different linked question while q1 is in flight.
    mockUseLesson.mockReturnValue({
      lesson: { ...exerciseLesson, question_id: 'q2' },
      isLoading: false,
      error: null,
    });
    rerender(<LessonPage />);
    await screen.findByText('Fresh problem body');

    staleQuestion.resolve(
      HttpResponse.json(linkedQuestionFixture('q1', 'Stale problem body')),
    );
    await flushAsyncWork();

    expect(screen.queryByText('Stale problem body')).not.toBeInTheDocument();
    expect(screen.getByText('Fresh problem body')).toBeInTheDocument();
  });

  it('ignores a stale adjacent-lessons response after the lesson changes', async () => {
    const staleAdjacent = deferredResponse();
    server.use(
      http.get('/api/courses/lessons/:lessonId/adjacent', ({ params }) =>
        params.lessonId === 'lesson-a'
          ? staleAdjacent.promise
          : HttpResponse.json({ prev_id: null, next_id: null }),
      ),
      http.get('/api/progress/:courseId', () =>
        HttpResponse.json({ completed_lessons: [] }),
      ),
    );

    mockUseLesson.mockReturnValue({
      lesson: { ...lesson, id: 'lesson-a', title: 'Lesson A' },
      isLoading: false,
      error: null,
    });
    const { rerender, container } = render(<LessonPage />);
    await screen.findByText('Lesson A');

    mockUseLesson.mockReturnValue({
      lesson: { ...lesson, id: 'lesson-b', title: 'Lesson B' },
      isLoading: false,
      error: null,
    });
    rerender(<LessonPage />);
    await screen.findByText('Lesson B');
    await flushAsyncWork();

    staleAdjacent.resolve(
      HttpResponse.json({ prev_id: null, next_id: 'lesson-stale' }),
    );
    await flushAsyncWork();

    expect(
      container.querySelector('a[href="/learn/lesson/lesson-stale"]'),
    ).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: /back to course/i })).toBeInTheDocument();
  });
});
