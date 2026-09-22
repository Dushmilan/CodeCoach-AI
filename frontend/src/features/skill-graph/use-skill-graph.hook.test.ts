import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useSkillGraph } from './use-skill-graph.hook';
import { skillGraphService } from './skill-graph.service';

vi.mock('./skill-graph.service', () => ({
  skillGraphService: {
    getGraph: vi.fn(),
    syncFromSubmissions: vi.fn(),
  },
}));

const mockedGetGraph = vi.mocked(skillGraphService.getGraph);

describe('useSkillGraph', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    mockedGetGraph.mockResolvedValue({ nodes: [], edges: [] } as never);
  });

  it('fetches the graph on mount', async () => {
    renderHook(() => useSkillGraph());
    await waitFor(() => expect(mockedGetGraph).toHaveBeenCalledTimes(1));
  });

  it('refetches on question-solved so the graph updates after a solve (#277)', async () => {
    renderHook(() => useSkillGraph());
    await waitFor(() => expect(mockedGetGraph).toHaveBeenCalledTimes(1));
    window.dispatchEvent(new CustomEvent('question-solved', { detail: { questionId: 'two-sum' } }));
    await waitFor(() => expect(mockedGetGraph).toHaveBeenCalledTimes(2));
  });
});
