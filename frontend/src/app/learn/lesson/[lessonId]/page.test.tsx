import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '@/mocks/server';
import { useCoaching } from '@/features/coaching/coaching.hook';
import { useLesson } from '@/features/curriculum/use-curriculum.hook';
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
  useAuth: () => ({
    isAuthenticated: true,
    isHydrated: true,
    user: { plan: 'premium' },
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

    render(<LessonPage />);
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
