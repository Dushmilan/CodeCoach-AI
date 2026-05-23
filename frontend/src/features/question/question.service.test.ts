import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QuestionService } from './question.service';
import { HttpClient } from '@/lib/http-client';

function createMockHttp(): HttpClient {
  return {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  };
}

describe('QuestionService', () => {
  let http: ReturnType<typeof createMockHttp>;
  let service: QuestionService;

  beforeEach(() => {
    http = createMockHttp();
    service = new QuestionService(http);
  });

  describe('getQuestions', () => {
    it('calls GET /api/questions with no-store cache', async () => {
      vi.mocked(http.get).mockResolvedValue({ questions: [] });

      await service.getQuestions();

      expect(http.get).toHaveBeenCalledWith('/api/questions', {
        cache: 'no-store',
      });
    });

    it('returns questions array from response', async () => {
      const mockQuestions = [
        { id: '1', title: 'Two Sum', difficulty: 'easy', category: 'arrays', company_tags: [] },
        { id: '2', title: 'Add Two Numbers', difficulty: 'medium', category: 'linked-list', company_tags: [] },
      ];
      vi.mocked(http.get).mockResolvedValue({ questions: mockQuestions });

      const result = await service.getQuestions();

      expect(result).toHaveLength(2);
      expect(result[0].id).toBe('1');
      expect(result[1].title).toBe('Add Two Numbers');
    });

    it('returns empty array when response has no questions field', async () => {
      vi.mocked(http.get).mockResolvedValue({});

      const result = await service.getQuestions();

      expect(result).toEqual([]);
    });

    it('returns empty array when questions is null', async () => {
      vi.mocked(http.get).mockResolvedValue({ questions: null });

      const result = await service.getQuestions();

      expect(result).toEqual([]);
    });

    it('throws when http.get fails', async () => {
      vi.mocked(http.get).mockRejectedValue(new Error('Server error'));

      await expect(service.getQuestions()).rejects.toThrow('Server error');
    });

    it('throws HttpError on 500', async () => {
      vi.mocked(http.get).mockRejectedValue(new Error('Request failed: 500 Internal Server Error'));

      await expect(service.getQuestions()).rejects.toThrow('Request failed: 500');
    });
  });

  describe('getQuestion', () => {
    it('calls GET /api/questions/:id with no-store cache', async () => {
      vi.mocked(http.get).mockResolvedValue({
        id: '1',
        title: 'Two Sum',
        difficulty: 'easy',
        category: 'arrays',
        company_tags: [],
        description: '...',
        starter: { python: '', javascript: '', java: '' },
        examples: [],
        test_cases: [],
        hints: [],
        solution: '',
        time_complexity: '',
        space_complexity: '',
      });

      await service.getQuestion('1');

      expect(http.get).toHaveBeenCalledWith('/api/questions/1', {
        cache: 'no-store',
      });
    });

    it('returns full question data', async () => {
      const mockQuestion = {
        id: '42',
        title: 'Test',
        difficulty: 'hard' as const,
        category: 'dp',
        company_tags: ['Google'],
        description: 'Solve this problem',
        starter: { python: 'def solve():', javascript: 'function solve() {}', java: 'class Solution {}' },
        examples: [{ input: '1', output: '1' }],
        test_cases: [{ input: '1', expected_output: '1' }],
        hints: [],
        solution: 'def solve(): pass',
        time_complexity: 'O(n)',
        space_complexity: 'O(1)',
      };
      vi.mocked(http.get).mockResolvedValue(mockQuestion);

      const result = await service.getQuestion('42');

      expect(result.id).toBe('42');
      expect(result.description).toBe('Solve this problem');
      expect(result.test_cases).toHaveLength(1);
      expect(result.company_tags).toContain('Google');
      expect(result.starter.python).toBe('def solve():');
    });

    it('throws when http.get fails for individual question', async () => {
      vi.mocked(http.get).mockRejectedValue(new Error('Not found'));

      await expect(service.getQuestion('999')).rejects.toThrow('Not found');
    });
  });
});
