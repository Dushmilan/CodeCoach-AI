import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useCurriculum } from './use-curriculum.hook';
import { FetchClient } from '@/lib/fetch-client';

// Mock FetchClient
vi.mock('@/lib/fetch-client', () => {
  const MockFetchClient = vi.fn(function FetchClient() {
    return {
      get: vi.fn(),
      post: vi.fn(),
    };
  });
  return { FetchClient: MockFetchClient };
});

describe('useCurriculum', () => {
  it('should fetch courses', async () => {
    // Get the instance created inside useCurriculum
    const mockInstance = (FetchClient as any).mock.results[0].value;
    mockInstance.get.mockResolvedValue({ courses: [{ id: '1', title: 'Test' }] });
    
    const { result } = renderHook(() => useCurriculum());
    
    // Initially loading
    expect(result.current.isLoading).toBe(true);
    
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    
    expect(result.current.courses).toEqual([{ id: '1', title: 'Test' }]);
  });
});
