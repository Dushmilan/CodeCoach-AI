"use client";

import { AnimationScript, AnimationStep } from "@/types";
import { cn } from "@/lib/utils";

interface CodeComparisonVisualizerProps {
  script: AnimationScript;
  step: AnimationStep;
  stepIndex: number;
}

function CodeColumn({
  label,
  lines,
  activeLine,
  isMatch,
  isMismatch,
}: {
  label: string;
  lines: string[];
  activeLine: number | null;
  isMatch: boolean;
  isMismatch: boolean;
}) {
  const lineClass = (index: number) => {
    if (index !== activeLine) {
      return "border-transparent text-muted-foreground/60";
    }
    if (isMatch) {
      return "border-emerald-500/50 bg-emerald-500/10 text-emerald-300";
    }
    if (isMismatch) {
      return "border-destructive/50 bg-destructive/10 text-destructive-foreground/90";
    }
    return "border-primary/40 bg-primary/10 text-foreground/90";
  };

  return (
    <div className="flex-1 min-w-0">
      <div className="mb-2 text-[10px] uppercase tracking-wider text-muted-foreground/50">
        {label}
      </div>
      <pre className="max-h-48 overflow-y-auto overflow-x-auto rounded-lg border border-white/[0.06] bg-black/20 p-3 font-mono text-xs leading-5">
        {lines.map((line, i) => (
          <div
            key={i}
            data-active-line={i === activeLine ? "true" : "false"}
            className={cn(
              "whitespace-pre border-l-2 py-px pl-2 transition-colors",
              lineClass(i),
            )}
          >
            <span className="mr-3 select-none tabular-nums text-muted-foreground/30">
              {i + 1}
            </span>
            {line || " "}
          </div>
        ))}
      </pre>
    </div>
  );
}

export function CodeComparisonVisualizer({
  script,
  step,
}: CodeComparisonVisualizerProps) {
  const data = script.data ?? {};
  const userCode = Array.isArray(data.user_code)
    ? (data.user_code as string[])
    : [];
  const solutionCode = Array.isArray(data.solution_code)
    ? (data.solution_code as string[])
    : [];
  const activeLine =
    typeof step.line_number === "number" ? step.line_number - 1 : null;
  const isMatch = step.result === "match";
  const isMismatch = step.result === "mismatch";

  return (
    <div className="space-y-3 rounded-2xl border border-white/[0.06] bg-white/[0.02] p-4">
      <div className="flex items-center justify-between">
        <span className="inline-flex items-center rounded-full bg-white/[0.05] px-2.5 py-1 text-xs font-medium text-foreground/80">
          {script.title || "Your code vs the solution"}
        </span>
        {isMismatch && (
          <span className="text-[10px] text-destructive/80">
            Differs from the solution
          </span>
        )}
        {isMatch && (
          <span className="text-[10px] text-emerald-300/80">
            Matches the solution
          </span>
        )}
      </div>

      <div className="flex gap-3">
        <CodeColumn
          label="Your code"
          lines={userCode}
          activeLine={activeLine}
          isMatch={isMatch}
          isMismatch={isMismatch}
        />
        <CodeColumn
          label="Solution code"
          lines={solutionCode}
          activeLine={activeLine}
          isMatch={isMatch}
          isMismatch={isMismatch}
        />
      </div>

      <p
        aria-live="polite"
        className="text-xs leading-relaxed text-muted-foreground/70"
      >
        {step.narration}
      </p>
    </div>
  );
}
