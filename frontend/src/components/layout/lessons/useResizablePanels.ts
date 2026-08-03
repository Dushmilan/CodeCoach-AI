'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

export type PanelBoundary = 'description' | 'reading' | 'ai';

export interface ResizablePanelsOptions {
  storageKey: string;
  percentageBoundary?: PanelBoundary;
  /** Override to share AI-open state across lessons; defaults to per-lesson. */
  aiOpenStorageKey?: string;
  defaults?: {
    descriptionWidth?: number;
    aiWidth?: number;
    isAIOpen?: boolean;
  };
  bounds?: {
    descriptionMinPct?: number;
    descriptionMaxPct?: number;
    readingMinPct?: number;
    readingMaxPct?: number;
    aiMinPx?: number;
    aiMaxPx?: number;
  };
}

const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value));

export function useResizablePanels({
  storageKey,
  percentageBoundary = 'description',
  aiOpenStorageKey = '',
  defaults = {},
  bounds = {},
}: ResizablePanelsOptions) {
  const {
    descriptionWidth: defaultDescriptionWidth = 40,
    aiWidth: defaultAiWidth = 400,
    isAIOpen: defaultIsAIOpen = true,
  } = defaults;

  const {
    descriptionMinPct = 24,
    descriptionMaxPct = 55,
    readingMinPct = 45,
    readingMaxPct = 80,
    aiMinPx = 300,
    aiMaxPx = 560,
  } = bounds;

  const percentMinPct = percentageBoundary === 'reading' ? readingMinPct : descriptionMinPct;
  const percentMaxPct = percentageBoundary === 'reading' ? readingMaxPct : descriptionMaxPct;

  const storagePrefix = `codecoach:lesson:${storageKey}`;

  // AI-open state defaults to per-lesson persistence (consistent with the
  // width keys). Callers can override with aiOpenStorageKey for a global panel.
  const aiOpenKey = aiOpenStorageKey || `${storagePrefix}:ai-open`;

  const readStoredNumber = useCallback((key: string, fallback: number) => {
    if (typeof window === 'undefined') return fallback;
    const raw = window.localStorage.getItem(key);
    if (raw === null) return fallback;
    const value = Number(raw);
    return Number.isFinite(value) ? value : fallback;
  }, []);

  const [descriptionWidth, setDescriptionWidth] = useState<number>(() =>
    clamp(
      readStoredNumber(`${storagePrefix}:desc-width`, defaultDescriptionWidth),
      percentMinPct,
      percentMaxPct,
    ),
  );

  const [aiWidth, setAiWidth] = useState<number>(() =>
    clamp(readStoredNumber(`${storagePrefix}:ai-width`, defaultAiWidth), aiMinPx, aiMaxPx),
  );

  const [isAIOpen, setIsAIOpen] = useState<boolean>(() => {
    if (typeof window === 'undefined') return defaultIsAIOpen;
    const raw = window.localStorage.getItem(aiOpenKey);
    if (raw === null) return defaultIsAIOpen;
    return raw === '1';
  });

  const [isDragging, setIsDragging] = useState(false);
  const [activeBoundary, setActiveBoundary] = useState<PanelBoundary | null>(null);

  const workspaceRef = useRef<HTMLDivElement | null>(null);

  const latestRef = useRef({ descriptionWidth, aiWidth, isAIOpen });
  const dragStateRef = useRef<{
    boundary: PanelBoundary;
    startX: number;
    startDescriptionPct: number;
    startAiWidth: number;
  } | null>(null);

  useEffect(() => {
    latestRef.current = { descriptionWidth, aiWidth, isAIOpen };
  }, [descriptionWidth, aiWidth, isAIOpen]);

  const startDrag = useCallback(
    (boundary: PanelBoundary) => (e: React.MouseEvent) => {
      e.preventDefault();
      dragStateRef.current = {
        boundary,
        startX: e.clientX,
        startDescriptionPct: latestRef.current.descriptionWidth,
        startAiWidth: latestRef.current.aiWidth,
      };
      setActiveBoundary(boundary);
      setIsDragging(true);
    },
    [],
  );

  const resizeBy = useCallback(
    (boundary: PanelBoundary, deltaX: number) => {
      const container = workspaceRef.current;
      if (!container) return;
      if (boundary === percentageBoundary) {
        const containerWidth = container.clientWidth || 1;
        const deltaPct = (deltaX / containerWidth) * 100;
        setDescriptionWidth((prev) => clamp(prev + deltaPct, percentMinPct, percentMaxPct));
      } else {
        setAiWidth((prev) => clamp(prev - deltaX, aiMinPx, aiMaxPx));
      }
    },
    [percentageBoundary, percentMinPct, percentMaxPct, aiMinPx, aiMaxPx],
  );

  const openAI = useCallback(() => setIsAIOpen(true), []);
  const closeAI = useCallback(() => setIsAIOpen(false), []);

  useEffect(() => {
    if (!isDragging || !dragStateRef.current) return;

    const handleMouseMove = (e: MouseEvent) => {
      const drag = dragStateRef.current;
      const container = workspaceRef.current;
      if (!drag || !container) return;
      const containerWidth = container.clientWidth || 1;
      const deltaX = e.clientX - drag.startX;
      if (drag.boundary === percentageBoundary) {
        setDescriptionWidth(
          clamp(
            drag.startDescriptionPct + (deltaX / containerWidth) * 100,
            percentMinPct,
            percentMaxPct,
          ),
        );
      } else {
        setAiWidth(clamp(drag.startAiWidth - deltaX, aiMinPx, aiMaxPx));
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      setActiveBoundary(null);
      dragStateRef.current = null;
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, percentageBoundary, percentMinPct, percentMaxPct, aiMinPx, aiMaxPx]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (isDragging) return;
    const { descriptionWidth: dW, aiWidth: aW, isAIOpen: open } = latestRef.current;
    window.localStorage.setItem(`${storagePrefix}:desc-width`, String(dW));
    window.localStorage.setItem(`${storagePrefix}:ai-width`, String(aW));
    window.localStorage.setItem(aiOpenKey, open ? '1' : '0');
  }, [descriptionWidth, aiWidth, isAIOpen, isDragging, storagePrefix, aiOpenKey]);

  return {
    descriptionWidth,
    aiWidth,
    isAIOpen,
    isDragging,
    activeBoundary,
    workspaceRef,
    startDrag,
    resizeBy,
    openAI,
    closeAI,
  };
}
