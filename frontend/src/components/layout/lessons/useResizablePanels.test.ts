import { describe, it, expect, beforeEach, vi } from 'vitest';
import { act, fireEvent, renderHook } from '@testing-library/react';
import { useResizablePanels } from './useResizablePanels';

const STORAGE_PREFIX = 'codecoach:lesson:test';

describe('useResizablePanels', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('applies defaults', () => {
    const { result } = renderHook(() => useResizablePanels({ storageKey: 'test' }));
    expect(result.current.descriptionWidth).toBe(40);
    expect(result.current.aiWidth).toBe(400);
    expect(result.current.isAIOpen).toBe(true);
  });

  it('clamps default sizes to bounds', () => {
    const { result } = renderHook(() =>
      useResizablePanels({
        storageKey: 'test',
        defaults: { descriptionWidth: 5, aiWidth: 10 },
      }),
    );
    expect(result.current.descriptionWidth).toBe(24);
    expect(result.current.aiWidth).toBe(300);
  });

  it('reads persisted values from localStorage', () => {
    window.localStorage.setItem(`${STORAGE_PREFIX}:desc-width`, '48');
    window.localStorage.setItem(`${STORAGE_PREFIX}:ai-width`, '500');
    window.localStorage.setItem(`${STORAGE_PREFIX}:ai-open`, '0');

    const { result } = renderHook(() => useResizablePanels({ storageKey: 'test' }));
    expect(result.current.descriptionWidth).toBe(48);
    expect(result.current.aiWidth).toBe(500);
    expect(result.current.isAIOpen).toBe(false);
  });

  it('persists ai open state to a per-lesson key by default', () => {
    const { result } = renderHook(() => useResizablePanels({ storageKey: 'test' }));
    act(() => result.current.closeAI());
    expect(window.localStorage.getItem(`${STORAGE_PREFIX}:ai-open`)).toBe('0');
    act(() => result.current.openAI());
    expect(window.localStorage.getItem(`${STORAGE_PREFIX}:ai-open`)).toBe('1');
  });

  it('persists ai open state to a custom key when provided', () => {
    const { result } = renderHook(() =>
      useResizablePanels({
        storageKey: 'test',
        aiOpenStorageKey: 'codecoach:workspace:ai-open',
      }),
    );
    act(() => result.current.closeAI());
    expect(window.localStorage.getItem('codecoach:workspace:ai-open')).toBe('0');
  });

  it('resizes description pane by delta clamped to bounds', () => {
    const { result } = renderHook(() => useResizablePanels({ storageKey: 'test' }));
    act(() => {
      result.current.workspaceRef.current = {
        clientWidth: 1000,
      } as HTMLDivElement;
    });
    act(() => result.current.resizeBy('description', 100));
    expect(result.current.descriptionWidth).toBe(50);
    act(() => result.current.resizeBy('description', 10000));
    expect(result.current.descriptionWidth).toBe(55);
  });

  it('resizes ai pane by delta clamped to bounds', () => {
    const { result } = renderHook(() => useResizablePanels({ storageKey: 'test' }));
    act(() => {
      result.current.workspaceRef.current = {
        clientWidth: 1000,
      } as HTMLDivElement;
    });
    act(() => result.current.resizeBy('ai', -100));
    expect(result.current.aiWidth).toBe(500);
    act(() => result.current.resizeBy('ai', 10000));
    expect(result.current.aiWidth).toBe(300);
  });

  it('resizes via drag and persists final width', () => {
    const { result } = renderHook(() => useResizablePanels({ storageKey: 'test' }));
    act(() => {
      result.current.workspaceRef.current = {
        clientWidth: 1000,
      } as HTMLDivElement;
    });

    act(() => {
      result.current.startDrag('description')({
        preventDefault: vi.fn(),
        clientX: 500,
      } as unknown as React.MouseEvent);
    });
    expect(result.current.isDragging).toBe(true);
    expect(result.current.activeBoundary).toBe('description');

    fireEvent.mouseMove(document, { clientX: 600 });
    expect(result.current.descriptionWidth).toBe(50);

    fireEvent.mouseUp(document);
    expect(result.current.isDragging).toBe(false);
    expect(result.current.activeBoundary).toBeNull();
    expect(window.localStorage.getItem(`${STORAGE_PREFIX}:desc-width`)).toBe('50');
  });

  it('tracks active boundary for the ai drag', () => {
    const { result } = renderHook(() => useResizablePanels({ storageKey: 'test' }));
    act(() => {
      result.current.startDrag('ai')({
        preventDefault: vi.fn(),
        clientX: 0,
      } as unknown as React.MouseEvent);
    });
    expect(result.current.activeBoundary).toBe('ai');
    fireEvent.mouseUp(document);
  });

  it('uses reading percentage bounds when percentageBoundary is reading', () => {
    const { result } = renderHook(() =>
      useResizablePanels({
        storageKey: 'test',
        percentageBoundary: 'reading',
        defaults: { descriptionWidth: 10 },
      }),
    );
    expect(result.current.descriptionWidth).toBe(45);
  });

  it('resizes the reading pane by delta clamped to reading bounds', () => {
    const { result } = renderHook(() =>
      useResizablePanels({
        storageKey: 'test',
        percentageBoundary: 'reading',
        defaults: { descriptionWidth: 60 },
      }),
    );
    act(() => {
      result.current.workspaceRef.current = {
        clientWidth: 1000,
      } as HTMLDivElement;
    });
    act(() => result.current.resizeBy('reading', 100));
    expect(result.current.descriptionWidth).toBe(70);
    act(() => result.current.resizeBy('reading', 10000));
    expect(result.current.descriptionWidth).toBe(80);
    act(() => result.current.resizeBy('reading', -10000));
    expect(result.current.descriptionWidth).toBe(45);
  });

  it('tracks the reading boundary as the active boundary', () => {
    const { result } = renderHook(() =>
      useResizablePanels({
        storageKey: 'test',
        percentageBoundary: 'reading',
      }),
    );
    act(() => {
      result.current.startDrag('reading')({
        preventDefault: vi.fn(),
        clientX: 0,
      } as unknown as React.MouseEvent);
    });
    expect(result.current.activeBoundary).toBe('reading');
    fireEvent.mouseUp(document);
  });
});
