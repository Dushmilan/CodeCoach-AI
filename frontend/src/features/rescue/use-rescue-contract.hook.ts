"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { SubmitResponse } from "@/features/code-execution/code-execution.types";
import { RESCUE_CONFIG, tierThresholds } from "./rescue.config";
import { buildRescueCheckpoints } from "./rescue.checkpoints";
import { AbandonedProblem, RescueCheckpoint, RescueTier } from "./rescue.types";
import {
  removeAbandonedProblem,
  saveAbandonedProblem,
} from "./rescue.storage";

interface UseRescueContractOptions {
  questionId: string;
  questionTitle: string;
  testCases: Array<{
    input: string;
    expected_output: string;
    description?: string;
    hidden?: boolean;
  }>;
  lastSubmitResult: SubmitResponse | null;
}

interface UseRescueContractReturn {
  tier: RescueTier;
  isStuck: boolean;
  isSuppressed: boolean;
  checkpoints: RescueCheckpoint[];
  registerActivity: () => void;
  leaveMeAlone: () => void;
  resume: () => void;
  abandon: () => void;
}

/**
 * The "never-alone rescue contract" for the problem workspace.
 *
 * Detects a stuck learner (idle past a threshold on an unsolved problem)
 * and escalates through intervention tiers:
 *   - T1: open the solution flow map highlighting the blocked checkpoint
 *   - T2: offer a targeted AI coach message for the failing test
 *   - T3: offer "re-plan your path"
 *
 * Idle time is not counted while the tab is hidden, and any activity
 * (code change, run, submit, chat) resets the timer. A "Leave me alone"
 * toggle silences interventions for the session. Abandoning an unsolved
 * problem is captured in localStorage and resurfaced on /problems.
 */
export function useRescueContract({
  questionId,
  questionTitle,
  testCases,
  lastSubmitResult,
}: UseRescueContractOptions): UseRescueContractReturn {
  const lastActivityRef = useRef<number>(Date.now());
  const questionIdRef = useRef(questionId);
  const titleRef = useRef(questionTitle);
  const tierRef = useRef<RescueTier>("none");
  const solvedRef = useRef(false);

  const [tier, setTierState] = useState<RescueTier>("none");
  const [isSuppressed, setSuppressed] = useState(false);

  questionIdRef.current = questionId;
  titleRef.current = questionTitle;

  const checkpoints = useMemo(
    () => buildRescueCheckpoints(testCases, lastSubmitResult),
    [testCases, lastSubmitResult],
  );

  const setTier = useCallback((next: RescueTier) => {
    tierRef.current = next;
    setTierState(next);
  }, []);

  // Detect when the problem becomes solved (transition into solved state).
  const prevSolvedRef = useRef(false);
  useEffect(() => {
    const solved =
      !!lastSubmitResult &&
      lastSubmitResult.total > 0 &&
      lastSubmitResult.passed_count === lastSubmitResult.total;
    solvedRef.current = solved;
    if (solved && !prevSolvedRef.current) {
      setTier("none");
      removeAbandonedProblem(questionIdRef.current);
    }
    prevSolvedRef.current = solved;
  }, [lastSubmitResult, questionId, setTier]);

  const resetIdle = useCallback(() => {
    lastActivityRef.current = Date.now();
    setTier("none");
  }, [setTier]);

  const registerActivity = useCallback(() => {
    resetIdle();
  }, [resetIdle]);

  // Idle timer: escalate through T1 -> T2 -> T3.
  useEffect(() => {
    if (isSuppressed) return;
    const interval = window.setInterval(() => {
      if (solvedRef.current) return;
      // Do not count time while the tab is hidden.
      if (
        typeof document !== "undefined" &&
        document.visibilityState === "hidden"
      ) {
        return;
      }

      const idleMs = Date.now() - lastActivityRef.current;
      if (idleMs >= tierThresholds.t3) {
        setTier("t3");
      } else if (idleMs >= tierThresholds.t2) {
        setTier("t2");
      } else if (idleMs >= tierThresholds.t1) {
        setTier("t1");
      }
    }, RESCUE_CONFIG.checkIntervalMs);
    return () => window.clearInterval(interval);
  }, [isSuppressed, setTier]);

  // Reset the idle clock when the tab becomes visible again (hidden time
  // must not count toward "stuck").
  useEffect(() => {
    const onVisibility = () => {
      if (document.visibilityState === "visible") {
        lastActivityRef.current = Date.now();
      }
    };
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, []);

  const buildAbandonedProblem = useCallback((): AbandonedProblem => {
    return {
      questionId: questionIdRef.current,
      title: titleRef.current,
      stuckCheckpoint:
        buildRescueCheckpoints(testCases, lastSubmitResult).find(
          (c) => c.state === "current",
        )?.label ?? null,
      passedCount: lastSubmitResult?.passed_count ?? 0,
      total: lastSubmitResult?.total ?? testCases.length,
      abandonedAt: Date.now(),
    };
  }, [testCases, lastSubmitResult]);
  const buildAbandonedRef = useRef(buildAbandonedProblem);
  buildAbandonedRef.current = buildAbandonedProblem;

  // Capture + resurface abandoned problems on unmount (only if unsolved and
  // the learner actually made an attempt / was at risk of being stuck).
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (!solvedRef.current && tierRef.current !== "none") {
        saveAbandonedProblem(buildAbandonedRef.current());
      }
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, []);

  const leaveMeAlone = useCallback(() => {
    setSuppressed(true);
    setTier("none");
  }, [setTier]);

  const resume = useCallback(() => {
    setSuppressed(false);
    resetIdle();
  }, [resetIdle]);

  const abandon = useCallback(() => {
    if (solvedRef.current) return;
    saveAbandonedProblem(buildAbandonedProblem());
  }, [buildAbandonedProblem]);

  return {
    tier,
    isStuck: tier !== "none",
    isSuppressed,
    checkpoints,
    registerActivity,
    leaveMeAlone,
    resume,
    abandon,
  };
}
