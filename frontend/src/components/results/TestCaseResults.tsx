"use client";

import { cn } from "@/lib/utils";
import { CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import { TestCaseResultView } from "@/features/code-execution/code-execution.types";

interface TestCaseResultsProps {
  results: TestCaseResultView[];
  title?: string;
}

function ValueCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <div className="text-[10px] font-semibold tracking-wider text-muted-foreground/60 uppercase mb-1">
        {label}
      </div>
      <pre
        className={cn(
          "whitespace-pre-wrap break-all rounded-md bg-white/[0.03] ring-1 ring-white/5 px-2 py-1.5 text-[11px] font-mono leading-relaxed",
          value === ""
            ? "text-muted-foreground/40 italic"
            : "text-foreground/90",
        )}
      >
        {value === "" ? "(empty)" : value}
      </pre>
    </div>
  );
}

export function TestCaseResults({ results, title }: TestCaseResultsProps) {
  const total = results.length;
  const passedCount = results.filter((r) => r.passed).length;
  const failedCount = total - passedCount;
  const allPassed = total > 0 && failedCount === 0;

  const bannerStyles = allPassed
    ? "bg-emerald-500/10 ring-emerald-500/30 text-emerald-300"
    : "bg-red-500/10 ring-red-500/30 text-red-300";

  return (
    <div className="flex flex-col gap-3">
      <div
        className={cn(
          "flex items-center gap-2 rounded-lg ring-1 px-3 py-2",
          bannerStyles,
        )}
        role="status"
        aria-label={`${passedCount} of ${total} tests passed`}
      >
        {allPassed ? (
          <CheckCircle2 className="h-4 w-4" />
        ) : (
          <XCircle className="h-4 w-4" />
        )}
        <span className="text-xs font-semibold tracking-wide">
          {title || "Test Results"}: {passedCount}/{total} passed
          {failedCount > 0 && ` · ${failedCount} failed`}
        </span>
      </div>

      <div className="flex flex-col gap-2">
        {results.map((result) => (
          <div
            key={result.index}
            className={cn(
              "rounded-lg ring-1 border bg-white/[0.02] overflow-hidden",
              result.passed
                ? "ring-emerald-500/20 border-emerald-500/10"
                : result.error
                  ? "ring-amber-500/30 border-amber-500/20"
                  : "ring-red-500/25 border-red-500/15",
            )}
          >
            <div className="flex items-center gap-2 px-3 py-2 border-b border-white/5">
              {result.error ? (
                <AlertCircle className="h-3.5 w-3.5 text-amber-400" />
              ) : result.passed ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              ) : (
                <XCircle className="h-3.5 w-3.5 text-red-400" />
              )}
              <span className="text-xs font-medium text-foreground/80">
                {result.testName}
              </span>
              <span
                className={cn(
                  "ml-auto text-[10px] font-semibold tracking-wider uppercase rounded-full px-2 py-0.5",
                  result.error
                    ? "bg-amber-500/10 text-amber-300 ring-1 ring-amber-500/30"
                    : result.passed
                      ? "bg-emerald-500/10 text-emerald-300 ring-1 ring-emerald-500/30"
                      : "bg-red-500/10 text-red-300 ring-1 ring-red-500/30",
                )}
              >
                {result.error ? "Error" : result.passed ? "Pass" : "Fail"}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 p-3">
              {result.error ? (
                <div className="sm:col-span-2">
                  <ValueCell label="Error" value={result.error} />
                </div>
              ) : result.hidden ? (
                <div className="sm:col-span-2 text-xs text-muted-foreground/50 italic py-1">
                  Hidden test case
                </div>
              ) : (
                <>
                  <ValueCell label="Input" value={result.input} />
                  <ValueCell label="Expected" value={result.expected} />
                  <ValueCell label="Actual" value={result.actual} />
                  {result.stderr ? (
                    <ValueCell label="Stderr" value={result.stderr} />
                  ) : null}
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
