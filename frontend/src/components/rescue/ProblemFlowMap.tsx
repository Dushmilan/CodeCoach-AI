"use client";

import { cn } from "@/lib/utils";
import { RescueCheckpoint } from "@/features/rescue/rescue.types";
import { CheckCircle2, Circle, MapPin, XCircle } from "lucide-react";

interface ProblemFlowMapProps {
  checkpoints: RescueCheckpoint[];
  open?: boolean;
}

export function ProblemFlowMap({ checkpoints, open = true }: ProblemFlowMapProps) {
  if (!open) return null;

  return (
    <div
      data-testid="problem-flow-map"
      className="rounded-lg bg-background/60 ring-1 ring-white/10 p-3"
    >
      <div className="text-[10px] font-semibold tracking-wider text-muted-foreground/60 uppercase mb-2">
        Solution Flow Map
      </div>
      <ol className="flex flex-col gap-0">
        {checkpoints.map((cp) => {
          const isCurrent = cp.state === "current";
          const isError = cp.state === "error";
          return (
            <li key={cp.id} className="flex gap-2">
              <div className="flex flex-col items-center">
                {isCurrent ? (
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/20 ring-1 ring-emerald-400/50">
                    <MapPin className="h-3 w-3 text-emerald-300" />
                  </span>
                ) : cp.state === "passed" ? (
                  <span className="flex h-5 w-5 items-center justify-center text-emerald-400/80">
                    <CheckCircle2 className="h-4 w-4" />
                  </span>
                ) : isError ? (
                  <span className="flex h-5 w-5 items-center justify-center text-red-400">
                    <XCircle className="h-4 w-4" />
                  </span>
                ) : (
                  <span className="flex h-5 w-5 items-center justify-center text-muted-foreground/30">
                    <Circle className="h-4 w-4" />
                  </span>
                )}
                {cp.id !== checkpoints[checkpoints.length - 1].id && (
                  <span
                    className={cn(
                      "w-px flex-1 min-h-4",
                      cp.state === "passed"
                        ? "bg-emerald-400/30"
                        : "bg-white/10",
                    )}
                  />
                )}
              </div>
              <div className="pb-3 min-w-0">
                <div
                  className={cn(
                    "text-xs",
                    isCurrent
                      ? "text-emerald-200 font-medium"
                      : cp.state === "passed"
                        ? "text-muted-foreground/70 line-through decoration-emerald-400/40"
                        : "text-muted-foreground/50",
                  )}
                >
                  {isCurrent && (
                    <span className="mr-1.5 text-[9px] font-bold uppercase tracking-wider text-emerald-300">
                      You are here
                    </span>
                  )}
                  {cp.label}
                </div>
                {cp.detail && isCurrent && (
                  <div className="mt-0.5 text-[10px] font-mono text-amber-300/90">
                    {cp.detail}
                  </div>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
