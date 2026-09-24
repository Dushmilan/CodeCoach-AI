"use client";

import { useEffect, useRef } from "react";

export interface CodePaneProps {
  /** The instrument-free code the animation choreographs (`animated_code`). */
  code?: string | null;
  /** 1-based line of the active beat; null/absent highlights nothing. */
  activeLine?: number | null;
}

/**
 * Dual-pane code view (#284): shows the canonical solution with the line of
 * the currently animated beat highlighted, beside the visual scene. Renders
 * nothing when the script carries no code, so animations without
 * `animated_code` keep their exact existing layout.
 */
export function CodePane({ code, activeLine }: CodePaneProps) {
  const activeRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // Keep the highlighted line in view as the beat advances.
    activeRef.current?.scrollIntoView?.({ block: "nearest" });
  }, [activeLine]);

  if (!code) return null;

  const lines = code.split("\n");
  const isActiveLine = (lineNo: number): boolean =>
    typeof activeLine === "number" &&
    Number.isInteger(activeLine) &&
    lineNo === activeLine;

  return (
    <div
      data-testid="code-pane"
      className="min-w-0 rounded-2xl border border-white/[0.06] bg-white/[0.02] p-4"
    >
      <div className="mb-2 text-[10px] uppercase tracking-wider text-muted-foreground/50">
        Animated code
      </div>
      <pre className="max-h-[420px] overflow-auto font-mono text-xs leading-5">
        {lines.map((line, i) => {
          const lineNo = i + 1;
          const isActive = isActiveLine(lineNo);
          return (
            <div
              key={lineNo}
              ref={isActive ? activeRef : null}
              data-active-line={isActive ? "true" : "false"}
              className={
                isActive
                  ? "whitespace-pre border-l-2 border-primary/40 bg-primary/10 pl-2 transition-colors"
                  : "whitespace-pre border-l-2 border-transparent pl-2 text-muted-foreground/60"
              }
            >
              <span className="mr-3 select-none tabular-nums text-muted-foreground/30">
                {lineNo}
              </span>
              <span>{line || " "}</span>
            </div>
          );
        })}
      </pre>
    </div>
  );
}
