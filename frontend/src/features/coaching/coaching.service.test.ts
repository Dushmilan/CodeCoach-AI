import { describe, it, expect, vi, beforeEach } from 'vitest';
import { CoachingService } from './coaching.service';
import { HttpClient } from '@/lib/http-client';

function createMockHttp(): HttpClient {
  return {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  };
}

describe('CoachingService', () => {
  let http: ReturnType<typeof createMockHttp>;
  let service: CoachingService;

  beforeEach(() => {
    http = createMockHttp();
    service = new CoachingService(http);
    const store: Record<string, string> = {};
    vi.stubGlobal('localStorage', {
      getItem: vi.fn((key: string) => store[key] ?? null),
      setItem: vi.fn((key: string, value: string) => {
        store[key] = value;
      }),
      removeItem: vi.fn((key: string) => {
        delete store[key];
      }),
      clear: vi.fn(() => {
        for (const k in store) delete store[k];
      }),
      get length() {
        return Object.keys(store).length;
      },
      key: vi.fn((i: number) => Object.keys(store)[i] ?? null),
    });
  });

  describe('getCoachResponse', () => {
    const defaultArgs = {
      problem: 'Two Sum',
      language: 'python',
      code: 'def two_sum(nums, target): pass',
      message: 'Help me optimize',
      mode: 'hint',
      difficulty: 'medium',
    };

    it('posts to /api/coach/ with request body', async () => {
      vi.mocked(http.post).mockResolvedValue({
        response: 'Try using a hash map',
        structured: null,
      });

      const result = await service.getCoachResponse(
        defaultArgs.problem,
        defaultArgs.language,
        defaultArgs.code,
        defaultArgs.message,
        defaultArgs.mode,
        defaultArgs.difficulty,
      );

      expect(http.post).toHaveBeenCalledWith('/api/coach/', {
        problem: 'Two Sum',
        code: 'def two_sum(nums, target): pass',
        message: 'Help me optimize',
        mode: 'hint',
        language: 'python',
        difficulty: 'medium',
        surface: 'questions',
      });
      expect(result.response).toBe('Try using a hash map');
      expect(result.structured).toBeNull();
    });

    it('passes initial_code when provided', async () => {
      vi.mocked(http.post).mockResolvedValue({
        response: 'Animating your code',
        structured: null,
      });

      await service.getCoachResponse(
        defaultArgs.problem,
        defaultArgs.language,
        defaultArgs.code,
        defaultArgs.message,
        'animate',
        defaultArgs.difficulty,
        undefined,
        undefined,
        'def two_sum(nums, target):\n    pass',
      );

      expect(http.post).toHaveBeenCalledWith(
        '/api/coach/',
        expect.objectContaining({
          mode: 'animate',
          initial_code: 'def two_sum(nums, target):\n    pass',
        }),
      );
    });

    it('omits initial_code when not provided', async () => {
      vi.mocked(http.post).mockResolvedValue({
        response: 'Ok',
        structured: null,
      });

      await service.getCoachResponse(
        defaultArgs.problem,
        defaultArgs.language,
        defaultArgs.code,
        defaultArgs.message,
        defaultArgs.mode,
        defaultArgs.difficulty,
      );

      expect(vi.mocked(http.post).mock.calls[0][1]).not.toHaveProperty(
        'initial_code',
      );
    });

    it('defaults difficulty to medium', async () => {
      vi.mocked(http.post).mockResolvedValue({
        response: 'Okay',
        structured: null,
      });

      await service.getCoachResponse(
        defaultArgs.problem,
        defaultArgs.language,
        defaultArgs.code,
        defaultArgs.message,
        defaultArgs.mode,
      );

      expect(http.post).toHaveBeenCalledWith(
        '/api/coach/',
        expect.objectContaining({ difficulty: 'medium' }),
      );
    });

    it('does not pass request options to http.post', async () => {
      vi.mocked(http.post).mockResolvedValue({
        response: 'Sure',
        structured: null,
      });

      await service.getCoachResponse(
        defaultArgs.problem,
        defaultArgs.language,
        defaultArgs.code,
        defaultArgs.message,
        defaultArgs.mode,
      );

      expect(vi.mocked(http.post).mock.calls[0][2]).toBeUndefined();
    });

    it('returns structured response when present', async () => {
      const structuredData = {
        summary: 'Great work',
        hints: ['Try a hash map'],
        code_review: null,
        complexity_analysis: null,
        suggestions: [],
        edge_cases: [],
        explanation: null,
        debug_help: null,
      };

      vi.mocked(http.post).mockResolvedValue({
        response: 'Here is your hint',
        structured: structuredData,
      });

      const result = await service.getCoachResponse(
        defaultArgs.problem,
        defaultArgs.language,
        defaultArgs.code,
        defaultArgs.message,
        defaultArgs.mode,
      );

      expect(result.structured).toEqual(structuredData);
      expect(result.structured?.hints).toContain('Try a hash map');
    });

    it('converts mode and language to lowercase', async () => {
      vi.mocked(http.post).mockResolvedValue({
        response: 'Ok',
        structured: null,
      });

      await service.getCoachResponse('Test', 'Python', 'code', 'help', 'HINT');

      expect(http.post).toHaveBeenCalledWith(
        '/api/coach/',
        expect.objectContaining({
          mode: 'hint',
          language: 'python',
        }),
      );
    });

    it('throws when http.post fails', async () => {
      vi.mocked(http.post).mockRejectedValue(new Error('Network error'));

      await expect(
        service.getCoachResponse(
          defaultArgs.problem,
          defaultArgs.language,
          defaultArgs.code,
          defaultArgs.message,
          defaultArgs.mode,
        ),
      ).rejects.toThrow('Network error');
    });

    it('defaults surface to questions', async () => {
      vi.mocked(http.post).mockResolvedValue({
        response: 'Ok',
        structured: null,
      });

      await service.getCoachResponse(
        defaultArgs.problem,
        defaultArgs.language,
        defaultArgs.code,
        defaultArgs.message,
        defaultArgs.mode,
      );

      expect(http.post).toHaveBeenCalledWith(
        '/api/coach/',
        expect.objectContaining({ surface: 'questions' }),
      );
    });

    it('forwards learn surface for curriculum chat', async () => {
      vi.mocked(http.post).mockResolvedValue({
        response: 'Ok',
        structured: null,
      });

      await service.getCoachResponse(
        defaultArgs.problem,
        defaultArgs.language,
        defaultArgs.code,
        defaultArgs.message,
        defaultArgs.mode,
        defaultArgs.difficulty,
        'Loops 101',
        undefined,
        undefined,
        'learn',
      );

      expect(http.post).toHaveBeenCalledWith(
        '/api/coach/',
        expect.objectContaining({
          surface: 'learn',
          lesson_context: 'Loops 101',
        }),
      );
    });

    it('throws HttpError when server returns error', async () => {
      const httpError = new Error('Request failed: 429 Too Many Requests');
      vi.mocked(http.post).mockRejectedValue(httpError);

      await expect(
        service.getCoachResponse(
          defaultArgs.problem,
          defaultArgs.language,
          defaultArgs.code,
          defaultArgs.message,
          defaultArgs.mode,
        ),
      ).rejects.toThrow('Request failed: 429 Too Many Requests');
    });
  });

  describe('warmContext', () => {
    it('posts question_id to /api/coach/warm', async () => {
      vi.mocked(http.post).mockResolvedValue({
        status: 'warming',
        warmed: true,
        ttl: 60,
      });

      const result = await service.warmContext('two-sum');

      expect(http.post).toHaveBeenCalledWith(
        '/api/coach/warm',
        { question_id: 'two-sum' },
        undefined,
      );
      expect(result).toEqual({ status: 'warming', warmed: true, ttl: 60 });
    });

    it('forwards AbortSignal when provided', async () => {
      vi.mocked(http.post).mockResolvedValue({
        status: 'warming',
        warmed: true,
        ttl: 60,
      });
      const ctrl = new AbortController();

      await service.warmContext('two-sum', ctrl.signal);

      expect(http.post).toHaveBeenCalledWith(
        '/api/coach/warm',
        { question_id: 'two-sum' },
        { signal: ctrl.signal },
      );
    });

    it('degrades to error status instead of throwing', async () => {
      vi.mocked(http.post).mockRejectedValue(new Error('429'));

      const result = await service.warmContext('two-sum');

      expect(result).toEqual({ status: 'error', warmed: false, ttl: 0 });
    });
  });
});
