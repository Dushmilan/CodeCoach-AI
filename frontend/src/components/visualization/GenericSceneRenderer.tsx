"use client";

import { useMemo } from "react";
import type { AnimationStep, MotionOp, SceneShape } from "@/types";
import type { VisualizerProps } from "./AnimationScriptRenderer";
import { TOKENS } from "./animationTokens";

// Validator bounds (mirrored, never clamped — violations stay visible).
const BOUND_X = 960;
const BOUND_Y = 540;
const BASE_W = BOUND_X * 2;
const BASE_H = BOUND_Y * 2;
const FULL_VIEWBOX = `-${BOUND_X} -${BOUND_Y} ${BASE_W} ${BASE_H}`;
const MIN_DURATION = 0.1;
const MAX_DURATION = 5.0;

interface Badge {
  time: string;
  space: string;
}

interface Camera {
  action?: string;
  region?: unknown;
  element?: unknown;
}

type StepExtras = {
  badge?: Badge;
  camera?: Camera;
};

interface ShapeOverride {
  fill?: string;
  stroke?: string;
  x?: number;
  y?: number;
  scale?: number;
  rotate?: number;
  text?: string;
  opacity?: number;
  duration: number;
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function toMoveTarget(to: unknown): { x: number; y: number } | null {
  if (Array.isArray(to) && isFiniteNumber(to[0]) && isFiniteNumber(to[1])) {
    return { x: to[0] as number, y: to[1] as number };
  }
  if (typeof to === "object" && to !== null) {
    const { x, y } = to as { x?: unknown; y?: unknown };
    if (isFiniteNumber(x) && isFiniteNumber(y)) return { x, y };
  }
  return null;
}

function inBounds(x: number, y: number): boolean {
  return Math.abs(x) <= BOUND_X && Math.abs(y) <= BOUND_Y;
}

function applyMotions(
  shapes: SceneShape[],
  motions: MotionOp[],
): Map<string, ShapeOverride> {
  const known = new Set(shapes.map((s) => s.id));
  const overrides = new Map<string, ShapeOverride>();
  for (const motion of motions) {
    const target = (motion as MotionOp).target;
    if (!known.has(target)) {
      console.warn(`GenericSceneRenderer: unknown motion target "${target}" — skipping op`);
      continue;
    }
    const duration = (motion as MotionOp).duration;
    if (!isFiniteNumber(duration) || duration < MIN_DURATION || duration > MAX_DURATION) {
      console.warn(
        `GenericSceneRenderer: invalid duration ${String(duration)} for target "${target}" — skipping op`,
      );
      continue;
    }
    const op = (motion as MotionOp).op;
    const to = (motion as MotionOp).to;
    const prev = overrides.get(target) ?? { duration };
    const next: ShapeOverride = { ...prev, duration: Math.max(prev.duration, duration) };
    switch (op) {
      case "fill":
        if (typeof to !== "string") {
          console.warn(`GenericSceneRenderer: invalid fill target for "${target}" — skipping op`);
          continue;
        }
        next.fill = to;
        break;
      case "stroke":
        if (typeof to !== "string") {
          console.warn(`GenericSceneRenderer: invalid stroke target for "${target}" — skipping op`);
          continue;
        }
        next.stroke = to;
        break;
      case "move": {
        const dest = toMoveTarget(to);
        if (!dest || !inBounds(dest.x, dest.y)) {
          console.warn(`GenericSceneRenderer: out-of-range move for "${target}" — skipping op`);
          continue;
        }
        next.x = dest.x;
        next.y = dest.y;
        break;
      }
      case "scale":
        if (!isFiniteNumber(to)) {
          console.warn(`GenericSceneRenderer: invalid scale for "${target}" — skipping op`);
          continue;
        }
        next.scale = to;
        break;
      case "rotate":
        if (!isFiniteNumber(to)) {
          console.warn(`GenericSceneRenderer: invalid rotate for "${target}" — skipping op`);
          continue;
        }
        next.rotate = to;
        break;
      case "label":
        if (typeof to !== "string") {
          console.warn(`GenericSceneRenderer: invalid label for "${target}" — skipping op`);
          continue;
        }
        next.text = to;
        break;
      case "appear":
        next.opacity = 1;
        break;
      case "disappear":
        next.opacity = 0;
        break;
      default:
        console.warn(`GenericSceneRenderer: unknown motion op "${op}" for "${target}" — skipping op`);
        continue;
    }
    overrides.set(target, next);
  }
  return overrides;
}

function mergeOverrides(
  into: Map<string, ShapeOverride>,
  from: Map<string, ShapeOverride>,
): void {
  from.forEach((override, target) => {
    const prev = into.get(target);
    into.set(
      target,
      prev
        ? {
            ...prev,
            ...override,
            duration: Math.max(prev.duration, override.duration),
          }
        : override,
    );
  });
}

function stepShapes(step: unknown): SceneShape[] {
  const shapes = (step as { shapes?: unknown })?.shapes;
  return Array.isArray(shapes) ? (shapes as SceneShape[]) : [];
}

function stepMotions(step: unknown): MotionOp[] {
  const motion = (step as { motion?: unknown })?.motion;
  return Array.isArray(motion) ? (motion as MotionOp[]) : [];
}

function resolveCenter(
  shapes: SceneShape[],
  camera: Camera | undefined,
): { x: number; y: number } | null {
  if (!camera) return null;
  if (camera.action !== "focus" && camera.action !== "panTo") return null;
  if (typeof camera.element === "string") {
    const found = shapes.find((s) => s.id === camera.element);
    if (found && isFiniteNumber(found.x) && isFiniteNumber(found.y)) {
      return { x: found.x, y: found.y };
    }
    return null;
  }
  if (Array.isArray(camera.region)) {
    // Numeric entries are element indices, not shape positions: the shapes
    // array interleaves cells and value labels, so resolve via cell_/node_
    // ids and skip anything unresolvable (never clamp — violations stay
    // visible to the backend validator).
    const byId = new Map(shapes.map((s) => [s.id, s]));
    const pts = (camera.region as unknown[])
      .map((r) => {
        if (typeof r === "number") {
          return byId.get(`cell_${r}`) ?? byId.get(`node_${r}`) ?? null;
        }
        if (typeof r === "string") return byId.get(r) ?? null;
        return null;
      })
      .filter((s): s is SceneShape => !!s && isFiniteNumber(s.x) && isFiniteNumber(s.y));
    if (pts.length === 0) return null;
    const x = pts.reduce((sum, s) => sum + (s.x as number), 0) / pts.length;
    const y = pts.reduce((sum, s) => sum + (s.y as number), 0) / pts.length;
    return { x, y };
  }
  return null;
}

function pointsToAttr(points: [number, number][] | undefined): string {
  if (!Array.isArray(points)) return "";
  return points
    .filter((p) => Array.isArray(p) && isFiniteNumber(p[0]) && isFiniteNumber(p[1]))
    .map((p) => `${p[0]},${p[1]}`)
    .join(" ");
}

export function GenericSceneRenderer({ script, step, stepIndex }: VisualizerProps) {
  // Cumulative scene state (#240): planners emit shapes only in the intro
  // beat, so resolving camera/motion targets against the current step's
  // shapes leaves every action beat with an empty scene, a dead camera,
  // and skipped motions. Fold shapes by id over all beats up to the
  // current one (current beat wins) and fold motions in play order so
  // highlights persist across beats.
  const sceneShapes = useMemo(() => {
    const byId = new Map<string, SceneShape>();
    const steps = Array.isArray(script?.steps) ? script.steps : [];
    const end = Math.max(0, Math.min(stepIndex, steps.length - 1));
    for (let i = 0; i <= end; i++) {
      for (const shape of stepShapes(steps[i])) {
        if (shape?.id) byId.set(shape.id, shape);
      }
    }
    for (const shape of stepShapes(step)) {
      if (shape?.id) byId.set(shape.id, shape);
    }
    return Array.from(byId.values());
  }, [script, step, stepIndex]);
  const motions = useMemo(() => stepMotions(step), [step]);

  const overrides = useMemo(() => {
    const folded = new Map<string, ShapeOverride>();
    const steps = Array.isArray(script?.steps) ? script.steps : [];
    const end = Math.max(0, Math.min(stepIndex, steps.length - 1));
    for (let i = 0; i <= end; i++) {
      mergeOverrides(folded, applyMotions(sceneShapes, stepMotions(steps[i])));
    }
    mergeOverrides(folded, applyMotions(sceneShapes, motions));
    return folded;
  }, [script, motions, sceneShapes, stepIndex]);

  const extras = (step ?? {}) as AnimationStep & StepExtras;
  const badge = extras.badge;
  const camera = extras.camera;

  const viewBox = useMemo(() => {
    const center = resolveCenter(sceneShapes, camera);
    if (!center) return FULL_VIEWBOX;
    const zoom = TOKENS.camera.zoom_focus;
    const w = BASE_W / zoom;
    const h = BASE_H / zoom;
    return `${center.x - w / 2} ${center.y - h / 2} ${w} ${h}`;
  }, [sceneShapes, camera]);

  const narration = step?.narration ?? script?.title ?? "animation";

  return (
    <div className="space-y-3" data-testid={`generic-scene-${stepIndex}`}>
      <style>{`@media (prefers-reduced-motion: reduce) { .a1-shape { transition: none !important; } }`}</style>
      <svg viewBox={viewBox} role="img" aria-label={narration} className="h-auto w-full">
        {sceneShapes.map((shape) => {
          const override = overrides.get(shape.id);
          const duration = override?.duration ?? TOKENS.duration.highlight;
          const style = { transition: `all ${duration}s ease-out` };
          const key = shape.id;
          switch (shape.type) {
            case "text": {
              const label = (override?.text ?? shape.text ?? "").slice(0, TOKENS.maxLabel);
              return (
                <text
                  key={key}
                  x={override?.x ?? shape.x ?? 0}
                  y={override?.y ?? shape.y ?? 0}
                  fontSize={shape.fontSize ?? TOKENS.cellLabelSize}
                  fill={override?.fill ?? shape.fill ?? TOKENS.palette.text}
                  opacity={override?.opacity ?? shape.opacity ?? 1}
                  textAnchor="middle"
                  dominantBaseline="central"
                  className="a1-shape"
                  style={style}
                >
                  {label}
                </text>
              );
            }
            case "rect": {
              const w = shape.width ?? 0;
              const h = shape.height ?? 0;
              const cx = override?.x ?? shape.x ?? 0;
              const cy = override?.y ?? shape.y ?? 0;
              const transform =
                override?.scale != null || override?.rotate != null
                  ? `translate(${cx} ${cy}) scale(${override.scale ?? 1}) rotate(${override.rotate ?? 0}) translate(${-cx} ${-cy})`
                  : undefined;
              return (
                <rect
                  key={key}
                  x={cx - w / 2}
                  y={cy - h / 2}
                  width={w}
                  height={h}
                  fill={override?.fill ?? shape.fill ?? TOKENS.palette.idle_fill}
                  stroke={override?.stroke ?? shape.stroke ?? TOKENS.palette.idle_stroke}
                  opacity={override?.opacity ?? shape.opacity ?? 1}
                  transform={transform}
                  className="a1-shape"
                  style={style}
                />
              );
            }
            case "ellipse": {
              const rx = shape.radius ?? (shape.width ?? 0) / 2;
              const ry = shape.radius ?? (shape.height ?? 0) / 2;
              const cx = override?.x ?? shape.x ?? 0;
              const cy = override?.y ?? shape.y ?? 0;
              const transform =
                override?.scale != null || override?.rotate != null
                  ? `translate(${cx} ${cy}) scale(${override.scale ?? 1}) rotate(${override.rotate ?? 0}) translate(${-cx} ${-cy})`
                  : undefined;
              return (
                <ellipse
                  key={key}
                  cx={cx}
                  cy={cy}
                  rx={rx}
                  ry={ry}
                  fill={override?.fill ?? shape.fill ?? TOKENS.palette.idle_fill}
                  stroke={override?.stroke ?? shape.stroke ?? TOKENS.palette.idle_stroke}
                  opacity={override?.opacity ?? shape.opacity ?? 1}
                  transform={transform}
                  className="a1-shape"
                  style={style}
                />
              );
            }
            case "line": {
              const pts = shape.points;
              if (!Array.isArray(pts) || pts.length < 2) return null;
              const [[x1, y1], [x2, y2]] = pts as [number, number][];
              if (!isFiniteNumber(x1) || !isFiniteNumber(y1) || !isFiniteNumber(x2) || !isFiniteNumber(y2)) {
                return null;
              }
              return (
                <line
                  key={key}
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke={override?.stroke ?? shape.stroke ?? TOKENS.palette.muted}
                  strokeWidth={shape.lineWidth ?? 2}
                  opacity={override?.opacity ?? shape.opacity ?? 1}
                  className="a1-shape"
                  style={style}
                />
              );
            }
            case "polygon": {
              const attr = pointsToAttr(shape.points);
              if (!attr) return null;
              return (
                <polygon
                  key={key}
                  points={attr}
                  fill={override?.fill ?? shape.fill ?? TOKENS.palette.idle_fill}
                  stroke={override?.stroke ?? shape.stroke ?? TOKENS.palette.idle_stroke}
                  opacity={override?.opacity ?? shape.opacity ?? 1}
                  className="a1-shape"
                  style={style}
                />
              );
            }
            default:
              return null;
          }
        })}
      </svg>
      <p aria-live="polite" className="text-sm text-foreground/80">
        {step?.narration}
      </p>
      {badge ? (
        <div aria-label="Complexity" className="flex gap-2 text-xs text-muted-foreground">
          <span className="rounded-full border border-white/[0.06] px-2 py-0.5">{badge.time}</span>
          <span className="rounded-full border border-white/[0.06] px-2 py-0.5">{badge.space}</span>
        </div>
      ) : null}
    </div>
  );
}
