'use client';

import { useCallback, useEffect, useState } from 'react';

export type WorkspaceMode = 'wide' | 'compact' | 'stacked';

export interface WorkspaceModeOptions {
  compactBelow?: number;
  stackedBelow?: number;
}

const getMode = (width: number, options: WorkspaceModeOptions): WorkspaceMode => {
  const { compactBelow = 1080, stackedBelow = 700 } = options;
  if (width > 0 && width < stackedBelow) return 'stacked';
  if (width > 0 && width < compactBelow) return 'compact';
  return 'wide';
};

/**
 * Observes the width of the element attached via the returned callback `ref`
 * and reports the matching workspace mode. Safe for SSR (mode starts "wide"
 * until the browser measures a real width) and works when the element mounts
 * asynchronously (e.g. after a page finishes loading).
 */
export function useWorkspaceMode<T extends HTMLElement = HTMLDivElement>(
  options: WorkspaceModeOptions = {},
) {
  const [element, setElement] = useState<T | null>(null);
  const [state, setState] = useState<{ width: number; isReady: boolean }>({
    width: 0,
    isReady: false,
  });

  const ref = useCallback((el: T | null) => setElement(el), []);

  const handleResize = useCallback((width: number) => setState({ width, isReady: true }), []);

  useEffect(() => {
    if (!element) return;

    const update = () => handleResize(element.getBoundingClientRect().width);
    update();

    if (typeof ResizeObserver === 'undefined') return;
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        handleResize(entry.contentRect.width);
      }
    });
    ro.observe(element);
    return () => ro.disconnect();
  }, [element, handleResize]);

  return {
    ref,
    mode: getMode(state.width, options) as WorkspaceMode,
    width: state.width,
    isReady: state.isReady,
  };
}
