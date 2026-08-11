"use client";

import { Pause, Play, RotateCcw, SkipBack, SkipForward } from "lucide-react";
import { ReactNode, useCallback, useEffect, useRef, useState } from "react";
import { AnimationStep } from "@/types";
import { cn } from "@/lib/utils";

const SPEEDS = [
  { label: "Slow", ms: 1400 },
  { label: "Normal", ms: 800 },
  { label: "Fast", ms: 350 },
];

interface AnimationPlayerProps {
  steps: AnimationStep[];
  children: (step: AnimationStep, index: number) => ReactNode;
  autoPauseOnMatch?: boolean;
}

export function AnimationPlayer({
  steps,
  children,
  autoPauseOnMatch = true,
}: AnimationPlayerProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speedMs, setSpeedMs] = useState(800);
  const currentRef = useRef(currentIndex);
  currentRef.current = currentIndex;

  const stepCount = steps.length;
  const currentStep = steps[currentIndex] as AnimationStep | undefined;

  useEffect(() => {
    if (!isPlaying) return;
    const timer = setInterval(() => {
      const next = currentRef.current + 1;
      if (next >= stepCount) {
        setIsPlaying(false);
        return;
      }
      setCurrentIndex(next);
      if (autoPauseOnMatch && steps[next]?.result === "match") {
        setIsPlaying(false);
      }
    }, speedMs);
    return () => clearInterval(timer);
  }, [isPlaying, speedMs, stepCount, steps, autoPauseOnMatch]);

  const togglePlay = useCallback(() => {
    if (!isPlaying && currentIndex >= stepCount - 1) {
      setCurrentIndex(0);
    }
    setIsPlaying((prev) => !prev);
  }, [isPlaying, currentIndex, stepCount]);

  const stepTo = useCallback((target: number) => {
    setCurrentIndex(Math.max(0, Math.min(target, stepCount - 1)));
    setIsPlaying(false);
  }, [stepCount]);

  const restart = useCallback(() => {
    setCurrentIndex(0);
    setIsPlaying(false);
  }, []);

  const progress = stepCount > 1 ? currentIndex / (stepCount - 1) : 1;

  return (
    <div className="space-y-3">
      <div>{currentStep ? children(currentStep, currentIndex) : null}</div>

      <div className="flex items-center gap-1.5">
        <button
          type="button"
          onClick={restart}
          aria-label="Restart animation"
          title="Restart"
          className="flex h-8 w-8 items-center justify-center rounded-full border border-white/[0.06] text-foreground/50 hover:bg-white/[0.04] hover:text-foreground/80 transition-all"
        >
          <RotateCcw width={13} height={13} />
        </button>
        <button
          type="button"
          onClick={() => stepTo(currentIndex - 1)}
          disabled={currentIndex === 0}
          aria-label="Previous step"
          title="Previous step"
          className="flex h-8 w-8 items-center justify-center rounded-full border border-white/[0.06] text-foreground/50 hover:bg-white/[0.04] hover:text-foreground/80 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <SkipBack width={13} height={13} />
        </button>
        <button
          type="button"
          onClick={togglePlay}
          aria-label={isPlaying ? "Pause animation" : "Play animation"}
          title={isPlaying ? "Pause" : "Play"}
          className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/15 text-primary hover:bg-primary/25 transition-all"
        >
          {isPlaying ? (
            <Pause width={14} height={14} fill="currentColor" />
          ) : (
            <Play width={14} height={14} fill="currentColor" className="ml-0.5" />
          )}
        </button>
        <button
          type="button"
          onClick={() => stepTo(currentIndex + 1)}
          disabled={currentIndex >= stepCount - 1}
          aria-label="Next step"
          title="Next step"
          className="flex h-8 w-8 items-center justify-center rounded-full border border-white/[0.06] text-foreground/50 hover:bg-white/[0.04] hover:text-foreground/80 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <SkipForward width={13} height={13} />
        </button>

        <div className="flex-1 flex items-center gap-2 mx-2">
          <div className="relative h-1 flex-1 rounded-full bg-white/[0.06] overflow-hidden">
            <div
              className="absolute inset-y-0 left-0 rounded-full bg-primary/60 transition-[width] duration-300"
              style={{ width: `${progress * 100}%` }}
            />
          </div>
          <span className="text-[10px] tabular-nums text-muted-foreground/50 whitespace-nowrap">
            {currentIndex + 1} / {stepCount}
          </span>
        </div>

        <div className="flex items-center gap-1">
          {SPEEDS.map((speed) => (
            <button
              key={speed.label}
              type="button"
              onClick={() => setSpeedMs(speed.ms)}
              aria-label={`Speed ${speed.label.toLowerCase()}`}
              className={cn(
                "px-2 py-1 rounded-full text-[10px] uppercase tracking-wider transition-all",
                speedMs === speed.ms
                  ? "bg-white/[0.08] text-foreground/80"
                  : "text-muted-foreground/40 hover:text-foreground/60",
              )}
            >
              {speed.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
