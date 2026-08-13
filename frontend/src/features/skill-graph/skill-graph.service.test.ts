import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SkillGraphService } from './skill-graph.service';
import { HttpClient } from '@/lib/http-client';
import { RecommendedQuestion } from '@/types';

function createMockHttp(): HttpClient {
  return {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  };
}

const sampleRecommendation: RecommendedQuestion = {
  skill_slug: 'arrays',
  skill_name: 'Arrays',
  reason: 'weak_skill',
  reason_text: 'Arrays needs practice to become a strength.',
  question: {
    id: 'two-sum',
    title: 'Two Sum',
    difficulty: 'easy',
    category: 'arrays',
    company_tags: ['Google'],
    description: 'Find two numbers that add up to target',
    starter: {
      python: 'def two_sum(nums, target):',
      javascript: 'function twoSum(nums, target) {}',
      java: 'class Solution {}',
      cpp: '',
      c: '',
      go: '',
      rust: '',
      typescript: '',
    },
    examples: [{ input: '[2,7,11,15], 9', output: '[0,1]' }],
    test_cases: [{ input: '[2,7], 9', expected_output: '[0,1]' }],
    hints: ['Use a hash map'],
    solution: 'def two_sum(nums, target): return [0, 1]',
    time_complexity: 'O(n)',
    space_complexity: 'O(n)',
  },
};

describe('SkillGraphService', () => {
  let http: ReturnType<typeof createMockHttp>;
  let service: SkillGraphService;

  beforeEach(() => {
    http = createMockHttp();
    service = new SkillGraphService(http);
  });

  describe('getRecommendedQuestions', () => {
    it('calls GET /api/skills/me/recommended-questions with limit query', async () => {
      vi.mocked(http.get).mockResolvedValue([sampleRecommendation]);

      await service.getRecommendedQuestions(5);

      expect(http.get).toHaveBeenCalledWith(
        '/api/skills/me/recommended-questions?limit=5',
        { cache: 'no-store' },
      );
    });

    it('defaults the limit to 5 when omitted', async () => {
      vi.mocked(http.get).mockResolvedValue([]);

      await service.getRecommendedQuestions();

      expect(http.get).toHaveBeenCalledWith(
        '/api/skills/me/recommended-questions?limit=5',
        expect.anything(),
      );
    });

    it('returns the resolved recommendations from the response', async () => {
      vi.mocked(http.get).mockResolvedValue([sampleRecommendation]);

      const result = await service.getRecommendedQuestions(3);

      expect(result).toHaveLength(1);
      expect(result[0]).toEqual(sampleRecommendation);
      expect(result[0].question.id).toBe('two-sum');
    });

    it('returns empty array when the response is empty', async () => {
      vi.mocked(http.get).mockResolvedValue([]);

      const result = await service.getRecommendedQuestions(5);

      expect(result).toEqual([]);
    });

    it('throws when http.get fails', async () => {
      vi.mocked(http.get).mockRejectedValue(new Error('Server error'));

      await expect(service.getRecommendedQuestions(5)).rejects.toThrow(
        'Server error',
      );
    });

    it('throws HttpError on 401', async () => {
      vi.mocked(http.get).mockRejectedValue(
        new Error('Request failed: 401 Unauthorized'),
      );

      await expect(service.getRecommendedQuestions(5)).rejects.toThrow(
        'Request failed: 401',
      );
    });
  });
});
