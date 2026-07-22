"use client";

import React, { useState, useRef, useCallback, useEffect } from "react";
import { cn } from "@/lib/utils";

interface PanelConfig {
  id: string;
  children: React.ReactNode;
  defaultSize: number;
  minSize: number;
}

interface ResizablePanelGroupProps {
  panels: PanelConfig[];
  className?: string;
  direction?: "horizontal" | "vertical";
}

export function ResizablePanelGroup({
  panels,
  className,
  direction = "horizontal",
}: ResizablePanelGroupProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [sizes, setSizes] = useState<number[]>([]);
  const [initialized, setInitialized] = useState(false);
  const [resizing, setResizing] = useState<{
    leftIdx: number;
    startX: number;
    startY: number;
    leftSize: number;
    rightSize: number;
    containerSize: number;
  } | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el || initialized) return;
    const rect = el.getBoundingClientRect();
    const containerSize = direction === "horizontal" ? rect.width : rect.height;
    if (containerSize <= 0) return;
    const initial = panels.map((p) => (containerSize * p.defaultSize) / 100);
    setSizes(initial);
    setInitialized(true);
  }, [panels, initialized, direction]);

  useEffect(() => {
    if (!initialized || !containerRef.current) return;
    const el = containerRef.current;
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const containerSize =
          direction === "horizontal"
            ? entry.contentBoxSize[0].inlineSize
            : entry.contentBoxSize[0].blockSize;
        if (containerSize <= 0) return;
        const total = sizes.reduce((a, b) => a + b, 0);
        if (total === 0) return;
        const scale = containerSize / total;
        setSizes((prev) => prev.map((s) => Math.round(s * scale)));
      }
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [initialized, sizes, direction]);

  const handleMouseDown = useCallback(
    (idx: number, e: React.MouseEvent) => {
      e.preventDefault();
      const el = containerRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const containerSize =
        direction === "horizontal" ? rect.width : rect.height;
      setResizing({
        leftIdx: idx,
        startX: e.clientX,
        startY: e.clientY,
        leftSize: sizes[idx],
        rightSize: sizes[idx + 1],
        containerSize,
      });
    },
    [sizes, direction],
  );

  useEffect(() => {
    if (!resizing) return;
    const handleMouseMove = (e: MouseEvent) => {
      const dx =
        direction === "horizontal"
          ? e.clientX - resizing.startX
          : e.clientY - resizing.startY;

      let newLeft = resizing.leftSize + dx;
      let newRight = resizing.rightSize - dx;

      const leftPanel = panels[resizing.leftIdx];
      const rightPanel = panels[resizing.leftIdx + 1];

      if (newLeft < leftPanel.minSize) {
        newRight -= leftPanel.minSize - newLeft;
        newLeft = leftPanel.minSize;
      }
      if (newRight < rightPanel.minSize) {
        newLeft -= rightPanel.minSize - newRight;
        newRight = rightPanel.minSize;
      }

      setSizes((prev) => {
        const next = [...prev];
        next[resizing.leftIdx] = newLeft;
        next[resizing.leftIdx + 1] = newRight;
        return next;
      });
    };
    const handleMouseUp = () => setResizing(null);
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [resizing, panels, direction]);

  if (panels.length === 0) return null;

  const isCol = direction === "vertical";

  return (
    <div
      ref={containerRef}
      className={cn(
        "flex w-full h-full overflow-hidden",
        isCol ? "flex-col" : "flex-row",
        className,
      )}
    >
      {resizing && (
        <div
          className={cn(
            "fixed inset-0 z-[9999] select-none",
            isCol ? "cursor-row-resize" : "cursor-col-resize",
          )}
        />
      )}
      {panels.map((panel, idx) => (
        <React.Fragment key={panel.id}>
          <div
            style={{
              flex: "0 0 auto",
              width:
                direction === "horizontal" && sizes[idx]
                  ? `${sizes[idx]}px`
                  : undefined,
              height:
                direction === "vertical" && sizes[idx]
                  ? `${sizes[idx]}px`
                  : undefined,
              minWidth: direction === "horizontal" ? panel.minSize : undefined,
              minHeight: direction === "vertical" ? panel.minSize : undefined,
            }}
            className="overflow-hidden"
          >
            {panel.children}
          </div>
          {idx < panels.length - 1 && (
            <div
              onMouseDown={(e) => handleMouseDown(idx, e)}
              className={cn(
                "flex-shrink-0 bg-transparent hover:bg-primary/20 transition-colors relative",
                isCol
                  ? "h-1 w-full cursor-row-resize"
                  : "w-1 h-full cursor-col-resize",
              )}
            >
              <div
                className={cn(
                  "absolute bg-white/10 rounded-full transition-all",
                  isCol
                    ? "left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-1 w-8 group-hover:h-2"
                    : "top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1 h-8 group-hover:w-2",
                )}
              />
            </div>
          )}
        </React.Fragment>
      ))}
    </div>
  );
}
