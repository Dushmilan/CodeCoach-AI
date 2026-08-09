"use client";

import { Button } from "@/components/ui/button";
import { UsageInfo } from "./usage.types";

interface UsageBarProps {
  usage: UsageInfo | null;
  onUpgrade: () => void;
}

function progressWidth(used: number, limit: number): string {
  if (!limit) return "0%";
  const pct = Math.min(100, Math.round((used / limit) * 100));
  return `${pct}%`;
}

export function UsageBar({ usage, onUpgrade }: UsageBarProps) {
  if (!usage) return null;

  const isFree = usage.plan === "free";
  const usedPct = progressWidth(usage.daily_used, usage.daily_limit);
  const exhausted = usage.daily_remaining <= 0;

  return (
    <div className="px-4 py-3 border-b border-white/[0.04]">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[11px] text-muted-foreground/70 tracking-wide">
          Daily AI messages
        </span>
        <span className="text-[11px] text-muted-foreground/70 tracking-wide">
          {usage.daily_used} / {usage.daily_limit}
        </span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-white/[0.06] overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${
            exhausted ? "bg-red-500/70" : "bg-primary/70"
          }`}
          style={{ width: usedPct }}
        />
      </div>
      {isFree && (
        <div className="mt-2 flex items-center justify-between">
          <span className="text-[11px] text-muted-foreground/60">
            {usage.daily_remaining} remaining today
          </span>
          <Button
            variant="outline"
            size="sm"
            className="text-primary"
            onClick={onUpgrade}
          >
            Upgrade
          </Button>
        </div>
      )}
    </div>
  );
}