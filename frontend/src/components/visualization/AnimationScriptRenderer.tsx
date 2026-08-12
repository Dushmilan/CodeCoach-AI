"use client";

import { ComponentType } from "react";
import { AnimationScript, AnimationStep } from "@/types";
import { AnimationPlayer } from "./AnimationPlayer";
import { LinearSearchVisualizer } from "./LinearSearchVisualizer";

export interface VisualizerProps {
  script: AnimationScript;
  step: AnimationStep;
  stepIndex: number;
}

const VISUALIZERS: Record<string, ComponentType<VisualizerProps>> = {
  linear_search: LinearSearchVisualizer,
};

function FallbackTrace({ script }: { script: AnimationScript }) {
  return (
    <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-4 space-y-2">
      <div className="text-xs font-medium text-foreground/80">
        {script.title || "Algorithm trace"}
      </div>
      {script.steps.map((step, i) => (
        <div key={i} className="flex gap-2 text-xs text-muted-foreground/70">
          <span className="tabular-nums text-muted-foreground/40">{i + 1}.</span>
          <span>{step.narration}</span>
        </div>
      ))}
    </div>
  );
}

export function AnimationScriptRenderer({ script }: { script: AnimationScript }) {
  const steps = Array.isArray(script?.steps) ? script.steps : [];
  if (steps.length === 0) return null;

  const Visualizer = VISUALIZERS[script.type];
  if (!Visualizer) return <FallbackTrace script={script} />;

  return (
    <AnimationPlayer steps={steps}>
      {(step, index) => (
        <Visualizer script={script} step={step} stepIndex={index} />
      )}
    </AnimationPlayer>
  );
}
