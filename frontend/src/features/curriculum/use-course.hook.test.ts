import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useCourse } from './use-curriculum.hook';

const mockGet = vi.fn();

vi.mock('@/lib/fetch-client', () => ({
  FetchClient: vi.fn(() => ({ get: mockGet })),
}));

describe('useCourse', () => {
  beforeEach(() => {
    mockGet.mockReset();
  });

  it('returns loading state initially', () => {
    mockGet.mockResolvedValue({ id: '1', title: 'Test' });
    const { result } = renderHook(() => useCourse('1'));
    expect(result.current.isLoading).toBe(true);
    expect(result.current.course).toBeNull();
  });

  it('fetches and returns course data', async () => {
    const courseData = { id: '1', title: 'Test Course', modules: [] };
    mockGet.mockResolvedValue(courseData);

    const { result } = renderHook(() => useCourse('1'));

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.course).toEqual(courseData);
    expect(mockGet).toHaveBeenCalledWith('/api/courses/1');
  });

  it('sets error when fetch fails', async () => {
    mockGet.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useCourse('1'));

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.course).toBeNull();
    expect(result.current.error).toBe('Network error');
  });

  it('refetches course data when refetch is called', async () => {
    mockGet.mockResolvedValue({ id: '1', title: 'Initial' });

    const { result } = renderHook(() => useCourse('1'));

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.course?.title).toBe('Initial');

    mockGet.mockResolvedValue({ id: '1', title: 'Refetched' });
    result.current.refetch();

    await waitFor(() => expect(result.current.course?.title).toBe('Refetched'));
  });

  it('does nothing when courseId is empty', () => {
    const { result } = renderHook(() => useCourse(''));
    expect(result.current.isLoading).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });
});
