"use client";

import { motion, useReducedMotion } from "framer-motion";
import { useMemo } from "react";
import { AnimationScript, AnimationStep } from "@/types";
import { cn } from "@/lib/utils";

interface LinearSearchVisualizerProps {
  script: AnimationScript;
  step: AnimationStep;
  stepIndex: number;
}

type CellStatus = "idle" | "visited" | "mismatch" | "match" | "checking";

function getCellStatuses(
  values: unknown[],
  steps: AnimationStep[],
  stepIndex: number,
): CellStatus[] {
  const statuses: CellStatus[] = values.map(() => "idle");
  for (let s = 0; s <= stepIndex; s++) {
    const st = steps[s];
    if (st.index == null) continue;
    const i = st.index;
    if (st.result === "match") statuses[i] = "match";
    else if (st.result === "mismatch") statuses[i] = "mismatch";
    else if (st.operation === "visit" || st.operation === "mark")
      statuses[i] = "visited";
    else if (st.operation === "compare") statuses[i] = "checking";
  }
  return statuses;
}

export function LinearSearchVisualizer({
  script,
  step,
  stepIndex,
}: LinearSearchVisualizerProps) {
  const reduceMotion = useReducedMotion();
  const values = useMemo(() => {
    const raw = script.data?.values;
    return Array.isArray(raw) ? (raw as unknown[]) : [];
  }, [script.data]);
  const target = script.data?.target as unknown;
  const rawSteps = script.steps;
  const steps = useMemo(() => rawSteps ?? [], [rawSteps]);

  const statuses = useMemo(
    () => getCellStatuses(values, steps, stepIndex),
    [values, steps, stepIndex],
  );
  const activeIndex = step.index ?? null;
  const isMatchFrame = step.result === "match";
  const isMismatchFrame = step.result === "mismatch";

  const cellClasses: Record<CellStatus, string> = {
    idle: "bg-white/[0.04] border-white/[0.06] text-foreground/50",
    visited: "bg-white/[0.03] border-white/[0.05] text-foreground/30",
    checking: "bg-primary/10 border-primary/40 text-foreground/90",
    mismatch: "bg-destructive/10 border-destructive/40 text-foreground/60",
    match:
      "bg-emerald-500/15 border-emerald-500/50 text-emerald-300 shadow-[0_0_18px_rgba(16,185,129,0.35)]",
  };

  return (
    <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 text-xs">
          <span className="inline-flex items-center rounded-full bg-white/[0.05] px-2.5 py-1 font-medium text-foreground/80">
            {script.title || "Linear Search"}
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground/50">
          <span>Target</span>
          <span className="inline-flex h-7 min-w-7 items-center justify-center rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-1.5 font-mono text-sm text-emerald-300">
            {String(target)}
          </span>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        {values.map((value, i) => {
          const status = statuses[i];
          const isActive = i === activeIndex;
          return (
            <motion.div
              key={i}
              layout
              initial={false}
              animate={{ scale: isActive ? 1.12 : 1 }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
              className={cn(
                "relative flex h-11 w-11 items-center justify-center overflow-hidden whitespace-nowrap rounded-xl border font-mono text-sm transition-colors duration-300",
                cellClasses[status],
              )}
            >
              {String(value)}

              {isActive && (
                <motion.div
                  key={`active-${stepIndex}`}
                  initial={{ opacity: 0, scale: 0.6 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.15 }}
                  className={cn(
                    "pointer-events-none absolute -inset-1 rounded-2xl",
                    isMatchFrame && "bg-emerald-500/15",
                    isMismatchFrame && "bg-destructive/15",
                    !isMatchFrame &&
                      !isMismatchFrame &&
                      "bg-primary/10",
                  )}
                />
              )}

              {isActive && !reduceMotion && (
                <motion.div
                  aria-hidden
                  className={cn(
                    "pointer-events-none absolute inset-0 rounded-xl",
                    isMatchFrame
                      ? "bg-emerald-500/20"
                      : isMismatchFrame
                        ? "bg-destructive/20"
                        : "bg-primary/20",
                  )}
                  animate={{ opacity: [0.25, 0.7, 0.25] }}
                  transition={{
                    duration: 1,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                />
              )}

              {status === "mismatch" && i !== activeIndex && (
                <span
                  aria-hidden
                  className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-destructive/30 text-[9px] text-destructive-foreground/70"
                >
                  ✕
                </span>
              )}
              {status === "match" && (
                <motion.span
                  aria-hidden
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute -top-1.5 -right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-emerald-500 text-[9px] font-bold text-white"
                >
                  ✓
                </motion.span>
              )}
            </motion.div>
          );
        })}
      </div>

      <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground/60">
        <span
          aria-live="polite"
          className={cn(
            "flex-1 leading-relaxed",
            isMatchFrame && "text-emerald-300/90",
            isMismatchFrame && "text-destructive/80",
          )}
        >
          {step.narration}
        </span>
        {activeIndex != null && (
          <span className="shrink-0 tabular-nums text-muted-foreground/40">
            i = {activeIndex}
          </span>
        )}
      </div>
    </div>
  );
}
