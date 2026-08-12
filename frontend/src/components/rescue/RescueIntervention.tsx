"use client";

import { RescueCheckpoint, RescueTier } from "@/features/rescue/rescue.types";
import { ProblemFlowMap } from "./ProblemFlowMap";

interface RescueInterventionProps {
  tier: RescueTier;
  checkpoints: RescueCheckpoint[];
  isSuppressed?: boolean;
  onLeaveMeAlone: () => void;
  onResume: () => void;
  onRequestCoachHelp: () => void;
  onReplan: () => void;
  onContinue: () => void;
}

export function RescueIntervention({
  tier,
  checkpoints,
  isSuppressed = false,
  onLeaveMeAlone,
  onResume,
  onRequestCoachHelp,
  onReplan,
  onContinue,
}: RescueInterventionProps) {
  if (tier === "none") return null;

  const tierLabel =
    tier === "t1" ? "It looks like you're stuck" : tier === "t2" ? "Still stuck?" : "Let's rethink";

  const tierDescription =
    tier === "t1"
      ? "You've been on this problem for a while. Here's exactly where your code stands."
      : tier === "t2"
        ? "Want a targeted hint from the AI coach about the failing test?"
        : "Maybe a fresh approach will unblock you — or try an easier next step.";

  return (
    <div
      data-testid="rescue-intervention"
      className="fixed bottom-4 right-4 z-50 w-80 max-w-[calc(100vw-2rem)]"
    >
      <div className="rounded-2xl bg-card ring-1 ring-white/15 shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/5 bg-white/[0.03]">
          <div>
            <div className="text-xs font-semibold text-foreground">
              {tierLabel}
            </div>
            <div className="text-[10px] text-muted-foreground/60">
              {tierDescription}
            </div>
          </div>
          <button
            onClick={isSuppressed ? onResume : onLeaveMeAlone}
            className="text-[10px] text-muted-foreground/50 hover:text-foreground transition-colors px-2 py-1 rounded hover:bg-white/5"
          >
            {isSuppressed ? "Resume rescue" : "Leave me alone"}
          </button>
        </div>

        <div className="px-4 py-3 max-h-72 overflow-y-auto">
          <ProblemFlowMap checkpoints={checkpoints} />
        </div>

        <div className="flex flex-col gap-1.5 px-4 py-3 border-t border-white/5">
          {tier === "t2" && (
            <button
              onClick={onRequestCoachHelp}
              className="text-xs font-medium text-foreground bg-emerald-500/15 hover:bg-emerald-500/25 ring-1 ring-emerald-500/30 rounded-lg px-3 py-2 transition-colors text-left"
            >
              Ask the AI coach about this failing test
            </button>
          )}
          {tier === "t3" && (
            <button
              onClick={onReplan}
              className="text-xs font-medium text-foreground bg-violet-500/15 hover:bg-violet-500/25 ring-1 ring-violet-500/30 rounded-lg px-3 py-2 transition-colors text-left"
            >
              Re-plan my path — suggest a smaller next step
            </button>
          )}
          <button
            onClick={onContinue}
            className="text-xs font-medium text-muted-foreground bg-white/[0.03] hover:bg-white/[0.07] ring-1 ring-white/10 rounded-lg px-3 py-2 transition-colors text-left"
          >
            I&apos;m still working on it
          </button>
        </div>
      </div>
    </div>
  );
}
