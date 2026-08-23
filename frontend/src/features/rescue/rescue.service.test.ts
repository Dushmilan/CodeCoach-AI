import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RescueService } from './rescue.service';
import { HttpClient } from '@/lib/http-client';

function createMockHttp(): HttpClient {
  return {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  };
}

const sampleItem = {
  id: 'abc123',
  user_id: 'u1',
  question_id: 'two-sum',
  status: 'abandoned',
  first_abandoned_at: '2026-08-23T12:00:00Z',
  due_at: '2026-08-24T09:00:00Z',
  resurface_count: 0,
  last_intervention_at: null,
  created_at: '2026-08-23T12:00:00Z',
  updated_at: '2026-08-23T12:00:00Z',
};

describe('RescueService', () => {
  let http: ReturnType<typeof createMockHttp>;
  let service: RescueService;

  beforeEach(() => {
    http = createMockHttp();
    service = new RescueService(http);
  });

  describe('getDue', () => {
    it('calls GET /api/rescue/due without cache', async () => {
      vi.mocked(http.get).mockResolvedValue({ items: [sampleItem], total: 1 });

      await service.getDue();

      expect(http.get).toHaveBeenCalledWith('/api/rescue/due?limit=50', {
        cache: 'no-store',
      });
    });

    it('returns items and total from the payload', async () => {
      vi.mocked(http.get).mockResolvedValue({ items: [sampleItem], total: 1 });

      const result = await service.getDue();

      expect(result.total).toBe(1);
      expect(result.items[0].question_id).toBe('two-sum');
    });

    it('propagates errors (e.g. 401)', async () => {
      vi.mocked(http.get).mockRejectedValue(new Error('Request failed: 401'));

      await expect(service.getDue()).rejects.toThrow('401');
    });
  });

  describe('abandon', () => {
    it('posts the question id and client tz offset (east-positive)', async () => {
      // Callers convert from Date.getTimezoneOffset(): UTC+8 -> -(-480) = 480.
      vi.mocked(http.post).mockResolvedValue({ item: sampleItem });

      await service.abandon('two-sum', 480);

      expect(http.post).toHaveBeenCalledWith('/api/rescue/two-sum/abandon', {
        tz_offset_minutes: 480,
      });
    });

    it('returns a null item when the question was dismissed before', async () => {
      vi.mocked(http.post).mockResolvedValue({ item: null });

      const result = await service.abandon('two-sum');

      expect(result).toBeNull();
    });
  });

  describe('complete / dismiss', () => {
    it('posts to the complete endpoint', async () => {
      vi.mocked(http.post).mockResolvedValue({ item: null });

      await service.complete('two-sum');

      expect(http.post).toHaveBeenCalledWith('/api/rescue/two-sum/complete');
    });

    it('posts to the dismiss endpoint', async () => {
      vi.mocked(http.post).mockResolvedValue({ item: null });

      await service.dismiss('two-sum');

      expect(http.post).toHaveBeenCalledWith('/api/rescue/two-sum/dismiss');
    });
  });
});
