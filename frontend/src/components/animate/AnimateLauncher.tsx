"use client";

import { Loader2, Play, RotateCcw, Sparkles } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  animationService,
  buildAnimateQuestion,
} from "@/features/animation/animation.service";
import { HttpError } from "@/lib/fetch-client";
import { Question } from "@/types";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export const ANIMATION_MESSAGE_TYPE = "CODECOACH_ANIMATION";
export const ANIMATION_ERROR_MESSAGE_TYPE = "CODECOACH_ANIMATION_ERROR";

export const ANIMATION_VIEWER_URL =
  process.env.NEXT_PUBLIC_ANIMATION_VIEWER_URL || "http://localhost:9000";

export const ANIMATION_VIEWER_PAGE = "/viewer.html";

const ANIMATE_502_MESSAGE = "Couldn't animate this problem. Try again.";

// Cosmetic phases shown while the backend traces, executes, and compiles the
// animation. Indeterminate progress — the real phase boundaries live server-side.
const GENERATION_PHASES = [
  "Compiling your solution",
  "Running the example input",
  "Rendering the animation",
];

const PHASE_TICK_MS = 1400;

function animationErrorMessage(err: unknown): string {
  if (err instanceof HttpError && err.status === 502) {
    return ANIMATE_502_MESSAGE;
  }
  return err instanceof Error
    ? err.message
    : "Failed to generate the animation.";
}

interface AnimateLauncherProps {
  problem: string;
  code: string;
  language: string;
  difficulty?: string;
  lessonContext?: string;
  initialCode?: string;
  question?: Question | null;
  disabled?: boolean;
}

export function AnimateLauncher({
  problem,
  code,
  language,
  difficulty = "medium",
  lessonContext,
  initialCode,
  question,
  disabled = false,
}: AnimateLauncherProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [phaseIndex, setPhaseIndex] = useState(0);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  // Guards against acting on a generation that outlived its dialog session
  // (dialog closed / unmounted while the request was in flight).
  const cancelledRef = useRef(false);

  useEffect(() => {
    return () => {
      cancelledRef.current = true;
    };
  }, []);

  const viewerUrl = useMemo(() => {
    if (!token) return null;
    const url = new URL(ANIMATION_VIEWER_PAGE, ANIMATION_VIEWER_URL);
    url.searchParams.set("token", token);
    return url.toString();
  }, [token]);

  useEffect(() => {
    if (!isLoading) return;
    setPhaseIndex(0);
    const id = window.setInterval(
      () => setPhaseIndex((index) => (index + 1) % GENERATION_PHASES.length),
      PHASE_TICK_MS,
    );
    return () => window.clearInterval(id);
  }, [isLoading]);

  const handleClick = useCallback(() => {
    if (!problem || !code || isLoading || disabled) return;
    cancelledRef.current = false;
    setError(null);
    setToken(crypto.randomUUID());
    setIsOpen(true);
  }, [problem, code, isLoading, disabled]);

  const handleIframeLoad = useCallback(async () => {
    const win = iframeRef.current?.contentWindow;
    if (!win || !token) return;
    setIsLoading(true);
    try {
      const animation = await animationService.generateAnimation({
        problem,
        code,
        language,
        difficulty,
        lessonContext,
        initialCode,
        question: buildAnimateQuestion(question),
      });
      if (cancelledRef.current) return;
      win.postMessage(
        { type: ANIMATION_MESSAGE_TYPE, token, animation },
        ANIMATION_VIEWER_URL,
      );
    } catch (err) {
      if (cancelledRef.current) return;
      const message = animationErrorMessage(err);
      win.postMessage(
        {
          type: ANIMATION_ERROR_MESSAGE_TYPE,
          token,
          message,
        },
        ANIMATION_VIEWER_URL,
      );
      setError(message);
    } finally {
      if (!cancelledRef.current) setIsLoading(false);
    }
  }, [
    token,
    problem,
    code,
    language,
    difficulty,
    lessonContext,
    initialCode,
    question,
  ]);

  const retry = useCallback(() => {
    cancelledRef.current = false;
    setError(null);
    // A fresh token re-mounts the iframe (key={token}), which re-fires `load`
    // and triggers a new generation attempt.
    setToken(crypto.randomUUID());
  }, []);

  const isDisabled = disabled || isLoading || !problem || !code;
  const title = question?.title || problem;

  return (
    <>
      <button
        type="button"
        onClick={handleClick}
        disabled={isDisabled}
        aria-label="Animate solution"
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium tracking-wide text-emerald-300/80 hover:text-emerald-200 bg-emerald-500/10 hover:bg-emerald-500/15 ring-1 ring-emerald-500/20 rounded-full transition-all disabled:opacity-40 disabled:pointer-events-none active:scale-[0.97]"
      >
        {isLoading ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : (
          <Play className="h-3.5 w-3.5" strokeWidth={2} />
        )}
        {isLoading ? "Generating…" : "Animate"}
      </button>
      <Dialog
        open={isOpen}
        onOpenChange={(open) => {
          if (!open) cancelledRef.current = true;
          setIsOpen(open);
        }}
      >
        <DialogContent className="w-[calc(100vw-2rem)]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 shrink-0 text-emerald-400/80" />
              <span className="truncate" title={title}>
                {title}
              </span>
            </DialogTitle>
            <p className="text-[11px] uppercase tracking-widest text-muted-foreground/40">
              Step-by-step algorithm trace
            </p>
          </DialogHeader>
          <div className="relative aspect-video w-full overflow-hidden rounded-lg border border-border bg-[#0b0f19]">
            {isLoading && !error && (
              <div
                role="status"
                aria-live="polite"
                className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 bg-[#0b0f19]/80 text-xs text-muted-foreground"
              >
                <Loader2 className="h-5 w-5 animate-spin text-emerald-400/80" />
                <span className="text-muted-foreground/80">
                  {GENERATION_PHASES[phaseIndex]}
                  <span aria-hidden="true">…</span>
                </span>
                <div className="flex items-center gap-1.5" aria-hidden="true">
                  {GENERATION_PHASES.map((_, i) => (
                    <span
                      key={i}
                      className={`h-1 w-6 rounded-full transition-colors ${
                        i === phaseIndex ? "bg-emerald-400/70" : "bg-white/10"
                      }`}
                    />
                  ))}
                </div>
              </div>
            )}
            {viewerUrl && (
              <iframe
                key={token}
                ref={iframeRef}
                title="Animation viewer"
                src={viewerUrl}
                onLoad={handleIframeLoad}
                className="h-full w-full"
                allowFullScreen
              />
            )}
          </div>
          {error && (
            <div
              role="alert"
              className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-destructive/25 bg-destructive/5 px-3 py-2.5"
            >
              <span className="text-[11px] leading-tight text-destructive/90">
                {error}
              </span>
              <button
                type="button"
                onClick={retry}
                className="inline-flex items-center gap-1.5 rounded-full bg-destructive/10 px-3 py-1.5 text-[11px] font-medium text-destructive/90 ring-1 ring-destructive/20 transition-all hover:bg-destructive/15 active:scale-[0.97]"
              >
                <RotateCcw className="h-3 w-3" />
                Try again
              </button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
